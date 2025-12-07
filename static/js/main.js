// Initialize CodeMirror editor
let editor;
let currentMode = 'python';

document.addEventListener('DOMContentLoaded', function() {
    // Initialize CodeMirror
    const textarea = document.getElementById('code-editor');
    editor = CodeMirror.fromTextArea(textarea, {
        lineNumbers: true,
        mode: 'python',
        theme: 'monokai',
        indentUnit: 4,
        lineWrapping: true,
        autoCloseBrackets: true,
        matchBrackets: true,
        indentWithTabs: false,
        tabSize: 4,
        extraKeys: {
            "Tab": function(cm) {
                if (cm.somethingSelected()) {
                    cm.indentSelection("add");
                } else {
                    cm.replaceSelection("    ", "end");
                }
            },
            "Shift-Tab": function(cm) {
                cm.indentSelection("subtract");
            }
        }
    });

    // Language selector change
    document.getElementById('language-select').addEventListener('change', function(e) {
        currentMode = e.target.value;
        editor.setOption('mode', currentMode === 'python' ? 'python' : 'text/x-c++src');
    });

    // Explain button
    document.getElementById('explain-btn').addEventListener('click', function() {
        handleRequest('explain');
    });

    // Improve button
    document.getElementById('improve-btn').addEventListener('click', function() {
        handleRequest('improve');
    });

    // Copy button
    document.getElementById('copy-btn').addEventListener('click', function() {
        const code = document.getElementById('improved-code').textContent;
        navigator.clipboard.writeText(code).then(function() {
            const btn = document.getElementById('copy-btn');
            const originalText = btn.textContent;
            btn.textContent = '✓ Copied!';
            btn.style.background = '#28a745';
            setTimeout(function() {
                btn.textContent = originalText;
                btn.style.background = '#28a745';
            }, 2000);
        }).catch(function(err) {
            console.error('Failed to copy:', err);
            alert('Failed to copy code. Please select and copy manually.');
        });
    });
});

function handleRequest(action) {
    const code = editor.getValue();
    const language = document.getElementById('language-select').value;

    if (!code.trim()) {
        showError('Please enter some code to explain.');
        return;
    }

    // Show loading state and disable buttons
    showLoading(true);
    setButtonsDisabled(true);
    hideError();
    hideResults();

    // Get CSRF token
    const csrftoken = getCookie('csrftoken');

    // Make API request
    fetch('/api/explain/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({
            language: language,
            code: code
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        showLoading(false);
        setButtonsDisabled(false);
        displayResults(data);
    })
    .catch(error => {
        showLoading(false);
        setButtonsDisabled(false);
        showError(error.message || 'An error occurred while processing your request.');
    });
}

function displayResults(data) {
    document.getElementById('explanation').textContent = data.explanation || 'No explanation available.';
    document.getElementById('errors').innerHTML = formatErrors(data.errors || 'No errors found.');
    document.getElementById('improved-code').textContent = data.improved_code || 'No improved code available.';
    document.getElementById('results-section').style.display = 'block';
    document.getElementById('result-panel').style.display = 'block';
    
    // Scroll results into view on mobile
    if (window.innerWidth <= 768) {
        document.getElementById('results-section').scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
    }
}

function formatErrors(errors) {
    // If errors is a string, try to format it as a list
    if (typeof errors === 'string') {
        // Check if it's already formatted as HTML or plain text
        if (errors.toLowerCase().includes('none') || errors.toLowerCase().includes('no errors')) {
            return '<p>No errors or warnings found.</p>';
        }
        // Try to detect bullet points
        if (errors.includes('-') || errors.includes('•')) {
            return '<ul>' + errors.split('\n').filter(line => line.trim()).map(line => {
                const cleanLine = line.replace(/^[-•]\s*/, '').trim();
                return cleanLine ? '<li>' + cleanLine + '</li>' : '';
            }).filter(li => li).join('') + '</ul>';
        }
        return '<p>' + errors + '</p>';
    }
    return '<p>' + errors + '</p>';
}

function showLoading(show) {
    const loadingEl = document.getElementById('loading');
    const resultPanel = document.getElementById('result-panel');
    const resultsSection = document.getElementById('results-section');
    
    if (show) {
        loadingEl.style.display = 'flex';
        resultPanel.style.display = 'none';
        resultsSection.style.display = 'block';
    } else {
        loadingEl.style.display = 'none';
        resultPanel.style.display = 'flex';
    }
}

function setButtonsDisabled(disabled) {
    const explainBtn = document.getElementById('explain-btn');
    const improveBtn = document.getElementById('improve-btn');
    
    explainBtn.disabled = disabled;
    improveBtn.disabled = disabled;
    
    if (disabled) {
        explainBtn.setAttribute('aria-busy', 'true');
        improveBtn.setAttribute('aria-busy', 'true');
    } else {
        explainBtn.removeAttribute('aria-busy');
        improveBtn.removeAttribute('aria-busy');
    }
}

function hideResults() {
    document.getElementById('results-section').style.display = 'none';
}

function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    
    // Scroll error into view
    errorDiv.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'nearest' 
    });
}

function hideError() {
    document.getElementById('error-message').style.display = 'none';
}

// Helper function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
