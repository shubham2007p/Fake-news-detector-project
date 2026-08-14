document.addEventListener("DOMContentLoaded", () => {
    const headlineInput = document.getElementById("headline-input");
    const bodyInput = document.getElementById("body-input");
    const analyzeBtn = document.getElementById("analyze-btn");
    const clearBtn = document.getElementById("clear-btn");
    
    const resultPlaceholder = document.getElementById("result-placeholder");
    const resultDisplay = document.getElementById("result-display");
    const badgeContainer = document.getElementById("badge-container");
    const statusLabelValue = document.getElementById("status-label-value");
    const confidencePercentage = document.getElementById("confidence-percentage");
    const confidenceFill = document.getElementById("confidence-fill");
    const explanationText = document.getElementById("explanation-text");
    
    const newsResultsList = document.getElementById("news-results-list");
    const factResultsList = document.getElementById("fact-results-list");
    
    const sampleBoxes = document.querySelectorAll(".sample-box");

    // Action: Analyze News
    analyzeBtn.addEventListener("click", async () => {
        const title = headlineInput.value.trim();
        const text = bodyInput.value.trim();
        
        if (!title && !text) {
            alert("Please enter a headline or article content to analyze.");
            return;
        }

        // Show loading state
        analyzeBtn.disabled = true;
        analyzeBtn.textContent = "🔍 Fetching & verifying evidence...";
        
        try {
            const response = await fetch("/predict", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ title, text })
            });
            
            const data = await response.json();
            
            if (response.ok && data.status === "success") {
                displayResult(data);
            } else {
                alert(`Error: ${data.message || "Failed to get prediction"}`);
            }
        } catch (error) {
            console.error("Verification Request failed:", error);
            alert("Communication error with server. Make sure Flask is active.");
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = "🚀 Analyze News Article";
        }
    });

    // Action: Clear Input
    clearBtn.addEventListener("click", () => {
        headlineInput.value = "";
        bodyInput.value = "";
        resetResult();
    });

    // Action: Load Sample Content
    sampleBoxes.forEach(box => {
        box.addEventListener("click", () => {
            const h4 = box.querySelector("h4").textContent;
            const p = box.querySelector("p").textContent;
            
            headlineInput.value = h4;
            bodyInput.value = p;
            
            headlineInput.scrollIntoView({ behavior: 'smooth' });
            analyzeBtn.click();
        });
    });

    // Function: Populate & Render Verdict
    function displayResult(data) {
        resultPlaceholder.classList.add("hidden");
        resultDisplay.classList.remove("hidden");
        
        const verdict = data.verdict; // FAKE, REAL, UNCERTAIN
        const ml_pred = data.prediction; // FAKE, REAL
        const confidence = data.confidence;
        const status = data.status_lbl;
        const reasoning = data.reasoning;
        const news = data.news_evidence;
        const facts = data.fact_evidence;
        
        // 1. Setup Badge Class
        badgeContainer.innerHTML = "";
        const badge = document.createElement("span");
        
        let badgeClass = "badge-uncertain";
        if (verdict === "REAL") badgeClass = "badge-real";
        if (verdict === "FAKE") badgeClass = "badge-fake";
        
        badge.className = `badge ${badgeClass}`;
        badge.textContent = verdict;
        badgeContainer.appendChild(badge);
        
        // 2. Setup Status
        statusLabelValue.textContent = status;
        
        // 3. Local ML model meter
        confidencePercentage.textContent = `${confidence.toFixed(2)}%`;
        confidenceFill.style.width = `${confidence}%`;
        confidenceFill.className = `meter-fill ${ml_pred.toLowerCase()}`;
        
        // 4. Set Reasoning Description
        const cleanReasoning = reasoning
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\+\+(.*?)\+\+/g, '<span class="highlight-text">$1</span>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
        explanationText.innerHTML = cleanReasoning;
        
        // 5. Render News Articles
        newsResultsList.innerHTML = "";
        if (news && news.length > 0) {
            news.forEach(item => {
                const el = document.createElement("div");
                el.className = "evidence-item";
                el.innerHTML = `
                    <div class="evidence-meta">
                        <span class="evidence-source">${item.source} (${item.published_at})</span>
                        <span class="evidence-tier">${item.tier}</span>
                    </div>
                    <a href="${item.url}" target="_blank" class="evidence-title">${item.title}</a>
                    <p class="evidence-desc">${item.description}</p>
                `;
                newsResultsList.appendChild(el);
            });
        } else {
            newsResultsList.innerHTML = `<p class="no-evidence">No active news matching this query was detected on the live web.</p>`;
        }
        
        // 6. Render Fact Checks
        factResultsList.innerHTML = "";
        if (facts && facts.length > 0) {
            facts.forEach(item => {
                const el = document.createElement("div");
                el.className = "evidence-item";
                el.innerHTML = `
                    <div class="evidence-meta">
                        <span class="evidence-source">Fact-Check by ${item.publisher}</span>
                        <span class="evidence-tier">${item.tier}</span>
                    </div>
                    <div class="evidence-desc"><strong>Claim by ${item.claimant}:</strong> "${item.claim_text}"</div>
                    <div class="evidence-rating">
                        <strong>Verdict:</strong> 
                        <span style="color: ${item.verdict.toLowerCase().includes('false') ? 'var(--error)' : 'var(--success)'}">
                            ${item.verdict}
                        </span>
                    </div>
                    <a href="${item.review_url}" target="_blank" style="font-size: 0.72rem; color: var(--primary);">Read Review</a>
                `;
                factResultsList.appendChild(el);
            });
        } else {
            factResultsList.innerHTML = `<p class="no-evidence">No pre-existing fact-check ratings were found for this query.</p>`;
        }
    }

    // Function: Clear screen
    function resetResult() {
        resultDisplay.classList.add("hidden");
        resultPlaceholder.classList.remove("hidden");
    }
});
