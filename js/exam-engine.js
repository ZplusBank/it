// ===== STATE =====
let sections = [];
let currentSection = null;
let chapters = [];
let selectedChapters = [];
let questions = [];
let current = 0;
let answers = {};
let start = 0;
let timer = null;
let scoreByChapter = {};

// ===== INIT =====
document.addEventListener('DOMContentLoaded', async () => {
    await loadSections();
    showHome();
});

// ===== SECTIONS =====
async function loadSections() {
    try {
        const res = await fetch('config/sections.json');
        sections = await res.json();
        if (sections.length > 0) {
            currentSection = sections[0].id;
            await loadChapters(currentSection);
        }
    } catch (e) {
        console.error('Error loading sections:', e);
        sections = [{ id: 'java2', name: 'Java 2', path: 'data/java2' }];
        currentSection = 'java2';
        await loadChapters(currentSection);
    }
}

// ===== CHAPTERS =====
async function loadChapters(sectionId) {
    try {
        const section = sections.find(s => s.id === sectionId);
        if (!section) return;

        const res = await fetch(`${section.path}/chapters.json`);
        const data = await res.json();
        chapters = Array.isArray(data) ? data : data.chapters || [];
    } catch (e) {
        console.error('Error loading chapters:', e);
        chapters = [];
    }
}

// ===== PAGE NAVIGATION =====
function show(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(page + 'Page').classList.add('active');
}

function showHome() {
    show('home');
    renderSections();
}

function showChapters() {
    show('chapter');
    renderChapters();
}

function exitExam() { show('home'); }
function reviewAnswers() { show('review'); renderReview(); }

// ===== SECTIONS DISPLAY =====
function renderSections() {
    const container = document.getElementById('sectionsContainer');
    if (!container) return;

    const html = sections.map(s => `
        <label class="chapter-item">
            <input type="radio" name="section" value="${s.id}" onchange="selectSection('${s.id}')">
            <div class="chapter-item-text">
                <h3>${s.name}</h3>
                <p>${s.path}</p>
            </div>
        </label>
    `).join('');

    container.innerHTML = html;
    const btn = document.getElementById('homeStartBtn');
    if (btn) btn.disabled = !currentSection;
}

async function selectSection(sectionId) {
    currentSection = sectionId;
    await loadChapters(sectionId);
    const btn = document.getElementById('homeStartBtn');
    if (btn) btn.disabled = false;
}

async function startFromHome() {
    if (!currentSection) return;
    selectedChapters = chapters;
    showChapters();
}

// ===== CHAPTERS DISPLAY =====
function renderChapters() {
    const titleEl = document.getElementById('sectionTitle');
    if (titleEl) {
        titleEl.textContent = `Select Chapters - ${sections.find(s => s.id === currentSection)?.name}`;
    }

    const html = chapters.map(c => `
        <label class="chapter-item">
            <input type="checkbox" value="${c.id}" onchange="updateSelection()">
            <div class="chapter-item-text">
                <h3>${c.name}</h3>
                <p>${c.q || 0} questions</p>
            </div>
        </label>
    `).join('');

    const container = document.getElementById('chaptersContainer');
    if (container) container.innerHTML = html;
    updateSelection();
}

function updateSelection() {
    const selected = Array.from(
        document.querySelectorAll('#chaptersContainer input:checked')
    ).map(x => {
        const val = x.value;
        return chapters.find(c => c.id === val);
    }).filter(c => c);

    selectedChapters = selected;

    const total = selectedChapters.reduce((s, c) => s + (c.q || 0), 0);

    const selCount = document.getElementById('selCount');
    if (selCount) selCount.textContent = selectedChapters.length;

    const qCount = document.getElementById('qCount');
    if (qCount) qCount.textContent = total;

    const footer = document.getElementById('selectionFooter');
    if (footer) footer.style.display = selectedChapters.length ? 'block' : 'none';

    const startBtn = document.getElementById('startBtn');
    if (startBtn) startBtn.disabled = !selectedChapters.length;
}

// ===== START EXAM =====
async function startExam() {
    if (!selectedChapters.length) return;

    questions = [];
    scoreByChapter = {};

    const section = sections.find(s => s.id === currentSection);
    if (!section) return;

    for (const ch of selectedChapters) {
        try {
            const res = await fetch(`${section.path}/chapter${ch.id}.json`);
            const data = await res.json();
            const chData = Array.isArray(data) ? data[0] : data;

            if (chData.questions) {
                chData.questions.forEach(q => {
                    q.chapter = ch.id;
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
    if (ring) {
        const circumference = 2 * Math.PI * 40;
        ring.style.strokeDashoffset = circumference - (pct / 100) * circumference;
    }

    // Per-chapter results
    let chHtml = '<h4>Per Chapter:</h4>';
    selectedChapters.forEach(ch => {
        const result = scoreByChapter[ch.id];
        if (result) {
            const chPct = Math.round((result.c / result.t) * 100);
            chHtml += `<div class="chapter-result">
                <span>${ch.name}</span>
                <span class="score ${chPct >= 80 ? 'high' : chPct >= 60 ? 'mid' : 'low'}">${chPct}%</span>
            </div>`;
        }
    });
    const perChapter = document.getElementById('perChapter');
    if (perChapter) perChapter.innerHTML = chHtml;

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
