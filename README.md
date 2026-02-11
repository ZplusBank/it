# IT Exam System

## Overview
A client-side exam engine for IT subjects using JSON-based data. Users select a subject → select chapters → take an exam → view results.

## How It Works
1. **Load subjects** from `js/exam-config.js`
2. **Select chapters** to study
3. **Take exam** - answer questions one by one
4. **View results** - score and explanations

## File Structure
```
index.html                    # Main app
js/exam-engine.js            # Exam logic & UI
js/exam-config.js            # Subject & chapter config
css/exam-styles.css          # Styles with dark/light theme
data/<subject>/              # Subject folders
  ├── chapter1.json          # Questions & answers
  ├── chapter2.json
  └── chapters.json          # Chapter index
config/sections.json         # Subject registry
builder/                      # Python tool to manage data
```

## Project Structure

### Web Application
- **index.html**: Single Page Application (SPA) entry point. Contains the layout and containers for Subjects, Chapters, Exam, and Results views.
- **js/exam-engine.js**: Core JavaScript logic. Handles routing, rendering, user state management, and exam scoring.
- **js/exam-config.js**: Generated configuration file. Defines the active subjects and loaded chapters for the web app.
- **css/exam-styles.css**: Stylesheet with support for CSS variables and dark/light theming.

### Data Layer
- **data/<subject>/**: Directory per subject (e.g., java1, algorithm).
  - **chapterX.json**: Source file containing questions, answers, and explanations.
  - **chapters.json**: Index file used by the builder to track chapters.
- **config/sections.json**: Registry of top-level subjects definition (ID, Name, Path).

### How to Add a New Subject / Section or Chapter

#### 1. Add a new subject (section)

**Option A: Create manually (recommended for new subjects)**  
- Click the **+** button in the "Sections" panel  
- Fill in:  
  - Section ID (e.g. `biology`, `grade10-math`)  
  - Section Name (e.g. Biology, Mathematics Grade 10)  
  - Data Path (usually keep default `data/`)  
- Click **Create Section**  

The program automatically creates the folder and empty `chapters.json` file.

**Option B: Import existing subject folder (fastest way)**  
- Click the **↑** (import) button in the "Sections" panel  
- Select the folder that contains your subject's files (must have `chapters.json` and chapter `.json` files)  
- Or select a `.zip` file containing the whole subject folder  
- The tool will copy everything into `data/<section-id>/` and add it to the list automatically

#### 2. Add a chapter inside a subject

**Option A: Create manually**  
- Select the subject in the left panel  
- Click the **+** button in the "Chapters" panel  
- A new chapter appears in the list  
- Select it → edit **Name**, **ID**, **Questions count** in the bottom form  
- Click **✓ Update Chapter**  
- Finally click **💾 Save All** in the top bar

**Option B: Import existing chapter files directly**  
- Select the subject in the left panel  
- Click the **↑** (import) button in the "Chapters" panel  
- Select one or more `.json` chapter files (or a `.zip` containing them)  
- The files are copied into the subject's folder and automatically added to `chapters.json`

#### Quick reminder

- Always click **💾 Save All** after manual changes  
- Use **🔄 Refresh** to reload everything and update the exam engine config (`js/exam-config.js`)  
- Chapter content (questions) must be valid JSON files in the subject's folder

**Example folder structure after adding/importing:**

## JSON Structure

### chapters.json
Index file for a subject containing metadata about all chapters. Located in `data/<subject>/chapters.json`.

**Structure:**
```json
[
  {
    "id": "1",
    "name": "Chapter Name",
    "q": 45,
    "file": "chapter1.json"
  }
]
```

**Fields:**
- **id** (string): Unique identifier for the chapter within the subject
- **name** (string): Display name of the chapter
- **q** (number): Total number of questions in this chapter
- **file** (string): Filename of the chapter data file (e.g., `chapter1.json`)

### Chapter File (chapterX.json)
Contains all questions, answers, and explanations for a chapter. Located in `data/<subject>/chapterX.json`.

**Structure:**
```json
{
  "id": "task-0",
  "label": "chapter=1, username=example",
  "params": {
    "chapter": "1",
    "username": "example"
  },
  "title": "Chapter Title",
  "questions": [
    {
      "id": "1.1",
      "number": "1.1",
      "text": "Question text here<br>",
      "image": "path/to/image.png",
      "choices": [
        {
          "value": "A",
          "label": "A",
          "text": "Choice text"
        }
      ],
      "inputName": "Q0",
      "inputType": "radio",
      "correctAnswer": "A",
      "explanation": "Answer explanation text"
    }
  ]
}
```

**Root Fields:**
- **id** (string): Unique identifier for the task/chapter
- **label** (string): Human-readable label
- **params** (object): Additional metadata parameters (chapter number, username, etc.)
- **title** (string): Display title of the chapter
- **questions** (array): Array of question objects

**Question Object Fields:**
- **id** (string): Unique identifier for the question
- **number** (string): Question number (e.g., "1.1")
- **text** (string): Question content (supports HTML markup)
- **image** (string, optional): URL to question illustration/diagram
- **choices** (array): Array of answer choice objects
- **inputName** (string): Form input field name
- **inputType** (string): Type of input (`radio` for multiple choice, `checkbox` for multiple answers)
- **correctAnswer** (string): Value of the correct choice (or space-separated letters for checkbox type)
- **explanation** (string, optional): Explanation of the correct answer

**Choice Object Fields:**
- **value** (string): Internal value (e.g., "A", "B", "C", "D")
- **label** (string): Display label for the choice
- **text** (string): Display text for the choice


