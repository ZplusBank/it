# IT Exam System

## Overview
A static, client-side exam engine for IT subjects. It uses a JSON-based data structure and a Python builder tool for management.

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


