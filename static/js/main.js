/**
 * VeritasAI — Main Frontend Script
 * Handles: analysis pipeline, verdict rendering, history, tabs, donut chart
 */

document.addEventListener("DOMContentLoaded", () => {

    // ── DOM REFS ──────────────────────────────────────────────────────────────
    const headlineInput    = document.getElementById("headline-input");
    const bodyInput        = document.getElementById("body-input");
    const analyzeBtn       = document.getElementById("analyze-btn");
    const btnLabel         = analyzeBtn.querySelector(".btn-label");
    const btnIcon          = analyzeBtn.querySelector(".btn-icon");
    const btnLoader        = analyzeBtn.querySelector(".btn-loader");
    const clearBtn         = document.getElementById("clear-btn");
    const charCounter      = document.getElementById("char-counter");
    const newAnalysisBtn   = document.getElementById("new-analysis-btn");
    const clearHistoryBtn  = document.getElementById("clear-history-btn");
    const historyList      = document.getElementById("history-list");

    const resultPlaceholder = document.getElementById("result-placeholder");
    const resultLoading     = document.getElementById("result-loading");
    const resultOutput      = document.getElementById("result-output");

    // Loading steps
    const ls1 = document.getElementById("ls-1");
    const ls2 = document.getElementById("ls-2");
    const ls3 = document.getElementById("ls-3");

    // Verdict hero
    const verdictHero      = document.getElementById("verdict-hero");
    const verdictIconWrap  = document.getElementById("verdict-icon-wrap");
    const verdictLabel     = document.getElementById("verdict-label");
    const verdictSub       = document.getElementById("verdict-sub");
    const donutFill        = document.getElementById("donut-fill");
    const donutPct         = document.getElementById("donut-pct");

    // Status + reasoning
    const statusLabelValue = document.getElementById("status-label-value");
    const explanationText  = document.getElementById("explanation-text");

    // Evidence
    const newsResultsList  = document.getElementById("news-results-list");
    const factResultsList  = document.getElementById("fact-results-list");
    const newsCount        = document.getElementById("news-count");
    const fcCount          = document.getElementById("fc-count");

    // Sidebar toggles
    const sidebar         = document.getElementById("sidebar");
    const sidebarToggle   = document.getElementById("sidebar-toggle");
    const topbarToggleBtn = document.getElementById("topbar-toggle-btn");

    // Sample pills
    const samplePills = document.querySelectorAll(".sample-pill");

    // Donut geometry
    const DONUT_CIRCUMFERENCE = 201.06; // 2 * π * r = 2 * π * 32

    // ── HISTORY (in-memory + localStorage) ───────────────────────────────────
    let history = [];

    function loadHistory() {
        try {
            history = JSON.parse(localStorage.getItem("veritas_history") || "[]");
            renderHistory();
        } catch(e) {
            history = [];
        }
    }

    function saveHistory() {
        try {
            // Keep top 30 items, stripping extra evidence bloat for localStorage safety
            const cleanHistory = (history || []).slice(0, 30).map(item => ({
                id: item.id,
                headline: item.headline,
                verdict: item.verdict,
                confidence: item.confidence,
                timestamp: item.timestamp,
                body: item.body,
                data: {
                    verdict: item.data ? item.data.verdict : item.verdict,
                    status_lbl: item.data ? item.data.status_lbl : "",
                    reasoning: item.data ? item.data.reasoning : "",
                    prediction: item.data ? item.data.prediction : "",
                    confidence: item.data ? item.data.confidence : item.confidence,
                    model_a: item.data ? item.data.model_a : null,
                    model_b: item.data ? item.data.model_b : null,
                    news_evidence: (item.data && item.data.news_evidence) ? item.data.news_evidence.slice(0, 3) : [],
                    fact_evidence: (item.data && item.data.fact_evidence) ? item.data.fact_evidence.slice(0, 3) : []
                }
            }));
            localStorage.setItem("veritas_history", JSON.stringify(cleanHistory));
        } catch(e) {
            console.error("LocalStorage save error:", e);
        }
    }

    function addToHistory(headline, body, data) {
        if (!data) return;
        const headlineText = (headline || body || "News Verification").trim();
        const entry = {
            id: Date.now(),
            headline: headlineText,
            verdict: data.verdict || "UNCERTAIN",
            confidence: data.confidence || 0,
            timestamp: new Date().toISOString(),
            data: data,
            body: body || ""
        };
        history.unshift(entry);
        saveHistory();
        renderHistory();
        return entry.id;
    }

    // ── DELEGATED HISTORY CLICK LISTENER ─────────────────────────────────────
    if (historyList) {
        historyList.addEventListener("click", (e) => {
            const item = e.target.closest(".history-item");
            if (!item) return;

            const id = parseInt(item.dataset.id);
            const entry = history.find(h => h.id === id);
            if (!entry) return;

            // Highlight active
            historyList.querySelectorAll(".history-item").forEach(i => i.classList.remove("active"));
            item.classList.add("active");

            // Restore inputs
            headlineInput.value = entry.headline || "";
            bodyInput.value = entry.body || "";
            updateCharCounter();

            // Show results
            displayResult(entry.data);
        });
    }

    function renderHistory() {
        if (!historyList) return;
        if (!history || history.length === 0) {
            historyList.innerHTML = `
                <div class="history-empty">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                    <p>No analyses yet</p>
                </div>`;
            return;
        }

        historyList.innerHTML = history.map(entry => {
            const verdictClass = entry.verdict ? entry.verdict.toLowerCase() : "uncertain";
            const timeAgo = formatTimeAgo(entry.timestamp);
            const rawTitle = (entry.headline || entry.body || "News Verification").trim();
            const truncatedHeadline = rawTitle.length > 40 ? rawTitle.substring(0, 40) + "…" : rawTitle;

            return `<div class="history-item" data-id="${entry.id}">
                <div class="history-verdict-dot ${verdictClass}"></div>
                <div class="history-item-text">
                    <div class="history-item-headline" title="${escapeHtml(rawTitle)}">${escapeHtml(truncatedHeadline)}</div>
                    <div class="history-item-meta">${escapeHtml(entry.verdict || "UNCERTAIN")} · ${timeAgo}</div>
                </div>
            </div>`;
        }).join("");
    }

    function formatTimeAgo(iso) {
        const diff = Date.now() - new Date(iso).getTime();
        if (diff < 60000) return "just now";
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
        return `${Math.floor(diff / 86400000)}d ago`;
    }

    function escapeHtml(str) {
        return (str || "").replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }

    clearHistoryBtn.addEventListener("click", () => {
        if (history.length === 0) return;
        history = [];
        saveHistory();
        renderHistory();
        showPlaceholder();
    });

    // ── SIDEBAR TOGGLE ────────────────────────────────────────────────────────
    function toggleSidebar() {
        sidebar.classList.toggle("collapsed");
    }

    sidebarToggle.addEventListener("click", toggleSidebar);
    topbarToggleBtn.addEventListener("click", toggleSidebar);

    // ── THEME TOGGLE ──────────────────────────────────────────────────────────
    const themeToggleBtn = document.getElementById("theme-toggle");
    const HTML = document.documentElement;

    // Restore saved theme preference
    const savedTheme = localStorage.getItem("veritas_theme") || "dark";
    HTML.setAttribute("data-theme", savedTheme);

    themeToggleBtn.addEventListener("click", () => {
        const current = HTML.getAttribute("data-theme");
        const next = current === "dark" ? "light" : "dark";
        HTML.setAttribute("data-theme", next);
        localStorage.setItem("veritas_theme", next);
    });

    // ── CHAR COUNTER ──────────────────────────────────────────────────────────
    function updateCharCounter() {
        const total = headlineInput.value.length + bodyInput.value.length;
        charCounter.textContent = `${total.toLocaleString()} characters`;
    }

    headlineInput.addEventListener("input", updateCharCounter);
    bodyInput.addEventListener("input", updateCharCounter);

    // ── KEYBOARD SHORTCUTS (ENTER TO ANALYZE) ──────────────────────────────────
    headlineInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            if (!analyzeBtn.disabled) {
                analyzeBtn.click();
            }
        }
    });

    bodyInput.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
            e.preventDefault();
            if (!analyzeBtn.disabled) {
                analyzeBtn.click();
            }
        }
    });

    // ── NEW ANALYSIS ──────────────────────────────────────────────────────────
    newAnalysisBtn.addEventListener("click", () => {
        headlineInput.value = "";
        bodyInput.value = "";
        updateCharCounter();
        showPlaceholder();
        headlineInput.focus();
        historyList.querySelectorAll(".history-item").forEach(i => i.classList.remove("active"));
    });

    clearBtn.addEventListener("click", () => {
        headlineInput.value = "";
        bodyInput.value = "";
        updateCharCounter();
        showPlaceholder();
    });

    // ── SAMPLE PILLS ──────────────────────────────────────────────────────────
    samplePills.forEach(pill => {
        pill.addEventListener("click", () => {
            headlineInput.value = pill.dataset.headline || "";
            bodyInput.value = pill.dataset.body || "";
            updateCharCounter();
            analyzeBtn.click();
        });
    });

    // ── TABS ──────────────────────────────────────────────────────────────────
    const tabBtns = document.querySelectorAll(".tab-btn");
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            const target = btn.dataset.tab;
            document.getElementById("tab-news").classList.add("hidden");
            document.getElementById("tab-factcheck").classList.add("hidden");

            if (target === "news") document.getElementById("tab-news").classList.remove("hidden");
            else if (target === "factcheck") document.getElementById("tab-factcheck").classList.remove("hidden");
        });
    });

    // ── STATE HELPERS ─────────────────────────────────────────────────────────
    function showPlaceholder() {
        resultPlaceholder.classList.remove("hidden");
        resultLoading.classList.add("hidden");
        resultOutput.classList.add("hidden");
    }

    function showLoading() {
        resultPlaceholder.classList.add("hidden");
        resultLoading.classList.remove("hidden");
        resultOutput.classList.add("hidden");

        // Reset loading steps
        [ls1, ls2, ls3].forEach(step => {
            step.classList.remove("active", "done");
            step.querySelector(".ls-check").classList.add("hidden");
        });
        ls1.classList.add("active");
    }

    function advanceLoadingStep(step) {
        if (step === 1) {
            ls1.classList.remove("active");
            ls1.classList.add("done");
            ls1.querySelector(".ls-check").classList.remove("hidden");
            ls2.classList.add("active");
        } else if (step === 2) {
            ls2.classList.remove("active");
            ls2.classList.add("done");
            ls2.querySelector(".ls-check").classList.remove("hidden");
            ls3.classList.add("active");
        } else if (step === 3) {
            ls3.classList.remove("active");
            ls3.classList.add("done");
            ls3.querySelector(".ls-check").classList.remove("hidden");
        }
    }

    function showOutput() {
        resultPlaceholder.classList.add("hidden");
        resultLoading.classList.add("hidden");
        resultOutput.classList.remove("hidden");
    }

    // ── ANALYZE ───────────────────────────────────────────────────────────────
    analyzeBtn.addEventListener("click", async () => {
        const title = headlineInput.value.trim();
        const text  = bodyInput.value.trim();

        if (!title && !text) {
            headlineInput.focus();
            headlineInput.style.borderColor = "var(--fake-color)";
            setTimeout(() => { headlineInput.style.borderColor = ""; }, 2000);
            return;
        }

        // Update button state
        analyzeBtn.disabled = true;
        btnLabel.textContent = "Analyzing…";
        btnIcon.classList.add("hidden");
        btnLoader.classList.remove("hidden");

        showLoading();

        // Simulate stepped loading for UX feel
        const step1Timer = setTimeout(() => advanceLoadingStep(1), 600);
        const step2Timer = setTimeout(() => advanceLoadingStep(2), 1800);

        try {
            const response = await fetch("/predict", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title, text })
            });

            const data = await response.json();
            clearTimeout(step1Timer);
            clearTimeout(step2Timer);

            if (response.ok && data.status === "success") {
                advanceLoadingStep(1);
                advanceLoadingStep(2);
                advanceLoadingStep(3);

                addToHistory(title, text, data);
                setTimeout(() => {
                    displayResult(data);
                }, 400);
            } else {
                clearTimeout(step1Timer);
                clearTimeout(step2Timer);
                showPlaceholder();
                showToast(`Error: ${data.message || "Failed to get prediction"}`, "error");
            }
        } catch (error) {
            clearTimeout(step1Timer);
            clearTimeout(step2Timer);
            console.error("Request failed:", error);
            showPlaceholder();
            showToast("Connection error. Is the Flask server running?", "error");
        } finally {
            analyzeBtn.disabled = false;
            btnLabel.textContent = "Analyze Article";
            btnIcon.classList.remove("hidden");
            btnLoader.classList.add("hidden");
        }
    });

    // ── DISPLAY RESULT ────────────────────────────────────────────────────────
    function displayResult(data) {
        showOutput();

        const verdict     = data.verdict;      // FAKE | REAL | UNCERTAIN
        const ml_pred     = data.prediction;   // FAKE | REAL
        const confidence  = data.confidence;   // 0–100
        const status      = data.status_lbl;
        const reasoning   = data.reasoning;
        const news        = data.news_evidence  || [];
        const facts       = data.fact_evidence  || [];

        // ── Verdict Hero ──
        const lc = verdict ? verdict.toLowerCase() : "uncertain";
        verdictHero.className = `verdict-hero hero-${lc}`;
        verdictLabel.className = `verdict-label ${lc}`;
        verdictLabel.textContent = verdict || "UNCERTAIN";
        verdictSub.textContent = status || "Verification complete";

        // Icon per verdict
        const iconWrap = verdictHero.querySelector(".verdict-icon-wrap");
        if (iconWrap) {
            iconWrap.innerHTML = lc === "fake" ? "❌" : lc === "real" ? "✅" : "⚠️";
            iconWrap.style.background = lc === "fake" ? "var(--fake-dim)" : lc === "real" ? "var(--real-dim)" : "var(--uncertain-dim)";
        }

        // ── Donut chart ──
        const pct = Math.max(0, Math.min(100, Number(confidence) || 0));
        const offset = DONUT_CIRCUMFERENCE - (pct / 100) * DONUT_CIRCUMFERENCE;
        donutFill.style.strokeDashoffset = offset;
        donutFill.style.stroke = lc === "real" ? "var(--real-color)" :
                                  lc === "fake" ? "var(--fake-color)" : "var(--uncertain-color)";
        donutPct.textContent = `${pct.toFixed(0)}%`;

        // ── Status ──
        statusLabelValue.textContent = status || "—";

        // ── Ensemble Models Cards ──
        const modelA = data.model_a;
        const modelB = data.model_b;
        const modelAVal = document.getElementById("model-a-val");
        const modelBVal = document.getElementById("model-b-val");

        if (modelAVal && modelA) {
            const colorA = modelA.prediction === "REAL" ? "var(--real-color)" : "var(--fake-color)";
            modelAVal.innerHTML = `<span style="color:${colorA}">${modelA.prediction}</span> (${modelA.confidence}%)`;
        }
        if (modelBVal && modelB) {
            const colorB = modelB.prediction === "REAL" ? "var(--real-color)" : "var(--fake-color)";
            modelBVal.innerHTML = `<span style="color:${colorB}">${modelB.prediction}</span> (${modelB.truth_probability}% Truth Score)`;
        }

        // ── Reasoning (markdown → HTML) ──
        const cleanReasoning = (reasoning || "No reasoning provided.")
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
            .replace(/\+\+(.*?)\+\+/g, '<span class="highlight-text">$1</span>')
            .replace(/`(.*?)`/g, "<code>$1</code>")
            .replace(/\n/g, "<br>");
        explanationText.innerHTML = cleanReasoning;

        // ── News Evidence ──
        newsCount.textContent = news.length;
        newsResultsList.innerHTML = "";
        if (news.length > 0) {
            news.forEach(item => {
                const el = document.createElement("div");
                el.className = "evidence-item";
                el.innerHTML = `
                    <div class="evidence-meta">
                        <span class="evidence-source">${escapeHtml(item.source)} · ${escapeHtml(item.published_at || "")}</span>
                        <span class="evidence-tier">${escapeHtml(item.tier || "")}</span>
                    </div>
                    <a href="${escapeHtml(item.url || "#")}" target="_blank" rel="noopener" class="evidence-title">${escapeHtml(item.title || "Untitled")}</a>
                    <p class="evidence-desc">${escapeHtml(item.description || "")}</p>
                `;
                newsResultsList.appendChild(el);
            });
        } else {
            newsResultsList.innerHTML = `<p class="no-evidence">No matching news articles found in live search.</p>`;
        }

        // ── Fact Check Evidence ──
        fcCount.textContent = facts.length;
        factResultsList.innerHTML = "";
        if (facts.length > 0) {
            facts.forEach(item => {
                const isTrue = !(item.verdict || "").toLowerCase().includes("false");
                const verdictColor = isTrue ? "var(--real-color)" : "var(--fake-color)";
                const el = document.createElement("div");
                el.className = "evidence-item";
                el.innerHTML = `
                    <div class="evidence-meta">
                        <span class="evidence-source">Fact-Check by ${escapeHtml(item.publisher || "Unknown")}</span>
                        <span class="evidence-tier">${escapeHtml(item.tier || "")}</span>
                    </div>
                    <p class="evidence-desc"><strong>Claim by ${escapeHtml(item.claimant || "Unknown")}:</strong> "${escapeHtml(item.claim_text || "")}"</p>
                    <div class="evidence-rating">Verdict: <span style="color:${verdictColor};font-weight:700;">${escapeHtml(item.verdict || "—")}</span></div>
                    <a href="${escapeHtml(item.review_url || "#")}" target="_blank" rel="noopener" class="evidence-read-link">Read full review →</a>
                `;
                factResultsList.appendChild(el);
            });
        } else {
            factResultsList.innerHTML = `<p class="no-evidence">No pre-existing fact checks found for this topic.</p>`;
        }

        // Scroll to top of result
        resultOutput.scrollTop = 0;
    }

    // ── TOAST NOTIFICATION ────────────────────────────────────────────────────
    function showToast(message, type = "info") {
        const existing = document.getElementById("veritas-toast");
        if (existing) existing.remove();

        const toast = document.createElement("div");
        toast.id = "veritas-toast";
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 24px;
            right: 24px;
            padding: 12px 18px;
            border-radius: 12px;
            font-size: 13px;
            font-weight: 500;
            color: #fff;
            z-index: 9999;
            animation: toast-in 0.3s ease;
            max-width: 360px;
            background: ${type === "error" ? "var(--fake-color)" : "var(--accent)"};
            box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        `;
        document.body.appendChild(toast);

        // Add keyframe if not present
        if (!document.getElementById("toast-styles")) {
            const style = document.createElement("style");
            style.id = "toast-styles";
            style.textContent = `
                @keyframes toast-in { from { transform: translateY(16px); opacity: 0; } to { transform: none; opacity: 1; } }
            `;
            document.head.appendChild(style);
        }

        setTimeout(() => {
            toast.style.transition = "opacity 0.3s ease, transform 0.3s ease";
            toast.style.opacity = "0";
            toast.style.transform = "translateY(8px)";
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    // ── ACTIVE LEARNING / TEACH THE SYSTEM (Delegated Listener) ────────────────
    document.addEventListener("click", async (e) => {
        const btnReal = e.target.closest("#btn-mark-real");
        const btnFake = e.target.closest("#btn-mark-fake");
        const targetBtn = btnReal || btnFake;

        if (!targetBtn) return;

        e.preventDefault();
        const label = btnReal ? "REAL" : "FAKE";
        const feedbackMsg = document.getElementById("feedback-msg");
        const textToTeach = (headlineInput.value.trim() + " " + bodyInput.value.trim()).trim();

        if (!textToTeach) {
            showToast("No active headline or text to teach.", "error");
            return;
        }

        // Tactile Click Animation & Visual Feedback State
        targetBtn.classList.add("clicked");
        targetBtn.style.transform = "scale(0.92)";
        targetBtn.style.opacity = "0.8";
        const origText = targetBtn.innerHTML;
        targetBtn.innerHTML = `<span>⏳ Retraining...</span>`;
        targetBtn.disabled = true;

        if (feedbackMsg) {
            feedbackMsg.style.color = "var(--text-muted)";
            feedbackMsg.textContent = "Updating learning parameters...";
        }

        try {
            const resp = await fetch("/feedback", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: textToTeach, label: label })
            });

            const res = await resp.json();
            if (res.status === "success") {
                targetBtn.style.transform = "scale(1)";
                targetBtn.style.opacity = "1";
                targetBtn.innerHTML = label === "REAL" ? `✓ Learned as REAL` : `✗ Learned as FAKE`;

                if (feedbackMsg) {
                    feedbackMsg.style.color = label === "REAL" ? "var(--real-color)" : "var(--fake-color)";
                    feedbackMsg.textContent = `🎉 Active learning fine-tuned Model A on ${label}!`;
                }

                showToast(`🎉 Active learning updated! Model trained on ${label}.`, "info");
            } else {
                targetBtn.innerHTML = origText;
                targetBtn.disabled = false;
                if (feedbackMsg) feedbackMsg.textContent = "Error saving feedback.";
                showToast(res.message || "Feedback failed", "error");
            }
        } catch (err) {
            targetBtn.innerHTML = origText;
            targetBtn.disabled = false;
            console.error("Feedback error:", err);
            showToast("Failed to connect for active learning update.", "error");
        }
    });

    // ── RESET APP / CLEAR ─────────────────────────────────────────────────────
    if (clearBtn) {
        clearBtn.addEventListener("click", (e) => {
            e.preventDefault();
            headlineInput.value = "";
            bodyInput.value = "";
            if (feedbackMsg) feedbackMsg.textContent = "";
            showPlaceholder();
            headlineInput.focus();
            showToast("App reset cleanly.", "info");
        });
    }

    // ── KEYBOARD SHORTCUT ─────────────────────────────────────────────────────
    document.addEventListener("keydown", (e) => {
        // Ctrl/Cmd + Enter = Analyze
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
            e.preventDefault();
            analyzeBtn.click();
        }
    });

    // ── INIT ──────────────────────────────────────────────────────────────────
    loadHistory();
    headlineInput.focus();
});
