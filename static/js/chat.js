document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('chat-send-btn');
    const clearBtn = document.getElementById('clear-chat-btn');

    // Auto-resize textarea
    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.value === '') {
            this.style.height = '45px';
        }
    });

    // Handle Enter to send
    chatInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', sendMessage);

    clearBtn.addEventListener('click', async () => {
        if(confirm('Are you sure you want to clear the chat history?')) {
            try {
                await fetch('/api/chat/clear', { method: 'POST' });
                // Keep the welcome message, remove others
                const welcomeMsg = chatMessages.firstElementChild.outerHTML;
                chatMessages.innerHTML = welcomeMsg;
            } catch(e) {
                console.error("Failed to clear chat", e);
            }
        }
    });

    function simpleMarkdown(text) {
        let html = text;
        // Bold
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Italic
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
        // Code blocks
        html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        // Inline code
        html = html.replace(/`(.*?)`/g, '<code>$1</code>');
        // Bullets
        html = html.replace(/^\- (.*$)/gim, '<ul><li>$1</li></ul>');
        html = html.replace(/<\/ul>\n<ul>/g, '\n');
        // New lines
        html = html.replace(/\n/g, '<br>');
        return html;
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function appendMessage(text, sender) {
        const wrapper = document.createElement('div');
        wrapper.className = `chat-bubble-wrapper ${sender}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'chat-avatar';
        avatar.innerHTML = sender === 'ai' ? '<i class="fas fa-robot"></i>' : '<i class="fas fa-user"></i>';
        
        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble';
        bubble.innerHTML = sender === 'ai' ? simpleMarkdown(text) : text.replace(/\n/g, '<br>');
        
        wrapper.appendChild(avatar);
        wrapper.appendChild(bubble);
        chatMessages.appendChild(wrapper);
        scrollToBottom();
    }

    function showTyping() {
        const wrapper = document.createElement('div');
        wrapper.className = 'chat-bubble-wrapper ai typing-indicator-wrapper';
        wrapper.innerHTML = `
            <div class="chat-avatar"><i class="fas fa-robot"></i></div>
            <div class="chat-bubble">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        chatMessages.appendChild(wrapper);
        scrollToBottom();
        return wrapper;
    }

    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        chatInput.value = '';
        chatInput.style.height = '45px';
        
        appendMessage(text, 'user');
        const typingEl = showTyping();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            
            const data = await response.json();
            typingEl.remove();
            
            if (data.response) {
                appendMessage(data.response, 'ai');
            } else {
                appendMessage("Sorry, I encountered an error. Please try again.", 'ai');
            }
        } catch (error) {
            console.error('Chat error:', error);
            typingEl.remove();
            appendMessage("Connection error. Please try again.", 'ai');
        }
    }
});
