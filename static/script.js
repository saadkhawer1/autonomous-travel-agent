document.addEventListener('DOMContentLoaded', () => {
    const promptInput = document.getElementById('prompt');
    const submitBtn = document.getElementById('submit-btn');
    const progressSection = document.getElementById('progress-section');
    const logContainer = document.getElementById('log-container');
    const resultSection = document.getElementById('result-section');
    const itineraryContent = document.getElementById('itinerary-content');
    const copyBtn = document.getElementById('copy-btn');
    const loader = document.getElementById('loader');
    
    // Configure Marked.js options (e.g. enabling breaks for newlines)
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,
            gfm: true
        });
    }

    submitBtn.addEventListener('click', startPlanning);
    promptInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') startPlanning();
    });

    function startPlanning() {
        const query = promptInput.value.trim();
        if (!query) return;

        // Reset UI state
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span>Planning...</span> <div class="loader pulse" style="width: 15px; height: 15px; margin-left: 10px; background: #000;"></div>`;
        
        progressSection.classList.remove('hidden');
        resultSection.classList.add('hidden');
        logContainer.innerHTML = '';
        itineraryContent.innerHTML = '';
        loader.style.display = 'block';

        const eventSource = new EventSource(`/api/plan?query=${encodeURIComponent(query)}`);

        eventSource.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                handleEvent(data, eventSource);
            } catch (e) {
                console.error("Parse error:", e);
            }
        };

        eventSource.onerror = function(error) {
            appendLog(`Connection Error or Server Closed`, 'error');
            eventSource.close();
            finishPlanning(false);
        };
    }

    function handleEvent(data, eventSource) {
        if (data.type === 'tool') {
            appendLog(`Using tool: ${data.name} (${JSON.stringify(data.args)})`, 'tool');
        } else if (data.type === 'critic') {
            appendLog(`Critic / Status: ${data.content}`, 'error');
            // If it's a critical error (like rate limit), close and finish
            if (data.content.includes('API Error')) {
                eventSource.close();
                finishPlanning(false);
            }
        } else if (data.type === 'log') {
            appendLog(`Agent: ${data.content}`, 'normal');
        } else if (data.type === 'result') {
            displayFinalItinerary(data.content);
            eventSource.close();
        } else if (data.type === 'error') {
            appendLog(`Error: ${data.message}`, 'error');
            eventSource.close();
            finishPlanning(false);
        }
    }

    function appendLog(message, type = 'normal') {
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        entry.textContent = message;
        logContainer.appendChild(entry);
        
        // Auto scroll to bottom
        logContainer.scrollTop = logContainer.scrollHeight;
    }

    function displayFinalItinerary(content) {
        resultSection.classList.remove('hidden');
        
        // Render Markdown using marked.js if available, else plain text
        if (typeof marked !== 'undefined') {
            itineraryContent.innerHTML = marked.parse(content);
        } else {
            itineraryContent.textContent = content;
        }
        
        finishPlanning(true);
    }

    function finishPlanning(success) {
        loader.style.display = 'none';
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<span>Generate Itinerary</span> <i class="ph-bold ph-arrow-right"></i>`;
    }

    // Copy to clipboard functionality
    copyBtn.addEventListener('click', () => {
        const textToCopy = itineraryContent.innerText;
        navigator.clipboard.writeText(textToCopy).then(() => {
            const icon = copyBtn.querySelector('i');
            icon.className = 'ph-fill ph-check-circle';
            icon.style.color = 'var(--primary)';
            setTimeout(() => {
                icon.className = 'ph ph-copy';
                icon.style.color = '';
            }, 2000);
        });
    });
});
