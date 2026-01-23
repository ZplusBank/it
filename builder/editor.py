#!/usr/bin/env python3
"""
Exam Engine GUI Editor
A user-friendly editor for managing exam sections, chapters, and questions.
Specially designed to edit loadSections in exam-engine.js and manage Java2 data.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from pathlib import Path
import re
from typing import List, Dict, Any

class ExamEngineEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Exam Engine Editor")
        self.root.geometry("1200x700")
        self.root.configure(bg="#f0f0f0")
        
        # Base paths
        self.base_path = Path(__file__).parent.parent
        self.data_path = self.base_path / "data"
        self.js_path = self.base_path / "js" / "exam-engine.js"
        
        # Data storage
        self.sections = []
        self.current_section = None
        
        # Create UI
        self.setup_ui()
        self.load_sections()
        
    def setup_ui(self):
        """Setup the main UI layout"""
        # Menu Bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Sync All Chapters", command=self.sync_all_chapters)
        file_menu.add_command(label="Save Changes to JS", command=self.save_all)
        file_menu.add_command(label="Load from JS File", command=self.load_from_js)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
        # Status bar
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_label = ttk.Label(self.status_frame, text="Ready", relief=tk.SUNKEN)
        self.status_label.pack(fill=tk.X)
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Sections list
        left_panel = ttk.Frame(main_frame, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        ttk.Label(left_panel, text="Sections", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        
        # Section buttons frame
        button_frame = ttk.Frame(left_panel)
        button_frame.pack(fill=tk.X, pady=(5, 10))
        ttk.Button(button_frame, text="Sync All", command=self.sync_all_chapters).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="+ Add", command=self.add_section).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="- Delete", command=self.delete_section).pack(side=tk.LEFT, padx=2)
        
        # Info label
        self.info_label = ttk.Label(left_panel, text="", font=("Arial", 9), foreground="blue")
        self.info_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Sections listbox
        self.sections_listbox = tk.Listbox(left_panel, height=15, width=35)
        self.sections_listbox.pack(fill=tk.BOTH, expand=True)
        self.sections_listbox.bind('<<ListboxSelect>>', self.on_section_select)
        
        # Scrollbar for listbox
        scrollbar = ttk.Scrollbar(left_panel, orient=tk.VERTICAL, command=self.sections_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sections_listbox.config(yscrollcommand=scrollbar.set)
        
        # Right panel - Details
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        ttk.Label(right_panel, text="Section Details", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Tab 1: Section Info
        self.info_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.info_tab, text="Info")
        self.setup_info_tab()
        
        # Tab 2: Chapters
        self.chapters_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.chapters_tab, text="Chapters")
        self.setup_chapters_tab()
        
        # Tab 3: Code Preview
        self.json_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.json_tab, text="JS Code Preview")
        self.setup_json_tab()
        
    def setup_info_tab(self):
        """Setup section information editor tab"""
        frame = ttk.Frame(self.info_tab, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # ID
        ttk.Label(frame, text="ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.info_id = ttk.Entry(frame, width=30)
        self.info_id.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Title
        ttk.Label(frame, text="Title:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.info_title = ttk.Entry(frame, width=30)
        self.info_title.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Icon
        ttk.Label(frame, text="Icon:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.info_icon = ttk.Entry(frame, width=30)
        self.info_icon.grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Folder
        ttk.Label(frame, text="Folder:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.info_folder = ttk.Entry(frame, width=30)
        self.info_folder.grid(row=3, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Status
        ttk.Label(frame, text="Status:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.info_status = ttk.Combobox(frame, values=["not-started", "in-progress", "completed"], width=27)
        self.info_status.grid(row=4, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Save button
        ttk.Button(frame, text="Save Section Info", command=self.save_section_info).grid(row=5, column=1, sticky=tk.W, padx=10, pady=15)
        
    def setup_chapters_tab(self):
        """Setup chapters editor tab"""
        frame = ttk.Frame(self.chapters_tab, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Chapters list
        ttk.Label(frame, text="Chapters:").pack(anchor=tk.W)
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(5, 10))
        ttk.Button(button_frame, text="+ Add Chapter", command=self.add_chapter).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="- Delete Chapter", command=self.delete_chapter).pack(side=tk.LEFT, padx=2)
        
        self.chapters_listbox = tk.Listbox(frame, height=8)
        self.chapters_listbox.pack(fill=tk.BOTH, expand=True)
        self.chapters_listbox.bind('<<ListboxSelect>>', self.on_chapter_select)
        
        # Chapter details
        ttk.Label(frame, text="Chapter Details:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        detail_frame = ttk.Frame(frame)
        detail_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(detail_frame, text="ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.chapter_id = ttk.Entry(detail_frame, width=30)
        self.chapter_id.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        ttk.Label(detail_frame, text="Title:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.chapter_title = ttk.Entry(detail_frame, width=30)
        self.chapter_title.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        ttk.Label(detail_frame, text="File:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.chapter_file = ttk.Entry(detail_frame, width=30)
        self.chapter_file.grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)
        
        ttk.Label(detail_frame, text="Questions:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.chapter_questions = ttk.Entry(detail_frame, width=30)
        self.chapter_questions.grid(row=3, column=1, sticky=tk.W, padx=10, pady=5)
        
        ttk.Button(detail_frame, text="Save Chapter", command=self.save_chapter).grid(row=4, column=1, sticky=tk.W, padx=10, pady=10)
        
    def setup_json_tab(self):
        """Setup JavaScript code preview tab"""
        frame = ttk.Frame(self.json_tab, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Generated JavaScript Code:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # Text editor
        self.json_text = tk.Text(frame, height=20, width=80)
        self.json_text.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.json_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.json_text.config(yscrollcommand=scrollbar.set)
        
        # Save button
        ttk.Button(frame, text="Save to exam-engine.js", command=self.save_to_js).pack(anchor=tk.W, pady=(0, 10))
        
    def load_sections(self):
        """Load sections from the sections.json or reconstruct from data folders"""
        self.sections = []
        
        # Check for java2 folder
        java2_path = self.data_path / "java2"
        if java2_path.exists():
            chapters = []
            # Scan ALL JSON files in the java2 folder
            for json_file in sorted(java2_path.glob("*.json")):
                # Read totalQuestions from JSON file
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list) and len(data) > 0:
                            # Try to get totalQuestions from the data
                            question_count = data[0].get('totalQuestions', None)
                            # Fallback to counting questions array if totalQuestions not found
                            if question_count is None:
                                questions = data[0].get('questions', [])
                                question_count = len(questions)
                        else:
                            question_count = 0
                except:
                    question_count = 0
                
                chapter_name = json_file.stem
                chapters.append({
                    'id': chapter_name,
                    'title': f'Chapter {chapter_name.replace("chapter", "")}',
                    'file': json_file.name,
                    'questions': question_count
                })
            
            section = {
                'id': 'java2',
                'title': 'Java 2',
                'icon': '🎯',
                'folder': 'java2',
                'chapters': chapters,
                'totalQuestions': sum(c['questions'] for c in chapters),
                'status': 'not-started'
            }
            self.sections.append(section)
            
            # Update status
            total_chapters = len(chapters)
            total_questions = sum(c['questions'] for c in chapters)
            self.update_status(f"Loaded: {total_chapters} chapters, {total_questions} total questions")
        
        self.refresh_sections_listbox()
        
    def refresh_sections_listbox(self):
        """Refresh the sections listbox"""
        self.sections_listbox.delete(0, tk.END)
        for section in self.sections:
            display_text = f"{section['title']} ({section['folder']}) - {section['totalQuestions']} questions"
            self.sections_listbox.insert(tk.END, display_text)
        
        # Update info label
        if self.sections:
            section = self.sections[0]
            self.info_label.config(text=f"✓ {len(section['chapters'])} chapters available")
    
    def on_section_select(self, event):
        """Handle section selection"""
        selection = self.sections_listbox.curselection()
        if not selection:
            return
        
        self.current_section = self.sections[selection[0]]
        self.update_info_tab()
        self.update_chapters_tab()
        self.update_json_tab()
    
    def update_info_tab(self):
        """Update info tab with current section"""
        if not self.current_section:
            return
        
        self.info_id.delete(0, tk.END)
        self.info_id.insert(0, self.current_section['id'])
        
        self.info_title.delete(0, tk.END)
        self.info_title.insert(0, self.current_section['title'])
        
        self.info_icon.delete(0, tk.END)
        self.info_icon.insert(0, self.current_section['icon'])
        
        self.info_folder.delete(0, tk.END)
        self.info_folder.insert(0, self.current_section['folder'])
        
        self.info_status.set(self.current_section['status'])
    
    def update_chapters_tab(self):
        """Update chapters tab with current section's chapters"""
        self.chapters_listbox.delete(0, tk.END)
        # Clear chapter details
        self.chapter_id.delete(0, tk.END)
        self.chapter_title.delete(0, tk.END)
        self.chapter_file.delete(0, tk.END)
        self.chapter_questions.delete(0, tk.END)
        
        if self.current_section:
            for chapter in self.current_section.get('chapters', []):
                display_text = f"{chapter['title']} ({chapter['questions']} Q)"
                self.chapters_listbox.insert(tk.END, display_text)
    
    def update_json_tab(self):
        """Update JS code preview tab with generated code"""
        if not self.current_section:
            return
        
        self.json_text.delete(1.0, tk.END)
        # Show the generated JavaScript code
        code = self.generate_loadSections()
        self.json_text.insert(1.0, code)
    
    def on_chapter_select(self, event=None):
        """Handle chapter selection"""
        selection = self.chapters_listbox.curselection()
        if not selection:
            return
        
        if not self.current_section or not self.current_section.get('chapters'):
            messagebox.showwarning("Warning", "No section selected. Please select a section first.")
            return
        
        chapter = self.current_section['chapters'][selection[0]]
        self.chapter_id.delete(0, tk.END)
        self.chapter_id.insert(0, chapter['id'])
        
        self.chapter_title.delete(0, tk.END)
        self.chapter_title.insert(0, chapter['title'])
        
        self.chapter_file.delete(0, tk.END)
        self.chapter_file.insert(0, chapter['file'])
        
        self.chapter_questions.delete(0, tk.END)
        self.chapter_questions.insert(0, str(chapter['questions']))
    
    def add_section(self):
        """Add a new section"""
        dialog = tk.Toplevel(self.root)
        dialog.title("New Section")
        dialog.geometry("400x200")
        
        ttk.Label(dialog, text="ID:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        entry_id = ttk.Entry(dialog, width=30)
        entry_id.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Title:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        entry_title = ttk.Entry(dialog, width=30)
        entry_title.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Icon:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        entry_icon = ttk.Entry(dialog, width=30)
        entry_icon.grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Folder:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        entry_folder = ttk.Entry(dialog, width=30)
        entry_folder.grid(row=3, column=1, padx=10, pady=5)
        
        def create():
            new_section = {
                'id': entry_id.get(),
                'title': entry_title.get(),
                'icon': entry_icon.get(),
                'folder': entry_folder.get(),
                'chapters': [],
                'totalQuestions': 0,
                'status': 'not-started'
            }
            self.sections.append(new_section)
            self.refresh_sections_listbox()
            dialog.destroy()
        
        ttk.Button(dialog, text="Create", command=create).grid(row=4, column=1, sticky=tk.W, padx=10, pady=10)
    
    def delete_section(self):
        """Delete current section"""
        if not self.current_section:
            messagebox.showwarning("Warning", "No section selected")
            return
        
        if messagebox.askyesno("Confirm", f"Delete '{self.current_section['title']}'?"):
            self.sections.remove(self.current_section)
            self.current_section = None
            self.refresh_sections_listbox()
    
    def add_chapter(self):
        """Add a new chapter to current section"""
        if not self.current_section:
            messagebox.showwarning("Warning", "No section selected")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("New Chapter")
        dialog.geometry("400x200")
        
        ttk.Label(dialog, text="ID:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        entry_id = ttk.Entry(dialog, width=30)
        entry_id.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Title:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        entry_title = ttk.Entry(dialog, width=30)
        entry_title.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="File:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        entry_file = ttk.Entry(dialog, width=30)
        entry_file.grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Label(dialog, text="Questions:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        entry_questions = ttk.Entry(dialog, width=30)
        entry_questions.grid(row=3, column=1, padx=10, pady=5)
        
        def create():
            new_chapter = {
                'id': entry_id.get(),
                'title': entry_title.get(),
                'file': entry_file.get(),
                'questions': int(entry_questions.get() or 0)
            }
            self.current_section['chapters'].append(new_chapter)
            self.current_section['totalQuestions'] = sum(c['questions'] for c in self.current_section['chapters'])
            self.update_chapters_tab()
            self.update_json_tab()
            self.refresh_sections_listbox()
            dialog.destroy()
        
        ttk.Button(dialog, text="Create", command=create).grid(row=4, column=1, sticky=tk.W, padx=10, pady=10)
    
    def delete_chapter(self):
        """Delete selected chapter"""
        if not self.current_section:
            messagebox.showwarning("Warning", "No section selected")
            return
        
        selection = self.chapters_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "No chapter selected")
            return
        
        chapter = self.current_section['chapters'][selection[0]]
        if messagebox.askyesno("Confirm", f"Delete '{chapter['title']}'?"):
            self.current_section['chapters'].pop(selection[0])
            self.current_section['totalQuestions'] = sum(c['questions'] for c in self.current_section['chapters'])
            self.update_chapters_tab()
            self.update_json_tab()
            self.refresh_sections_listbox()
    
    def save_section_info(self):
        """Save section information"""
        if not self.current_section:
            messagebox.showwarning("Warning", "No section selected")
            return
        
        self.current_section['id'] = self.info_id.get()
        self.current_section['title'] = self.info_title.get()
        self.current_section['icon'] = self.info_icon.get()
        self.current_section['folder'] = self.info_folder.get()
        self.current_section['status'] = self.info_status.get()
        
        self.refresh_sections_listbox()
        self.update_json_tab()
        messagebox.showinfo("Success", "Section information saved!")
    
    def save_chapter(self):
        """Save chapter information"""
        if not self.current_section:
            messagebox.showwarning("Warning", "No section selected")
            return
        
        selection = self.chapters_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "No chapter selected")
            return
        
        chapter = self.current_section['chapters'][selection[0]]
        chapter['id'] = self.chapter_id.get()
        chapter['title'] = self.chapter_title.get()
        chapter['file'] = self.chapter_file.get()
        chapter['questions'] = int(self.chapter_questions.get() or 0)
        
        self.current_section['totalQuestions'] = sum(c['questions'] for c in self.current_section['chapters'])
        self.update_chapters_tab()
        self.update_json_tab()
        self.refresh_sections_listbox()
        messagebox.showinfo("Success", "Chapter saved!")
    
    def save_json(self):
        """Save the generated code to exam-engine.js file"""
        try:
            code = self.generate_loadSections()
            
            # Read the current JS file
            with open(self.js_path, 'r', encoding='utf-8') as f:
                js_content = f.read()
            
            # Replace the loadSections function
            pattern = r'async function loadSections\(\)\s*{[\s\S]*?^}'
            new_js = re.sub(pattern, code, js_content, flags=re.MULTILINE)
            
            # Write back to file
            with open(self.js_path, 'w', encoding='utf-8') as f:
                f.write(new_js)
            
            messagebox.showinfo("Success", f"JavaScript code saved to:\n{self.js_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")
    
    def save_to_js(self):
        """Save to exam-engine.js"""
        self.save_json()
    
    def save_all(self):
        """Save all changes to the exam-engine.js file"""
        try:
            # Generate the loadSections function
            loadSections_code = self.generate_loadSections()
            
            # Read the current JS file
            with open(self.js_path, 'r', encoding='utf-8') as f:
                js_content = f.read()
            
            # Replace the loadSections function
            pattern = r'async function loadSections\(\)\s*{[\s\S]*?^}'
            new_js = re.sub(pattern, loadSections_code, js_content, flags=re.MULTILINE)
            
            # Write back to file
            with open(self.js_path, 'w', encoding='utf-8') as f:
                f.write(new_js)
            
            messagebox.showinfo("Success", f"Changes saved to {self.js_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")
    
    def generate_loadSections(self) -> str:
        """Generate the loadSections function from current sections"""
        sections_json = json.dumps(self.sections, indent=12, ensure_ascii=False)
        
        code = f"""async function loadSections() {{
    try {{
        // Auto-generated by Exam Engine Editor
        sections = {sections_json};

        renderSections();
        updateFilterCounts();
    }} catch (error) {{
        console.error('Error loading sections:', error);
    }}
}}"""
        return code
    
    def load_from_js(self):
        """Load sections from the JS file"""
        try:
            with open(self.js_path, 'r', encoding='utf-8') as f:
                js_content = f.read()
            
            # Extract sections array
            pattern = r'sections\s*=\s*(\[[\s\S]*?\]);'
            match = re.search(pattern, js_content)
            
            if match:
                sections_str = match.group(1)
                self.sections = json.loads(sections_str)
                self.refresh_sections_listbox()
                messagebox.showinfo("Success", "Loaded sections from JS file!")
            else:
                messagebox.showwarning("Warning", "Could not find sections in JS file")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load: {e}")
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo("About", 
            "Exam Engine Editor v1.0\n\n"
            "A GUI tool for managing exam sections and chapters.\n"
            "Easily edit the loadSections function and Java2 data.\n\n"
            "© 2024")
    
    def update_status(self, message):
        """Update status bar"""
        self.status_label.config(text=message)
        self.root.update()
    
    def sync_all_chapters(self):
        """Automatically sync all chapters from data folder"""
        if not self.sections:
            messagebox.showwarning("Warning", "No sections loaded")
            return
        
        if messagebox.askyesno("Confirm", "Sync all chapters from data folder to exam-engine.js?"):
            # Reload sections to ensure we have all chapters
            self.load_sections()
            self.refresh_sections_listbox()
            
            # Save to JS file
            self.save_json()
            self.update_status("All chapters synced successfully!")
            messagebox.showinfo("Success", "All chapters have been synced to exam-engine.js!")

def main():
    root = tk.Tk()
    app = ExamEngineEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
