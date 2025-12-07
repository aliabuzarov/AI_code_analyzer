// Initialize CodeMirror editor
let editor;
let currentMode = 'python';
let messageCount = 0;

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

    // Update character count
    editor.on('change', function() {
        updateCharCount();
    });

    // Language selector change (main header)
    const languageSelect = document.getElementById('language-select');
    if (languageSelect) {
        languageSelect.addEventListener('change', function(e) {
            currentMode = e.target.value;
            editor.setOption('mode', currentMode === 'python' ? 'python' : 'text/x-c++src');
            // Sync sidebar selector
            const sidebarSelect = document.getElementById('language-select-sidebar');
            if (sidebarSelect) {
                sidebarSelect.value = e.target.value;
            }
        });
    }

    // Language selector change (sidebar)
    const sidebarLanguageSelect = document.getElementById('language-select-sidebar');
    if (sidebarLanguageSelect) {
        sidebarLanguageSelect.addEventListener('change', function(e) {
            currentMode = e.target.value;
            editor.setOption('mode', currentMode === 'python' ? 'python' : 'text/x-c++src');
            // Sync main selector
            if (languageSelect) {
                languageSelect.value = e.target.value;
            }
        });
    }

    // Sidebar toggle
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
        });
    }

    // Mobile menu toggle
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    if (mobileMenuBtn && sidebar) {
        mobileMenuBtn.addEventListener('click', function() {
            sidebar.classList.toggle('open');
        });
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 768 && sidebar && sidebar.classList.contains('open')) {
            if (!sidebar.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        }
    });

    // New chat button
    const newChatBtn = document.getElementById('new-chat-btn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', function() {
            clearChat();
        });
    }

    // Clear code button
    const clearBtn = document.getElementById('clear-btn');
    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            editor.setValue('');
            updateCharCount();
        });
    }

    // Explain button
    const explainBtn = document.getElementById('explain-btn');
    if (explainBtn) {
        explainBtn.addEventListener('click', function() {
            handleRequest('explain');
        });
    }

    // Improve button
    const improveBtn = document.getElementById('improve-btn');
    if (improveBtn) {
        improveBtn.addEventListener('click', function() {
            handleRequest('improve');
        });
    }

    // Initialize character count
    updateCharCount();
});

function updateCharCount() {
    const charCount = document.getElementById('char-count');
    if (charCount && editor) {
        const code = editor.getValue();
        const lines = code.split('\n').length;
        const chars = code.length;
        charCount.textContent = `${chars} characters, ${lines} lines`;
    }
}

function clearChat() {
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        // Remove all messages except welcome
        const messages = chatMessages.querySelectorAll('.message');
        messages.forEach(msg => msg.remove());
        
        // Show welcome message if hidden
        const welcomeMsg = chatMessages.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.style.display = 'flex';
        }
    }
    messageCount = 0;
}

function handleRequest(action) {
    const code = editor.getValue();
    const language = document.getElementById('language-select')?.value || 'python';

    if (!code.trim()) {
        showError('Please enter some code to explain.');
        return;
    }

    // Add user message
    addUserMessage(code, language);

    // Show loading state and disable buttons
    showLoading(true);
    setButtonsDisabled(true);
    hideError();

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
        addAssistantMessage(data);
        scrollToBottom();
    })
    .catch(error => {
        showLoading(false);
        setButtonsDisabled(false);
        showError(error.message || 'An error occurred while processing your request.');
    });
}

