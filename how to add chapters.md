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

5.  **Configure the Engine**
    - Click the **Configure Engine** button in the editor.
    - This updates the website to include your new chapters.

6.  **Test**
    - Open `index.html` in your browser to see your changes.
