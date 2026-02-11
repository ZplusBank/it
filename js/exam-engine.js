// Data loading and app initialization
const app = {
    subjects: [],
    allChapters: [],
    selectedChapters: [],
    currentQuestionIndex: 0,
    questions: [],
    userAnswers: {},
    checkedAnswers: {},
    currentView: 'subjects',

    async init() {
        this.initTheme(); // Initialize theme
        await this.loadData();
        this.showSubjectsView();
    },

    initTheme() {
        const toggle = document.getElementById('themeToggle');
        if (!toggle) return;

        // Check local storage or system preference
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            document.documentElement.setAttribute('data-theme', savedTheme);
        }

        toggle.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';

            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });
    },

    async loadData() {
        try {
            if (typeof EXAM_CONFIG === 'undefined') {
                console.error('EXAM_CONFIG not found in exam-config.js');
                this.subjects = [];
                return;
            }

            // Map basic subject info from config without loading chapter files yet
            this.subjects = EXAM_CONFIG.map(subjectConfig => ({
                id: subjectConfig.id,
                name: subjectConfig.name,
                description: subjectConfig.description,
                icon: this.getIconForSubject(subjectConfig.id),
                chaptersConfig: subjectConfig.chapters || [], // Save config for later loading
                chapters: [], // Loaded data goes here
                loaded: false // Track if chapters are loaded
            }));

            // subjects loaded
        } catch (error) {
            console.error('Error loading initial data:', error);
            alert('Error initializing exam data.');
        }
    },

    escapeHtml(text) {
        if (!text && text !== 0) return '';
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\"/g, '&quot;')
            .replace(/'/g, '&#039;');
    },

    getIconForSubject(id) {
        const icons = {
            'java1': '☕',
            'java2': '☕',
            'algorithm': '🧮',
            'data_structure': '🌲',
            'java_advanced': '🚀'
        };
        return icons[id] || '📚';
    },

    showSubjectsView() {
        this.currentView = 'subjects';
        this.resetExam();
        this.hideAllViews();
        document.getElementById('subjectsView').style.display = 'block';
        this.renderSubjects();
    },

    renderSubjects() {
        const grid = document.getElementById('subjectsGrid');
        grid.innerHTML = this.subjects.map(subject => `
            <div class="subject-card" onclick="app.selectSubject('${subject.id}')">
                <div style="font-size: 2.5em; margin-bottom: 10px;">${subject.icon}</div>
                <h2>${this.escapeHtml(subject.name)}</h2>
                <p>${this.escapeHtml(subject.description)}</p>
                <p style="margin-top: 15px; font-size: 0.85em; color: #999;">
                    ${subject.chaptersConfig.length} Chapters Available
                </p>
            </div>
        `).join('');
    },

    async selectSubject(subjectId) {
        const subject = this.subjects.find(s => s.id === subjectId);

        if (!subject) return;

        // If not loaded, fetch chapters now
        if (!subject.loaded) {
            // Show some loading state if possible, though it's usually fast
            try {
                // UX refinement: could show a "Loading chapters..." message here
                await this.loadChaptersForSubject(subject);
            } catch (error) {
                console.error('Failed to load chapters:', error);
                alert('Failed to load chapters for this subject.');
                return;
            }
        }

        // UX: Check if subject has chapters after loading
        if (subject.chapters.length === 0) {
            alert("Coming soon... This subject has no chapters yet.");
            return;
        }

        this.showChaptersView(subject);
    },

    async loadChaptersForSubject(subject) {
        if (!subject.chaptersConfig || subject.chaptersConfig.length === 0) {
            subject.loaded = true;
            return;
        }

        // loading chapters for subject

        const loadingPromises = subject.chaptersConfig.map(async (chInfo) => {
            if (!chInfo.file) return null;
            try {
                const response = await fetch(`./${chInfo.file}`);
                if (response.ok) {
                    const data = await response.json();
                    let chapterData = Array.isArray(data) ? data[0] : data;

                    if (chapterData && chapterData.title && Array.isArray(chapterData.questions)) {
                        return {
                            id: chInfo.id,
                            title: chInfo.name || chapterData.title,
                            questions: chapterData.questions,
                            totalQuestions: chapterData.questions.length
                        };
                    }
                }
            } catch (e) {
                console.warn(`Failed to load ${chInfo.file}:`, e);
            }
            return null;
        });

        const results = await Promise.all(loadingPromises);
        subject.chapters = results.filter(ch => ch !== null);
        subject.loaded = true;
    },

    showChaptersView(subject) {
        this.currentView = 'chapters';
        this.hideAllViews();
        document.getElementById('chaptersView').style.display = 'block';
        this.renderChapters(subject.chapters);
    },

    renderChapters(chapters) {
        const grid = document.getElementById('chaptersGrid');
        grid.innerHTML = chapters.map((chapter, idx) => `
            <div class="chapter-card">
                <input type="checkbox" id="ch-${idx}" value="${chapter.id}" 
                       onchange="app.updateSelectedChapters()">
                <label for="ch-${idx}">
                    <strong>Chapter ${chapter.id}:</strong> ${this.escapeHtml(chapter.title)}<br>
                    <span style="font-size: 0.8em; color: #999;">${chapter.totalQuestions} questions</span>
                </label>
            </div>
        `).join('');
    },

    updateSelectedChapters() {
        const checkboxes = document.querySelectorAll('#chaptersGrid input[type="checkbox"]:checked');
        this.selectedChapters = Array.from(checkboxes).map(cb => cb.value);
        document.getElementById('startExamBtn').disabled = this.selectedChapters.length === 0;
    },

    startExam() {
        // Collect questions from selected chapters
        this.questions = [];
        const selectedChapterIds = new Set(this.selectedChapters);

        this.allChapters = []; // Re-populate for safety or just search in subjects

        // Flatten all chapters from all subjects for easy lookup
        this.subjects.forEach(s => {
            this.allChapters.push(...s.chapters);
        });

        this.allChapters.forEach(chapter => {
            if (selectedChapterIds.has(chapter.id)) {
                this.questions.push(...chapter.questions);
            }
        });

        if (this.questions.length === 0) {
            alert('Please select at least one chapter');
            return;
        }

        this.currentQuestionIndex = 0;
        this.userAnswers = {};
        this.checkedAnswers = {};

        this.showExamView();
    },

    showExamView() {
        this.currentView = 'exam';
        this.hideAllViews();
        document.querySelector('header').style.display = 'none'; // Hide header
        document.getElementById('examView').style.display = 'block';

        // Update title
        document.getElementById('examTitle').textContent = `Java 2 - Chapter Exam (${this.questions.length} questions)`;
        document.getElementById('totalQuestions').textContent = this.questions.length;

        this.renderQuestionNumbers();
        this.renderCurrentQuestion();
    },

    renderQuestionNumbers() {
        const container = document.getElementById('questionNumbers');
        container.innerHTML = this.questions.map((q, idx) => `
            <button class="question-number ${idx === 0 ? 'active' : ''} ${this.userAnswers[idx] ? 'answered' : ''}"
                    onclick="app.goToQuestion(${idx})">
                ${idx + 1}
            </button>
        `).join('');
    },

    renderCurrentQuestion() {
        const question = this.questions[this.currentQuestionIndex];
        const container = document.getElementById('questionContainer');

        document.getElementById('currentQuestion').textContent = this.currentQuestionIndex + 1;

        // Clean and format question text
        let questionText = question.text
            .replace(/&nbsp;/g, ' ')
            .replace(/<br>/g, '<br>')
            .replace(/<span class="keyword">/g, '<span class="keyword">')
            .replace(/<span class="literal">/g, '<span class="literal">')
            .replace(/<span class="constant">/g, '<span class="constant">');

        let imageHtml = '';
        if (question.image) {
            imageHtml = `<div class="question-image"><img src="${question.image}" alt="Question illustration"></div>`;
        }
        let html = `${imageHtml}<div class="question-text">${questionText}</div>`;

        const isCheckbox = question.inputType === 'checkbox';
        const inputType = isCheckbox ? 'checkbox' : 'radio';
        const currentAnswer = this.userAnswers[this.currentQuestionIndex] || (isCheckbox ? [] : '');

        html += '<div class="choices">';
        question.choices.forEach(choice => {
            const isSelected = isCheckbox
                ? (Array.isArray(currentAnswer) && currentAnswer.includes(choice.value))
                : currentAnswer === choice.value;

            html += `
                <div class="choice ${isSelected ? 'selected' : ''}">
                    <input type="${inputType}" 
                           id="choice-${choice.value}" 
                           name="answer"
                           value="${choice.value}"
                           ${isSelected ? 'checked' : ''}
                           onchange="app.selectAnswer('${choice.value}', ${isCheckbox})">
                    <label for="choice-${choice.value}">${choice.text}</label>
                </div>
            `;
        });
        html += '</div>';

        container.innerHTML = html;

        // Update button states
        document.getElementById('prevBtn').disabled = this.currentQuestionIndex === 0;
        document.getElementById('nextBtn').disabled = false;
        document.getElementById('checkBtn').style.display = this.currentQuestionIndex === this.questions.length - 1 ? 'none' : 'block';
        document.getElementById('submitBtn').style.display = this.currentQuestionIndex === this.questions.length - 1 ? 'block' : 'none';

        // Clear feedback
        document.getElementById('feedback').className = 'feedback';
        document.getElementById('feedback').innerHTML = '';

        // Restore check state if already checked
        if (this.checkedAnswers[this.currentQuestionIndex]) {
            this.showFeedback(this.currentQuestionIndex);
        }
    },

    selectAnswer(value, isCheckbox) {
        if (isCheckbox) {
            const currentSelection = this.userAnswers[this.currentQuestionIndex] || [];

            if (currentSelection.includes(value)) {
                this.userAnswers[this.currentQuestionIndex] = currentSelection.filter(v => v !== value);
            } else {
                this.userAnswers[this.currentQuestionIndex] = [...currentSelection, value];
            }
        } else {
            this.userAnswers[this.currentQuestionIndex] = value;
        }
    },

    checkAnswer() {
        this.checkedAnswers[this.currentQuestionIndex] = true;
        this.showFeedback(this.currentQuestionIndex);
    },

    showFeedback(index) {
        const question = this.questions[index];
        const userAnswer = this.userAnswers[index];
        const feedbackEl = document.getElementById('feedback');

        let isCorrect = false;
        if (question.inputType === 'checkbox') {
            const correctAnswers = question.correctAnswer.split('');
            const userAnswers = Array.isArray(userAnswer) ? userAnswer : [];
            isCorrect = correctAnswers.length === userAnswers.length &&
                correctAnswers.every(a => userAnswers.includes(a));
        } else {
            isCorrect = userAnswer === question.correctAnswer;
        }

        feedbackEl.className = `feedback ${isCorrect ? 'correct' : 'incorrect'}`;
        const message = isCorrect ? '✓ Correct!' : '✗ Incorrect';
        const correctText = question.inputType === 'checkbox'
            ? `Correct answers: ${question.correctAnswer.split('').join(', ')}`
            : `Correct answer: ${question.correctAnswer}`;

        const explanationText = question.explanation || "Coming soon...";

        feedbackEl.innerHTML = `
            <strong>${message}</strong>
            <div class="correct-answer">${correctText}</div>
            <div class="explanation" style="margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(0,0,0,0.1);">
                <strong>Explanation:</strong><br>
                ${explanationText}
            </div>
        `;
    },

    goToQuestion(index) {
        this.currentQuestionIndex = index;
        this.renderCurrentQuestion();
        this.updateQuestionNumberStyles();
        this.scrollToActiveQuestion();
    },

    scrollToActiveQuestion() {
        const activeBtn = document.querySelector('.question-number.active');
        if (activeBtn) {
            activeBtn.scrollIntoView({
                behavior: 'smooth',
                block: 'nearest',
                inline: 'center'
            });
        }
    },

    nextQuestion() {
        if (this.currentQuestionIndex < this.questions.length - 1) {
            this.currentQuestionIndex++;
            this.renderCurrentQuestion();
            this.updateQuestionNumberStyles();
        }
    },

    previousQuestion() {
        if (this.currentQuestionIndex > 0) {
            this.currentQuestionIndex--;
            this.renderCurrentQuestion();
            this.updateQuestionNumberStyles();
        }
    },

    updateQuestionNumberStyles() {
        document.querySelectorAll('.question-number').forEach((btn, idx) => {
            btn.classList.remove('active');
            if (idx === this.currentQuestionIndex) {
                btn.classList.add('active');
            }
            if (this.userAnswers[idx]) {
                btn.classList.add('answered');
            } else {
                btn.classList.remove('answered');
            }
        });
    },

    submitExam() {
        this.showResultsView();
    },

    showResultsView() {
        this.currentView = 'results';
        this.hideAllViews();
        document.getElementById('resultsView').style.display = 'block';
        this.calculateAndDisplayResults();
    },

    calculateAndDisplayResults() {
        let correctCount = 0;
        let totalCount = this.questions.length;
        let details = '';

        this.questions.forEach((question, idx) => {
            const userAnswer = this.userAnswers[idx];
            let isCorrect = false;

            if (question.inputType === 'checkbox') {
                const correctAnswers = question.correctAnswer.split('');
                const userAnswers = Array.isArray(userAnswer) ? userAnswer : [];
                isCorrect = correctAnswers.length === userAnswers.length &&
                    correctAnswers.every(a => userAnswers.includes(a));
            } else {
                isCorrect = userAnswer === question.correctAnswer;
            }

            if (isCorrect) correctCount++;

            details += `
                <div class="result-item">
                    <span>Question ${idx + 1}</span>
                    <span>${isCorrect ? '✓' : '✗'}</span>
                </div>
            `;
        });

        const percentage = Math.round((correctCount / totalCount) * 100);

        document.getElementById('scoreDisplay').textContent = `${correctCount} / ${totalCount}`;
        document.getElementById('scoreText').textContent = `Score: ${percentage}%`;

        let resultMessage = '';
        if (percentage >= 90) {
            resultMessage = '🌟 Outstanding! You have mastered this material!';
        } else if (percentage >= 80) {
            resultMessage = '😊 Great job! You have a good understanding.';
        } else if (percentage >= 70) {
            resultMessage = '👍 Good effort! Keep practicing to improve.';
        } else if (percentage >= 60) {
            resultMessage = '📚 You\'re making progress. Study more and try again.';
        } else {
            resultMessage = '💪 Keep practicing! Review the material and try again.';
        }

        document.getElementById('resultDetails').innerHTML = `
            <div style="text-align: center; margin-bottom: 20px; font-size: 1.1em; color: #667eea; font-weight: 600;">
                ${resultMessage}
            </div>
            <div style="max-height: 300px; overflow-y: auto;">
                ${details}
            </div>
        `;
    },

    goBackToSubjects() {
        this.showSubjectsView();
    },

    restart() {
        this.selectedChapters = [];
        this.showSubjectsView();
    },

    hideAllViews() {
        document.querySelector('header').style.display = 'block'; // Show header by default
        document.getElementById('subjectsView').style.display = 'none';
        document.getElementById('chaptersView').style.display = 'none';
        document.getElementById('examView').style.display = 'none';
        document.getElementById('resultsView').style.display = 'none';
    },

    resetExam() {
        this.currentQuestionIndex = 0;
        this.questions = [];
        this.userAnswers = {};
        this.checkedAnswers = {};
    }
};

// Initialize app when page loads
window.addEventListener('DOMContentLoaded', () => {
    app.init();
});
