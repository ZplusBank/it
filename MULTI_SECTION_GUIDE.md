# Multi-Section Exam Platform

## Overview

The exam platform has been redesigned to support multiple subjects/sections, each with its own chapters and questions. This modular structure allows easy addition of new subjects without modifying the core code.

## Directory Structure

```
it/
├── config/
│   └── sections.json          # List of all sections
├── data/
│   ├── java2/                 # Java 2 section
│   │   ├── chapters.json      # Chapter metadata
│   │   ├── chapter9.json      # Questions for chapter 9
│   │   ├── chapter10.json     # Questions for chapter 10
│   │   └── ...
│   ├── cpp/                   # C++ section (future)
│   │   ├── chapters.json
│   │   └── chapter*.json
│   └── python/                # Python section (future)
│       ├── chapters.json
│       └── chapter*.json
├── js/
│   └── exam-engine.js         # Main exam engine
├── css/
│   └── styles.css             # Styling
├── builder/
│   └── editor.py              # Section/chapter management tool
└── index.html                 # Main interface
```

## File Formats

### 1. config/sections.json
Defines all available sections/subjects:

```json
[
  {
    "id": "java2",
    "name": "Java 2",
    "path": "data/java2",
    "description": "Java Programming Advanced Topics"
  },
  {
    "id": "cpp",
    "name": "C++",
    "path": "data/cpp",
    "description": "C++ Programming"
  }
]
```

### 2. data/{section}/chapters.json
Defines chapters for a section:

```json
[
  { "id": "9", "name": "Chapter 9 Objects and Classes", "q": 52 },
  { "id": "10", "name": "Chapter 10 OOP Thinking", "q": 47 },
  { "id": "11", "name": "Chapter 11 Inheritance", "q": 65 }
]
```

### 3. data/{section}/chapter{id}.json
Contains actual questions for a chapter:

```json
{
  "chapter": 9,
  "totalQuestions": 52,
  "questions": [
    {
      "text": "What is an object?",
      "choices": [
        { "text": "An instance of a class", "value": "a" },
        { "text": "A blueprint", "value": "b" }
      ],
      "correctAnswer": "a",
      "inputType": "radio"
    }
  ]
}
```

## Adding a New Section

### Step 1: Create data folder
```
mkdir data/cpp
```

### Step 2: Add chapters.json
Create `data/cpp/chapters.json` with chapter metadata.

### Step 3: Add chapter JSON files
Create `data/cpp/chapter1.json`, `data/cpp/chapter2.json`, etc. with questions.

### Step 4: Register section
Use the editor to add the new section:
```bash
python builder/editor.py
```
Click "Add" button and fill in:
- Section ID: `cpp`
- Section Name: `C++`
- Data Path: `data/cpp`

Or manually edit `config/sections.json`:
```json
{
  "id": "cpp",
  "name": "C++",
  "path": "data/cpp",
  "description": "C++ Programming"
}
```

## Using the Editor

Launch the editor GUI:
```bash
python builder/editor.py
```

Features:
- **View Sections**: List all available sections
- **Add/Delete Sections**: Add new subjects or remove existing ones
- **Manage Chapters**: Add/edit/delete chapters for each section
- **Edit Metadata**: Update chapter names and question counts
- **Save Changes**: Persist all changes to JSON files

## How It Works

### Loading Flow
1. App loads → calls `loadSections()` 
2. Fetches `config/sections.json`
3. User selects a section
4. App fetches `data/{section}/chapters.json`
5. User selects chapters
6. App loads questions from `data/{section}/chapter{id}.json` files

### Flexible Chapter Selection
- Users can select one or multiple chapters
- Exam combines all selected chapters
- Questions are shuffled/organized dynamically
- Results show per-chapter breakdown

## JavaScript API

### Loading Sections
```javascript
async function loadSections()
// Loads sections from config/sections.json
```

### Loading Chapters
```javascript
async function loadChapters(sectionId)
// Loads chapters for a specific section
```

### Selecting Section
```javascript
async function selectSection(sectionId)
// Selects a section and loads its chapters
```

### Starting Exam
```javascript
async function startExam()
// Starts exam with selected chapters
```

## Benefits

✅ **Modular Design** - Each section is independent
✅ **Easy to Expand** - Add new subjects without code changes
✅ **Scalable** - Supports unlimited sections and chapters
✅ **Maintainable** - Centralized configuration
✅ **User-Friendly** - Simple section/chapter selection
✅ **Fast Loading** - Only loads what's needed

## Future Sections

Ready to add:
- C++ Programming
- Python Programming
- Data Structures
- Algorithms
- Database Design
- Web Development

## Configuration Tips

### For Large Question Banks
- Split chapters into smaller chunks
- Use logical groupings
- Update `chapters.json` metadata

### For Multi-Language Content
- Create section per language
- Use same question structure
- Point to language-specific data folders

### Performance Optimization
- Keep chapter JSON files under 5MB
- Use lazy loading for large sections
- Consider pagination for large chapters

## Support

For issues or questions, refer to:
- `index.html` - UI structure
- `js/exam-engine.js` - Core logic
- `builder/editor.py` - Management tool
- This README - Documentation
