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

### Builder Tools (Python)
All scripts are located in the `builder/` directory.

- **editor.py**: Main GUI application built with Tkinter.
  - Allows management of Sections and Chapters.
  - **Configure Engine**: Core function that scans data directories, updates `chapters.json` indices, and generates the `js/exam-config.js` file for the frontend.
- **setup_builder.py**: Utility script to initialize the folder structure and default configuration.
- **test_chapters.py**: CLI validation tool to scan JSON files and report question counts and errors.

## Workflow
1.  **Add Data**: Place new or modified `.json` question files into the appropriate `data/<subject>/` directory.
2.  **Sync**: Run `python3 builder/editor.py` and select **Tools > Configure Engine**.
3.  **Run**: Open `index.html` in a web browser.
