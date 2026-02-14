#!/usr/bin/env python3
"""
Exam Engine Editor - Multi-Section Version
Manages multiple subjects/sections with chapters.json structure
"""

import uuid
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from pathlib import Path
import re
import shutil
import zipfile

class AdvancedChapterEditor:
    """Advanced editor for chapter questions, choices, and images"""
    def __init__(self, parent, chapter_file, section_path, base_path):
        self.parent = parent
        self.chapter_file = Path(chapter_file)
        self.section_path = Path(section_path)
        self.base_path = Path(base_path)
        # Create images folder with correct absolute path
        self.images_folder = self.base_path / self.section_path / "images"
        
        # Create images folder if it doesn't exist
        self.images_folder.mkdir(parents=True, exist_ok=True)
        
        self.window = tk.Toplevel(parent)
        self.window.title(f"Advanced Chapter Editor - {self.chapter_file.stem}")
        self.window.geometry("1000x700")
        self.window.transient(parent)
        
        self.chapter_data = None
        self.current_question_idx = None
        self.questions = []
        self.current_image_path = None
        
        self.load_chapter_data()
        self.setup_ui()
        self.refresh_questions_list()
        
    def load_chapter_data(self):
        """Load chapter JSON file"""
        try:
            with open(self.chapter_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both list and dict formats
            if isinstance(data, list) and data:
                self.chapter_data = data[0]
            else:
                self.chapter_data = data
            
            if not self.chapter_data:
                self.chapter_data = {"questions": [], "title": ""}
            
            self.questions = self.chapter_data.get("questions", [])
            
            # Debug: Show how many questions loaded and if they have images
            print(f"DEBUG: Loaded {len(self.questions)} questions from {self.chapter_file.name}")
            questions_with_images = sum(1 for q in self.questions if q.get('image'))
            print(f"DEBUG: {questions_with_images} questions have image paths")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load chapter: {e}")
            self.window.destroy()
    
    def setup_ui(self):
        """Create the UI for advanced editor"""
        # Top toolbar
        toolbar = ttk.Frame(self.window)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        ttk.Button(toolbar, text="➕ Add Question", command=self.add_question,
                  width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="🗑️ Delete Question", command=self.delete_question,
                  width=18).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="💾 Save Changes", command=self.save_chapter,
                  width=15).pack(side=tk.RIGHT, padx=5)
        
        # Main container
        container = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Left panel - Questions list
        left_frame = ttk.Frame(container)
        container.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="Questions", font=("", 10, "bold")).pack(
            fill=tk.X, pady=(0, 5))
        
        list_scroll = ttk.Scrollbar(left_frame, orient=tk.VERTICAL)
        self.questions_listbox = tk.Listbox(left_frame, yscrollcommand=list_scroll.set)
        list_scroll.config(command=self.questions_listbox.yview)
        
        self.questions_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.questions_listbox.bind("<<ListboxSelect>>", self.on_question_select)
        
        # Right panel - Question editor
        right_frame = ttk.Frame(container)
        container.add(right_frame, weight=2)
        
        ttk.Label(right_frame, text="Edit Question", font=("", 10, "bold")).pack(
            fill=tk.X, pady=(0, 5))
        
        # Create scrollable frame for question editor
        self.editor_scroll = ttk.Scrollbar(right_frame, orient=tk.VERTICAL)
        self.editor_canvas = tk.Canvas(right_frame, yscrollcommand=self.editor_scroll.set)
        self.editor_scroll.config(command=self.editor_canvas.yview)
        
        self.editor_frame = ttk.Frame(self.editor_canvas)
        self.editor_frame.bind("<Configure>", lambda e: self.editor_canvas.configure(
            scrollregion=self.editor_canvas.bbox("all")))
        
        self.canvas_window = self.editor_canvas.create_window((0, 0), window=self.editor_frame,
                                                               anchor=tk.NW)
        
        self.editor_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.editor_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Initialize editor widgets (will be populated when question is selected)
        self.init_editor_widgets()
    
    def init_editor_widgets(self):
        """Initialize editor widget placeholders"""
        for widget in self.editor_frame.winfo_children():
            widget.destroy()
        
        # Question ID
        ttk.Label(self.editor_frame, text="Question ID:", font=("", 9, "bold")).pack(
            fill=tk.X, padx=10, pady=(10, 5))
        self.q_id = ttk.Entry(self.editor_frame)
        self.q_id.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Question Number
        ttk.Label(self.editor_frame, text="Question Number:", font=("", 9, "bold")).pack(
            fill=tk.X, padx=10, pady=(0, 5))
        self.q_number = ttk.Entry(self.editor_frame)
        self.q_number.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Question Text
        ttk.Label(self.editor_frame, text="Question Text:", font=("", 9, "bold")).pack(
            fill=tk.X, padx=10, pady=(0, 5))
        self.q_text = tk.Text(self.editor_frame, height=6, wrap=tk.WORD)
        self.q_text.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Image
        ttk.Label(self.editor_frame, text="Question Image:", font=("", 9, "bold")).pack(
            fill=tk.X, padx=10, pady=(0, 5))
        
        img_frame = ttk.Frame(self.editor_frame)
        img_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.q_image = ttk.Entry(img_frame, state="readonly")
        self.q_image.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(img_frame, text="Browse", command=self.select_image,
                  width=10).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(img_frame, text="Clear", command=self.clear_image,
                  width=8).pack(side=tk.LEFT, padx=2)
        
        # Image preview section
        ttk.Label(self.editor_frame, text="Image Preview:", font=("", 9, "bold")).pack(
            fill=tk.X, padx=10, pady=(10, 5))
        self.image_preview_frame = ttk.Frame(self.editor_frame, relief=tk.SUNKEN, borderwidth=1)
        self.image_preview_frame.pack(fill=tk.BOTH, padx=10, pady=(0, 10), ipady=20, expand=False)
        
        self.image_preview_label = ttk.Label(self.image_preview_frame, text="No image selected")
        self.image_preview_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Input Type
        ttk.Label(self.editor_frame, text="Input Type:", font=("", 9, "bold")).pack(
            fill=tk.X, padx=10, pady=(0, 5))
        self.q_input_type = ttk.Combobox(self.editor_frame, values=["radio", "checkbox"],
                                        state="readonly", width=20)
        self.q_input_type.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Correct Answer
        ttk.Label(self.editor_frame, text="Correct Answer(s):", font=("", 9, "bold")).pack(
            fill=tk.X, padx=10, pady=(0, 5))
        self.q_correct = ttk.Entry(self.editor_frame)
        self.q_correct.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Explanation
        ttk.Label(self.editor_frame, text="Explanation:", font=("", 9, "bold")).pack(
            fill=tk.X, padx=10, pady=(0, 5))
        self.q_explanation = tk.Text(self.editor_frame, height=4, wrap=tk.WORD)
        self.q_explanation.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Choices section
        ttk.Label(self.editor_frame, text="Choices:", font=("", 9, "bold")).pack(
            fill=tk.X, padx=10, pady=(10, 5))
        
        # Choices listbox
        choices_frame = ttk.Frame(self.editor_frame)
        choices_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        choices_scroll = ttk.Scrollbar(choices_frame, orient=tk.VERTICAL)
        self.choices_listbox = tk.Listbox(choices_frame, height=5,
                                         yscrollcommand=choices_scroll.set)
        choices_scroll.config(command=self.choices_listbox.yview)
        
        self.choices_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        choices_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.choices_listbox.bind("<<ListboxSelect>>", self.on_choice_select)
        
        # Choice edit buttons
        choice_btn_frame = ttk.Frame(self.editor_frame)
        choice_btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(choice_btn_frame, text="➕ Add Choice", command=self.add_choice,
                  width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(choice_btn_frame, text="✏️ Edit Choice", command=self.edit_choice,
                  width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(choice_btn_frame, text="🗑️ Delete Choice", command=self.delete_choice,
                  width=14).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(choice_btn_frame, text="Update Question", command=self.update_current_question,
                  width=16).pack(side=tk.RIGHT, padx=2)
    
    def refresh_questions_list(self):
        """Refresh questions list"""
        self.questions_listbox.delete(0, tk.END)
        for idx, q in enumerate(self.questions):
            display = f"{idx + 1}. {q.get('number', '')} - {q.get('text', '')[:60]}"
            self.questions_listbox.insert(tk.END, display)
    
    def on_question_select(self, event):
        """Handle question selection"""
        selection = self.questions_listbox.curselection()
        if not selection:
            return
        
        self.current_question_idx = selection[0]
        self.display_question()
    
    def display_question(self):
        """Display current question in editor"""
        if self.current_question_idx is None or self.current_question_idx >= len(self.questions):
            return
        
        q = self.questions[self.current_question_idx]
        
        self.q_id.delete(0, tk.END)
        self.q_id.insert(0, q.get('id', ''))
        
        self.q_number.delete(0, tk.END)
        self.q_number.insert(0, q.get('number', ''))
        
        self.q_text.delete(1.0, tk.END)
        self.q_text.insert(1.0, q.get('text', ''))
        
        # Update image field and preview
        image_path = q.get('image', '')
        self.q_image.config(state="normal")
        self.q_image.delete(0, tk.END)
        if image_path:
            self.q_image.insert(0, str(image_path))  # Ensure it's a string
        self.q_image.config(state="readonly")
        
        # Update image preview - with better path handling
        if image_path and str(image_path).strip():
            image_path_str = str(image_path).strip()
            # Convert forward slashes to backslashes for Windows
            normalized_path = image_path_str.replace('/', '\\')
            full_path = self.base_path / normalized_path
            
            print(f"DEBUG: Checking image path")
            print(f"  Stored path: {image_path_str}")
            print(f"  Normalized: {normalized_path}")
            print(f"  Full path: {full_path}")
            print(f"  Exists: {full_path.exists()}")
            
            if full_path.exists():
                try:
                    img_size = full_path.stat().st_size / 1024
                    img_name = Path(image_path_str).name
                    preview_text = f"✓ Image: {img_name}\nSize: {img_size:.1f} KB"
                    self.image_preview_label.config(text=preview_text)
                except Exception as e:
                    self.image_preview_label.config(text=f"Error: {str(e)}")
            else:
                # File not found - show diagnostic info
                self.image_preview_label.config(text=f"⚠️ Image not found\n\nPath: {image_path_str}\n\n(Checked: {full_path})")
        else:
            self.image_preview_label.config(text="No image selected")
        
        self.q_input_type.set(q.get('inputType', 'radio'))
        
        self.q_correct.delete(0, tk.END)
        self.q_correct.insert(0, q.get('correctAnswer', ''))
        
        self.q_explanation.delete(1.0, tk.END)
        self.q_explanation.insert(1.0, q.get('explanation', ''))
        
        # Load choices
        self.refresh_choices_list()
    
    def refresh_choices_list(self):
        """Refresh choices list"""
        if self.current_question_idx is None:
            return
        
        self.choices_listbox.delete(0, tk.END)
        q = self.questions[self.current_question_idx]
        choices = q.get('choices', [])
        
        for choice in choices:
            display = f"{choice.get('value', '')} - {choice.get('text', '')}"
            self.choices_listbox.insert(tk.END, display)
    
    def on_choice_select(self, event):
        """Handle choice selection"""
        pass  # Can add more features later
    
    def add_choice(self):
        """Add new choice to current question"""
        if self.current_question_idx is None:
            messagebox.showwarning("Warning", "Select a question first")
            return
        
        dialog = tk.Toplevel(self.window)
        dialog.title("Add Choice")
        dialog.geometry("400x200")
        dialog.transient(self.window)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Choice Value (A, B, C, D):", font=("", 9, "bold")).pack(
            fill=tk.X, pady=(0, 5))
        val_entry = ttk.Entry(frame)
        val_entry.pack(fill=tk.X, pady=(0, 10))
        val_entry.focus()
        
        ttk.Label(frame, text="Choice Text:", font=("", 9, "bold")).pack(
            fill=tk.X, pady=(0, 5))
        text_entry = tk.Text(frame, height=4, wrap=tk.WORD)
        text_entry.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        def save():
            value = val_entry.get().strip()
            text = text_entry.get(1.0, tk.END).strip()
            
            if not value or not text:
                messagebox.showwarning("Warning", "Value and text are required")
                return
            
            q = self.questions[self.current_question_idx]
            new_choice = {
                "value": value,
                "label": value,
                "text": text
            }
            
            if "choices" not in q:
                q["choices"] = []
            
            q["choices"].append(new_choice)
            self.refresh_choices_list()
            dialog.destroy()
        
        ttk.Button(frame, text="✓ Add", command=save, width=20).pack(pady=10)
        dialog.bind('<Return>', lambda e: save())
    
    def edit_choice(self):
        """Edit selected choice"""
        if self.current_question_idx is None:
            messagebox.showwarning("Warning", "Select a question first")
            return
        
        selection = self.choices_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Select a choice first")
            return
        
        choice_idx = selection[0]
        q = self.questions[self.current_question_idx]
        choice = q.get('choices', [])[choice_idx]
        
        dialog = tk.Toplevel(self.window)
        dialog.title("Edit Choice")
        dialog.geometry("400x200")
        dialog.transient(self.window)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Choice Value:", font=("", 9, "bold")).pack(
            fill=tk.X, pady=(0, 5))
        val_entry = ttk.Entry(frame)
        val_entry.insert(0, choice.get('value', ''))
        val_entry.pack(fill=tk.X, pady=(0, 10))
        val_entry.focus()
        
        ttk.Label(frame, text="Choice Text:", font=("", 9, "bold")).pack(
            fill=tk.X, pady=(0, 5))
        text_entry = tk.Text(frame, height=4, wrap=tk.WORD)
        text_entry.insert(1.0, choice.get('text', ''))
        text_entry.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        def save():
            value = val_entry.get().strip()
            text = text_entry.get(1.0, tk.END).strip()
            
            if not value or not text:
                messagebox.showwarning("Warning", "Value and text are required")
                return
            
            choice["value"] = value
            choice["label"] = value
            choice["text"] = text
            self.refresh_choices_list()
            dialog.destroy()
        
        ttk.Button(frame, text="✓ Save", command=save, width=20).pack(pady=10)
        dialog.bind('<Return>', lambda e: save())
    
    def delete_choice(self):
        """Delete selected choice"""
        selection = self.choices_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Select a choice first")
            return
        
        choice_idx = selection[0]
        q = self.questions[self.current_question_idx]
        del q.get('choices', [])[choice_idx]
        self.refresh_choices_list()
    
    def select_image(self):
        """Select image for current question"""
        if self.current_question_idx is None:
            messagebox.showwarning("Warning", "Select a question first")
            return
        
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.gif"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            src = Path(file_path)
            
            # Get question number for image naming
            q = self.questions[self.current_question_idx]
            q_number = q.get('number', str(self.current_question_idx + 1))
            file_ext = src.suffix.lower()  # Get extension like .jpg, .png
            
            # Rename image to imageN_UUID.ext format (unique to prevent overwrites)
            safe_q_number = q_number.replace('.', '_')
            unique_id = uuid.uuid4().hex[:8]
            image_name = f"image{safe_q_number}_{unique_id}{file_ext}"
            dest = self.images_folder / image_name
            
            # Copy image to images folder
            shutil.copy2(src, dest)
            
            # Get the section name from section_path
            section_name = Path(self.section_path).name
            
            # Update image path (relative path for web)
            rel_path = f"data/{section_name}/images/{image_name}"
            
            # Store path and update entry field
            self.current_image_path = rel_path
            
            # Update entry field (readonly, so use different method)
            self.q_image.config(state="normal")
            self.q_image.delete(0, tk.END)
            self.q_image.insert(0, rel_path)
            self.q_image.config(state="readonly")
            
            # Update preview
            self.update_image_preview(dest, image_name)
            
            messagebox.showinfo("Success", f"Image saved as:\n{image_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy image: {e}")
            self.image_preview_label.config(text=f"Error: {str(e)}")
    
    def clear_image(self):
        """Clear image for current question"""
        self.q_image.config(state="normal")
        self.q_image.delete(0, tk.END)
        self.q_image.config(state="readonly")
        self.current_image_path = None
        self.image_preview_label.config(text="No image selected")
    
    def update_image_preview(self, image_path, image_name):
        """Update image preview in UI"""
        try:
            if not Path(image_path).exists():
                self.image_preview_label.config(text="Image file not found ❌")
                return
            
            # Show file info as text (file size and name)
            img_size = Path(image_path).stat().st_size / 1024  # Size in KB
            preview_text = f"✓ Image loaded: {image_name}\nSize: {img_size:.1f} KB"
            self.image_preview_label.config(text=preview_text)
        except Exception as e:
            self.image_preview_label.config(text=f"Error: {str(e)}")
    
    def update_current_question(self):
        """Update current question with edited values"""
        if self.current_question_idx is None:
            messagebox.showwarning("Warning", "No question selected")
            return
        
        q = self.questions[self.current_question_idx]
        
        q['id'] = self.q_id.get()
        q['number'] = self.q_number.get()
        q['text'] = self.q_text.get(1.0, tk.END).strip()
        
        # Get image path from entry field and save it properly
        image_path = self.q_image.get().strip()
        if image_path:
            q['image'] = image_path
        else:
            # Remove image key if empty
            q.pop('image', None)
        
        q['inputType'] = self.q_input_type.get()
        q['correctAnswer'] = self.q_correct.get()
        q['explanation'] = self.q_explanation.get(1.0, tk.END).strip()
        
        self.refresh_questions_list()
        self.questions_listbox.selection_set(self.current_question_idx)
        # Force display refresh to show updated data including image path
        self.display_question()
        messagebox.showinfo("Success", "Question updated ✓\n(Click 'Save Changes' to save to file)")
    
    def add_question(self):
        """Add new question"""
        new_q = {
            "id": f"{len(self.questions) + 1}",
            "number": f"{len(self.questions) + 1}",
            "text": "New question",
            "image": "",
            "choices": [
                {"value": "A", "label": "A", "text": "Choice A"},
                {"value": "B", "label": "B", "text": "Choice B"}
            ],
            "inputName": f"Q{len(self.questions)}",
            "inputType": "radio",
            "correctAnswer": "A",
            "explanation": ""
        }
        
        self.questions.append(new_q)
        self.refresh_questions_list()
        self.current_question_idx = len(self.questions) - 1
        self.questions_listbox.selection_set(self.current_question_idx)
        # Force display of the new question
        self.display_question()
        messagebox.showinfo("Success", "New question added")
    
    def delete_question(self):
        """Delete current question"""
        if self.current_question_idx is None:
            messagebox.showwarning("Warning", "Select a question first")
            return

        question = self.questions[self.current_question_idx]
        image_path = question.get('image', '')

        # Custom dialog with optional image deletion
        dlg = tk.Toplevel(self.window)
        dlg.title("Delete Question")
        dlg.geometry("480x180" if image_path else "480x140")
        dlg.transient(self.window)
        dlg.grab_set()

        frame = ttk.Frame(dlg, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        q_num = question.get('number', str(self.current_question_idx + 1))
        ttk.Label(frame, text=f"Delete question {q_num}?", font=("", 10, "bold")).pack(anchor=tk.W, pady=(0, 8))

        del_image_var = tk.BooleanVar(value=False)
        if image_path:
            ttk.Label(frame, text=f"This question has an image: {image_path}").pack(anchor=tk.W)
            ttk.Checkbutton(frame, text="Also delete image file from disk (permanent)", variable=del_image_var).pack(anchor=tk.W, pady=(4, 8))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        def do_delete():
            # Delete the image file if the user opted in
            if del_image_var.get() and image_path:
                try:
                    img_path = self.base_path / image_path
                    if img_path.exists():
                        img_path.unlink()
                        print(f"Deleted image: {image_path}")
                except Exception as e:
                    print(f"Warning: Failed to delete image {image_path}: {e}")

            del self.questions[self.current_question_idx]
            self.current_question_idx = None
            self.refresh_questions_list()
            self.init_editor_widgets()
            dlg.destroy()
            messagebox.showinfo("Success", "Question deleted")

        def cancel():
            dlg.destroy()

        ttk.Button(btn_frame, text="Delete", command=do_delete, width=12).pack(side=tk.RIGHT, padx=6)
        ttk.Button(btn_frame, text="Cancel", command=cancel, width=12).pack(side=tk.RIGHT)
    
    def save_chapter(self):
        """Save chapter data back to JSON file"""
        try:
            # First, make sure current question is updated
            if self.current_question_idx is not None:
                q = self.questions[self.current_question_idx]
                
                print(f"DEBUG: Updating question #{self.current_question_idx}: {q.get('number', 'N/A')}")
                
                # Update all fields from the editor
                q['id'] = self.q_id.get()
                q['number'] = self.q_number.get()
                q['text'] = self.q_text.get(1.0, tk.END).strip()
                
                # Save image path
                image_path = self.q_image.get().strip()
                print(f"DEBUG: Entry field contains: '{image_path}'")
                print(f"DEBUG: Entry field state: {self.q_image.cget('state')}")
                
                if image_path:
                    q['image'] = image_path
                    print(f"DEBUG: Saving image path for question {q['number']}: {image_path}")
                else:
                    print(f"DEBUG: Image path is empty, removing from question")
                    q.pop('image', None)
                
                q['inputType'] = self.q_input_type.get()
                q['correctAnswer'] = self.q_correct.get()
                q['explanation'] = self.q_explanation.get(1.0, tk.END).strip()
            
            # Update chapter data
            if self.chapter_data:
                self.chapter_data["questions"] = self.questions
            
            # Save to file
            with open(self.chapter_file, 'w', encoding='utf-8') as f:
                json.dump(self.chapter_data, f, indent=2, ensure_ascii=False)
            
            # Count questions with images
            questions_with_images = sum(1 for q in self.questions if q.get('image'))
            print(f"DEBUG: Saved chapter with {len(self.questions)} questions ({questions_with_images} with images)")
            
            # Debug: Print first 3 questions to see what was saved
            for idx, q in enumerate(self.questions[:3]):
                print(f"  Q{idx}: id={q.get('id')}, image='{q.get('image', 'N/A')}'")
            
            messagebox.showinfo("Success", 
                f"Chapter saved successfully! ✓\n\n"
                f"Total questions: {len(self.questions)}\n"
                f"Questions with images: {questions_with_images}\n"
                f"File: {self.chapter_file.name}")
        except Exception as e:
            print(f"DEBUG: Error saving chapter: {e}")
            messagebox.showerror("Error", f"Failed to save chapter: {e}")

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
        ttk.Button(sections_header, text="⬆️", command=self.import_section,
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
        ttk.Button(chapters_header, text="⬆️", command=self.import_chapters,
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
        self.chapters_tree.bind("<Double-1>", self.on_chapter_double_click)
        
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
        """Refresh all data and auto-configure engine"""
        self.load_sections()
        if self.current_section:
            self.load_chapters()
        
        # Auto-configure engine on refresh
        try:
            self.generate_js_config()
            self.update_status("✓ Refreshed & Configured", "green")
        except Exception as e:
            self.update_status("Refreshed (config failed)", "orange")
            print(f"Auto-config error: {e}")
    
    def load_sections(self):
        """Load sections from config"""
        try:
                config_file = self.config_path / "sections.json"
                with open(config_file, encoding='utf-8') as f:
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
                with open(ch_file, encoding='utf-8') as f:
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
    
    def on_chapter_double_click(self, event):
        """Open advanced chapter editor when double-clicking a chapter"""
        selection = self.chapters_tree.selection()
        if not selection:
            return
        
        if not self.current_section:
            messagebox.showwarning("Warning", "Select a section first")
            return
        
        self.current_chapter_idx = int(selection[0])
        chapter = self.chapters[self.current_chapter_idx]
        
        # Get the chapter file path
        section = next((s for s in self.sections if s['id'] == self.current_section), None)
        if not section:
            messagebox.showerror("Error", "Section not found")
            return
        
        chapter_file_path = self.base_path / section['path'] / chapter.get('file', '')
        
        if not chapter_file_path.exists():
            messagebox.showerror("Error", f"Chapter file not found: {chapter_file_path}")
            return
        
        # Open advanced editor
        AdvancedChapterEditor(self.root, chapter_file_path, section['path'], self.base_path)
    
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
        
        # Sync changes to the actual file
        try:
            self._sync_chapter_file(chapter)
            self.update_status("Chapter updated and file synced", "orange")
        except Exception as e:
            messagebox.showerror("Sync Error", f"Failed to sync to file: {e}")
            self.update_status("Chapter updated in list (Sync Failed)", "red")

    def _sync_chapter_file(self, chapter_data):
        """Sync chapter metadata to the actual JSON file and rename if ID changed"""
        section = next((s for s in self.sections if s['id'] == self.current_section), None)
        if not section:
            return

        old_file_name = chapter_data.get('file', '')
        if not old_file_name:
            return

        section_path = self.base_path / section['path']
        old_file_path = section_path / old_file_name

        if not old_file_path.exists():
            return

        # 1. Load content
        with open(old_file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)

        data = content[0] if isinstance(content, list) and content else content
        if isinstance(content, list) and not content:
            data = {}
            content = [data]

        # 2. Update Content
        new_id = chapter_data['id']
        new_name = chapter_data['name']
        
        # Update params.chapter
        if 'params' not in data:
            data['params'] = {}
        data['params']['chapter'] = new_id
        
        # Update title - preserve format if possible or just set it
        # Try to construct "Chapter {ID} {Name}" if it looks like that pattern was used
        if data.get('title', '').startswith('Chapter'):
             data['title'] = f"Chapter {new_id} {new_name}"
        else:
             data['title'] = new_name

        # 3. Determine new filename
        # If the file follows the pattern chapterN.json, rename it to match new ID
        new_file_name = old_file_name
        if re.match(r'chapter\d+\.json', old_file_name):
            new_file_name = f"chapter{new_id}.json"
        
        # 4. Save file
        # If renaming, we write to new path and remove old one (or git mv equivalent)
        new_file_path = section_path / new_file_name
        
        # If target exists and it's not the same file, warn? 
        # For now, just overwrite if it's a rename
        
        if new_file_name != old_file_name:
            # Rename logic
            if new_file_path.exists():
                 # basic collision avoidance
                 pass 
            
            with open(new_file_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            
            try:
                old_file_path.unlink()
            except:
                pass
            
            # Update chapter data with new filename
            chapter_data['file'] = new_file_name
        else:
            # Just save content
            with open(old_file_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
    
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
        # Custom dialog with optional checkbox to also delete files on disk
        dlg = tk.Toplevel(self.root)
        dlg.title("Delete Section")
        dlg.geometry("480x180")
        dlg.transient(self.root)
        dlg.grab_set()

        frame = ttk.Frame(dlg, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=f"Delete section '{section['name']}'?", font=("", 10, "bold")).pack(anchor=tk.W, pady=(0,8))
        ttk.Label(frame, text="This will remove the section from the config.").pack(anchor=tk.W)

        del_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Also delete section files from disk (permanent)", variable=del_var).pack(anchor=tk.W, pady=8)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10,0))

        def do_delete():
            # If user opted to delete files, attempt to remove directory
            if del_var.get():
                try:
                    full_path = self.base_path / section.get('path', '')
                    if full_path.exists():
                        shutil.rmtree(full_path)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete section files: {e}")
                    return

            # Remove from config regardless
            try:
                del self.sections[self.current_section_idx]
            except Exception:
                pass
            self.current_section = None
            self.current_section_idx = None
            self.save_sections()
            self.load_sections()
            self.chapters = []
            self.refresh_chapters_tree()
            self.update_status("Section deleted", "orange")
            dlg.destroy()

        def cancel():
            dlg.destroy()

        ttk.Button(btn_frame, text="Delete", command=do_delete, width=12).pack(side=tk.RIGHT, padx=6)
        ttk.Button(btn_frame, text="Cancel", command=cancel, width=12).pack(side=tk.RIGHT)
    
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

    def _copy_source_to_dest(self, src_path, dest_path):
        """Copy or extract src_path (dir or zip) into dest_path.
        Handles copying 'theme' or 'themes' directories correctly."""
        src = Path(src_path)
        dest = Path(dest_path)
        try:
            dest.mkdir(parents=True, exist_ok=True)

            # If zip file
            if src.is_file() and zipfile.is_zipfile(src):
                with zipfile.ZipFile(src, 'r') as z:
                    z.extractall(dest)
                return True, None

            # If directory, copy contents
            if src.is_dir():
                for item in src.iterdir():
                    target = dest / item.name
                    if item.is_dir():
                        # If target exists, merge by removing and replacing
                        if target.exists():
                            shutil.rmtree(target)
                        shutil.copytree(item, target)
                    else:
                        shutil.copy2(item, target)
                return True, None

            # If single file, copy
            if src.is_file():
                shutil.copy2(src, dest / src.name)
                return True, None

            return False, 'Source not found'
        except Exception as e:
            return False, str(e)

    def import_section(self):
        """Import a section from a directory or zip. Copies theme if present."""
        src_dir = filedialog.askdirectory(title="Select section folder to import")
        if not src_dir:
            # allow zip selection as alternative
            src_file = filedialog.askopenfilename(title="Select section zip to import",
                                                  filetypes=[("Zip Archives","*.zip")])
            if not src_file:
                return
            src_dir = src_file

        src = Path(src_dir)
        sec_id = src.stem if src.is_file() else src.name
        section_exists = any(s['id'] == sec_id for s in self.sections)
        if section_exists:
            if not messagebox.askyesno("Exists", f"Section '{sec_id}' already exists. Overwrite?"):
                return

        dest_rel = f"data/{sec_id}"
        dest = self.base_path / dest_rel

        ok, err = self._copy_source_to_dest(src, dest)
        if not ok:
            messagebox.showerror("Import Failed", f"Failed to import section: {err}")
            return

        # Add or update section entry
        new_section = {
            "id": sec_id,
            "name": sec_id,
            "path": dest_rel,
            "description": ""
        }

        # remove existing section with same id
        self.sections = [s for s in self.sections if s['id'] != sec_id]
        self.sections.append(new_section)
        self.save_sections()
        self.load_sections()
        self.update_status(f"Imported section: {sec_id}", "green")

    def import_chapters(self):
        """Import chapter files (JSON or ZIP) into the currently selected section."""
        if not self.current_section:
            messagebox.showwarning("Warning", "Select a section first")
            return

        files = filedialog.askopenfilenames(title="Select chapter files or zip",
                                            filetypes=[("JSON","*.json"), ("Zip","*.zip"), ("All","*.*")])
        if not files:
            return

        section = next((s for s in self.sections if s['id'] == self.current_section), None)
        if not section:
            messagebox.showerror("Error", "Selected section not found")
            return

        dest = self.base_path / section.get('path', '')
        dest.mkdir(parents=True, exist_ok=True)

        for f in files:
            src = Path(f)
            if src.is_file() and zipfile.is_zipfile(src):
                ok, err = self._copy_source_to_dest(src, dest)
                if not ok:
                    messagebox.showerror("Import Failed", f"Failed to extract {src.name}: {err}")
                    return
            else:
                try:
                    # copy single file
                    shutil.copy2(src, dest / src.name)
                except Exception as e:
                    messagebox.showerror("Import Failed", f"Failed to copy {src.name}: {e}")
                    return

        # Reload chapters and save
        self.load_chapters()
        self.save_chapter()
        self.update_status("Chapters imported (and saved)", "green")
    
    def delete_chapter(self):
        """Delete chapter"""
        if self.current_chapter_idx is None:
            messagebox.showwarning("Warning", "Select a chapter first")
            return
        
        chapter = self.chapters[self.current_chapter_idx]
        # Custom dialog with optional checkboxes to also delete file and images on disk
        dlg = tk.Toplevel(self.root)
        dlg.title("Delete Chapter")
        dlg.geometry("500x200")
        dlg.transient(self.root)
        dlg.grab_set()

        frame = ttk.Frame(dlg, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=f"Delete chapter '{chapter.get('name','')}'?", font=("", 10, "bold")).pack(anchor=tk.W, pady=(0,8))
        ttk.Label(frame, text="This will remove the chapter from the list.").pack(anchor=tk.W)

        del_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Also delete chapter file from disk (permanent)", variable=del_var).pack(anchor=tk.W, pady=(8, 0))

        del_images_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Also delete chapter images from disk (permanent)", variable=del_images_var).pack(anchor=tk.W, pady=(4, 8))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10,0))

        def do_delete():
            section = next((s for s in self.sections if s['id'] == self.current_section), None)

            # Collect image paths from the chapter JSON before deleting it
            image_paths = []
            if section and (del_var.get() or del_images_var.get()):
                try:
                    fpath = self.base_path / section.get('path', '') / chapter.get('file', '')
                    if fpath.exists():
                        with open(fpath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        # Handle both list and dict formats
                        chapter_data = data[0] if isinstance(data, list) and data else data
                        if isinstance(chapter_data, dict):
                            for q in chapter_data.get('questions', []):
                                img = q.get('image', '')
                                if img:
                                    image_paths.append(img)
                except Exception as e:
                    print(f"Warning: Could not read chapter images: {e}")

            # Delete image files if the user opted in
            if del_images_var.get() and image_paths:
                deleted_count = 0
                for img_rel in image_paths:
                    try:
                        img_path = self.base_path / img_rel
                        if img_path.exists():
                            img_path.unlink()
                            deleted_count += 1
                    except Exception as e:
                        print(f"Warning: Failed to delete image {img_rel}: {e}")
                if deleted_count:
                    print(f"Deleted {deleted_count} image(s) for chapter '{chapter.get('name', '')}'")

            # If user chose to delete the file, attempt it
            if del_var.get():
                try:
                    if section:
                        fpath = self.base_path / section.get('path', '') / chapter.get('file', '')
                        if fpath.exists():
                            fpath.unlink()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete chapter file: {e}")
                    return

            try:
                del self.chapters[self.current_chapter_idx]
            except Exception:
                pass
            self.current_chapter_idx = None
            self.refresh_chapters_tree()
            self.ch_id.delete(0, tk.END)
            self.ch_name.delete(0, tk.END)
            self.ch_count.delete(0, tk.END)
            self.update_chapter_btn.config(state="disabled")
            self.update_status("Chapter deleted (click Save All)", "orange")
            dlg.destroy()

        def cancel():
            dlg.destroy()

        ttk.Button(btn_frame, text="Delete", command=do_delete, width=12).pack(side=tk.RIGHT, padx=6)
        ttk.Button(btn_frame, text="Cancel", command=cancel, width=12).pack(side=tk.RIGHT)
            
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
            with open(ch_file, 'w', encoding='utf-8') as f:
                json.dump(self.chapters, f, indent=2)
            self.update_status("Chapters saved", "green")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def save_sections(self):
        """Save sections to config"""
        try:
            self.config_path.mkdir(parents=True, exist_ok=True)
            config_file = self.config_path / "sections.json"
            with open(config_file, 'w', encoding='utf-8') as f:
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
                        with open(ch_file, encoding='utf-8') as f:
                            chapters = json.load(f)
                            for ch in chapters:
                                ch['file'] = f"{section['path']}/{ch.get('file', '')}"
                                if 'q' not in ch or ch['q'] == 0:
                                    try:
                                        q_path = self.base_path / section['path'] / ch.get('file', '')
                                        with open(q_path, encoding='utf-8') as qf:
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
            
            # Refresh tables after configuration
            self.load_sections()
            if self.current_section:
                self.load_chapters()
                
            messagebox.showinfo("Success", 
                              f"Engine Configured Successfully!\n\nGenerated: {js_path.relative_to(self.base_path)}\nTables refreshed with latest data.")
            self.update_status("✓ Engine configured", "green")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate config: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ExamEditor(root)
    root.mainloop()