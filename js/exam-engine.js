// ===== STATE =====
let chapters = [];
let selectedChapters = [];
let questions = [];
let current = 0;
let answers = {};
let start = 0;
let timer = null;
let scoreByChapter = {};

// ===== INIT =====
document.addEventListener('DOMContentLoaded', () => {
    loadChapters();
    showHome();
});

// ===== CHAPTERS =====
async function loadChapters() {
    chapters = [
        { id: '9', name: 'Chapter 9 Objects and Classes', q: 52 },
        { id: '10', name: 'Chapter 10 Object-Oriented Thinking', q: 47 },
        { id: '11', name: 'Chapter 11 Inheritance and Polymorphism', q: 65 },
        { id: '12', name: 'Chapter 12 Exception Handling and Text I/O', q: 48 },
        { id: '13', name: 'Chapter 13 Abstract Classes and Interfaces', q: 35 },
        { id: '17', name: 'Chapter 17 Binary I/O', q: 20 }
    ];
}

// ===== PAGE NAVIGATION =====
function show(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(page + 'Page').classList.add('active');
}

function showHome() { show('home'); }
function showChapters() { show('chapter'); renderChapters(); }
function exitExam() { show('home'); }
function reviewAnswers() { show('review'); renderReview(); }

// ===== CHAPTERS DISPLAY =====
function renderChapters() {
    const html = chapters.map(c => `
        <label class="chapter-item">
            <input type="checkbox" value="${c.id}" onchange="updateSelection()">
            <div class="chapter-item-text">
                <h3>${c.name}</h3>
                <p>${c.q} questions</p>
            </div>
        </label>
    `).join('');

    document.getElementById('chaptersContainer').innerHTML = html;
    updateSelection();
}

function updateSelection() {
    selectedChapters = Array.from(
        document.querySelectorAll('#chaptersContainer input:checked')
    ).map(x => x.value);

    const total = selectedChapters.reduce((s, id) => {
        return s + (chapters.find(c => c.id === id)?.q || 0);
    }, 0);

    document.getElementById('selCount').textContent = selectedChapters.length;
    document.getElementById('qCount').textContent = total;
    document.getElementById('selectionFooter').style.display = selectedChapters.length ? 'block' : 'none';
    document.getElementById('startBtn').disabled = !selectedChapters.length;
}

// ===== START EXAM =====
async function startExam() {
    if (!selectedChapters.length) return;

    questions = [];
    scoreByChapter = {};

    for (const chId of selectedChapters) {
        try {
            const res = await fetch(`data/java2/chapter${chId}.json`);
            const data = await res.json();
            const ch = Array.isArray(data) ? data[0] : data;

            if (ch.questions) {
                ch.questions.forEach(q => {
                    q.chapter = chId;
                    questions.push(q);
                });
            }
        } catch (e) {
            console.error('Error loading chapter:', e);
        }
    }

    if (!questions.length) {
        alert('No questions found');
        return;
    }

    current = 0;
    answers = {};
    start = Date.now();
    show('exam');
    startTimer();
    renderQuestion();
}

// ===== QUESTION RENDERING =====
function renderQuestion() {
    if (current < 0 || current >= questions.length) return;

    const q = questions[current];
    const progress = current + 1;
    const total = questions.length;
    const pct = (progress / total) * 100;

    document.getElementById('qNumber').textContent = `Q${progress}`;
    document.getElementById('qChapter').textContent = `Chapter ${q.chapter}`;
    document.getElementById('qProgress').textContent = `${progress}/${total}`;
    document.getElementById('progFill').style.width = pct + '%';
    document.getElementById('qText').textContent = q.text;

    const isMulipte = q.inputType === 'checkbox';
    const saved = answers[current];

    const optHtml = q.choices.map((c, i) => `
        <label class="option">
            <input type="${q.inputType}" name="q${current}" value="${c.value}" 
                   ${(isMulipte && saved?.includes(c.value)) || (!isMulipte && saved === c.value) ? 'checked' : ''}
                   onchange="handleAnswer()">
            <span class="option-text">${c.text}</span>
        </label>
    `).join('');

    document.getElementById('optionsBox').innerHTML = optHtml;
    document.getElementById('feedback').style.display = 'none';
    document.getElementById('feedback').textContent = '';

    const hasAns = isMulipte ? (saved && saved.length > 0) : (saved !== undefined);
    document.getElementById('checkBtn').disabled = !hasAns;
    document.getElementById('prevBtn').disabled = current === 0;
    document.getElementById('nextBtn').style.display = current === questions.length - 1 ? 'none' : 'inline-flex';
    document.getElementById('submitBtn').style.display = current === questions.length - 1 ? 'inline-flex' : 'none';
}

