# Exam Platform - Java 2 Edition

A modern, fully-featured exam platform with **267 questions** across **6 chapters** (Chapter 9, 10, 11, 12, 13, 17). Features MCQ, code highlighting, smart answer checking, and comprehensive results tracking.

## 🎯 Features

### Core Functionality
- ✅ **Multiple Question Types**: Support for radio (MCQ) and checkbox (multiple selection) questions
- ✅ **Answer Verification**: Check your answer BEFORE submitting - see if it's correct instantly
- ✅ **Code Syntax Highlighting**: Beautiful code rendering using Highlight.js
- ✅ **6 Complete Chapters**: 267 total questions (Ch 9-13, Ch 17)
- ✅ **Progress Tracking**: Visual progress bar and question counter
- ✅ **Timer**: Exam timer with elapsed time tracking
- ✅ **Results Dashboard**: Score, correct/incorrect counts, time spent
- ✅ **Review Mode**: Review all answers with highlighting after exam

### UI/UX
- 🎨 **Modern Dark Theme**: Premium dark mode with glassmorphism effects
- 🌈 **Gradient Accents**: Beautiful HSL-based gradient colors
- ✨ **Smooth Animations**: Micro-animations and transitions
- 📱 **Responsive Design**: Works on desktop and mobile devices
- 🎯 **Accessible**: Semantic HTML with ARIA labels

## 📊 Content

### Available Chapters
| Chapter | Title | Questions |
|---------|-------|-----------|
| 9 | Objects and Classes | 52 |
| 10 | Object-Oriented Thinking | 47 |
| 11 | Inheritance and Polymorphism | 65 |
| 12 | Exception Handling and Text I/O | 48 |
| 13 | Abstract Classes and Interfaces | 35 |
| 17 | Binary I/O | 20 |
| **Total** | | **267** |

## 📁 Project Structure

```
it/
├── index.html                # Main exam platform
├── README.md                 # This file
├── css/
│   └── styles.css           # All styling
├── js/
│   └── exam-engine.js       # Exam logic & answer checking
├── data/
│   └── java2/
│       ├── chapter9.json    # Chapter data files
│       ├── chapter10.json
│       ├── chapter11.json
│       ├── chapter12.json
│       ├── chapter13.json
│       └── chapter17.json
└── builder/
    └── editor.py            # GUI editor for managing questions
```

## 🚀 Quick Start

### 1. Open in Browser
Simply open `index.html` in a modern web browser (Chrome, Firefox, Safari, Edge).

### 2. How to Use
1. Click on **"Java 2"** section to see available chapters
2. Select a chapter to start the exam
3. **Check your answer** before clicking "Next" to verify if it's correct
4. Complete all questions
5. View your results and review all answers

### 3. Features Explained

#### ✨ Answer Checking (NEW!)
- After selecting an answer, a **"Check Answer"** button appears
- Click it to see if your answer is correct BEFORE submitting
- Helps you learn while taking the exam
- No penalty for checking - learning is encouraged!

#### ⏱️ Timer
- Automatic timer starts when you begin
- Tracks total time spent
- Shows in results dashboard

#### 📊 Results
- Score percentage
- Number of correct/incorrect answers
- Time spent
- Option to review all answers
- Return to home to retake

## 🛠️ Managing Questions

### Using the Editor (GUI)

Edit questions easily with the Python GUI editor:

```bash
cd builder
python3 editor.py
```

#### Features:
- **View all chapters** in a user-friendly list
- **Edit chapter details** (title, question count)
- **See question count** from JSON files
- **Sync all chapters** to exam-engine.js
- **Generate JavaScript code** automatically
- **Check HTML status** to ensure proper setup

### Manual Editing

Edit JSON files directly in `data/java2/` to modify questions, or use the editor for a point-and-click experience.

## 💾 Data Format

Each chapter file is a JSON object with:

```json
{
  "id": "task-0",
  "title": "Chapter 9 Objects and Classes",
  "questions": [
    {
      "id": "9.1",
      "number": "9.1",
      "text": "Question text here...",
      "choices": [
        {"value": "A", "label": "A", "text": "Choice A"},
        {"value": "B", "label": "B", "text": "Choice B"}
      ],
      "inputType": "radio",
      "correctAnswer": "B"
    }
  ],
  "totalQuestions": 52,
  "status": "completed"
}
```

## 🎓 Technologies Used

- **HTML5** - Semantic structure
- **CSS3** - Modern styling with gradients and animations
- **JavaScript (Vanilla)** - No frameworks, pure JS
- **Highlight.js** - Code syntax highlighting
- **Python** - Editor GUI tool

## 🔄 Workflow

