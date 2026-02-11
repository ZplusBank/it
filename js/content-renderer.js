/**
 * Content Renderer Module
 * Processes question text through: Markdown → Code Highlighting → Math Typesetting
 * 
 * Supports:
 *   - LaTeX math/physics: $...$ (inline), $$...$$ (display)
 *   - Chemistry (mhchem): \ce{...}
 *   - Markdown: bold, italic, lists, tables, etc.
 *   - Fenced code blocks: ```java ... ``` with Prism.js highlighting
 *   - Legacy HTML: <span class="keyword">, <br>, &nbsp; pass through unchanged
 */
const ContentRenderer = {

    _placeholder: '%%MATH_BLOCK_',
    _counter: 0,

    /**
     * Initialize Marked.js with Prism.js integration
     */
    init() {
        if (typeof marked === 'undefined') {
            console.warn('Marked.js not loaded — Markdown rendering disabled');
            return;
        }

        const renderer = new marked.Renderer();

        // Override code block renderer to use Prism.js
        renderer.code = function ({ text, lang }) {
            const language = lang && Prism.languages[lang] ? lang : 'plaintext';
            let highlighted;
            try {
                highlighted = Prism.languages[language]
                    ? Prism.highlight(text, Prism.languages[language], language)
                    : ContentRenderer._escapeHtml(text);
            } catch (e) {
                highlighted = ContentRenderer._escapeHtml(text);
            }
            return `<pre class="code-block language-${language}"><code class="language-${language}">${highlighted}</code></pre>`;
        };

        marked.setOptions({
            renderer: renderer,
            gfm: true,
            breaks: true
        });
    },

    /**
     * Render text content: protect math → Markdown → restore math
     * Returns HTML string (MathJax typesetting must be triggered separately)
     */
    render(text) {
        if (!text && text !== 0) return '';
        text = String(text);

        // If Marked is not available, just return the text as-is (backward compat)
        if (typeof marked === 'undefined') {
            return text;
        }

        // Step 1: Protect math/chemistry delimiters from Markdown processing
        const { text: safeText, blocks } = this._protectMath(text);

        // Step 2: Run through Marked.js (Markdown → HTML)
        let html = marked.parse(safeText);

        // Step 3: Restore math blocks
        html = this._restoreMath(html, blocks);

        return html;
    },

    /**
     * Trigger MathJax typesetting on a DOM element
     */
    async typeset(element) {
        if (typeof MathJax !== 'undefined' && MathJax.typesetPromise) {
            try {
                await MathJax.typesetPromise([element]);
            } catch (e) {
                console.warn('MathJax typeset error:', e);
            }
        }
    },

    /**
     * Render text and typeset in one step — sets innerHTML then typesets
     */
    async renderAndTypeset(element, text) {
        element.innerHTML = this.render(text);
        await this.typeset(element);
    },

    /**
     * Replace math delimiters with placeholders so Marked doesn't mangle them
     */
    _protectMath(text) {
        const blocks = [];

        // Protect display math: $$...$$
        text = text.replace(/\$\$([\s\S]*?)\$\$/g, (match) => {
            const id = this._placeholder + (this._counter++) + '%%';
            blocks.push({ id, content: match });
            return id;
        });

        // Protect \ce{...} (chemistry) — handles nested braces
        text = text.replace(/\\ce\{([^}]*(?:\{[^}]*\}[^}]*)*)\}/g, (match) => {
            const id = this._placeholder + (this._counter++) + '%%';
            blocks.push({ id, content: match });
            return id;
        });

        // Protect inline math: $...$  (but not $$)
        text = text.replace(/(?<!\$)\$(?!\$)((?:[^$\\]|\\.)+?)\$/g, (match) => {
            const id = this._placeholder + (this._counter++) + '%%';
            blocks.push({ id, content: match });
            return id;
        });

        return { text, blocks };
    },

    /**
     * Restore math blocks from placeholders
     */
    _restoreMath(html, blocks) {
        for (const block of blocks) {
            html = html.replace(block.id, block.content);
        }
        return html;
    },

    /**
     * Basic HTML escape for fallback
     */
    _escapeHtml(text) {
        if (!text && text !== 0) return '';
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    ContentRenderer.init();
});
