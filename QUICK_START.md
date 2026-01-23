# Quick Start Guide - Multi-Section Platform

## 🚀 Getting Started

### Current Structure
Your platform now supports multiple subjects, starting with **Java 2**:

```
Home Page
  ↓ (Select Java 2)
  ↓
Chapter Selection (9, 10, 11, 12, 13, 17)
  ↓ (Select chapters & click Start)
  ↓
Exam (Answer questions)
  ↓ (Submit)
  ↓
Results (Score + Per-chapter breakdown)
```

## 📁 File Organization

### Configuration
- `config/sections.json` - Register subjects/sections here

### Data
- `data/java2/chapters.json` - Chapter metadata
- `data/java2/chapter9.json` - Questions for chapter 9
- `data/java2/chapter10.json` - Questions for chapter 10
- ... (more chapter files)

## ➕ Adding a New Subject (e.g., C++)

### 1. Create Data Folder
```bash
mkdir data/cpp
```

### 2. Create chapters.json
`data/cpp/chapters.json`:
```json
[
  { "id": "1", "name": "Introduction to C++", "q": 30 },
  { "id": "2", "name": "Variables and Types", "q": 25 },
  { "id": "3", "name": "Functions", "q": 40 }
]
```

### 3. Create Question Files
`data/cpp/chapter1.json`:
```json
{
  "chapter": 1,
  "totalQuestions": 30,
  "questions": [
    {
      "text": "What does C++ stand for?",
      "choices": [
        { "text": "C Plus Plus", "value": "a" },
        { "text": "Computer Plus", "value": "b" }
      ],
      "correctAnswer": "a",
      "inputType": "radio"
    }
  ]
}
```

Repeat for each chapter file (chapter2.json, chapter3.json, etc.)

### 4. Register Section
Option A: Edit `config/sections.json` directly:
```json
[
  {
    "id": "java2",
    "name": "Java 2",
    "path": "data/java2",
    "description": "Java Programming"
  },
  {
    "id": "cpp",
    "name": "C++",
    "path": "data/cpp",
    "description": "C++ Programming"
  }
]
```

Option B: Use the Editor GUI:
```bash
python builder/editor.py
```
- Click "+ Add" in Sections panel
- Fill in: ID, Name, Path
- Click "Save"

## 🎯 How It Works

### Home Page
- Shows all available sections (Java 2, C++, Python, etc.)
- User selects a section
- System loads chapters for that section

### Chapter Selection
- Shows all chapters for selected section
- User checks boxes for chapters to study
- Total question count updates in real-time
- Click "Start Exam" to begin

### Exam
- Questions from selected chapters
- Navigation buttons (Previous/Next)
- "Check Answer" button to verify
- Timer running in background
- "Submit" when complete

### Results
- Overall score percentage
- Correct/Wrong count
- Time taken
- Per-chapter breakdown showing:
  - Chapter name
  - Score for that chapter
  - Visual indicator (color coded)

## 🔧 Editor Tool

Launch: `python builder/editor.py`

Features:
- **Left Panel**: List all sections
  - Add/Delete sections
  - Click to select a section

- **Right Panel**: Manage chapters
  - Add/Delete/Edit chapters
  - Edit chapter ID, name, question count
  - Click "Save" to persist changes

### Workflow
1. Select a section (left panel)
2. View chapters (right panel)
3. Click "Add" to add a new chapter
4. Fill in Chapter ID, Name, Question Count
5. Click "Save"
6. Changes saved to `data/{section}/chapters.json`

## 📊 File Format Reference

### Correct Question Format
```json
{
  "text": "What is OOP?",
  "choices": [
    { "text": "Object-Oriented Programming", "value": "a" },
    { "text": "Optional Output Program", "value": "b" },
    { "text": "Object Ordering Protocol", "value": "c" }
  ],
  "correctAnswer": "a",
  "inputType": "radio"
}
```

### Multiple Choice Question
```json
{
  "text": "Select correct OOP concepts:",
  "choices": [
    { "text": "Inheritance", "value": "a" },
    { "text": "Polymorphism", "value": "b" },
    { "text": "Encapsulation", "value": "c" },
    { "text": "Explosion", "value": "d" }
  ],
  "correctAnswer": ["a", "b", "c"],
  "inputType": "checkbox"
}
```

## ✅ Testing Your Setup

1. Open `index.html` in browser
2. You should see:
   - Home page with Java 2 option
3. Click Java 2
   - Should load all 6 chapters
4. Select some chapters
   - Question count should update
5. Click "Start Exam"
   - Should show first question

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Sections not loading | Check `config/sections.json` exists and is valid JSON |
| Chapters not showing | Verify `data/{section}/chapters.json` exists |
| Questions don't appear | Confirm `data/{section}/chapter{id}.json` files exist |
| Wrong question count | Update `q` field in `chapters.json` to match actual count |
| Editor won't open | Install Python 3.6+, run from correct directory |

## 📝 Next Steps

1. **Verify Java 2 works** - Test selecting chapters and starting exam
2. **Add new section** - Use editor to add C++ or Python
3. **Add questions** - Populate chapter JSON files with test questions
4. **Test thoroughly** - Try all features on mobile and desktop
5. **Deploy** - Copy files to web server

## 🎓 Example Workflow

```
Step 1: User visits index.html
Step 2: Sees "Java 2" button on home page
Step 3: Clicks Java 2
Step 4: Sees chapters 9-17 with checkboxes
Step 5: Selects chapters 9 and 10 (52 + 47 = 99 questions)
Step 6: Clicks "Start Exam"
Step 7: Answers questions with timer running
Step 8: Clicks "Submit"
Step 9: Sees results (e.g., 78% correct, 77/99 questions)
Step 10: Sees breakdown (Chapter 9: 85%, Chapter 10: 72%)
Step 11: Reviews all answers or starts new exam
```

## 💡 Pro Tips

- Keep chapter JSON files under 5MB for better performance
- Use consistent question formats within a section
- Test new sections before adding to sections.json
- Back up your data before making bulk changes
- Use the editor GUI for safe modifications

## 📞 Support Resources

- `MULTI_SECTION_GUIDE.md` - Detailed documentation
- `README.md` - General project info
- `js/exam-engine.js` - Core JavaScript logic
- `builder/editor.py` - Management tool source
