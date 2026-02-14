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
    currentSubject: null,

    async init() {
        this.initTheme();
        await this.loadData();
        this.showSubjectsView();
        this.initSearch();
    },

    initSearch() {
        const subjectInput = document.getElementById('subjectSearch');
        const chapterInput = document.getElementById('chapterSearch');

        if (subjectInput) {
            subjectInput.addEventListener('input', (e) => {
                this.filterSubjects(e.target.value);
            });
        }
        if (chapterInput) {
            chapterInput.addEventListener('input', (e) => {
                this.filterChapters(e.target.value);
            });
        }
    },

    filterSubjects(query) {
        const cards = document.querySelectorAll('#subjectsGrid .subject-card');
        const q = query.toLowerCase().trim();
        let visibleCount = 0;

        cards.forEach(card => {
            const name = (card.getAttribute('data-name') || '').toLowerCase();
            const desc = (card.getAttribute('data-desc') || '').toLowerCase();
            const match = !q || name.includes(q) || desc.includes(q);
            card.style.display = match ? '' : 'none';
            if (match) visibleCount++;
        });

        const noResults = document.getElementById('subjectNoResults');
        if (noResults) noResults.style.display = visibleCount === 0 ? 'block' : 'none';
    },

    filterChapters(query) {
        const cards = document.querySelectorAll('#chaptersGrid .chapter-card');
        const q = query.toLowerCase().trim();
        let visibleCount = 0;

        cards.forEach(card => {
            const name = (card.getAttribute('data-name') || '').toLowerCase();
            const match = !q || name.includes(q);
            card.style.display = match ? '' : 'none';
            if (match) visibleCount++;
        });

        const noResults = document.getElementById('chapterNoResults');
        if (noResults) noResults.style.display = visibleCount === 0 ? 'block' : 'none';
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
        // Clear search
        const searchInput = document.getElementById('subjectSearch');
        if (searchInput) { searchInput.value = ''; }
        const noResults = document.getElementById('subjectNoResults');
        if (noResults) noResults.style.display = 'none';
    },

    renderSubjects() {
        const grid = document.getElementById('subjectsGrid');
        grid.innerHTML = this.subjects.map((subject, i) => `
            <div class="subject-card" onclick="app.selectSubject('${subject.id}')"
                 data-name="${this.escapeHtml(subject.name)}" data-desc="${this.escapeHtml(subject.description)}"
                 style="--i: ${i}">
                <span class="subject-icon">${subject.icon}</span>
                <h2>${this.escapeHtml(subject.name)}</h2>
                <p>${this.escapeHtml(subject.description)}</p>
                <span class="chapter-count">${subject.chaptersConfig.length} Chapters</span>
            </div>
        `).join('');
    },

    async selectSubject(subjectId) {
        const subject = this.subjects.find(s => s.id === subjectId);
        this.currentSubject = subject;

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
        // Clear search
        const searchInput = document.getElementById('chapterSearch');
        if (searchInput) { searchInput.value = ''; }
        const noResults = document.getElementById('chapterNoResults');
        if (noResults) noResults.style.display = 'none';
    },

    renderChapters(chapters) {
        const grid = document.getElementById('chaptersGrid');
        grid.innerHTML = chapters.map((chapter, idx) => `
            <div class="chapter-card" data-name="${this.escapeHtml(chapter.title)}" style="--i: ${idx}">
                <input type="checkbox" id="ch-${idx}" value="${chapter.id}" 
                       onchange="app.updateSelectedChapters()">
                <label for="ch-${idx}">
                    <strong>Chapter ${chapter.id}:</strong> ${this.escapeHtml(chapter.title)}<br>
                    <span>${chapter.totalQuestions} questions</span>
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
        const subjectName = this.currentSubject ? this.currentSubject.name : 'Exam';
        document.getElementById('examTitle').textContent = `${subjectName} - Chapter Exam (${this.questions.length} questions)`;
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

        // Render question text through ContentRenderer (Markdown + Math + Code)
        const renderedText = ContentRenderer.render(question.text);

        let imageHtml = '';
        if (question.image) {
            imageHtml = `<div class="question-image"><img src="${question.image}" alt="Question illustration"></div>`;
        }
        let html = `${imageHtml}<div class="question-text">${renderedText}</div>`;

        const isCheckbox = question.inputType === 'checkbox';
        const inputType = isCheckbox ? 'checkbox' : 'radio';
        const currentAnswer = this.userAnswers[this.currentQuestionIndex] || (isCheckbox ? [] : '');

        html += '<div class="choices">';
        question.choices.forEach(choice => {
            const isSelected = isCheckbox
                ? (Array.isArray(currentAnswer) && currentAnswer.includes(choice.value))
                : currentAnswer === choice.value;

            // Render choice text through ContentRenderer
            const renderedChoice = ContentRenderer.render(choice.text);

            html += `
                <div class="choice ${isSelected ? 'selected' : ''}">
                    <input type="${inputType}" 
                           id="choice-${choice.value}" 
                           name="answer"
                           value="${choice.value}"
                           ${isSelected ? 'checked' : ''}
                           onchange="app.selectAnswer('${choice.value}', ${isCheckbox})">
                    <label for="choice-${choice.value}">${renderedChoice}</label>
                </div>
            `;
        });
        html += '</div>';

        container.innerHTML = html;

        // Typeset MathJax on the question container
        ContentRenderer.typeset(container);

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

        const explanationRaw = question.explanation || "Coming soon...";
        const renderedExplanation = ContentRenderer.render(explanationRaw);

        feedbackEl.innerHTML = `
            <strong>${message}</strong>
            <div class="correct-answer">${correctText}</div>
            <div class="explanation" style="margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(0,0,0,0.1);">
                <strong>Explanation:</strong><br>
                ${renderedExplanation}
            </div>
        `;

        // Typeset MathJax on the feedback element
        ContentRenderer.typeset(feedbackEl);
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
        const totalCount = this.questions.length;
        let correctCount = 0;
        let wrongCount = 0;
        let skippedCount = 0;
        const questionResults = [];

        this.questions.forEach((question, idx) => {
            const userAnswer = this.userAnswers[idx];
            const wasSkipped = userAnswer === undefined || userAnswer === '' ||
                (Array.isArray(userAnswer) && userAnswer.length === 0);
            let isCorrect = false;

            if (!wasSkipped) {
                if (question.inputType === 'checkbox') {
                    const correctAnswers = question.correctAnswer.split('');
                    const userAnswers = Array.isArray(userAnswer) ? userAnswer : [];
                    isCorrect = correctAnswers.length === userAnswers.length &&
                        correctAnswers.every(a => userAnswers.includes(a));
                } else {
                    isCorrect = userAnswer === question.correctAnswer;
                }
            }

            if (wasSkipped) skippedCount++;
            else if (isCorrect) correctCount++;
            else wrongCount++;

            questionResults.push({ question, idx, userAnswer, isCorrect, wasSkipped });
        });

        const percentage = Math.round((correctCount / totalCount) * 100);

        document.getElementById('scoreDisplay').textContent = `${correctCount} / ${totalCount}`;
        document.getElementById('scoreText').textContent = `Score: ${percentage}%`;

        // Result message
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

        // Stats bar
        const statsHtml = `
            <div class="results-message">${resultMessage}</div>
            <div class="results-stats">
                <div class="results-stat-card stat-correct" onclick="app.filterResults('correct')" title="Show only correct answers">
                    <div class="stat-icon">✓</div>
                    <div class="stat-number">${correctCount}</div>
                    <div class="stat-label">Correct</div>
                </div>
                <div class="results-stat-card stat-wrong" onclick="app.filterResults('wrong')" title="Show only wrong answers">
                    <div class="stat-icon">✗</div>
                    <div class="stat-number">${wrongCount}</div>
                    <div class="stat-label">Wrong</div>
                </div>
                <div class="results-stat-card stat-skipped" onclick="app.filterResults('skipped')" title="Show only skipped answers">
                    <div class="stat-icon">○</div>
                    <div class="stat-number">${skippedCount}</div>
                    <div class="stat-label">Skipped</div>
                </div>
            </div>
            <div style="text-align: center; margin-bottom: 20px;">
                <button class="nav-btn" onclick="app.filterResults('all')" style="display: inline-block; width: auto; padding: 8px 16px; font-size: 0.9rem; opacity: 0.8;">
                    Show All Questions
                </button>
            </div>
        `;

        // Question review cards
        let cardsHtml = '';
        questionResults.forEach(({ question, idx, userAnswer, isCorrect, wasSkipped }) => {
            const statusClass = wasSkipped ? 'skipped' : (isCorrect ? 'correct' : 'wrong');
            const statusText = wasSkipped ? 'Skipped' : (isCorrect ? 'Correct' : 'Wrong');
            const statusIcon = wasSkipped ? '○' : (isCorrect ? '✓' : '✗');

            const renderedText = ContentRenderer.render(question.text);

            // Question image
            let imageHtml = '';
            if (question.image) {
                imageHtml = `<div class="question-image"><img src="${question.image}" alt="Question illustration"></div>`;
            }

            // Build choices list
            let choicesHtml = '';
            const correctAnswers = question.inputType === 'checkbox'
                ? question.correctAnswer.split('')
                : [question.correctAnswer];
            const userAnswers = wasSkipped ? []
                : (Array.isArray(userAnswer) ? userAnswer : [userAnswer]);

            question.choices.forEach(choice => {
                const isThisCorrect = correctAnswers.includes(choice.value);
                const isUserPick = userAnswers.includes(choice.value);

                let choiceClass = '';
                let choiceIcon = '';
                if (isThisCorrect && isUserPick) {
                    choiceClass = 'correct';
                    choiceIcon = '✓';
                } else if (isThisCorrect) {
                    choiceClass = 'correct';
                    choiceIcon = '✓';
                } else if (isUserPick) {
                    choiceClass = 'user-wrong';
                    choiceIcon = '✗';
                }

                const renderedChoice = ContentRenderer.render(choice.text);
                choicesHtml += `
                    <div class="results-choice ${choiceClass}">
                        <div class="results-choice-letter">${choice.value}</div>
                        <div class="results-choice-text">${renderedChoice}</div>
                        ${choiceIcon ? `<div class="results-choice-icon">${choiceIcon}</div>` : ''}
                    </div>
                `;
            });

            // Explanation
            const explanationRaw = question.explanation || '';
            let explanationHtml = '';
            if (explanationRaw) {
                const renderedExplanation = ContentRenderer.render(explanationRaw);
                explanationHtml = `
                    <div class="results-explanation">
                        <strong>💡 Explanation:</strong>
                        <div class="results-explanation-text">${renderedExplanation}</div>
                    </div>
                `;
            }

            cardsHtml += `
                <div class="results-question-card ${statusClass}">
                    <div class="results-q-header">
                        <span class="results-q-number">Question ${idx + 1}</span>
                        <span class="results-q-badge ${statusClass}">${statusIcon} ${statusText}</span>
                    </div>
                    ${imageHtml}
                    <div class="results-q-text question-text">${renderedText}</div>
                    <div class="results-choices-list">${choicesHtml}</div>
                    ${explanationHtml}
                </div>
            `;
        });

        document.getElementById('resultDetails').innerHTML = `
            ${statsHtml}
            <div class="results-questions-list">${cardsHtml}</div>
        `;

        // Typeset MathJax on the entire results container
        ContentRenderer.typeset(document.getElementById('resultDetails'));
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
    },

    handleHomeClick() {
        if (this.currentView === 'exam' || this.currentView === 'results') {
            if (confirm("Are you sure you want to go to the Home screen? Your current exam progress will be lost.")) {
                this.restart();
            }
        } else {
            this.showSubjectsView();
        }
    },

    filterResults(status) {
        // status: 'correct', 'wrong', 'skipped', 'all'
        const cards = document.querySelectorAll('.results-question-card');

        // Update visual state of filters
        document.querySelectorAll('.results-stat-card').forEach(c => c.style.opacity = '0.5');
        document.querySelectorAll('.results-stat-card').forEach(c => c.style.transform = 'scale(0.95)');

        if (status === 'all') {
            document.querySelectorAll('.results-stat-card').forEach(c => {
                c.style.opacity = '1';
                c.style.transform = '';
            });
        } else {
            const activeCard = document.querySelector(`.results-stat-card.stat-${status}`);
            if (activeCard) {
                activeCard.style.opacity = '1';
                activeCard.style.transform = 'scale(1.05)';
            }
        }

        cards.forEach(card => {
            if (status === 'all') {
                card.style.display = 'block';
            } else {
                if (card.classList.contains(status)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            }
        });
    },

    confirmExit() {
        document.getElementById('confirmModal').style.display = 'flex';
    },

    closeConfirmModal() {
        document.getElementById('confirmModal').style.display = 'none';
    },

    exitExam() {
        this.closeConfirmModal();
        this.restart();
    }
};

// Initialize app when page loads
window.addEventListener('DOMContentLoaded', () => {
    app.init();
});