function handleAnswer() {
    const type = questions[current].inputType;
    if (type === 'checkbox') {
        answers[current] = Array.from(
            document.querySelectorAll(`input[name="q${current}"]:checked`)
        ).map(x => x.value);
    } else {
        answers[current] = document.querySelector(`input[name="q${current}"]:checked`)?.value || undefined;
    }
    document.getElementById('checkBtn').disabled = !answers[current];
}

// ===== CHECK ANSWER =====
function checkAnswer() {
    const q = questions[current];
    const ans = answers[current];
    const type = q.inputType;

    let correct = false;

    if (type === 'checkbox') {
        const userAns = ans.sort();
        const rightAns = Array.isArray(q.correctAnswer)
            ? q.correctAnswer.sort()
            : q.correctAnswer.split('').sort();
        correct = JSON.stringify(userAns) === JSON.stringify(rightAns);
    } else {
        correct = ans === q.correctAnswer;
    }

    const fb = document.getElementById('feedback');
    fb.style.display = 'block';
    fb.textContent = correct ? '✓ Correct!' : `✗ Incorrect. Correct: ${Array.isArray(q.correctAnswer) ? q.correctAnswer.join(', ') : q.correctAnswer}`;
    fb.className = correct ? 'correct' : 'incorrect';
}

// ===== NAVIGATION =====
function nextQ() {
    if (current < questions.length - 1) {
        current++;
        renderQuestion();
    }
}

function prevQ() {
    if (current > 0) {
        current--;
        renderQuestion();
    }
}

// ===== SUBMIT EXAM =====
function submitExam() {
    clearInterval(timer);

    let correct = 0;
    scoreByChapter = {};

    questions.forEach((q, i) => {
        const ch = q.chapter;
        if (!scoreByChapter[ch]) scoreByChapter[ch] = { c: 0, t: 0 };
        scoreByChapter[ch].t++;

        let isCorrect = false;
        const ans = answers[i];

        if (q.inputType === 'checkbox') {
            const userAns = (ans || []).sort();
            const rightAns = Array.isArray(q.correctAnswer)
                ? q.correctAnswer.sort()
                : q.correctAnswer.split('').sort();
            isCorrect = JSON.stringify(userAns) === JSON.stringify(rightAns);
        } else {
            isCorrect = ans === q.correctAnswer;
        }

        if (isCorrect) {
            correct++;
            scoreByChapter[ch].c++;
        }
    });

    const total = questions.length;
    const pct = Math.round((correct / total) * 100);
    const time = Math.floor((Date.now() - start) / 1000);

    document.getElementById('scorePct').textContent = pct;
    document.getElementById('cCount').textContent = correct;
    document.getElementById('wCount').textContent = total - correct;
    document.getElementById('time').textContent = formatTime(time);

    // Ring animation
    const ring = document.getElementById('ring');
    const circumference = 2 * Math.PI * 40;
    ring.style.strokeDashoffset = circumference - (pct / 100) * circumference;

    // Per-chapter results
    let chHtml = '<h4>Per Chapter:</h4>';
    selectedChapters.forEach(chId => {
        const result = scoreByChapter[chId];
        if (result) {
            const chName = chapters.find(c => c.id === chId)?.name;
            const chPct = Math.round((result.c / result.t) * 100);
            chHtml += `<div class="chapter-result">
                <span>${chName}</span>
                <span class="score ${chPct >= 80 ? 'high' : chPct >= 60 ? 'mid' : 'low'}">${chPct}%</span>
            </div>`;
        }
    });
    document.querySelector('.per-chapter').innerHTML = chHtml;

    show('results');
}

// ===== REVIEW =====
function renderReview() {
    let html = '';

    questions.forEach((q, i) => {
        const ans = answers[i];
        const type = q.inputType;
        let correct = false;

        if (type === 'checkbox') {
            const userAns = (ans || []).sort();
            const rightAns = Array.isArray(q.correctAnswer)
                ? q.correctAnswer.sort()
                : q.correctAnswer.split('').sort();
            correct = JSON.stringify(userAns) === JSON.stringify(rightAns);
        } else {
            correct = ans === q.correctAnswer;
        }

        html += `<div class="review-item ${correct ? 'correct' : 'incorrect'}">
            <div class="review-q">Q${i + 1}: ${q.text}</div>
            <div class="review-answer review-${correct ? 'correct' : 'wrong'}">
                Your answer: ${ans ? (Array.isArray(ans) ? ans.join(', ') : ans) : 'Not answered'}
            </div>
            ${!correct ? `<div class="review-answer review-correct">Correct: ${Array.isArray(q.correctAnswer) ? q.correctAnswer.join(', ') : q.correctAnswer}</div>` : ''}
        </div>`;
    });

    document.getElementById('reviewBox').innerHTML = html;
}

// ===== TIMER =====
function startTimer() {
    timer = setInterval(() => {
        const elapsed = Math.floor((Date.now() - start) / 1000);
        document.getElementById('timer').textContent = formatTime(elapsed);
    }, 1000);
}

function formatTime(secs) {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
}
