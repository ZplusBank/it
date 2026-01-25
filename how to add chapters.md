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
