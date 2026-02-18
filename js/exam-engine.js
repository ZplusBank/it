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
            await this.startExam();
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

    // Active fetch controller — allows cancelling in-flight chapter loads
    _chapterLoadController: null,

    async loadChaptersForSubject(subject) {
        if (!subject.chaptersConfig || subject.chaptersConfig.length === 0) {
            subject.loaded = true;
            return;
        }

        // Cancel any previous in-flight load
        if (this._chapterLoadController) {
            this._chapterLoadController.abort();
        }
        this._chapterLoadController = new AbortController();
        const signal = this._chapterLoadController.signal;

        // Concurrency-limited parallel fetch (max 4 at once to avoid saturating network)
        const MAX_CONCURRENT = 4;
        const configs = subject.chaptersConfig.filter(ch => ch.file);
        const chapters = [];

        for (let i = 0; i < configs.length; i += MAX_CONCURRENT) {
            if (signal.aborted) break;
            const batch = configs.slice(i, i + MAX_CONCURRENT);
            const batchResults = await Promise.allSettled(
                batch.map(chInfo => this._fetchChapter(chInfo, signal))
            );
            for (const result of batchResults) {
                if (result.status === 'fulfilled' && result.value) {
                    chapters.push(result.value);
                }
            }
        }

        subject.chapters = chapters;
        subject.loaded = true;
        this._chapterLoadController = null;
    },

    /** Fetch and parse a single chapter file */
    async _fetchChapter(chInfo, signal) {
        try {
            const response = await fetch(`./${chInfo.file}`, { signal });
            if (!response.ok) return null;

            const data = await response.json();
            const chapterData = Array.isArray(data) ? data[0] : data;

            if (!chapterData?.title || !Array.isArray(chapterData.questions)) return null;

            return {
                id: chInfo.id,
                title: chInfo.name || chapterData.title,
                questions: chapterData.questions,
                totalQuestions: chapterData.questions.length
            };
        } catch (e) {
            if (e.name !== 'AbortError') {
                console.warn(`Failed to load ${chInfo.file}:`, e);
            }
            return null;
        }
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

    // Track whether content libs are loaded
    _contentLibsReady: false,

    /**
     * Load content-rendering libraries on demand (Marked, Prism).
     * Called once before first question render.
     */
    async _ensureContentLibs() {
        if (this._contentLibsReady) return;
        if (typeof LibLoader !== 'undefined') {
            await LibLoader.loadContentLibs();
        }
        // Re-initialize ContentRenderer now that libs are loaded
        if (typeof ContentRenderer !== 'undefined') {
            ContentRenderer.init();
        }
        this._contentLibsReady = true;
    },

    async startExam() {
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

        // Lazy-load content rendering libs before showing exam
        this.showLoading('Preparing exam...');
        try {
            await this._ensureContentLibs();
        } catch (e) {
            console.warn('Some content libs failed to load:', e);
        }
        this.hideLoading();

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

    // Cached question number buttons for O(1) class updates
    _questionBtns: [],

    renderQuestionNumbers() {
        const container = document.getElementById('questionNumbers');
        const fragment = document.createDocumentFragment();
        const count = this.questions.length;
        this._questionBtns = new Array(count);

        // Use event delegation instead of per-button onclick
        container.textContent = '';
        container.onclick = (e) => {
            const btn = e.target.closest('.question-number');
            if (!btn) return;
            const idx = parseInt(btn.dataset.idx, 10);
            if (!isNaN(idx)) this.goToQuestion(idx);
        };

        for (let idx = 0; idx < count; idx++) {
            const btn = document.createElement('button');
            btn.className = 'question-number' + (idx === 0 ? ' active' : '') + (this.userAnswers[idx] ? ' answered' : '');
            btn.textContent = idx + 1;
            btn.dataset.idx = idx;
            fragment.appendChild(btn);
            this._questionBtns[idx] = btn;
        }
        container.appendChild(fragment);
    },

    renderCurrentQuestion() {
        const idx = this.currentQuestionIndex;
        const question = this.questions[idx];
        const container = document.getElementById('questionContainer');
        const isCheckbox = question.inputType === 'checkbox';
        const inputType = isCheckbox ? 'checkbox' : 'radio';
        const currentAnswer = this.userAnswers[idx] || (isCheckbox ? [] : '');
        const isLastQuestion = idx === this.questions.length - 1;

        document.getElementById('currentQuestion').textContent = idx + 1;

        // Build DOM with DocumentFragment for single reflow
        const fragment = document.createDocumentFragment();

        // Question image (lazy loaded with decode hints)
        if (question.image) {
            const imgWrapper = document.createElement('div');
            imgWrapper.className = 'question-image';
            const img = document.createElement('img');
            img.src = question.image;
            img.alt = 'Question illustration';
            img.loading = 'lazy';
            img.decoding = 'async';
            imgWrapper.appendChild(img);
            fragment.appendChild(imgWrapper);
        }

        // Question text
        const textDiv = document.createElement('div');
        textDiv.className = 'question-text';
        textDiv.innerHTML = ContentRenderer.render(question.text);
        fragment.appendChild(textDiv);

        // Choices container with event delegation
        const choicesDiv = document.createElement('div');
        choicesDiv.className = 'choices';
        choicesDiv.addEventListener('change', (e) => {
            const input = e.target;
            if (input.name === 'answer') {
                this.selectAnswer(input.value, isCheckbox);
            }
        });

        for (let i = 0; i < question.choices.length; i++) {
            const choice = question.choices[i];
            const isSelected = isCheckbox
                ? (Array.isArray(currentAnswer) && currentAnswer.includes(choice.value))
                : currentAnswer === choice.value;

            const choiceDiv = document.createElement('div');
            choiceDiv.className = 'choice' + (isSelected ? ' selected' : '');

            const input = document.createElement('input');
            input.type = inputType;
            input.id = `choice-${choice.value}`;
            input.name = 'answer';
            input.value = choice.value;
            if (isSelected) input.checked = true;

            const label = document.createElement('label');
            label.htmlFor = `choice-${choice.value}`;
            label.innerHTML = ContentRenderer.render(choice.text);

            choiceDiv.appendChild(input);
            choiceDiv.appendChild(label);
            choicesDiv.appendChild(choiceDiv);
        }
        fragment.appendChild(choicesDiv);

        // Single DOM write
        container.textContent = '';
        container.appendChild(fragment);

        // Typeset MathJax + attach image listeners
        ContentRenderer.typeset(container);
        ContentRenderer.attachImageListeners(container);

        // Update button states (batch reads then writes to avoid layout thrashing)
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const checkBtn = document.getElementById('checkBtn');
        const submitBtn = document.getElementById('submitBtn');
        const feedbackEl = document.getElementById('feedback');

        prevBtn.disabled = idx === 0;
        nextBtn.disabled = false;
        checkBtn.style.display = isLastQuestion ? 'none' : 'block';
        submitBtn.style.display = isLastQuestion ? 'block' : 'none';

        // Clear feedback
        feedbackEl.className = 'feedback';
        feedbackEl.textContent = '';

        // Restore check state if already checked
        if (this.checkedAnswers[idx]) {
            this.showFeedback(idx);
        }
    },

    selectAnswer(value, isCheckbox) {
        const idx = this.currentQuestionIndex;
        if (isCheckbox) {
            const current = this.userAnswers[idx] || [];
            const pos = current.indexOf(value);
            if (pos !== -1) {
                current.splice(pos, 1);
                this.userAnswers[idx] = current;
            } else {
                current.push(value);
                this.userAnswers[idx] = current;
            }
        } else {
            this.userAnswers[idx] = value;
        }
        // Auto-save on answer change
        this.saveProgress();
    },

    checkAnswer() {
        this.checkedAnswers[this.currentQuestionIndex] = true;
        this.showFeedback(this.currentQuestionIndex);
    },

    /** Check if an answer is correct (reusable helper) */
    _isAnswerCorrect(question, userAnswer) {
        if (question.inputType === 'checkbox') {
            const correct = question.correctAnswer.split('');
            const user = Array.isArray(userAnswer) ? userAnswer : [];
            return correct.length === user.length && correct.every(a => user.includes(a));
        }
        return userAnswer === question.correctAnswer;
    },

    showFeedback(index) {
        const question = this.questions[index];
        const userAnswer = this.userAnswers[index];
        const feedbackEl = document.getElementById('feedback');
        const isCorrect = this._isAnswerCorrect(question, userAnswer);

        feedbackEl.className = `feedback ${isCorrect ? 'correct' : 'incorrect'}`;

        const message = isCorrect ? '✓ Correct!' : '✗ Incorrect';
        const correctText = question.inputType === 'checkbox'
            ? `Correct answers: ${question.correctAnswer.split('').join(', ')}`
            : `Correct answer: ${question.correctAnswer}`;

        const explanationRaw = question.explanation || 'Coming soon...';

        // Build feedback DOM
        const frag = document.createDocumentFragment();

        const strong = document.createElement('strong');
        strong.textContent = message;
        frag.appendChild(strong);

        const correctDiv = document.createElement('div');
        correctDiv.className = 'correct-answer';
        correctDiv.textContent = correctText;
        frag.appendChild(correctDiv);

        const explanationDiv = document.createElement('div');
        explanationDiv.className = 'explanation';
        explanationDiv.style.cssText = 'margin-top:10px;padding-top:10px;border-top:1px solid rgba(0,0,0,0.1)';
        explanationDiv.innerHTML = `<strong>Explanation:</strong><br>${ContentRenderer.render(explanationRaw)}`;
        frag.appendChild(explanationDiv);

        feedbackEl.textContent = '';
        feedbackEl.appendChild(frag);

        ContentRenderer.typeset(feedbackEl);
        ContentRenderer.attachImageListeners(feedbackEl);
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
        const btns = this._questionBtns;
        const currentIdx = this.currentQuestionIndex;
        const answers = this.userAnswers;
        for (let idx = 0; idx < btns.length; idx++) {
            const btn = btns[idx];
            if (!btn) continue;
            btn.classList.toggle('active', idx === currentIdx);
            btn.classList.toggle('answered', !!answers[idx]);
        }
        this.updateProgressIndicator();
    },

    updateProgressIndicator() {
        const totalQuestions = this.questions.length;
        let answeredCount = 0;
        for (const idx in this.userAnswers) {
            if (!this._isSkipped(this.userAnswers[idx])) answeredCount++;
        }

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
        let answeredCount = 0;
        for (const idx in this.userAnswers) {
            if (!this._isSkipped(this.userAnswers[idx])) answeredCount++;
        }
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
            const isAnswered = !this._isSkipped(this.userAnswers[idx]);
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

    /** Check if answer was skipped */
    _isSkipped(answer) {
        return answer === undefined || answer === '' ||
            (Array.isArray(answer) && answer.length === 0);
    },

    calculateAndDisplayResults() {
        const totalCount = this.questions.length;
        let correctCount = 0, wrongCount = 0, skippedCount = 0;
        const questionResults = new Array(totalCount);

        // Single pass classification
        for (let idx = 0; idx < totalCount; idx++) {
            const question = this.questions[idx];
            const userAnswer = this.userAnswers[idx];
            const wasSkipped = this._isSkipped(userAnswer);
            const isCorrect = wasSkipped ? false : this._isAnswerCorrect(question, userAnswer);

            if (wasSkipped) skippedCount++;
            else if (isCorrect) correctCount++;
            else wrongCount++;

            questionResults[idx] = { question, idx, userAnswer, isCorrect, wasSkipped };
        }

        const percentage = totalCount > 0 ? Math.round((correctCount / totalCount) * 100) : 0;

        document.getElementById('scoreDisplay').textContent = `${correctCount} / ${totalCount}`;
        document.getElementById('scoreText').textContent = `Score: ${percentage}%`;

        if (percentage >= 90) this.triggerConfetti();

        // Result message lookup (avoids if-else chain)
        const messages = [
            [90, '🌟 Outstanding! You have mastered this material!'],
            [80, '😊 Great job! You have a good understanding.'],
            [70, '👍 Good effort! Keep practicing to improve.'],
            [60, '📚 You\'re making progress. Study more and try again.'],
            [0, '💪 Keep practicing! Review the material and try again.']
        ];
        const resultMessage = messages.find(([threshold]) => percentage >= threshold)[1];

        // Build results DOM using DocumentFragment
        const resultDetails = document.getElementById('resultDetails');
        const mainFrag = document.createDocumentFragment();

        // Stats section
        const messageDiv = document.createElement('div');
        messageDiv.className = 'results-message';
        messageDiv.textContent = resultMessage;
        mainFrag.appendChild(messageDiv);

        const statsDiv = document.createElement('div');
        statsDiv.className = 'results-stats';
        const statDefs = [
            { cls: 'stat-correct', icon: '✓', count: correctCount, label: 'Correct', filter: 'correct' },
            { cls: 'stat-wrong', icon: '✗', count: wrongCount, label: 'Wrong', filter: 'wrong' },
            { cls: 'stat-skipped', icon: '○', count: skippedCount, label: 'Skipped', filter: 'skipped' },
        ];
        for (const stat of statDefs) {
            const card = document.createElement('div');
            card.className = `results-stat-card ${stat.cls}`;
            card.title = `Show only ${stat.label.toLowerCase()} answers`;
            card.onclick = () => this.filterResults(stat.filter);
            card.innerHTML = `<div class="stat-icon">${stat.icon}</div><div class="stat-number">${stat.count}</div><div class="stat-label">${stat.label}</div>`;
            statsDiv.appendChild(card);
        }
        mainFrag.appendChild(statsDiv);

        // Show All button
        const showAllWrap = document.createElement('div');
        showAllWrap.style.cssText = 'text-align:center;margin-bottom:20px';
        const showAllBtn = document.createElement('button');
        showAllBtn.className = 'nav-btn';
        showAllBtn.style.cssText = 'display:inline-block;width:auto;padding:8px 16px;font-size:0.9rem;opacity:0.8';
        showAllBtn.textContent = 'Show All Questions';
        showAllBtn.onclick = () => this.filterResults('all');
        showAllWrap.appendChild(showAllBtn);
        mainFrag.appendChild(showAllWrap);

        // Question cards list
        const listDiv = document.createElement('div');
        listDiv.className = 'results-questions-list';

        for (let i = 0; i < questionResults.length; i++) {
            const { question, idx, userAnswer, isCorrect, wasSkipped } = questionResults[i];
            const statusClass = wasSkipped ? 'skipped' : (isCorrect ? 'correct' : 'wrong');
            const statusText = wasSkipped ? 'Skipped' : (isCorrect ? 'Correct' : 'Wrong');
            const statusIcon = wasSkipped ? '○' : (isCorrect ? '✓' : '✗');

            const card = document.createElement('div');
            card.className = `results-question-card ${statusClass}`;

            // Header
            const header = document.createElement('div');
            header.className = 'results-q-header';
            header.innerHTML = `<span class="results-q-number">Question ${idx + 1}</span><span class="results-q-badge ${statusClass}">${statusIcon} ${statusText}</span>`;
            card.appendChild(header);

            // Image
            if (question.image) {
                const imgWrap = document.createElement('div');
                imgWrap.className = 'question-image';
                const img = document.createElement('img');
                img.src = question.image;
                img.alt = 'Question illustration';
                img.loading = 'lazy';
                img.decoding = 'async';
                imgWrap.appendChild(img);
                card.appendChild(imgWrap);
            }

            // Question text
            const qText = document.createElement('div');
            qText.className = 'results-q-text question-text';
            qText.innerHTML = ContentRenderer.render(question.text);
            card.appendChild(qText);

            // Choices
            const correctAnswers = question.inputType === 'checkbox'
                ? question.correctAnswer.split('') : [question.correctAnswer];
            const userAnswers = wasSkipped ? []
                : (Array.isArray(userAnswer) ? userAnswer : [userAnswer]);

            const choicesList = document.createElement('div');
            choicesList.className = 'results-choices-list';

            for (const choice of question.choices) {
                const isThisCorrect = correctAnswers.includes(choice.value);
                const isUserPick = userAnswers.includes(choice.value);

                let choiceClass = '', choiceIcon = '';
                if (isThisCorrect) { choiceClass = 'correct'; choiceIcon = '✓'; }
                else if (isUserPick) { choiceClass = 'user-wrong'; choiceIcon = '✗'; }

                const choiceDiv = document.createElement('div');
                choiceDiv.className = `results-choice ${choiceClass}`;
                choiceDiv.innerHTML = `<div class="results-choice-letter">${choice.value}</div><div class="results-choice-text">${ContentRenderer.render(choice.text)}</div>${choiceIcon ? `<div class="results-choice-icon">${choiceIcon}</div>` : ''}`;
                choicesList.appendChild(choiceDiv);
            }
            card.appendChild(choicesList);

            // Explanation
            if (question.explanation) {
                const expDiv = document.createElement('div');
                expDiv.className = 'results-explanation';
                expDiv.innerHTML = `<strong>💡 Explanation:</strong><div class="results-explanation-text">${ContentRenderer.render(question.explanation)}</div>`;
                card.appendChild(expDiv);
            }

            listDiv.appendChild(card);
        }
        mainFrag.appendChild(listDiv);

        // Single DOM write
        resultDetails.textContent = '';
        resultDetails.appendChild(mainFrag);

        // Batch typeset & image listeners on the whole container
        ContentRenderer.typeset(resultDetails);
        ContentRenderer.attachImageListeners(resultDetails);
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
