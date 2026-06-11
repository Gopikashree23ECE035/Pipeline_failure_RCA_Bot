/**
 * main.js — Pipeline RCA Bot
 * Global JS: navbar scroll effect, diff syntax highlighting.
 * NOTE: Upload zone interaction is handled fully inside upload.html
 *       to avoid duplicate event handlers causing double file dialogs.
 */

document.addEventListener('DOMContentLoaded', function () {

    // ── 1. Navbar scroll effect ────────────────────────────────
    const nav = document.getElementById('mainNav');
    if (nav) {
        window.addEventListener('scroll', function () {
            nav.classList.toggle('scrolled', window.scrollY > 20);
        }, { passive: true });
    }

    // ── 2. Diff syntax highlighting (shared across pages) ─────
    //    upload.html, report.html and github_analysis.html all
    //    render .raw-diff blocks. Each page also calls this on
    //    its own, but this global handler acts as a safety net.
    highlightDiffs();

    // ── 3. Auto-dismiss flash alerts after 6 s ─────────────────
    document.querySelectorAll('.flash-alert').forEach(el => {
        setTimeout(() => {
            el.style.transition = 'opacity 0.5s ease';
            el.style.opacity = '0';
            setTimeout(() => el.remove(), 500);
        }, 6000);
    });

    // ── 4. Entrance animations via IntersectionObserver ────────
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'none';
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.glass-card').forEach(card => {
        // Skip cards that are already in view on load (handled by CSS animation)
        if (!card.closest('.fade-in-up')) {
            card.style.opacity = '0';
            card.style.transform = 'translateY(16px)';
            card.style.transition = 'opacity 0.45s ease, transform 0.45s ease';
            observer.observe(card);
        }
    });
});

/**
 * Syntax-highlight raw git diff blocks already on the page.
 */
function highlightDiffs() {
    document.querySelectorAll('.raw-diff').forEach(block => {
        if (block.dataset.highlighted) return;   // skip if already done
        block.dataset.highlighted = '1';

        const lines = block.textContent.split('\n');
        let html = '';
        lines.forEach(line => {
            if (line.startsWith('+') && !line.startsWith('+++')) {
                html += `<span class="diff-line-added">${escapeHTML(line)}</span>`;
            } else if (line.startsWith('-') && !line.startsWith('---')) {
                html += `<span class="diff-line-removed">${escapeHTML(line)}</span>`;
            } else {
                html += `<span>${escapeHTML(line)}</span>\n`;
            }
        });
        block.innerHTML = html;
    });
}

function escapeHTML(str) {
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
