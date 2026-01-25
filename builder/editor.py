#!/usr/bin/env python3
"""
Exam Engine Editor - Multi-Section Version
Manages multiple subjects/sections with chapters.json structure
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path
import re

class ExamEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Exam Engine Editor")
        self.root.geometry("1200x700")
        
        self.base_path = Path(__file__).parent.parent
        self.data_path = self.base_path / "data"
        self.config_path = self.base_path / "config"
        
        self.sections = []
        self.current_section = None
        self.current_section_idx = None
        self.chapters = []
        self.current_chapter_idx = None
        
        self.setup_ui()
        self.load_sections()
        
    def setup_ui(self):
        """Setup main UI with improved layout"""
        # Top toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        ttk.Button(toolbar, text="💾 Save All", command=self.save_all, 
                  width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="⚙️ Configure Engine", command=self.generate_js_config,
                  width=18).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="🔄 Refresh", command=self.refresh_all,
                  width=12).pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(toolbar, text="Ready", foreground="green")
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # Main container with PanedWindow
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Left Panel - Sections
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
        # Sections header
        sections_header = ttk.Frame(left_frame)
        sections_header.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(sections_header, text="📚 Sections", 
                 font=("", 11, "bold")).pack(side=tk.LEFT)
        
        ttk.Button(sections_header, text="➕", command=self.add_section,
                  width=3).pack(side=tk.RIGHT, padx=2)
        ttk.Button(sections_header, text="🗑️", command=self.delete_section,
                  width=3).pack(side=tk.RIGHT, padx=2)
        
        # Sections table
        sections_scroll = ttk.Scrollbar(left_frame, orient=tk.VERTICAL)
        
        self.sections_tree = ttk.Treeview(left_frame, 
                                         columns=("Name", "ID", "Path"),
                                         show="headings",
                                         yscrollcommand=sections_scroll.set,
                                         selectmode="browse",
                                         height=15)
        
        sections_scroll.config(command=self.sections_tree.yview)
        
        self.sections_tree.heading("Name", text="Name")
        self.sections_tree.heading("ID", text="ID")
        self.sections_tree.heading("Path", text="Path")
        
        self.sections_tree.column("Name", width=150)
        self.sections_tree.column("ID", width=80)
        self.sections_tree.column("Path", width=120)
        
        self.sections_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sections_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.sections_tree.bind("<<TreeviewSelect>>", self.on_section_select)
        
        # Right Panel - Chapters
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)
        
        # Chapters header
        chapters_header = ttk.Frame(right_frame)
        chapters_header.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(chapters_header, text="📖 Chapters", 
                 font=("", 11, "bold")).pack(side=tk.LEFT)
        
        ttk.Button(chapters_header, text="➕", command=self.add_chapter,
                  width=3).pack(side=tk.RIGHT, padx=2)
        ttk.Button(chapters_header, text="🗑️", command=self.delete_chapter,
                  width=3).pack(side=tk.RIGHT, padx=2)
        
        # Chapters table
        chapters_scroll = ttk.Scrollbar(right_frame, orient=tk.VERTICAL)
        
        self.chapters_tree = ttk.Treeview(right_frame,
                                         columns=("ID", "Name", "Questions", "File"),
                                         show="headings",
                                         yscrollcommand=chapters_scroll.set,
                                         selectmode="browse",
                                         height=10)
        
        chapters_scroll.config(command=self.chapters_tree.yview)
        
        self.chapters_tree.heading("ID", text="ID")
        self.chapters_tree.heading("Name", text="Chapter Name")
        self.chapters_tree.heading("Questions", text="Questions")
        self.chapters_tree.heading("File", text="File")
        
        self.chapters_tree.column("ID", width=50)
        self.chapters_tree.column("Name", width=250)
        self.chapters_tree.column("Questions", width=80)
        self.chapters_tree.column("File", width=150)
        
        self.chapters_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        chapters_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.chapters_tree.bind("<<TreeviewSelect>>", self.on_chapter_select)
        
        # Chapter editor panel
        editor_frame = ttk.LabelFrame(right_frame, text="✏️ Edit Chapter", padding=15)
        editor_frame.pack(fill=tk.X, pady=(10, 0))
        
        # ID
        ttk.Label(editor_frame, text="ID:", font=("", 9, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=8)
        self.ch_id = ttk.Entry(editor_frame, width=15)
        self.ch_id.grid(row=0, column=1, sticky=tk.W, padx=10, pady=8)
        
        # Name
        ttk.Label(editor_frame, text="Name:", font=("", 9, "bold")).grid(
            row=0, column=2, sticky=tk.W, pady=8, padx=(20, 0))
        self.ch_name = ttk.Entry(editor_frame, width=40)
        self.ch_name.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=10, pady=8)
        
        # Questions count
        ttk.Label(editor_frame, text="Questions:", font=("", 9, "bold")).grid(
            row=1, column=0, sticky=tk.W, pady=8)
        self.ch_count = ttk.Entry(editor_frame, width=15)
        self.ch_count.grid(row=1, column=1, sticky=tk.W, padx=10, pady=8)
        
        # Update button
        self.update_chapter_btn = ttk.Button(editor_frame, text="✓ Update Chapter",
                                            command=self.update_chapter,
                                            state="disabled")
        self.update_chapter_btn.grid(row=1, column=3, sticky=tk.E, padx=10, pady=8)
        
        editor_frame.columnconfigure(3, weight=1)
    
    def update_status(self, message, color="green"):
        """Update status message"""
        self.status_label.config(text=message, foreground=color)
        self.root.after(3000, lambda: self.status_label.config(text="Ready", foreground="green"))
    
    def refresh_all(self):
        """Refresh all data"""
        self.load_sections()
        if self.current_section:
            self.load_chapters()
        self.update_status("Refreshed", "blue")
    
    def load_sections(self):
        """Load sections from config"""
        try:
            config_file = self.config_path / "sections.json"
            with open(config_file) as f:
                self.sections = json.load(f)
        except:
            self.sections = []
        
        self.refresh_sections_tree()
    
    def refresh_sections_tree(self):
        """Refresh sections tree"""
        for item in self.sections_tree.get_children():
            self.sections_tree.delete(item)
        
        for idx, section in enumerate(self.sections):
            self.sections_tree.insert("", tk.END, iid=str(idx), values=(
                section['name'],
                section['id'],
                section.get('path', '')
            ))
    
    def on_section_select(self, event):
        """Handle section selection"""
        selection = self.sections_tree.selection()
        if selection:
            self.current_section_idx = int(selection[0])
            self.current_section = self.sections[self.current_section_idx]['id']
            self.load_chapters()
            self.update_status(f"Selected: {self.sections[self.current_section_idx]['name']}", "blue")
    
    def load_chapters(self):
        """Load chapters for current section"""
        if not self.current_section:
            self.chapters = []
            self.refresh_chapters_tree()
            return
        
        section = next((s for s in self.sections if s['id'] == self.current_section), None)
        if not section:
            return
        
        try:
            ch_file = self.base_path / f"{section['path']}" / "chapters.json"
            with open(ch_file) as f:
                self.chapters = json.load(f)
        except:
            self.chapters = []
        
        self.refresh_chapters_tree()
    
    def refresh_chapters_tree(self):
        """Refresh chapters tree"""
        for item in self.chapters_tree.get_children():
            self.chapters_tree.delete(item)
        
        for idx, chapter in enumerate(self.chapters):
            self.chapters_tree.insert("", tk.END, iid=str(idx), values=(
                chapter.get('id', ''),
                chapter.get('name', ''),
                chapter.get('q', 0),
                chapter.get('file', '')
            ))
    
    def on_chapter_select(self, event):
        """Handle chapter selection"""
        selection = self.chapters_tree.selection()
        if selection:
            self.current_chapter_idx = int(selection[0])
            chapter = self.chapters[self.current_chapter_idx]
            
            self.ch_id.delete(0, tk.END)
            self.ch_id.insert(0, chapter.get('id', ''))
            
            self.ch_name.delete(0, tk.END)
            self.ch_name.insert(0, chapter.get('name', ''))
            
            self.ch_count.delete(0, tk.END)
            self.ch_count.insert(0, str(chapter.get('q', 0)))
            
            self.update_chapter_btn.config(state="normal")
        else:
            self.current_chapter_idx = None
            self.update_chapter_btn.config(state="disabled")
    
    def update_chapter(self):
        """Update the selected chapter"""
        if self.current_chapter_idx is None:
            messagebox.showwarning("Warning", "No chapter selected")
            return
        
        chapter = self.chapters[self.current_chapter_idx]
        chapter['id'] = self.ch_id.get()
        chapter['name'] = self.ch_name.get()
        try:
            chapter['q'] = int(self.ch_count.get())
        except:
            chapter['q'] = 0
        
        self.refresh_chapters_tree()
        self.chapters_tree.selection_set(str(self.current_chapter_idx))
        self.update_status("Chapter updated (not saved yet)", "orange")
    
    def add_section(self):
        """Add new section"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Section")
        dialog.geometry("450x280")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Section ID:", font=("", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=10)
        sec_id = ttk.Entry(frame, width=30)
        sec_id.grid(row=0, column=1, pady=10, padx=10)
        sec_id.focus()
        
        ttk.Label(frame, text="Section Name:", font=("", 10, "bold")).grid(
            row=1, column=0, sticky=tk.W, pady=10)
        sec_name = ttk.Entry(frame, width=30)
        sec_name.grid(row=1, column=1, pady=10, padx=10)
        
        ttk.Label(frame, text="Data Path:", font=("", 10, "bold")).grid(
            row=2, column=0, sticky=tk.W, pady=10)
        sec_path = ttk.Entry(frame, width=30)
        sec_path.insert(0, "data/")
        sec_path.grid(row=2, column=1, pady=10, padx=10)
        
        ttk.Label(frame, text="Description:", font=("", 10, "bold")).grid(
            row=3, column=0, sticky=tk.W, pady=10)
        sec_desc = ttk.Entry(frame, width=30)
        sec_desc.grid(row=3, column=1, pady=10, padx=10)
        
        def save():
            if not sec_id.get() or not sec_name.get():
                messagebox.showerror("Error", "ID and Name are required")
                return
            
            new_section = {
                "id": sec_id.get(),
                "name": sec_name.get(),
                "path": sec_path.get() + sec_id.get(),
                "description": sec_desc.get()
            }
            
            # Create directory and init chapters.json
            try:
                full_path = self.base_path / new_section['path']
                full_path.mkdir(parents=True, exist_ok=True)
                ch_file = full_path / "chapters.json"
                if not ch_file.exists():
                    with open(ch_file, 'w') as f:
                        json.dump([], f)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create directory: {e}")
                return

            self.sections.append(new_section)
            self.save_sections()
            self.load_sections()
            self.update_status(f"Added section: {sec_id.get()}", "green")
            dialog.destroy()
        
        ttk.Button(frame, text="✓ Create Section", command=save, 
                  width=20).grid(row=4, column=0, columnspan=2, pady=20)
        
        dialog.bind('<Return>', lambda e: save())
    
    def delete_section(self):
        """Delete selected section"""
        if self.current_section_idx is None:
            messagebox.showwarning("Warning", "Select a section first")
            return
        
        section = self.sections[self.current_section_idx]
        if messagebox.askyesno("Confirm Delete", 
                              f"Delete section '{section['name']}'?\n\nThis will not delete files, only remove from config."):
            del self.sections[self.current_section_idx]
            self.current_section = None
            self.current_section_idx = None
            self.save_sections()
            self.load_sections()
            self.chapters = []
            self.refresh_chapters_tree()
            self.update_status("Section deleted", "orange")
    
    def add_chapter(self):
        """Add new chapter"""
        if not self.current_section:
            messagebox.showwarning("Warning", "Select a section first")
            return
        
        new_chapter = {
            "id": str(len(self.chapters) + 1),
            "name": "New Chapter",
            "q": 0,
            "file": f"chapter{len(self.chapters) + 1}.json"
        }
        self.chapters.append(new_chapter)
        self.refresh_chapters_tree()
        self.update_status("Chapter added (click Save All)", "orange")
    
    def delete_chapter(self):
        """Delete chapter"""
        if self.current_chapter_idx is None:
            messagebox.showwarning("Warning", "Select a chapter first")
            return
        
        chapter = self.chapters[self.current_chapter_idx]
        if messagebox.askyesno("Confirm Delete", 
                              f"Delete chapter '{chapter['name']}'?\n\nThis will not delete the file."):
            del self.chapters[self.current_chapter_idx]
            self.current_chapter_idx = None
            self.refresh_chapters_tree()
            self.ch_id.delete(0, tk.END)
            self.ch_name.delete(0, tk.END)
            self.ch_count.delete(0, tk.END)
            self.update_chapter_btn.config(state="disabled")
            self.update_status("Chapter deleted (click Save All)", "orange")
    
    def save_chapter(self):
        """Save chapter changes"""
        if not self.current_section:
            return
        
        section = next((s for s in self.sections if s['id'] == self.current_section), None)
        if not section:
            return
        
        try:
            ch_file = self.base_path / f"{section['path']}" / "chapters.json"
            ch_file.parent.mkdir(parents=True, exist_ok=True)
            with open(ch_file, 'w') as f:
                json.dump(self.chapters, f, indent=2)
            self.update_status("Chapters saved", "green")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def save_sections(self):
        """Save sections to config"""
        try:
            self.config_path.mkdir(parents=True, exist_ok=True)
            config_file = self.config_path / "sections.json"
            with open(config_file, 'w') as f:
                json.dump(self.sections, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def save_all(self):
        """Save everything"""
        self.save_sections()
        self.save_chapter()
        messagebox.showinfo("Success", "All changes saved successfully!")
        self.update_status("✓ All saved", "green")
        
    def generate_js_config(self):
        """Generate js/exam-config.js from current sections and chapters"""
        try:
            full_config = []
            
            for section in self.sections:
                sec_data = {
                    "id": section['id'],
                    "name": section['name'],
                    "description": section.get('description', ''),
                    "path": section['path'],
                    "chapters": []
                }
                
                # AUTO-SYNC: Update chapters.json from directory content
                sec_path = self.base_path / section['path']
                if sec_path.exists():
                     chapter_files = sorted(sec_path.glob("*.json"))
                     
                     # Sort helper
                     def get_chapter_num(path):
                        match = re.search(r'chapter(\d+)', path.name)
                        return int(match.group(1)) if match else 999
                     
                     chapter_files.sort(key=get_chapter_num)
                     
                     synced_chapters = []
                     for ch_file in chapter_files:
                         if ch_file.name == "chapters.json":
                             continue
                             
                         try:
                             with open(ch_file, 'r', encoding='utf-8') as f:
                                 content = json.load(f)
                                 
                             data_obj = content[0] if isinstance(content, list) and content else content
                             if isinstance(content, list) and not content: 
                                 data_obj = {}
                             
                             f_match = re.search(r'chapter(\d+)', ch_file.name)
                             if f_match:
                                 c_id = f_match.group(1)
                             else:
                                 c_id = str(data_obj.get("params", {}).get("chapter", ch_file.stem))
                                 
                             c_title = data_obj.get("title", ch_file.stem)
                             c_title = c_title.replace(f"Chapter {c_id} ", "").strip()
                             
                             c_q = len(data_obj.get("questions", []))
                             if not c_q and 'totalQuestions' in data_obj:
                                 c_q = data_obj['totalQuestions']
                                 
                             synced_chapters.append({
                                 "id": str(c_id),
                                 "name": c_title,
                                 "q": c_q,
                                 "file": ch_file.name
                             })
                         except Exception as e:
                             print(f"Skipping {ch_file}: {e}")
                             
                     ch_json_path = sec_path / "chapters.json"
                     try:
                         with open(ch_json_path, 'w', encoding='utf-8') as f:
                             json.dump(synced_chapters, f, indent=2)
                     except Exception as e:
                         print(f"Failed to save chapters.json: {e}")

                ch_file = self.base_path / section['path'] / "chapters.json"
                if ch_file.exists():
                    try:
                        with open(ch_file) as f:
                            chapters = json.load(f)
                            for ch in chapters:
                                ch['file'] = f"{section['path']}/{ch.get('file', '')}"
                                if 'q' not in ch or ch['q'] == 0:
                                     try:
                                         q_path = self.base_path / section['path'] / ch.get('file', '')
                                         with open(q_path) as qf:
                                             q_data = json.load(qf)
                                             if isinstance(q_data, list):
                                                 q_data = q_data[0]
                                             ch['q'] = len(q_data.get('questions', []))
                                     except:
                                         pass
                            sec_data["chapters"] = chapters
                    except:
                        sec_data["chapters"] = []
                
                full_config.append(sec_data)
            
            js_path = self.base_path / "js" / "exam-config.js"
            js_path.parent.mkdir(parents=True, exist_ok=True)
            with open(js_path, 'w', encoding='utf-8') as f:
                json_str = json.dumps(full_config, indent=2)
                f.write(f"const EXAM_CONFIG = {json_str};\n")
                
            messagebox.showinfo("Success", 
                              f"Engine Configured Successfully!\n\nGenerated: {js_path.relative_to(self.base_path)}")
            self.update_status("✓ Engine configured", "green")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate config: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ExamEditor(root)
    root.mainloop()