# How to Add Chapters

1.  **Open the Editor**
    Run the editor script:
    ```bash
    python3 builder/editor.py
    ```

2.  **Select or Create a Section**
    - Click **+ Add** on the left to create a new subject (e.g., "Python Basics").
    - Or select an existing section from the list.

3.  **Add a Chapter**
    - Click **+ Add** on the right side.
    - Enter the **Chapter ID** (e.g., `1` or `intro`).
    - Enter the **Chapter Name**.
    - Click **Save**.

4.  **Add Questions**
    - The editor creates a basic `chapters.json` entry for you.
    - You need to create the actual question file in `data/<section>/chapter<id>.json`.
    - You can copy an existing file (like `data/java2/chapter1.json`) and edit it.
    - **Tip**: You can also just drop any `.json` file into the folder, and the next step will automatically find it!

5.  **Configure and Sync**
    - After you have added your question files:
    - Go to **File > Save All** (optional, but good practice).
    - Go to **Tools > Configure Engine**.
    - This will:
        1.  Scan your folder for new files.
        2.  Update `chapters.json` automatically.
        3.  Update the website configuration.

6.  **Test**
    - Open `index.html` in your browser to see your changes.

---

## JSON Structure Example
Here is a template for a chapter file (e.g., `chapter1.json`):

```json
{
  "title": "Chapter 1: Introduction",
  "questions": [
    {
      "id": "1.1",
      "text": "What is the output of print('Hello')?",
      "choices": [
        { "value": "A", "text": "Hello" },
        { "value": "B", "text": "Hi" }
      ],
      "inputType": "radio",
      "correctAnswer": "A",
      "explanation": "The print function outputs the string to the console."
    }
  ]
}
```

## Handling Questions with Code

When a question includes a code snippet, you must use HTML tags directly inside the `"text"` field of the JSON.

### 1. Structure the Code Block
Wrapped your code in a `span` with monospace styling:
```json
"text": "Analyze the following code:<br><span style=\"font-family:monospace;\"> ... </span>"
```

### 2. Layout & Colors
- **New Lines**: Use `<br>` for every line break.
- **Indentation**: Use `&nbsp;` for each lead space.
- **Syntax Highlighting**: Wrap Java code in these specific classes:
  - `<span class=\"keyword\">`: for keywords (`class`, `public`, `int`, `static`).
  - `<span class=\"literal\">`: for string quotes or decimals.
  - `<span class=\"constant\">`: for numbers.
  - `<span class=\"string\">`: for string content.
  - `<span class=\"comment\">`: for comments.

### Full Example of a Code Question:
```json
{
  "id": "1.2",
  "text": "What is the output of the following code:<br><span style=\"font-family:monospace;\"><br><span class=\"keyword\">int</span> x = <span class=\"constant\">5</span>;<br>System.out.println(x);<br></span>",
  "choices": [
    { "value": "A", "text": "5" },
    { "value": "B", "text": "x" }
  ],
  "inputType": "radio",
  "correctAnswer": "A"
}
```

## Purpose of Files
- **`chapterX.json`**: Contains the actual questions, choices, and answers.
- **`chapters.json`**: Index file inside each data folder. Updated automatically by the engine tool.
- **`sections.json`**: Global config in `config/sections.json` for main subjects.
