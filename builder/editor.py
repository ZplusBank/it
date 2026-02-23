#!/usr/bin/env python3
"""
Exam Engine Editor - Multi-Section Version
Manages multiple subjects/sections with chapters.json structure
"""

import uuid
import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import json
from pathlib import Path
import re
import shutil
import zipfile

# -- Dark Theme Color Constants (matches web app CSS dark theme) --
COLORS = {
    "bg_body": "#0f172a",
    "bg_card": "#1e293b",
    "bg_input": "#0f172a",
    "bg_input_alt": "#1a2332",
    "text_main": "#f1f5f9",
    "text_muted": "#94a3b8",
    "text_secondary": "#cbd5e1",
    "border": "#334155",
    "primary": "#6366f1",
    "primary_light": "#818cf8",
    "secondary": "#8b5cf6",
    "accent": "#06b6d4",
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "selection_bg": "#6366f1",
    "selection_fg": "#ffffff",
    "treeview_row_odd": "#1e293b",
    "treeview_row_even": "#172033",
}


def _configure_custom_styles(style):
    """Override ttkbootstrap darkly theme to match web app indigo/purple palette."""
    style.configure("Treeview",
                     background=COLORS["bg_card"],
                     foreground=COLORS["text_main"],
                     fieldbackground=COLORS["bg_card"],
                     rowheight=28,
                     borderwidth=0,
                     font=("Segoe UI", 10))
    style.configure("Treeview.Heading",
                     background=COLORS["bg_body"],
                     foreground=COLORS["text_muted"],
                     font=("Segoe UI", 10, "bold"),
                     borderwidth=0,
                     relief="flat")
    style.map("Treeview",
              background=[("selected", COLORS["primary"])],
              foreground=[("selected", COLORS["selection_fg"])])

    style.configure("TLabelframe",
                     background=COLORS["bg_card"],
                     foreground=COLORS["primary_light"],
                     bordercolor=COLORS["border"])
    style.configure("TLabelframe.Label",
                     background=COLORS["bg_card"],
                     foreground=COLORS["primary_light"],
                     font=("Segoe UI", 10, "bold"))

    style.configure("Header.TLabel",
                     font=("Segoe UI", 12, "bold"),
                     foreground=COLORS["text_main"])
    style.configure("SubHeader.TLabel",
                     font=("Segoe UI", 10, "bold"),
                     foreground=COLORS["text_secondary"])
    style.configure("Muted.TLabel",
                     foreground=COLORS["text_muted"])
    style.configure("Status.TLabel",
                     font=("Segoe UI", 9))

    style.configure("TPanedwindow",
                     background=COLORS["bg_body"],
                     sashthickness=6)


def _style_tk_text(widget, height=None):
    """Apply dark theme to a tk.Text widget."""
    widget.configure(
        bg=COLORS["bg_input"],
        fg=COLORS["text_main"],
        insertbackground=COLORS["text_main"],
        selectbackground=COLORS["selection_bg"],
        selectforeground=COLORS["selection_fg"],
        relief="flat",
        borderwidth=1,
        highlightbackground=COLORS["border"],
        highlightcolor=COLORS["primary"],
        highlightthickness=1,
        font=("Segoe UI", 10),
        padx=8,
        pady=6,
    )
    if height is not None:
        widget.configure(height=height)


def _style_tk_listbox(widget):
    """Apply dark theme to a tk.Listbox widget."""
    widget.configure(
        bg=COLORS["bg_card"],
        fg=COLORS["text_main"],
        selectbackground=COLORS["primary"],
        selectforeground=COLORS["selection_fg"],
        relief="flat",
        borderwidth=0,
        highlightbackground=COLORS["border"],
        highlightcolor=COLORS["primary"],
        highlightthickness=1,
        font=("Segoe UI", 10),
        activestyle="none",
    )


def _style_dialog(dialog, title, geometry):
    """Apply dark theme to a tk.Toplevel dialog."""
    dialog.title(title)
    dialog.geometry(geometry)
    dialog.configure(bg=COLORS["bg_body"])