function addUserMessage(code, language) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;

    // Hide welcome message
    const welcomeMsg = chatMessages.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.style.display = 'none';
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user';
    messageDiv.innerHTML = `
        <div class="message-avatar">U</div>
        <div class="message-content">
            <div class="message-header">
                <span class="message-author">You</span>
                <span class="message-time">${getCurrentTime()}</span>
            </div>
            <div class="message-body">
                <div class="message-section">
                    <div class="message-section-title">Code (${language})</div>
                    <pre><code>${escapeHtml(code)}</code></pre>
                </div>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    messageCount++;
    scrollToBottom();
}

function addAssistantMessage(data) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    
    const explanation = data.explanation || 'No explanation available.';
    const errors = formatErrors(data.errors || 'No errors found.');
    const improvedCode = data.improved_code || 'No improved code available.';
    
    messageDiv.innerHTML = `
        <div class="message-avatar">AI</div>
        <div class="message-content">
            <div class="message-header">
                <span class="message-author">AI Assistant</span>
                <span class="message-time">${getCurrentTime()}</span>
            </div>
            <div class="message-body">
                <div class="message-section">
                    <div class="message-section-title">Explanation</div>
                    <div class="message-section-content">${formatText(explanation)}</div>
                </div>
                <div class="message-section">
                    <div class="message-section-title">Potential Errors/Warnings</div>
                    <div class="message-section-content">${errors}</div>
                </div>
                <div class="message-section">
                    <div class="message-section-title">Improved Code</div>
                    <div class="message-section-content">
                        <div class="message-actions">
                            <button class="action-btn-small" onclick="copyCode(this)" data-code="${escapeHtml(improvedCode)}">
                                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                                    <path d="M9.5 1.5H4.5C3.67 1.5 3 2.17 3 3V9.5C3 10.33 3.67 11 4.5 11H9.5C10.33 11 11 10.33 11 9.5V3C11 2.17 10.33 1.5 9.5 1.5Z" stroke="currentColor" stroke-width="1.5"/>
                                    <path d="M7 7V11M7 7H11M7 7H3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                                </svg>
                                Copy
                            </button>
                        </div>
                        <pre><code>${escapeHtml(improvedCode)}</code></pre>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    messageCount++;
    scrollToBottom();
}

function formatText(text) {
    // Convert markdown-style formatting to HTML
    text = escapeHtml(text);
    // Convert line breaks
    text = text.replace(/\n/g, '<br>');
    // Convert bullet points
    text = text.replace(/^[-•]\s*(.+)$/gm, '<li>$1</li>');
    if (text.includes('<li>')) {
        text = '<ul>' + text + '</ul>';
    }
    return text;
}

function formatErrors(errors) {
    if (typeof errors === 'string') {
        if (errors.toLowerCase().includes('none') || errors.toLowerCase().includes('no errors')) {
            return '<p>No errors or warnings found.</p>';
        }
        if (errors.includes('-') || errors.includes('•')) {
            const items = errors.split('\n')
                .filter(line => line.trim())
                .map(line => {
                    const cleanLine = line.replace(/^[-•]\s*/, '').trim();
                    return cleanLine ? `<li>${escapeHtml(cleanLine)}</li>` : '';
                })
                .filter(li => li)
                .join('');
            return items ? `<ul>${items}</ul>` : `<p>${escapeHtml(errors)}</p>`;
        }
        return `<p>${escapeHtml(errors)}</p>`;
    }
    return `<p>${escapeHtml(errors)}</p>`;
}

function copyCode(button) {
    const code = button.getAttribute('data-code');
    navigator.clipboard.writeText(code).then(function() {
        const originalText = button.innerHTML;
        button.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M11.5 3.5L5 10L2.5 7.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Copied!
        `;
        button.style.color = '#10b981';
        setTimeout(function() {
            button.innerHTML = originalText;
            button.style.color = '';
        }, 2000);
    }).catch(function(err) {
        console.error('Failed to copy:', err);
        showError('Failed to copy code. Please select and copy manually.');
    });
}

function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function scrollToBottom() {
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

function showLoading(show) {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = show ? 'flex' : 'none';
    }
}

function setButtonsDisabled(disabled) {
    const explainBtn = document.getElementById('explain-btn');
    const improveBtn = document.getElementById('improve-btn');
    
    if (explainBtn) {
        explainBtn.disabled = disabled;
        explainBtn.setAttribute('aria-busy', disabled ? 'true' : 'false');
    }
    if (improveBtn) {
        improveBtn.disabled = disabled;
        improveBtn.setAttribute('aria-busy', disabled ? 'true' : 'false');
    }
}

function showError(message) {
    const errorToast = document.getElementById('error-toast');
    if (errorToast) {
        errorToast.textContent = message;
        errorToast.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(function() {
            errorToast.style.display = 'none';
        }, 5000);
    }
}

function hideError() {
    const errorToast = document.getElementById('error-toast');
    if (errorToast) {
        errorToast.style.display = 'none';
    }
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
