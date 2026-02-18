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
    modalCallback: null,

    // Show custom modal (replaces alert/confirm)
    showModal(title, message, isConfirm = false, callback = null) {
        const modal = document.getElementById('appModal');
        const titleEl = document.getElementById('modalTitle');
        const messageEl = document.getElementById('modalMessage');
        const confirmBtn = document.getElementById('modalConfirmBtn');
        const cancelBtn = document.getElementById('modalCancelBtn');

        titleEl.textContent = title;
        messageEl.textContent = message;
        modal.style.display = 'flex';

        if (isConfirm) {
            cancelBtn.style.display = 'inline-block';
            confirmBtn.textContent = 'Confirm';
            confirmBtn.className = 'btn-confirm';
            this.modalCallback = callback;
        } else {
            cancelBtn.style.display = 'none';
            confirmBtn.textContent = 'OK';
            confirmBtn.className = 'btn-confirm';
            this.modalCallback = callback;
        }

        // Focus on confirm button
        setTimeout(() => confirmBtn.focus(), 100);
    },

    closeModal() {
        const modal = document.getElementById('appModal');
        modal.style.display = 'none';
        this.modalCallback = null;
    },

    handleModalConfirm() {
        if (this.modalCallback) {
            this.modalCallback();
        }
        this.closeModal();
    },

    // Loading overlay
    showLoading(message = 'Loading...') {
        const overlay = document.getElementById('loadingOverlay');
        const text = overlay.querySelector('.loading-text');
        text.textContent = message;
        overlay.style.display = 'flex';
    },

    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        overlay.style.display = 'none';
    },

    // Keyboard help
    showKeyboardHelp() {
        document.getElementById('keyboardHelp').style.display = 'flex';
    },

    closeKeyboardHelp() {
        document.getElementById('keyboardHelp').style.display = 'none';
    },

    // Local storage helpers
    saveProgress() {
        if (this.currentView === 'exam' && this.questions.length > 0) {
            const progress = {
                subjectId: this.currentSubject?.id,
                selectedChapters: this.selectedChapters,
                currentQuestionIndex: this.currentQuestionIndex,
                userAnswers: this.userAnswers,
                checkedAnswers: this.checkedAnswers,
                timestamp: Date.now()
            };
            localStorage.setItem('examProgress', JSON.stringify(progress));
        }
    },

    loadProgress() {
        const saved = localStorage.getItem('examProgress');
        if (saved) {
            try {
                const progress = JSON.parse(saved);
                // Check if progress is recent (within 24 hours)
                if (Date.now() - progress.timestamp < 24 * 60 * 60 * 1000) {
                    return progress;
                }
            } catch (e) {
                console.error('Failed to parse saved progress:', e);
            }
        }
        return null;
    },

    clearProgress() {
        localStorage.removeItem('examProgress');
    },

    // Confetti animation (optimized: fewer particles, batched DOM)
    triggerConfetti() {
        const colors = ['#6366f1', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444'];
        const fragment = document.createDocumentFragment();
        const confettiElements = [];
        for (let i = 0; i < 50; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.cssText = `left:${Math.random() * 100}vw;background:${colors[Math.floor(Math.random() * colors.length)]};animation-delay:${Math.random() * 0.5}s;animation-duration:${2 + Math.random() * 2}s`;
            fragment.appendChild(confetti);
            confettiElements.push(confetti);
        }
        document.body.appendChild(fragment);
        setTimeout(() => {
            confettiElements.forEach(el => el.remove());
        }, 5000);
    },

    async init() {
        this.initTheme();
        this.initKeyboardShortcuts();
        this.initModalHandlers();
        await this.loadData();

        // Check for saved progress
        const progress = this.loadProgress();
        if (progress) {
            this.showModal(
                'Resume Exam?',
                'You have an unfinished exam. Would you like to continue where you left off?',
                true,
                () => this.resumeExam(progress)
            );
        }

        this.showSubjectsView();
        this.initSearch();
    },

    initModalHandlers() {
        // Set up modal button handlers
        const confirmBtn = document.getElementById('modalConfirmBtn');
        const cancelBtn = document.getElementById('modalCancelBtn');

        confirmBtn.onclick = () => this.handleModalConfirm();
        cancelBtn.onclick = () => this.closeModal();

        // Close modal on overlay click
        document.getElementById('appModal').addEventListener('click', (e) => {
            if (e.target.id === 'appModal') {
                this.closeModal();
            }
        });

        // Keyboard help button
        const helpBtn = document.getElementById('keyboardHelpBtn');
        if (helpBtn) {
            helpBtn.onclick = () => this.showKeyboardHelp();
        }

        // Close keyboard help on overlay click
        document.getElementById('keyboardHelp').addEventListener('click', (e) => {
            if (e.target.id === 'keyboardHelp') {
                this.closeKeyboardHelp();
            }
        });
    },

    initKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ignore if typing in input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }

            // Escape - Close modals
            if (e.key === 'Escape') {
                this.closeModal();
                this.closeKeyboardHelp();
                return;
            }

            // ? - Show keyboard help
            if (e.key === '?' && this.currentView === 'exam') {
                this.showKeyboardHelp();
                return;
            }

            // Exam view shortcuts
            if (this.currentView === 'exam') {
                // Arrow keys for navigation
                if (e.key === 'ArrowLeft' && !document.getElementById('prevBtn').disabled) {
                    e.preventDefault();
                    this.previousQuestion();
                } else if (e.key === 'ArrowRight' && !document.getElementById('nextBtn').disabled) {
                    e.preventDefault();
                    this.nextQuestion();
                }
                // Enter - Check answer or next
                else if (e.key === 'Enter') {
                    e.preventDefault();
                    const checkBtn = document.getElementById('checkBtn');
                    const nextBtn = document.getElementById('nextBtn');
                    const submitBtn = document.getElementById('submitBtn');

                    if (checkBtn.style.display !== 'none' && !this.checkedAnswers[this.currentQuestionIndex]) {
                        this.checkAnswer();
                    } else if (submitBtn.style.display !== 'none') {
                        this.showReviewModal();
                    } else if (!nextBtn.disabled) {
                        this.nextQuestion();
                    }
                }
                // A, B, C, D - Select answer
                else if (['a', 'b', 'c', 'd', 'e', 'f'].includes(e.key.toLowerCase())) {
                    e.preventDefault();
                    const value = e.key.toUpperCase();
                    const input = document.getElementById(`choice-${value}`);
                    if (input) {
                        input.click();
                    }
                }
            }
        });

        // Auto-save progress periodically during exam
        setInterval(() => {
            if (this.currentView === 'exam') {
                this.saveProgress();
            }
        }, 30000); // Every 30 seconds
    },

    async resumeExam(progress) {
        try {
            this.showLoading('Resuming exam...');

            // Find and select the subject
            const subject = this.subjects.find(s => s.id === progress.subjectId);
            if (!subject) {
                throw new Error('Subject not found');
            }

            this.currentSubject = subject;

            // Load chapters if needed
            if (!subject.loaded) {
                await this.loadChaptersForSubject(subject);
            }

            // Restore state
            this.selectedChapters = progress.selectedChapters;
            this.startExam();
            this.currentQuestionIndex = progress.currentQuestionIndex;
            this.userAnswers = progress.userAnswers;
            this.checkedAnswers = progress.checkedAnswers;

            this.renderCurrentQuestion();
            this.updateQuestionNumberStyles();

            this.hideLoading();
        } catch (error) {
            console.error('Failed to resume exam:', error);
            this.hideLoading();
            this.showModal('Error', 'Failed to resume exam. Starting fresh.');
            this.clearProgress();
        }
    },

    initSearch() {
        const subjectInput = document.getElementById('subjectSearch');
        const chapterInput = document.getElementById('chapterSearch');
        const subjectClear = document.getElementById('subjectSearchClear');
        const chapterClear = document.getElementById('chapterSearchClear');

        // Debounce helper for search performance
        const debounce = (fn, delay) => {
            let timer;
            return (...args) => {
                clearTimeout(timer);
                timer = setTimeout(() => fn(...args), delay);
            };
        };

        if (subjectInput) {
            const debouncedSubjectFilter = debounce((value) => this.filterSubjects(value), 80);
            subjectInput.addEventListener('input', (e) => {
                debouncedSubjectFilter(e.target.value);
                if (subjectClear) {
                    subjectClear.style.display = e.target.value ? 'flex' : 'none';
                }
            });
        }
        if (chapterInput) {
            const debouncedChapterFilter = debounce((value) => this.filterChapters(value), 80);
            chapterInput.addEventListener('input', (e) => {
                debouncedChapterFilter(e.target.value);
                if (chapterClear) {
                    chapterClear.style.display = e.target.value ? 'flex' : 'none';
                }
            });
        }
    },

    clearSearch(type) {
        if (type === 'subject') {
            const input = document.getElementById('subjectSearch');
            const clearBtn = document.getElementById('subjectSearchClear');
            if (input) {
                input.value = '';
                input.focus();
                this.filterSubjects('');
            }
            if (clearBtn) clearBtn.style.display = 'none';
        } else if (type === 'chapter') {
            const input = document.getElementById('chapterSearch');
            const clearBtn = document.getElementById('chapterSearchClear');
            if (input) {
                input.value = '';
                input.focus();
                this.filterChapters('');
            }
            if (clearBtn) clearBtn.style.display = 'none';
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
                this.showModal('Error', 'Exam configuration not found. Please contact support.');
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
            this.showModal('Error', 'Error initializing exam data. Please refresh the page.');
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
            this.showLoading('Loading chapters...');
            try {
                await this.loadChaptersForSubject(subject);
                this.hideLoading();
            } catch (error) {
                console.error('Failed to load chapters:', error);
                this.hideLoading();
                this.showModal('Error', 'Failed to load chapters for this subject. Please try again.');
                return;
            }
        }

        // UX: Check if subject has chapters after loading
        if (subject.chapters.length === 0) {
            this.showModal('Coming Soon', 'This subject has no chapters yet. Please check back later!');
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

        // Reset selection and button state
        this.selectedChapters = [];
        const startBtn = document.getElementById('startExamBtn');
        if (startBtn) {
            startBtn.disabled = true;
            startBtn.style.display = 'none'; // Initially hidden
        }

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
                    <strong>${chapter.id}:</strong> ${this.escapeHtml(chapter.title)}<br>
                    <span>${chapter.totalQuestions} questions</span>
                </label>
            </div>
        `).join('');
    },

    updateSelectedChapters() {
        const checkboxes = document.querySelectorAll('#chaptersGrid input[type="checkbox"]:checked');
        this.selectedChapters = Array.from(checkboxes).map(cb => cb.value);

        const startBtn = document.getElementById('startExamBtn');
        if (startBtn) {
            const hasSelection = this.selectedChapters.length > 0;
            startBtn.disabled = !hasSelection;
            startBtn.style.display = hasSelection ? 'block' : 'none';
        }
    },

    selectAllChapters() {
        const checkboxes = document.querySelectorAll('#chaptersGrid input[type="checkbox"]');
        checkboxes.forEach(cb => {
            if (cb.closest('.chapter-card').style.display !== 'none') {
                cb.checked = true;
            }
        });
        this.updateSelectedChapters();
    },

    selectNoneChapters() {
        const checkboxes = document.querySelectorAll('#chaptersGrid input[type="checkbox"]');
        checkboxes.forEach(cb => cb.checked = false);
        this.updateSelectedChapters();
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
            this.showModal('No Questions', 'Please select at least one chapter.');
            return;
        }

        this.currentQuestionIndex = 0;
        this.userAnswers = {};
        this.checkedAnswers = {};
        this.clearProgress(); // Clear any old progress when starting new exam

        this.showExamView();
    },

    showExamView() {
        this.currentView = 'exam';
        this.hideAllViews();
        document.body.classList.add('exam-active');
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
        const fragment = document.createDocumentFragment();
        this.questions.forEach((q, idx) => {
            const btn = document.createElement('button');
            btn.className = `question-number${idx === 0 ? ' active' : ''}${this.userAnswers[idx] ? ' answered' : ''}`;
            btn.textContent = idx + 1;
            btn.onclick = () => this.goToQuestion(idx);
            fragment.appendChild(btn);
        });
        container.textContent = '';
        container.appendChild(fragment);
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
        if (typeof ContentRenderer.attachImageListeners === 'function') {
            ContentRenderer.attachImageListeners(container);
        } else {
            console.error('ContentRenderer.attachImageListeners is not a function');
        }

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
        // Auto-save on answer change
        this.saveProgress();
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
        if (typeof ContentRenderer.attachImageListeners === 'function') {
            ContentRenderer.attachImageListeners(feedbackEl);
        }
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
                behavior: 'auto',
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
        const buttons = document.querySelectorAll('.question-number');
        const currentIdx = this.currentQuestionIndex;
        const answers = this.userAnswers;
        for (let idx = 0; idx < buttons.length; idx++) {
            const btn = buttons[idx];
            const isActive = idx === currentIdx;
            const isAnswered = !!answers[idx];
            btn.classList.toggle('active', isActive);
            btn.classList.toggle('answered', isAnswered);
        }
        this.updateProgressIndicator();
    },

    updateProgressIndicator() {
        const totalQuestions = this.questions.length;
        const answeredCount = Object.keys(this.userAnswers).filter(idx => {
            const answer = this.userAnswers[idx];
            return answer !== undefined && answer !== '' &&
                (!Array.isArray(answer) || answer.length > 0);
        }).length;

        const percentage = totalQuestions > 0 ? (answeredCount / totalQuestions) * 100 : 0;

        const progressBar = document.getElementById('examProgressBar');
        const answeredCountEl = document.getElementById('answeredCount');
        const totalAnswerableEl = document.getElementById('totalAnswerable');

        if (progressBar) progressBar.style.width = `${percentage}%`;
        if (answeredCountEl) answeredCountEl.textContent = answeredCount;
        if (totalAnswerableEl) totalAnswerableEl.textContent = totalQuestions;
    },

    showReviewModal() {
        const totalQuestions = this.questions.length;
        const answeredCount = Object.keys(this.userAnswers).filter(idx => {
            const answer = this.userAnswers[idx];
            return answer !== undefined && answer !== '' &&
                (!Array.isArray(answer) || answer.length > 0);
        }).length;
        const unansweredCount = totalQuestions - answeredCount;

        // Create review modal content
        const modalHtml = `
            <div class="modal-overlay" id="reviewModal" style="display: flex;">
                <div class="modal review-modal">
                    <div class="modal-header">
                        <h3>📋 Review Your Exam</h3>
                    </div>
                    <div class="modal-body">
                        <div class="review-stats">
                            <div class="review-stat">
                                <div class="review-stat-number">${totalQuestions}</div>
                                <div class="review-stat-label">Total</div>
                            </div>
                            <div class="review-stat">
                                <div class="review-stat-number" style="color: var(--success);">${answeredCount}</div>
                                <div class="review-stat-label">Answered</div>
                            </div>
                            <div class="review-stat">
                                <div class="review-stat-number" style="color: var(--warning);">${unansweredCount}</div>
                                <div class="review-stat-label">Unanswered</div>
                            </div>
                        </div>
                        ${unansweredCount > 0 ? `<p style="color: var(--warning); text-align: center; margin-bottom: 16px;">⚠️ You have ${unansweredCount} unanswered question${unansweredCount > 1 ? 's' : ''}.</p>` : ''}
                        <div class="review-questions-grid">
                            ${this.questions.map((q, idx) => {
            const answer = this.userAnswers[idx];
            const isAnswered = answer !== undefined && answer !== '' &&
                (!Array.isArray(answer) || answer.length > 0);
            return `<button class="review-q-btn ${isAnswered ? 'answered' : 'unanswered'}" 
                                        onclick="app.closeReviewModal(); app.goToQuestion(${idx});">
                                    ${idx + 1}
                                </button>`;
        }).join('')}
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn-cancel" onclick="app.closeReviewModal()">Continue Exam</button>
                        <button class="btn-confirm" onclick="app.confirmSubmit()" style="background: var(--success);">✓ Submit Exam</button>
                    </div>
                </div>
            </div>
        `;

        // Add to body
        const existingModal = document.getElementById('reviewModal');
        if (existingModal) {
            existingModal.remove();
        }
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    },

    closeReviewModal() {
        const modal = document.getElementById('reviewModal');
        if (modal) {
            modal.remove();
        }
    },

    confirmSubmit() {
        this.closeReviewModal();
        this.submitExam();
    },

    submitExam() {
        this.clearProgress(); // Clear saved progress on submit
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

        // Trigger confetti for high scores
        if (percentage >= 90) {
            this.triggerConfetti();
        }

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
        if (typeof ContentRenderer.attachImageListeners === 'function') {
            ContentRenderer.attachImageListeners(document.getElementById('resultDetails'));
        }
    },

    goBackToSubjects() {
        this.showSubjectsView();
    },

    restart() {
        this.selectedChapters = [];
        this.showSubjectsView();
    },

    hideAllViews() {
        document.body.classList.remove('exam-active');
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
            this.showModal(
                'Exit to Home?',
                'Are you sure you want to go to the Home screen? Your current exam progress will be lost.',
                true,
                () => this.restart()
            );
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
        this.showModal(
            'Exit Exam?',
            'Are you sure you want to exit? Your current progress will be lost.',
            true,
            () => this.exitExam()
        );
    },

    closeConfirmModal() {
        // Legacy function for compatibility
        this.closeModal();
    },

    exitExam() {
        this.clearProgress();
        this.restart();
    }
};

// Initialize app when page loads
window.addEventListener('DOMContentLoaded', () => {
    app.init();
});
