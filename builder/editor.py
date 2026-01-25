#!/usr/bin/env python3
"""
Exam Engine Editor - Multi-Section Version
Manages multiple subjects/sections with chapters.json structure
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import json
from pathlib import Path
import re

class ExamEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Exam Engine Editor")
        self.root.geometry("1000x600")
        
        self.base_path = Path(__file__).parent.parent
        self.data_path = self.base_path / "data"
        self.config_path = self.base_path / "config"
        
        self.sections = []
        self.current_section = None
        self.chapters = []
        
        self.setup_ui()
        self.load_sections()
        
    def setup_ui(self):
        """Setup main UI"""
        # Menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save All", command=self.save_all)
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools Menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Configure Engine", command=self.generate_js_config)
        
        # Main frame
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)
        
        # Left: Sections
        left = ttk.LabelFrame(main, text="Sections", padding=10)
        left.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        
        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(btn_frame, text="+ Add", command=self.add_section).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="- Delete", command=self.delete_section).pack(side=tk.LEFT, padx=2)
        
        self.sections_list = tk.Listbox(left, height=20, width=25)
        self.sections_list.pack(fill=tk.BOTH, expand=True)
        self.sections_list.bind('<<ListboxSelect>>', self.on_section_select)
        
        # Right: Details
        right = ttk.LabelFrame(main, text="Chapters", padding=10)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        btn_frame2 = ttk.Frame(right)
        btn_frame2.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(btn_frame2, text="+ Add", command=self.add_chapter).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame2, text="- Delete", command=self.delete_chapter).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame2, text="Save", command=self.save_chapter).pack(side=tk.LEFT, padx=2)
        
        self.chapters_list = tk.Listbox(right, height=12, width=30)
        self.chapters_list.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.chapters_list.bind('<<ListboxSelect>>', self.on_chapter_select)
        
        # Chapter details
        detail_frame = ttk.Frame(right)
        detail_frame.pack(fill=tk.X)
        
        ttk.Label(detail_frame, text="ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.ch_id = ttk.Entry(detail_frame, width=20)
        self.ch_id.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        ttk.Label(detail_frame, text="Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.ch_name = ttk.Entry(detail_frame, width=40)
        self.ch_name.grid(row=1, column=1, sticky=tk.W, padx=10)
        
        ttk.Label(detail_frame, text="Questions:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.ch_count = ttk.Entry(detail_frame, width=20)
        self.ch_count.grid(row=2, column=1, sticky=tk.W, padx=10)
    
    def load_sections(self):
        """Load sections from config"""
        try:
            config_file = self.config_path / "sections.json"
            with open(config_file) as f:
                self.sections = json.load(f)
        except:
            self.sections = []
        
        self.refresh_sections_list()
    
    def refresh_sections_list(self):
        """Refresh sections listbox"""
        self.sections_list.delete(0, tk.END)
        for s in self.sections:
            self.sections_list.insert(tk.END, f"{s['name']} ({s['id']})")
    
    def on_section_select(self, evt):
        """Section selected"""
        sel = self.sections_list.curselection()
        if sel:
            self.current_section = self.sections[sel[0]]['id']
            self.load_chapters()
    
    def load_chapters(self):
        """Load chapters for current section"""
        if not self.current_section:
            self.chapters = []
            self.chapters_list.delete(0, tk.END)
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
        
        self.refresh_chapters_list()
    
    def refresh_chapters_list(self):
        """Refresh chapters listbox"""
        self.chapters_list.delete(0, tk.END)
        for ch in self.chapters:
            self.chapters_list.insert(tk.END, f"Chapter {ch['id']}: {ch['name']} ({ch.get('q', 0)} Q)")
    
    def on_chapter_select(self, evt):
        """Chapter selected"""
        sel = self.chapters_list.curselection()
        if sel:
            ch = self.chapters[sel[0]]
            self.ch_id.delete(0, tk.END)
            self.ch_id.insert(0, ch['id'])
            self.ch_name.delete(0, tk.END)
            self.ch_name.insert(0, ch['name'])
            self.ch_count.delete(0, tk.END)
            self.ch_count.insert(0, str(ch.get('q', 0)))
    
    def add_section(self):
        """Add new section"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Section")
        dialog.geometry("300x200")
        
        ttk.Label(dialog, text="Section ID:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        sec_id = ttk.Entry(dialog, width=20)
        sec_id.grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Section Name:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        sec_name = ttk.Entry(dialog, width=20)
        sec_name.grid(row=1, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Data Path:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        sec_path = ttk.Entry(dialog, width=20)
        sec_path.insert(0, "data/")
        sec_path.grid(row=2, column=1, padx=10, pady=10)
        
        def save():
            if not sec_id.get() or not sec_name.get():
                messagebox.showerror("Error", "Fill all fields")
                return
            
            new_section = {
                "id": sec_id.get(),
                "name": sec_name.get(),
                "path": sec_path.get() + sec_id.get(),
                "description": ""
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
            dialog.destroy()
        
        ttk.Button(dialog, text="Save", command=save).grid(row=3, column=1, padx=10, pady=10)
    
    def delete_section(self):
        """Delete selected section"""
        sel = self.sections_list.curselection()
        if not sel:
            messagebox.showwarning("Warning", "Select a section first")
            return
        
        if messagebox.askyesno("Confirm", "Delete this section?"):
            del self.sections[sel[0]]
            self.save_sections()
            self.load_sections()
    
    def add_chapter(self):
        """Add new chapter"""
        if not self.current_section:
            messagebox.showwarning("Warning", "Select a section first")
            return
        
        new_chapter = {
            "id": str(len(self.chapters) + 1),
            "name": "New Chapter",
            "q": 0
        }
        self.chapters.append(new_chapter)
        self.save_chapter()
    
    def delete_chapter(self):
        """Delete chapter"""
        sel = self.chapters_list.curselection()
        if not sel:
            messagebox.showwarning("Warning", "Select a chapter first")
            return
        
        if messagebox.askyesno("Confirm", "Delete this chapter?"):
            del self.chapters[sel[0]]
            self.save_chapter()
    
    def save_chapter(self):
        """Save chapter changes"""
        sel = self.chapters_list.curselection()
        if sel:
            ch = self.chapters[sel[0]]
            ch['id'] = self.ch_id.get()
            ch['name'] = self.ch_name.get()
            try:
                ch['q'] = int(self.ch_count.get())
            except:
                ch['q'] = 0
        
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
            messagebox.showinfo("Success", "Chapters saved")
            self.refresh_chapters_list()
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
        messagebox.showinfo("Success", "All changes saved")
        
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
                             # Try to read info from file
                             # Handle list or dict
                             with open(ch_file, 'r', encoding='utf-8') as f:
                                 content = json.load(f)
                                 
                             data_obj = content[0] if isinstance(content, list) and content else content
                             if isinstance(content, list) and not content: data_obj = {}
                             
                             # Extract ID from filename or content
                             # Prefer filename number if available
                             f_match = re.search(r'chapter(\d+)', ch_file.name)
                             if f_match:
                                 c_id = f_match.group(1)
                             else:
                                 c_id = str(data_obj.get("params", {}).get("chapter", ch_file.stem))
                                 
                             # Extract Title
                             c_title = data_obj.get("title", ch_file.stem)
                             # Clean title if it contains "Chapter X" prefix from book data
                             c_title = c_title.replace(f"Chapter {c_id} ", "").strip()
                             
                             # Count
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
                             
                     # Write updated chapters.json
                     ch_json_path = sec_path / "chapters.json"
                     try:
                         with open(ch_json_path, 'w', encoding='utf-8') as f:
                             json.dump(synced_chapters, f, indent=2)
                     except Exception as e:
                         print(f"Failed to save chapters.json: {e}")

                # Load chapters for config generation
                ch_file = self.base_path / section['path'] / "chapters.json"
                if ch_file.exists():
                    try:
                        with open(ch_file) as f:
                            chapters = json.load(f)
                            # Add path prefix to chapter file
                            for ch in chapters:
                                ch['file'] = f"{section['path']}/{ch.get('file', '')}"
                                # Calculate total questions if missing
                                if 'q' not in ch or ch['q'] == 0:
                                     # Try to read actual file
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
            
            # Write key to js/exam-config.js
            js_path = self.base_path / "js" / "exam-config.js"
            with open(js_path, 'w', encoding='utf-8') as f:
                json_str = json.dumps(full_config, indent=2)
                f.write(f"const EXAM_CONFIG = {json_str};\n")
                
            messagebox.showinfo("Success", f"Engine Configured!\nGenerated {js_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate config: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ExamEditor(root)
    root.mainloop()