class FormattedTextEditor(ttk.Frame):
    """Rich text editor with formatting toolbar, syntax highlighting, and live preview."""

    FORMATS = [
        # (label, prefix, suffix, bootstyle)
        ("B", "**", "**", "warning-outline"),
        ("I", "*", "*", "info-outline"),
        ("SEP", None, None, None),
        ("<>", "`", "`", "success-outline"),
        ("{..}", "```java\n", "\n```", "success-outline"),
        ("SEP", None, None, None),
        ("f(x)", "\\(", "\\)", "primary-outline"),
        ("[=]", "\\[", "\\]", "primary-outline"),
        ("SEP", None, None, None),
        ("BR", "<br>", "", "danger-outline"),
        ("SP", "&nbsp;", "", "secondary-outline"),
    ]

    def __init__(self, parent, height=6, show_preview=True):
        super().__init__(parent)
        self.show_preview = show_preview
        self._highlight_job = None
        self._build_toolbar()
        self._build_text(height)
        if show_preview:
            self._build_preview()
        self._setup_tags()
        self._bind_events()

    def _build_toolbar(self):
        tb = ttk.Frame(self)
        tb.pack(fill=tk.X, pady=(0, 2))

        for label, prefix, suffix, bstyle in self.FORMATS:
            if label == "SEP":
                sep = ttk.Separator(tb, orient=tk.VERTICAL)
                sep.pack(side=tk.LEFT, fill=tk.Y, padx=4, pady=2)
                continue
            btn = ttk.Button(
                tb, text=label, width=max(len(label) + 1, 4),
                bootstyle=bstyle, takefocus=0,
                command=lambda p=prefix, s=suffix: self._insert_format(p, s),
            )
            btn.pack(side=tk.LEFT, padx=1, pady=1)

        if self.show_preview:
            self._preview_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(
                tb, text="Preview", variable=self._preview_var,
                command=self._toggle_preview, bootstyle="info-round-toggle",
            ).pack(side=tk.RIGHT, padx=4)

    def _build_text(self, height):
        self.text = tk.Text(self, height=height, wrap=tk.WORD, undo=True,
                            exportselection=False)
        _style_tk_text(self.text, height=height)
        self.text.pack(fill=tk.BOTH, expand=True)

    def _build_preview(self):
        self._preview_frame = ttk.LabelFrame(self, text="Preview")
        self._preview_frame.pack(fill=tk.X, pady=(3, 0))
        self._preview_text = tk.Text(
            self._preview_frame, height=3, wrap=tk.WORD,
            state="disabled", cursor="arrow",
        )
        self._preview_text.configure(
            bg=COLORS["bg_input_alt"], fg=COLORS["text_main"],
            insertbackground=COLORS["text_main"],
            selectbackground=COLORS["selection_bg"],
            selectforeground=COLORS["selection_fg"],
            relief="flat", borderwidth=0, highlightthickness=0,
            font=("Segoe UI", 10), padx=8, pady=4,
        )
        self._preview_text.pack(fill=tk.BOTH, expand=True)

        # Preview rendering tags
        self._preview_text.tag_configure("bold", font=("Segoe UI", 10, "bold"))
        self._preview_text.tag_configure("italic", font=("Segoe UI", 10, "italic"))
        self._preview_text.tag_configure("code", font=("Consolas", 10),
                                          foreground=COLORS["success"],
                                          background="#1a2332")
        self._preview_text.tag_configure("codeblock", font=("Consolas", 9),
                                          foreground=COLORS["success"],
                                          background="#1a2332")
        self._preview_text.tag_configure("math", foreground=COLORS["accent"],
                                          font=("Cambria Math", 10))

    def _toggle_preview(self):
        if self._preview_var.get():
            self._preview_frame.pack(fill=tk.X, pady=(3, 0))
            self._update_preview()
        else:
            self._preview_frame.pack_forget()

    def _setup_tags(self):
        """Configure syntax highlighting tags for the editor."""
        t = self.text
        t.tag_configure("fmt_bold_marker", foreground="#f59e0b")
        t.tag_configure("fmt_bold_text", font=("Segoe UI", 10, "bold"),
                         foreground="#fbbf24")
        t.tag_configure("fmt_italic_marker", foreground="#38bdf8")
        t.tag_configure("fmt_italic_text", font=("Segoe UI", 10, "italic"),
                         foreground="#7dd3fc")
        t.tag_configure("fmt_code_marker", foreground="#065f46")
        t.tag_configure("fmt_code", font=("Consolas", 10),
                         foreground=COLORS["success"])
        t.tag_configure("fmt_codeblock", font=("Consolas", 9),
                         foreground=COLORS["success"], background="#1a2332")
        t.tag_configure("fmt_math_marker", foreground="#0e7490")
        t.tag_configure("fmt_math", foreground=COLORS["accent"])
        t.tag_configure("fmt_html", foreground=COLORS["warning"])
        t.tag_configure("fmt_entity", foreground=COLORS["text_muted"],
                         background="#1c1c2e")

    def _bind_events(self):
        self.text.bind("<KeyRelease>", self._schedule_highlight)

        # Keyboard shortcuts
        def make_handler(p, s):
            def handler(event):
                self._insert_format(p, s)
                return "break"
            return handler

        for key, p, s in [("b", "**", "**"), ("i", "*", "*"),
                           ("e", "`", "`"), ("m", "\\(", "\\)")]:
            self.text.bind(f"<Control-{key}>", make_handler(p, s))
            self.text.bind(f"<Control-{key.upper()}>", make_handler(p, s))

    def _schedule_highlight(self, event=None):
        if self._highlight_job:
            self.after_cancel(self._highlight_job)
        self._highlight_job = self.after(250, self._do_highlight)

    def _do_highlight(self):
        self._highlight_syntax()
        if (self.show_preview and hasattr(self, '_preview_var')
                and self._preview_var.get()):
            self._update_preview()

    def _char_to_index(self, content, pos):
        """Convert character offset to tkinter text index."""
        line = content[:pos].count('\n') + 1
        col = pos - content[:pos].rfind('\n') - 1
        return f"{line}.{col}"

    def _highlight_syntax(self):
        """Apply syntax highlighting to the editor text."""
        content = self.text.get("1.0", "end-1c")
        idx = lambda pos: self._char_to_index(content, pos)

        # Clear existing formatting tags
        for tag in list(self.text.tag_names()):
            if tag.startswith("fmt_"):
                self.text.tag_remove(tag, "1.0", tk.END)

        # Code blocks (highest priority)
        codeblock_ranges = []
        for m in re.finditer(r'```[\w]*\n?([\s\S]*?)```', content):
            s, e = m.start(), m.end()
            codeblock_ranges.append((s, e))
            self.text.tag_add("fmt_codeblock", idx(s), idx(e))

        def in_codeblock(pos):
            return any(s <= pos < e for s, e in codeblock_ranges)

        # Bold **...**
        for m in re.finditer(r'\*\*(.+?)\*\*', content):
            if in_codeblock(m.start()):
                continue
            self.text.tag_add("fmt_bold_marker", idx(m.start()), idx(m.start() + 2))
            self.text.tag_add("fmt_bold_text", idx(m.start() + 2), idx(m.end() - 2))
            self.text.tag_add("fmt_bold_marker", idx(m.end() - 2), idx(m.end()))

        # Italic *...*
        for m in re.finditer(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', content):
            if in_codeblock(m.start()):
                continue
            self.text.tag_add("fmt_italic_marker", idx(m.start()), idx(m.start() + 1))
            self.text.tag_add("fmt_italic_text", idx(m.start() + 1), idx(m.end() - 1))
            self.text.tag_add("fmt_italic_marker", idx(m.end() - 1), idx(m.end()))

        # Inline code `...`
        for m in re.finditer(r'(?<!`)`(?!`)([^`]+?)(?<!`)`(?!`)', content):
            if in_codeblock(m.start()):
                continue
            self.text.tag_add("fmt_code_marker", idx(m.start()), idx(m.start() + 1))
            self.text.tag_add("fmt_code", idx(m.start() + 1), idx(m.end() - 1))
            self.text.tag_add("fmt_code_marker", idx(m.end() - 1), idx(m.end()))

        # Math inline \(...\)
        for m in re.finditer(r'\\\((.+?)\\\)', content, re.DOTALL):
            if in_codeblock(m.start()):
                continue
            self.text.tag_add("fmt_math_marker", idx(m.start()), idx(m.start() + 2))
            self.text.tag_add("fmt_math", idx(m.start() + 2), idx(m.end() - 2))
            self.text.tag_add("fmt_math_marker", idx(m.end() - 2), idx(m.end()))

        # Math display \[...\]
        for m in re.finditer(r'\\\[(.+?)\\\]', content, re.DOTALL):
            if in_codeblock(m.start()):
                continue
            self.text.tag_add("fmt_math_marker", idx(m.start()), idx(m.start() + 2))
            self.text.tag_add("fmt_math", idx(m.start() + 2), idx(m.end() - 2))
            self.text.tag_add("fmt_math_marker", idx(m.end() - 2), idx(m.end()))

        # HTML tags
        for m in re.finditer(r'<[^>]+>', content):
            if in_codeblock(m.start()):
                continue
            self.text.tag_add("fmt_html", idx(m.start()), idx(m.end()))

        # Entities &nbsp; etc
        for m in re.finditer(r'&\w+;', content):
            if in_codeblock(m.start()):
                continue
            self.text.tag_add("fmt_entity", idx(m.start()), idx(m.end()))

    def _update_preview(self):
        """Update the live preview panel."""
        content = self.text.get("1.0", "end-1c")
        self._preview_text.configure(state="normal")
        self._preview_text.delete("1.0", tk.END)
        self._render_preview(content)
        self._preview_text.configure(state="disabled")

    def _render_preview(self, content):
        """Render simplified formatted preview."""
        # Pre-process HTML line breaks and entities
        text = re.sub(r'<br\s*/?>', '\n', content)
        text = text.replace('&nbsp;', ' ')

        all_matches = []

        # Code blocks
        for m in re.finditer(r'```\w*\n?([\s\S]*?)```', text):
            all_matches.append((m.start(), m.end(), m.group(1).strip(), 'codeblock'))
        # Bold
        for m in re.finditer(r'\*\*(.+?)\*\*', text):
            all_matches.append((m.start(), m.end(), m.group(1), 'bold'))
        # Italic
        for m in re.finditer(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', text):
            all_matches.append((m.start(), m.end(), m.group(1), 'italic'))
        # Inline code
        for m in re.finditer(r'(?<!`)`(?!`)([^`]+?)(?<!`)`(?!`)', text):
            all_matches.append((m.start(), m.end(), m.group(1), 'code'))
        # Math inline
        for m in re.finditer(r'\\\((.+?)\\\)', text):
            all_matches.append((m.start(), m.end(), m.group(1), 'math'))
        # Math display
        for m in re.finditer(r'\\\[(.+?)\\\]', text):
            all_matches.append((m.start(), m.end(), m.group(1), 'math'))
        # Remaining HTML tags (remove from preview)
        for m in re.finditer(r'<[^>]+>', text):
            all_matches.append((m.start(), m.end(), '', '_skip'))
        # Remaining entities
        for m in re.finditer(r'&\w+;', text):
            all_matches.append((m.start(), m.end(), '', '_skip'))

        # Sort by position, longer matches first for same position
        all_matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))

        # Remove overlapping matches
        filtered = []
        last_end = 0
        for start, end, inner, tag in all_matches:
            if start >= last_end:
                filtered.append((start, end, inner, tag))
                last_end = end

        # Render segments into preview
        pw = self._preview_text
        pos = 0
        for start, end, inner, tag in filtered:
            if pos < start:
                pw.insert(tk.END, text[pos:start])
            if tag != '_skip':
                pw.insert(tk.END, inner, tag)
            pos = end
        if pos < len(text):
            pw.insert(tk.END, text[pos:])

    def _insert_format(self, prefix, suffix):
        """Insert formatting around selection or at cursor."""
        try:
            sel_start = self.text.index(tk.SEL_FIRST)
            sel_end = self.text.index(tk.SEL_LAST)
            selected = self.text.get(sel_start, sel_end)
            self.text.delete(sel_start, sel_end)
            self.text.insert(sel_start, f"{prefix}{selected}{suffix}")
        except tk.TclError:
            # No selection - insert at cursor
            pos = self.text.index(tk.INSERT)
            self.text.insert(pos, f"{prefix}{suffix}")
            if suffix:
                new_pos = f"{pos}+{len(prefix)}c"
                self.text.mark_set(tk.INSERT, new_pos)
        self.text.focus_set()
        self._schedule_highlight()

    # -- Compatibility proxy methods (match tk.Text interface) --

    def get(self, *args, **kwargs):
        return self.text.get(*args, **kwargs)

    def insert(self, *args, **kwargs):
        result = self.text.insert(*args, **kwargs)
        self._schedule_highlight()
        return result

    def delete(self, *args, **kwargs):
        result = self.text.delete(*args, **kwargs)
        self._schedule_highlight()
        return result


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
        self.window.geometry("1100x800")
        self.window.configure(bg=COLORS["bg_body"])
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

        ttk.Button(toolbar, text="Add Question", command=self.add_question,
                  width=15, bootstyle="success").pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Delete Question", command=self.delete_question,
                  width=18, bootstyle="danger-outline").pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="▲", command=self.move_question_up,
                  width=3, bootstyle="secondary-outline").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="▼", command=self.move_question_down,
                  width=3, bootstyle="secondary-outline").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Save Changes", command=self.save_chapter,
                  width=15, bootstyle="primary").pack(side=tk.RIGHT, padx=5)

        # Main container
        container = ttk.Panedwindow(self.window, orient=tk.HORIZONTAL)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Left panel - Questions list
        left_frame = ttk.Frame(container)
        container.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Questions", style="Header.TLabel").pack(
            fill=tk.X, pady=(0, 5))

        list_scroll = ttk.Scrollbar(left_frame, orient=tk.VERTICAL)
        self.questions_listbox = tk.Listbox(left_frame, yscrollcommand=list_scroll.set)
        _style_tk_listbox(self.questions_listbox)
        list_scroll.config(command=self.questions_listbox.yview)

        self.questions_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.questions_listbox.bind("<<ListboxSelect>>", self.on_question_select)

        # Right panel - Question editor
        right_frame = ttk.Frame(container)
        container.add(right_frame, weight=2)

        ttk.Label(right_frame, text="Edit Question", style="Header.TLabel").pack(
            fill=tk.X, pady=(0, 5))

        # Create scrollable frame for question editor
        self.editor_scroll = ttk.Scrollbar(right_frame, orient=tk.VERTICAL)
        self.editor_canvas = tk.Canvas(right_frame, yscrollcommand=self.editor_scroll.set,
                                        bg=COLORS["bg_card"], highlightthickness=0)
        self.editor_scroll.config(command=self.editor_canvas.yview)

        self.editor_frame = ttk.Frame(self.editor_canvas)
        self.editor_frame.bind("<Configure>", lambda e: self.editor_canvas.configure(
            scrollregion=self.editor_canvas.bbox("all")))

        self.canvas_window = self.editor_canvas.create_window((0, 0), window=self.editor_frame,
                                                               anchor=tk.NW)

        # Stretch editor frame to fill canvas width
        self.editor_canvas.bind('<Configure>',
            lambda e: self.editor_canvas.itemconfigure(self.canvas_window, width=e.width))

        self.editor_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.editor_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Initialize editor widgets (will be populated when question is selected)
        self.init_editor_widgets()
    
    def init_editor_widgets(self):
        """Initialize editor widget placeholders"""
        for widget in self.editor_frame.winfo_children():
            widget.destroy()

        # Question ID
        ttk.Label(self.editor_frame, text="Question ID:", style="SubHeader.TLabel").pack(
            fill=tk.X, padx=10, pady=(10, 5))
        self.q_id = ttk.Entry(self.editor_frame, bootstyle="info")
        self.q_id.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Question Number
        ttk.Label(self.editor_frame, text="Question Number:", style="SubHeader.TLabel").pack(
            fill=tk.X, padx=10, pady=(0, 5))
        self.q_number = ttk.Entry(self.editor_frame, bootstyle="info")
        self.q_number.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Question Text
        ttk.Label(self.editor_frame, text="Question Text:", style="SubHeader.TLabel").pack(
            fill=tk.X, padx=10, pady=(0, 5))
        self.q_text = FormattedTextEditor(self.editor_frame, height=6, show_preview=True)
        self.q_text.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Image
        ttk.Label(self.editor_frame, text="Question Image:", style="SubHeader.TLabel").pack(
            fill=tk.X, padx=10, pady=(0, 5))

        img_frame = ttk.Frame(self.editor_frame)
        img_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.q_image = ttk.Entry(img_frame, state="readonly", bootstyle="info")
        self.q_image.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(img_frame, text="Browse", command=self.select_image,
                  width=10, bootstyle="info-outline").pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(img_frame, text="Clear", command=self.clear_image,
                  width=8, bootstyle="warning-outline").pack(side=tk.LEFT, padx=2)

        # Image preview section
        ttk.Label(self.editor_frame, text="Image Preview:", style="SubHeader.TLabel").pack(
            fill=tk.X, padx=10, pady=(10, 5))
        self.image_preview_frame = ttk.Frame(self.editor_frame, bootstyle="dark")
        self.image_preview_frame.pack(fill=tk.BOTH, padx=10, pady=(0, 10), ipady=20, expand=False)

        self.image_preview_label = ttk.Label(self.image_preview_frame, text="No image selected",
                                              style="Muted.TLabel")
        self.image_preview_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Input Type
        ttk.Label(self.editor_frame, text="Input Type:", style="SubHeader.TLabel").pack(
            fill=tk.X, padx=10, pady=(0, 5))
        self.q_input_type = ttk.Combobox(self.editor_frame, values=["radio", "checkbox"],
                                        state="readonly", width=20, bootstyle="info")
        self.q_input_type.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Correct Answer
        ttk.Label(self.editor_frame, text="Correct Answer(s):", style="SubHeader.TLabel").pack(
            fill=tk.X, padx=10, pady=(0, 5))
        self.q_correct = ttk.Entry(self.editor_frame, bootstyle="info")
        self.q_correct.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Explanation
        ttk.Label(self.editor_frame, text="Explanation:", style="SubHeader.TLabel").pack(
            fill=tk.X, padx=10, pady=(0, 5))
        self.q_explanation = FormattedTextEditor(self.editor_frame, height=4, show_preview=False)
        self.q_explanation.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Choices section
        ttk.Label(self.editor_frame, text="Choices:", style="SubHeader.TLabel").pack(
            fill=tk.X, padx=10, pady=(10, 5))

        # Choices listbox
        choices_frame = ttk.Frame(self.editor_frame)
        choices_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        choices_scroll = ttk.Scrollbar(choices_frame, orient=tk.VERTICAL)
        self.choices_listbox = tk.Listbox(choices_frame, height=5,
                                         yscrollcommand=choices_scroll.set)
        _style_tk_listbox(self.choices_listbox)
        choices_scroll.config(command=self.choices_listbox.yview)

        self.choices_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        choices_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.choices_listbox.bind("<<ListboxSelect>>", self.on_choice_select)

        # Choice edit buttons
        choice_btn_frame = ttk.Frame(self.editor_frame)
        choice_btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Button(choice_btn_frame, text="Add Choice", command=self.add_choice,
                  width=12, bootstyle="success-outline").pack(side=tk.LEFT, padx=2)
        ttk.Button(choice_btn_frame, text="Edit Choice", command=self.edit_choice,
                  width=12, bootstyle="info-outline").pack(side=tk.LEFT, padx=2)
        ttk.Button(choice_btn_frame, text="Delete Choice", command=self.delete_choice,
                  width=14, bootstyle="danger-outline").pack(side=tk.LEFT, padx=2)

        ttk.Button(choice_btn_frame, text="Update Question", command=self.update_current_question,
                  width=16, bootstyle="primary").pack(side=tk.RIGHT, padx=2)
    
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
        _style_dialog(dialog, "Add Choice", "550x380")
        dialog.transient(self.window)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=15, bootstyle="dark")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Choice Value (A, B, C, D):", style="SubHeader.TLabel").pack(
            fill=tk.X, pady=(0, 5))
        val_entry = ttk.Entry(frame, bootstyle="info")
        val_entry.pack(fill=tk.X, pady=(0, 10))
        val_entry.focus()

        ttk.Label(frame, text="Choice Text:", style="SubHeader.TLabel").pack(
            fill=tk.X, pady=(0, 5))
        text_entry = FormattedTextEditor(frame, height=4, show_preview=False)
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

        ttk.Button(frame, text="Add", command=save, width=20, bootstyle="success").pack(pady=10)
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
        _style_dialog(dialog, "Edit Choice", "550x380")
        dialog.transient(self.window)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=15, bootstyle="dark")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Choice Value:", style="SubHeader.TLabel").pack(
            fill=tk.X, pady=(0, 5))
        val_entry = ttk.Entry(frame, bootstyle="info")
        val_entry.insert(0, choice.get('value', ''))
        val_entry.pack(fill=tk.X, pady=(0, 10))
        val_entry.focus()

        ttk.Label(frame, text="Choice Text:", style="SubHeader.TLabel").pack(
            fill=tk.X, pady=(0, 5))
        text_entry = FormattedTextEditor(frame, height=4, show_preview=False)
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

        ttk.Button(frame, text="Save", command=save, width=20, bootstyle="success").pack(pady=10)
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

        dlg = tk.Toplevel(self.window)
        _style_dialog(dlg, "Delete Question", "480x180" if image_path else "480x140")
        dlg.transient(self.window)
        dlg.grab_set()

        frame = ttk.Frame(dlg, padding=12, bootstyle="dark")
        frame.pack(fill=tk.BOTH, expand=True)

        q_num = question.get('number', str(self.current_question_idx + 1))
        ttk.Label(frame, text=f"Delete question {q_num}?", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 8))

        del_image_var = tk.BooleanVar(value=False)
        if image_path:
            ttk.Label(frame, text=f"This question has an image: {image_path}").pack(anchor=tk.W)
            ttk.Checkbutton(frame, text="Also delete image file from disk (permanent)", variable=del_image_var, bootstyle="warning").pack(anchor=tk.W, pady=(4, 8))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        def do_delete():
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

        ttk.Button(btn_frame, text="Delete", command=do_delete, width=12, bootstyle="danger").pack(side=tk.RIGHT, padx=6)
        ttk.Button(btn_frame, text="Cancel", command=cancel, width=12, bootstyle="secondary-outline").pack(side=tk.RIGHT)
    
    def move_question_up(self):
        """Move the selected question up in the list"""
        if self.current_question_idx is None:
            messagebox.showwarning("Warning", "Select a question first")
            return

        idx = self.current_question_idx
        if idx <= 0:
            return

        self.questions[idx], self.questions[idx - 1] = self.questions[idx - 1], self.questions[idx]
        self.current_question_idx = idx - 1
        self.refresh_questions_list()
        self.questions_listbox.selection_set(self.current_question_idx)
        self.display_question()

    def move_question_down(self):
        """Move the selected question down in the list"""
        if self.current_question_idx is None:
            messagebox.showwarning("Warning", "Select a question first")
            return

        idx = self.current_question_idx
        if idx >= len(self.questions) - 1:
            return

        self.questions[idx], self.questions[idx + 1] = self.questions[idx + 1], self.questions[idx]
        self.current_question_idx = idx + 1
        self.refresh_questions_list()
        self.questions_listbox.selection_set(self.current_question_idx)
        self.display_question()

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

        ttk.Button(toolbar, text="Save All", command=self.save_all,
                  width=15, bootstyle="primary").pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Refresh", command=self.refresh_all,
                  width=12, bootstyle="info-outline").pack(side=tk.LEFT, padx=5)

        self.status_label = ttk.Label(toolbar, text="Ready",
                                       foreground=COLORS["success"],
                                       style="Status.TLabel")
        self.status_label.pack(side=tk.RIGHT, padx=10)

        # Main container with PanedWindow
        paned = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Left Panel - Sections
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        # Sections header
        sections_header = ttk.Frame(left_frame)
        sections_header.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(sections_header, text="Sections",
                 style="Header.TLabel").pack(side=tk.LEFT)

        ttk.Button(sections_header, text="+", command=self.add_section,
                  width=3, bootstyle="success-outline").pack(side=tk.RIGHT, padx=2)
        ttk.Button(sections_header, text="Import", command=self.import_section,
              width=6, bootstyle="info-outline").pack(side=tk.RIGHT, padx=2)
        ttk.Button(sections_header, text="Edit", command=self.edit_section,
                  width=4, bootstyle="warning-outline").pack(side=tk.RIGHT, padx=2)
        ttk.Button(sections_header, text="Del", command=self.delete_section,
                  width=3, bootstyle="danger-outline").pack(side=tk.RIGHT, padx=2)

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

        self.sections_tree.tag_configure("oddrow", background=COLORS["treeview_row_odd"])
        self.sections_tree.tag_configure("evenrow", background=COLORS["treeview_row_even"])

        self.sections_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sections_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.sections_tree.bind("<<TreeviewSelect>>", self.on_section_select)

        # Right Panel - Chapters
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)

        # Chapters header
        chapters_header = ttk.Frame(right_frame)
        chapters_header.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(chapters_header, text="Chapters",
                 style="Header.TLabel").pack(side=tk.LEFT)

        ttk.Button(chapters_header, text="+", command=self.add_chapter,
                  width=3, bootstyle="success-outline").pack(side=tk.RIGHT, padx=2)
        ttk.Button(chapters_header, text="Import", command=self.import_chapters,
              width=6, bootstyle="info-outline").pack(side=tk.RIGHT, padx=2)
        ttk.Button(chapters_header, text="Del", command=self.delete_chapter,
                  width=3, bootstyle="danger-outline").pack(side=tk.RIGHT, padx=2)
        ttk.Button(chapters_header, text="▼", command=self.move_chapter_down,
                  width=3, bootstyle="secondary-outline").pack(side=tk.RIGHT, padx=2)
        ttk.Button(chapters_header, text="▲", command=self.move_chapter_up,
                  width=3, bootstyle="secondary-outline").pack(side=tk.RIGHT, padx=2)

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

        self.chapters_tree.tag_configure("oddrow", background=COLORS["treeview_row_odd"])
        self.chapters_tree.tag_configure("evenrow", background=COLORS["treeview_row_even"])

        self.chapters_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        chapters_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.chapters_tree.bind("<<TreeviewSelect>>", self.on_chapter_select)
        self.chapters_tree.bind("<Double-1>", self.on_chapter_double_click)

        # Chapter editor panel
        editor_frame = ttk.LabelFrame(right_frame, text="Edit Chapter")
        editor_frame.pack(fill=tk.X, pady=(10, 0))

        # ID
        ttk.Label(editor_frame, text="ID:", style="SubHeader.TLabel").grid(
            row=0, column=0, sticky=tk.W, pady=8)
        self.ch_id = ttk.Entry(editor_frame, width=15, bootstyle="info")
        self.ch_id.grid(row=0, column=1, sticky=tk.W, padx=10, pady=8)

        # Name
        ttk.Label(editor_frame, text="Name:", style="SubHeader.TLabel").grid(
            row=0, column=2, sticky=tk.W, pady=8, padx=(20, 0))
        self.ch_name = ttk.Entry(editor_frame, width=40, bootstyle="info")
        self.ch_name.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=10, pady=8)

        # Questions count
        ttk.Label(editor_frame, text="Questions:", style="SubHeader.TLabel").grid(
            row=1, column=0, sticky=tk.W, pady=8)
        self.ch_count = ttk.Entry(editor_frame, width=15, bootstyle="info")
        self.ch_count.grid(row=1, column=1, sticky=tk.W, padx=10, pady=8)

        # Update button
        self.update_chapter_btn = ttk.Button(editor_frame, text="Update Chapter",
                                            command=self.update_chapter,
                                            state="disabled",
                                            bootstyle="primary")
        self.update_chapter_btn.grid(row=1, column=3, sticky=tk.E, padx=10, pady=8)

        editor_frame.columnconfigure(3, weight=1)

    def update_status(self, message, color="green"):
        """Update status message"""
        color_map = {
            "green": COLORS["success"],
            "blue": COLORS["primary_light"],
            "orange": COLORS["warning"],
            "red": COLORS["danger"],
        }
        mapped = color_map.get(color, color)
        self.status_label.config(text=message, foreground=mapped)
        self.root.after(3000, lambda: self.status_label.config(
            text="Ready", foreground=COLORS["success"]))
    
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
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.sections_tree.insert("", tk.END, iid=str(idx), values=(
                section['name'],
                section['id'],
                section.get('path', '')
            ), tags=(tag,))
    
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
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.chapters_tree.insert("", tk.END, iid=str(idx), values=(
                chapter.get('id', ''),
                chapter.get('name', ''),
                chapter.get('q', 0),
                chapter.get('file', '')
            ), tags=(tag,))
    
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
        _style_dialog(dialog, "Add New Section", "450x320")
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=20, bootstyle="dark")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Section ID:", style="SubHeader.TLabel").grid(
            row=0, column=0, sticky=tk.W, pady=10)
        sec_id = ttk.Entry(frame, width=30, bootstyle="info")
        sec_id.grid(row=0, column=1, pady=10, padx=10)
        sec_id.focus()

        ttk.Label(frame, text="Section Name:", style="SubHeader.TLabel").grid(
            row=1, column=0, sticky=tk.W, pady=10)
        sec_name = ttk.Entry(frame, width=30, bootstyle="info")
        sec_name.grid(row=1, column=1, pady=10, padx=10)

        ttk.Label(frame, text="Data Path:", style="SubHeader.TLabel").grid(
            row=2, column=0, sticky=tk.W, pady=10)
        sec_path = ttk.Entry(frame, width=30, bootstyle="info")
        sec_path.insert(0, "data/")
        sec_path.grid(row=2, column=1, pady=10, padx=10)

        ttk.Label(frame, text="Description:", style="SubHeader.TLabel").grid(
            row=3, column=0, sticky=tk.W, pady=10)
        sec_desc = ttk.Entry(frame, width=30, bootstyle="info")
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

        ttk.Button(frame, text="Create Section", command=save,
                  width=20, bootstyle="success").grid(row=4, column=0, columnspan=2, pady=20)

        dialog.bind('<Return>', lambda e: save())
    
    def delete_section(self):
        """Delete selected section"""
        if self.current_section_idx is None:
            messagebox.showwarning("Warning", "Select a section first")
            return

        section = self.sections[self.current_section_idx]
        dlg = tk.Toplevel(self.root)
        _style_dialog(dlg, "Delete Section", "480x180")
        dlg.transient(self.root)
        dlg.grab_set()

        frame = ttk.Frame(dlg, padding=12, bootstyle="dark")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=f"Delete section '{section['name']}'?", style="Header.TLabel").pack(anchor=tk.W, pady=(0,8))
        ttk.Label(frame, text="This will remove the section from the config.").pack(anchor=tk.W)

        del_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Also delete section files from disk (permanent)", variable=del_var, bootstyle="warning").pack(anchor=tk.W, pady=8)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10,0))

        def do_delete():
            if del_var.get():
                try:
                    full_path = self.base_path / section.get('path', '')
                    if full_path.exists():
                        shutil.rmtree(full_path)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete section files: {e}")
                    return

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

        ttk.Button(btn_frame, text="Delete", command=do_delete, width=12, bootstyle="danger").pack(side=tk.RIGHT, padx=6)
        ttk.Button(btn_frame, text="Cancel", command=cancel, width=12, bootstyle="secondary-outline").pack(side=tk.RIGHT)
    
    def edit_section(self):
        """Edit the selected section"""
        if self.current_section_idx is None:
            messagebox.showwarning("Warning", "Select a section first")
            return

        section = self.sections[self.current_section_idx]

        dialog = tk.Toplevel(self.root)
        _style_dialog(dialog, "Edit Section", "450x320")
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=20, bootstyle="dark")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Section ID:", style="SubHeader.TLabel").grid(
            row=0, column=0, sticky=tk.W, pady=10)
        sec_id = ttk.Entry(frame, width=30, bootstyle="info")
        sec_id.insert(0, section.get('id', ''))
        sec_id.grid(row=0, column=1, pady=10, padx=10)
        sec_id.focus()

        ttk.Label(frame, text="Section Name:", style="SubHeader.TLabel").grid(
            row=1, column=0, sticky=tk.W, pady=10)
        sec_name = ttk.Entry(frame, width=30, bootstyle="info")
        sec_name.insert(0, section.get('name', ''))
        sec_name.grid(row=1, column=1, pady=10, padx=10)

        ttk.Label(frame, text="Data Path:", style="SubHeader.TLabel").grid(
            row=2, column=0, sticky=tk.W, pady=10)
        sec_path = ttk.Entry(frame, width=30, bootstyle="info")
        sec_path.insert(0, section.get('path', ''))
        sec_path.grid(row=2, column=1, pady=10, padx=10)

        ttk.Label(frame, text="Description:", style="SubHeader.TLabel").grid(
            row=3, column=0, sticky=tk.W, pady=10)
        sec_desc = ttk.Entry(frame, width=30, bootstyle="info")
        sec_desc.insert(0, section.get('description', ''))
        sec_desc.grid(row=3, column=1, pady=10, padx=10)

        def save():
            if not sec_id.get() or not sec_name.get():
                messagebox.showerror("Error", "ID and Name are required")
                return

            section['id'] = sec_id.get()
            section['name'] = sec_name.get()
            section['path'] = sec_path.get()
            section['description'] = sec_desc.get()

            self.current_section = section['id']
            self.refresh_sections_tree()
            self.sections_tree.selection_set(str(self.current_section_idx))
            self.update_status(f"Section updated: {section['name']}", "orange")
            dialog.destroy()

        ttk.Button(frame, text="Save Changes", command=save,
                  width=20, bootstyle="success").grid(row=4, column=0, columnspan=2, pady=20)

        dialog.bind('<Return>', lambda e: save())

    def move_chapter_up(self):
        """Move the selected chapter up in the list"""
        if self.current_chapter_idx is None:
            messagebox.showwarning("Warning", "Select a chapter first")
            return

        idx = self.current_chapter_idx
        if idx <= 0:
            return

        self.chapters[idx], self.chapters[idx - 1] = self.chapters[idx - 1], self.chapters[idx]
        self.current_chapter_idx = idx - 1
        self.refresh_chapters_tree()
        self.chapters_tree.selection_set(str(self.current_chapter_idx))
        self.update_status("Chapter moved up (click Save All)", "orange")

    def move_chapter_down(self):
        """Move the selected chapter down in the list"""
        if self.current_chapter_idx is None:
            messagebox.showwarning("Warning", "Select a chapter first")
            return

        idx = self.current_chapter_idx
        if idx >= len(self.chapters) - 1:
            return

        self.chapters[idx], self.chapters[idx + 1] = self.chapters[idx + 1], self.chapters[idx]
        self.current_chapter_idx = idx + 1
        self.refresh_chapters_tree()
        self.chapters_tree.selection_set(str(self.current_chapter_idx))
        self.update_status("Chapter moved down (click Save All)", "orange")

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
        dlg = tk.Toplevel(self.root)
        _style_dialog(dlg, "Delete Chapter", "500x200")
        dlg.transient(self.root)
        dlg.grab_set()

        frame = ttk.Frame(dlg, padding=12, bootstyle="dark")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=f"Delete chapter '{chapter.get('name','')}'?", style="Header.TLabel").pack(anchor=tk.W, pady=(0,8))
        ttk.Label(frame, text="This will remove the chapter from the list.").pack(anchor=tk.W)

        del_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Also delete chapter file from disk (permanent)", variable=del_var, bootstyle="warning").pack(anchor=tk.W, pady=(8, 0))

        del_images_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Also delete chapter images from disk (permanent)", variable=del_images_var, bootstyle="warning").pack(anchor=tk.W, pady=(4, 8))

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

        ttk.Button(btn_frame, text="Delete", command=do_delete, width=12, bootstyle="danger").pack(side=tk.RIGHT, padx=6)
        ttk.Button(btn_frame, text="Cancel", command=cancel, width=12, bootstyle="secondary-outline").pack(side=tk.RIGHT)

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
        try:
            self.generate_js_config()
        except Exception as e:
            print(f"Auto-config error: {e}")
        self.update_status("✓ All saved & configured", "green")
        
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
                
                # AUTO-SYNC: Respect existing chapters.json order, only append new files
                sec_path = self.base_path / section['path']
                if sec_path.exists():
                    # Load existing chapters.json to preserve manual ordering
                    ch_json_path = sec_path / "chapters.json"
                    existing_chapters = []
                    if ch_json_path.exists():
                        try:
                            with open(ch_json_path, 'r', encoding='utf-8') as f:
                                existing_chapters = json.load(f)
                        except Exception:
                            existing_chapters = []

                    # Track which files are already in chapters.json
                    known_files = {ch.get('file', '') for ch in existing_chapters}

                    # Scan for new chapter files not yet in chapters.json
                    chapter_files = [p for p in sec_path.glob("*.json") if p.name != "chapters.json"]

                    def get_chapter_num(path):
                        match = re.search(r'chapter(\d+)', path.name)
                        return int(match.group(1)) if match else 999

                    chapter_files.sort(key=get_chapter_num)

                    new_chapters = []
                    for ch_file in chapter_files:
                        if ch_file.name in known_files:
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

                            new_chapters.append({
                                "id": str(c_id),
                                "name": c_title,
                                "q": c_q,
                                "file": ch_file.name
                            })
                        except Exception as e:
                            print(f"Skipping {ch_file}: {e}")

                    # Update question counts for existing chapters
                    for ch in existing_chapters:
                        ch_path = sec_path / ch.get('file', '')
                        if ch_path.exists():
                            try:
                                with open(ch_path, 'r', encoding='utf-8') as f:
                                    content = json.load(f)
                                data_obj = content[0] if isinstance(content, list) and content else content
                                if isinstance(content, list) and not content:
                                    data_obj = {}
                                c_q = len(data_obj.get("questions", []))
                                if c_q:
                                    ch['q'] = c_q
                            except Exception:
                                pass

                    # Preserve existing order, append new files at end
                    synced_chapters = existing_chapters + new_chapters

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
    root = ttk.Window(
        title="Exam Engine Editor",
        themename="darkly",
        size=(1200, 700),
    )
    style = ttk.Style()
    _configure_custom_styles(style)
    app = ExamEditor(root)
    root.mainloop()