1. **Create/Edit Questions** → Use `builder/editor.py` or edit JSON directly
2. **Verify Data** → Run `test_chapters.py` to check all chapters load correctly
3. **Sync Changes** → Use editor to sync to `exam-engine.js`
4. **Test in Browser** → Open `index.html` and test the exam
5. **Review Results** → Check the results dashboard
data/
├── Objects_and_Classes/
├── Data_Structures/
└── Algorithms/
```

### 3. Creating Chapter Files

Each chapter is a JSON file with the following structure:

```json
[
  {
    "id": "task-0",
    "label": "chapter=9, username=liang12e",
    "params": {
      "chapter": "9",
      "username": "liang12e"
    },
    "title": "Chapter 9 Objects and Classes",
    "questions": [
      {
        "id": "9.1",
        "number": "9.1",
        "text": "Question text here with <strong>HTML</strong> support",
        "choices": [
          {
            "value": "A",
            "label": "A",
            "text": "First choice"
          },
          {
            "value": "B",
            "label": "B",
            "text": "Second choice"
          }
        ],
        "inputName": "Q0",
        "inputType": "radio",
        "correctAnswer": "B"
      }
    ],
    "status": "completed",
    "totalQuestions": 52
  }
]
```

### 4. Registering Sections

In `js/exam-engine.js`, update the `loadSections()` function:

```javascript
sections = [
    {
        id: 'objects-and-classes',
        title: 'Objects and Classes',
        icon: '🎯',
        folder: 'Objects_and_Classes',
        chapters: [
            { 
                id: 'chapter9', 
                title: 'Chapter 9 Objects and Classes', 
                file: 'chapter9.json', 
                questions: 52 
            }
        ],
        totalQuestions: 52,
        status: 'not-started'
    },
    // Add more sections here...
];
```

## 📝 Question Types

### Radio (MCQ) - Single Selection

```json
{
  "id": "9.1",
  "number": "9.1",
  "text": "Question text",
  "choices": [...],
  "inputName": "Q0",
  "inputType": "radio",
  "correctAnswer": "B"
}
```

### Checkbox - Multiple Selection

```json
{
  "id": "9.7",
  "number": "9.7",
  "text": "Select all that apply",
  "choices": [...],
  "inputName": "QD6",
  "inputType": "checkbox",
  "correctAnswer": "ABCD"
}
```

For multiple selection, the `correctAnswer` is a string of all correct choice values concatenated (e.g., "ABCD" means A, B, C, and D are all correct).

## 💻 Code Highlighting

The template supports code blocks with syntax highlighting. Use HTML with proper class names:

```html
<span style="font-family:monospace; font-size: 109%;">
  <span class="keyword">public</span> 
  <span class="keyword">class</span> 
  Test {
    <span class="keyword">int</span> x = 
    <span class="constant">5</span>;
  }
</span>
```

Supported classes:
- `.keyword` - Programming keywords (purple)
- `.constant` - Numbers and constants (orange)
- `.literal` - String literals (green)

## 🎨 Customization

### Colors

Edit CSS variables in `css/styles.css`:

```css
:root {
    --primary: hsl(250, 84%, 54%);
    --secondary: hsl(199, 89%, 48%);
    --success: hsl(142, 71%, 45%);
    --danger: hsl(0, 84%, 60%);
    /* ... more colors */
}
```

### Icons

Section icons use emojis. Change them in the sections array:

```javascript
icon: '🎯',  // Change to any emoji
```

### Fonts

The template uses Inter font from Google Fonts. To change:

1. Update the `<link>` in `index.html`
2. Update `font-family` in CSS

## 🔧 Advanced Features

### Status Tracking

The system automatically tracks section status:
- **Not Started**: No chapters attempted
- **In Progress**: Score < 80%
- **Completed**: Score ≥ 80%

### Local Storage

Currently, the template doesn't persist data. To add persistence:

```javascript
// Save answers
localStorage.setItem('exam-answers', JSON.stringify(userAnswers));

// Load answers
const saved = localStorage.getItem('exam-answers');
if (saved) userAnswers = JSON.parse(saved);
```

## 📱 Browser Support

- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ⚠️ IE11 (not supported)

## 🤝 Contributing

To add new features:

1. **New Question Types**: Extend the `renderQuestion()` function
2. **Analytics**: Add tracking in `submitExam()`
3. **Export Results**: Add export functionality in results page

## 📄 License

This template is free to use for educational purposes.

## 🎓 Example Usage

1. **Educational Institutions**: Create course exams
2. **Self-Study**: Build practice quizzes
3. **Certification Prep**: Organize study materials
4. **Code Challenges**: Technical interview preparation

## 🐛 Troubleshooting

### Questions not loading
- Check JSON syntax in chapter files
- Verify file paths in `loadSections()`
- Check browser console for errors

### Code not highlighting
- Ensure Highlight.js CDN is accessible
- Verify code block HTML structure
- Check CSS class names

### Styles not applying
- Clear browser cache
- Check CSS file path
- Verify CSS variable names

## 📞 Support

For issues or questions, please check:
1. JSON structure matches the example
2. File paths are correct
3. Browser console for errors

---

**Built with ❤️ for developers and learners**
