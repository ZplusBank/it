/**
 * Lazy Library Loader
 * Loads 3rd-party scripts on-demand to eliminate TBT on initial page load.
 * Each library is loaded at most once; subsequent calls return immediately.
 */
const LibLoader = {
    _loaded: {},
    _loading: {},

    /**
     * Load a single script by URL. Returns a Promise.
     * Deduplicates: if already loaded or loading, reuses the promise.
     */
    loadScript(url) {
        if (this._loaded[url]) return Promise.resolve();
        if (this._loading[url]) return this._loading[url];

        this._loading[url] = new Promise((resolve, reject) => {
            const s = document.createElement('script');
            s.src = url;
            s.onload = () => {
                this._loaded[url] = true;
                delete this._loading[url];
                resolve();
            };
            s.onerror = () => {
                delete this._loading[url];
                reject(new Error('Failed to load: ' + url));
            };
            document.head.appendChild(s);
        });
        return this._loading[url];
    },

    /**
     * Load multiple scripts sequentially (order matters for dependencies).
     */
    async loadScriptsSequential(urls) {
        for (const url of urls) {
            await this.loadScript(url);
        }
    },

    /**
     * Load Marked.js + Prism.js (needed for rendering question content)
     */
    async loadMarkdownAndPrism() {
        if (this._loaded._markdownPrism) return;

        // Load Marked first, then Prism core, then language packs in parallel
        await this.loadScript('https://cdn.jsdelivr.net/npm/marked/marked.min.js');
        await this.loadScript('https://cdn.jsdelivr.net/npm/prismjs@1/prism.min.js');

        // Language packs can load in parallel (they depend on Prism core only)
        await Promise.all([
            this.loadScript('https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-java.min.js'),
            this.loadScript('https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-python.min.js'),
            this.loadScript('https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-c.min.js'),
            this.loadScript('https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-cpp.min.js'),
            this.loadScript('https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-csharp.min.js'),
            this.loadScript('https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-sql.min.js'),
            this.loadScript('https://cdn.jsdelivr.net/npm/prismjs@1/plugins/line-numbers/prism-line-numbers.min.js'),
        ]);

        this._loaded._markdownPrism = true;
    },

    /**
     * Load MathJax (only when math content is detected)
     */
    async loadMathJax() {
        if (this._loaded._mathjax) return;
        if (typeof MathJax !== 'undefined' && MathJax.typesetPromise) {
            this._loaded._mathjax = true;
            return;
        }
        await this.loadScript('https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js');
        // MathJax needs a moment to initialize after script load
        await new Promise(resolve => {
            const check = () => {
                if (typeof MathJax !== 'undefined' && MathJax.typesetPromise) {
                    resolve();
                } else {
                    setTimeout(check, 50);
                }
            };
            check();
        });
        this._loaded._mathjax = true;
    },

    /**
     * Load all content-rendering libs (call before first question render)
     */
    async loadContentLibs() {
        if (this._loaded._contentLibs) return;
        await this.loadMarkdownAndPrism();
        // MathJax loaded lazily on first typeset call, not here
        this._loaded._contentLibs = true;
    }
};
