/**
 * Content Renderer Module
 * Processes question text through: Markdown → Code Highlighting → Math Typesetting
 * 
 * Supports:
 *   - LaTeX math/physics: \(...\) (inline), \[...\] (display)
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

        // Override code block renderer to use Prism.js with line numbers, language badge, and copy button
        renderer.code = function ({ text, lang }) {
            const language = lang && Prism.languages[lang] ? lang : 'plaintext';
            const displayLang = language.charAt(0).toUpperCase() + language.slice(1);
            let highlighted;
            try {
                highlighted = Prism.languages[language]
                    ? Prism.highlight(text, Prism.languages[language], language)
                    : ContentRenderer._escapeHtml(text);
            } catch (e) {
                highlighted = ContentRenderer._escapeHtml(text);
            }
            return `<div class="code-block-wrapper">
                <div class="code-block-header">
                    <span class="code-block-dots"><span></span><span></span><span></span></span>
                    <span class="code-block-lang">${displayLang}</span>
                    <button class="code-copy-btn" onclick="ContentRenderer.copyCode(this)" title="Copy code">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                        <span class="copy-label">Copy</span>
                    </button>
                </div>
                <pre class="code-block language-${language} line-numbers"><code class="language-${language}">${highlighted}</code></pre>
            </div>`;
        };

        // Override em (italic) — skip if content is empty or whitespace-only
        renderer.em = function ({ text }) {
            if (!text || !text.trim()) return `*${text || ''}*`;
            return `<em>${text}</em>`;
        };

        // Override strong (bold) — skip if content is empty or whitespace-only
        // Override strong (bold) — skip if content is empty or whitespace-only
        renderer.strong = function ({ text }) {
            if (!text || !text.trim()) return `**${text || ''}**`;
            return `<strong>${text}</strong>`;
        };


        marked.setOptions({
            renderer: renderer,
            gfm: true,
            breaks: true
        });
    },

    /**
     * Copy code content to clipboard
     */
    copyCode(button) {
        const wrapper = button.closest('.code-block-wrapper');
        const codeEl = wrapper.querySelector('code');
        const text = codeEl.textContent;
        navigator.clipboard.writeText(text).then(() => {
            const label = button.querySelector('.copy-label');
            label.textContent = 'Copied!';
            button.classList.add('copied');
            setTimeout(() => {
                label.textContent = 'Copy';
                button.classList.remove('copied');
            }, 2000);
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

        // Step 1.5: Escape lone asterisks that Marked would misinterpret
        // *** on its own line → literal asterisks (not <hr>)
        // * on its own line → literal asterisk (not empty <li>)
        let processedText = safeText
            .replace(/^\*{3,}\s*$/gm, (m) => m.replace(/\*/g, '\\*'))
            .replace(/^\*\s*$/gm, '\\*');

        // Step 2: Run through Marked.js (Markdown → HTML)
        let html = marked.parse(processedText);

        // Step 2.5: Wrap tables in scrolling container
        html = html.replace(/(<table\b[^>]*>[\s\S]*?<\/table>)/g, '<div class="table-overflow">$1</div>');

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
     * Replace math delimiters with placeholders so Marked doesn't mangle them.
     * Protects: \[...\] (display), \ce{...} (chemistry), \(...\) (inline)
     */
    _protectMath(text) {
        const blocks = [];

        // Protect display math: \[...\]
        text = text.replace(/\\\[[\s\S]*?\\\]/g, (match) => {
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

        // Protect inline math: \(...\)
        text = text.replace(/\\\([\s\S]*?\\\)/g, (match) => {
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
            let content = block.content;
            // Wrap inline math in scrollable container
            if (content.startsWith('\\(')) {
                content = `<span class="math-scroll-wrapper">${content}</span>`;
            }
            html = html.replace(block.id, content);
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
