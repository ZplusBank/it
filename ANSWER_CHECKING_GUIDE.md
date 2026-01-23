# Answer Checking Feature Guide

## 🆕 What's New: Smart Answer Verification

The exam platform now includes a **"Check Answer"** button that lets you verify your answer BEFORE submitting the exam. This is perfect for learning and ensuring you understand the material.

## 🎯 How It Works

### For Single-Choice Questions (MCQ)
1. Select an answer (A, B, C, D, E)
2. A **"Check Answer"** button appears below the choices
3. Click it to see if your answer is **correct** or **incorrect**
4. If incorrect, the button shows you the **correct answer**
5. You can change your answer and check again!

### For Multiple-Choice Questions (Multiple Selections)
1. Select multiple answers
2. Click **"Check Answer"**
3. See if your combination of answers is correct
4. Adjust and recheck if needed

## 💡 Key Benefits

- ✅ **Learn as you go** - Understand why answers are right or wrong
- ✅ **No penalties** - Check as many times as you want
- ✅ **Instant feedback** - Know immediately if you're correct
- ✅ **Better retention** - Verify understanding before moving on
- ✅ **Confidence boost** - Submit with confidence knowing your answers

## 📊 Feedback Display

### ✓ Correct Answer
```
✓ Correct!
```
- Green highlight
- Shows your selected answer was right
- You can now proceed to the next question

### ✗ Incorrect Answer
```
✗ Incorrect. Correct answer: B
```
- Red highlight
- Shows the correct answer clearly
- Change your answer and check again if you want

## 🎮 User Flow

```
1. Answer a question
   ↓
2. Click "Check Answer" button
   ↓
3. See if you're correct
   ├─ If Correct → Click "Next" to continue
   └─ If Incorrect → Change answer & check again
   ↓
4. When satisfied, proceed to next question
   ↓
5. Complete all questions
   ↓
6. Submit exam for final scoring
```

## 🔧 Technical Details

### Implementation

The feature is implemented in `js/exam-engine.js`:

```javascript
function checkAnswer(questionId) {
    // Get the current question
    const question = currentChapter.questions.find(q => q.id === questionId);
    
    // Compare user answer with correct answer
    // Supports both single and multiple selections
    
    // Display feedback immediately
    // Allow user to modify and recheck
}
```

### CSS Styling

The visual feedback is styled in `css/styles.css` with:
- Smooth animations (`slideInUp`)
- Color-coded feedback (green for correct, red for incorrect)
- Responsive design for mobile devices
- Accessible contrast ratios

## 📝 Answer Format in JSON

Each question in the JSON files has:

```json
{
  "id": "9.1",
  "text": "Question text...",
  "choices": [
    {"value": "A", "label": "A", "text": "Choice A"},
    {"value": "B", "label": "B", "text": "Choice B"}
  ],
  "inputType": "radio",        // or "checkbox" for multiple
  "correctAnswer": "B"          // or ["A", "B"] for multiple
}
```

## 🚀 Usage Instructions

1. **Open the exam** - Open `index.html` in your browser
2. **Select a chapter** - Click on "Java 2" and choose a chapter
3. **Answer questions** - Select your answer(s)
4. **Check your work** - Click "Check Answer" for instant feedback
5. **Review if needed** - Change your answer and check again
6. **Proceed** - Click "Next" when satisfied
7. **Submit** - Click "Submit" on the last question
8. **View results** - See your final score and review all answers

## 💾 Tracking

- Answer status is tracked during the exam
- Checking an answer does NOT affect your final score
- Only your FINAL submitted answers count
- The feedback is purely educational

## 🎓 Learning Tips

1. **Try first** - Attempt the answer without checking
2. **Check your answer** - Verify your understanding
3. **Learn** - If wrong, read the question again
4. **Recheck** - Change and verify your new answer
5. **Move on** - Proceed only when confident

## ⚙️ Configuration

The feature is automatically enabled for all questions. No configuration needed!

To modify feedback messages or styling, edit:
- Message text: `js/exam-engine.js` - `checkAnswer()` function
- Styling: `css/styles.css` - `.answer-feedback` class

## 🐛 Troubleshooting

**Q: The "Check Answer" button doesn't appear**
- A: Make sure you've selected an answer first. The button only appears after you make a selection.

**Q: The feedback is wrong**
- A: Check the JSON file's `correctAnswer` field matches the actual correct answer.

**Q: Can I check the same answer multiple times?**
- A: Yes! You can check as many times as you want before submitting.

**Q: Does checking affect my score?**
- A: No! Only your final submitted answers affect your score.

## 📞 Support

For questions or issues:
1. Check the `README.md` file
2. Run the editor: `python3 builder/editor.py`
3. Review question data in `data/java2/` JSON files
