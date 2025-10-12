document.addEventListener("DOMContentLoaded", function () {
    const chatIcon = document.getElementById("chat-icon");
    const chatContainer = document.getElementById("chat-container");
    const chatPopup = document.getElementById("chat-popup");
    const chatMessages = document.getElementById("chat-messages");
    const userInput = document.getElementById("user-input");
    const sendButton = document.getElementById("send-button");

    let hideTimeout;
    let isGenerating = false;
    let typingAnimation = null;

    // Show/hide chatbox functions remain the same
    chatIcon.addEventListener("mouseenter", function () {
        clearTimeout(hideTimeout);
        chatContainer.classList.add("show");
    });

    chatContainer.addEventListener("mouseleave", function () {
        hideTimeout = setTimeout(() => {
            chatContainer.classList.remove("show");
        }, 500);
    });

    chatIcon.addEventListener("mouseleave", function () {
        hideTimeout = setTimeout(() => {
            if (!chatContainer.matches(":hover")) {
                chatContainer.classList.remove("show");
            }
        }, 500);
    });

    // Chatbot Popup Message (unchanged)
    function showChatPopup() {
        chatPopup.style.display = "block";
        chatPopup.style.opacity = "1";
        setTimeout(() => {
            chatPopup.style.opacity = "0";
            setTimeout(() => {
                chatPopup.style.display = "none";
            }, 500);
        }, 2500);
    }

    setTimeout(showChatPopup, 1000);
    setInterval(showChatPopup, 4000);

    // Improved typing animation function
    function typeText(element, text, speed = 30) {
        let i = 0;
        let isInTag = false;
        let tagBuffer = '';
        
        // Clear any existing animation
        if (typingAnimation) {
            clearTimeout(typingAnimation);
        }

        function type() {
            if (i < text.length) {
                const char = text.charAt(i);
                
                // Handle HTML tags
                if (char === '<') {
                    isInTag = true;
                    tagBuffer = char;
                } else if (char === '>' && isInTag) {
                    tagBuffer += char;
                    element.innerHTML += tagBuffer;
                    isInTag = false;
                    tagBuffer = '';
                    i++;
                } else if (isInTag) {
                    tagBuffer += char;
                    i++;
                } else {
                    // Handle regular text
                    element.innerHTML += char === '\n' ? '<br>' : char;
                    i++;
                }

                // Scroll to keep visible
                element.scrollIntoView({ behavior: "smooth", block: "nearest" });
                
                // Continue typing with variation in speed
                typingAnimation = setTimeout(type, isInTag ? speed/2 : speed + Math.random()*10);
            }
        }
        
        // Start typing
        type();
    }

    // Improved sendMessage function with better typing animation
    async function sendMessage() {
        const message = userInput.value.trim();
        if (message === "" || isGenerating) return;

        // Display user message
        const userMessage = document.createElement("div");
        userMessage.className = "user-message";
        userMessage.innerHTML = `<strong>You:</strong> ${message}`;
        chatMessages.appendChild(userMessage);
        userInput.value = "";

        // Show animated typing indicator
        const typingIndicator = document.createElement("div");
        typingIndicator.className = "bot-message typing-indicator";
        typingIndicator.innerHTML = `
            <strong>Bot:</strong>
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        chatMessages.appendChild(typingIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        isGenerating = true;

        try {
            const response = await fetch("/groq-api", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ message }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            chatMessages.removeChild(typingIndicator);

            // Create bot message container
            const botMessage = document.createElement("div");
            botMessage.className = "bot-message";
            const messageContent = document.createElement("span");
            messageContent.className = "message-content";
            botMessage.innerHTML = `<strong>Bot:</strong> `;
            botMessage.appendChild(messageContent);
            chatMessages.appendChild(botMessage);

            // Display response with animated typing effect
            const formattedText = data.response || "No response received";
            typeText(messageContent, formattedText);
            
        } catch (error) {
            console.error("Error:", error);
            chatMessages.removeChild(typingIndicator);
            const errorMessage = document.createElement("div");
            errorMessage.className = "error-message";
            errorMessage.innerHTML = `<strong>Error:</strong> ${error.message || "Failed to get response"}`;
            chatMessages.appendChild(errorMessage);
        } finally {
            isGenerating = false;
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    // Handle Enter key (allows Shift+Enter for new lines)
    userInput.addEventListener("keydown", function (event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });

    sendButton.addEventListener("click", sendMessage);

    // Auto-scroll to the latest message
    const observer = new MutationObserver(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
    observer.observe(chatMessages, { childList: true, subtree: true });

    // Enhanced CSS for the chat interface
    const style = document.createElement("style");
    style.textContent = `
        .user-message {
            background-color: #e3f2fd;
            padding: 10px 15px;
            border-radius: 18px 18px 0 18px;
            margin: 8px 0;
            max-width: 80%;
            align-self: flex-end;
            word-wrap: break-word;
        }
        .bot-message {
            background-color: #f5f5f5;
            padding: 10px 15px;
            border-radius: 18px 18px 18px 0;
            margin: 8px 0;
            max-width: 80%;
            align-self: flex-start;
            word-wrap: break-word;
        }
        .error-message {
            background-color: #ffebee;
            padding: 10px 15px;
            border-radius: 18px;
            margin: 8px 0;
            max-width: 80%;
            align-self: flex-start;
            word-wrap: break-word;
        }
        .typing-indicator {
            color: #666;
        }
        .typing-dots {
            display: inline-flex;
            align-items: center;
            height: 17px;
            margin-left: 4px;
        }
        .typing-dots span {
            width: 6px;
            height: 6px;
            margin: 0 2px;
            background: #666;
            border-radius: 50%;
            display: inline-block;
            animation: typingAnimation 1.4s infinite ease-in-out;
        }
        .typing-dots span:nth-child(1) {
            animation-delay: 0s;
        }
        .typing-dots span:nth-child(2) {
            animation-delay: 0.2s;
        }
        .typing-dots span:nth-child(3) {
            animation-delay: 0.4s;
        }
        @keyframes typingAnimation {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-3px); }
        }
        #chat-messages {
            display: flex;
            flex-direction: column;
            padding: 10px;
            overflow-y: auto;
            height: 100%;
        }
    `;
    document.head.appendChild(style);
});



////////prediction





