// script.js - Updated with detailed error reporting
document.addEventListener('DOMContentLoaded', function() {
    const micButton = document.getElementById('micButton');
    const chatHistory = document.getElementById('chatHistory');

    micButton.addEventListener('click', startRecognition);

    async function startRecognition() {
        try {
            if (!('webkitSpeechRecognition' in window)) {
                throw new Error("Speech recognition not supported");
            }

            const userQuery = await recognizeSpeech();
            addMessage('User', userQuery);
            
            const aiResponse = await processQuery(userQuery);
            addMessage('Jarvis', aiResponse);
            speakResponse(aiResponse);
            
        } catch (error) {
            console.error('Full error:', error);
            const errorMsg = error.message || 'Error processing request';
            addMessage('Jarvis', errorMsg);
            
            // Detailed error reporting
            if (error.response) {
                console.error('API Error:', await error.response.json());
            }
        }
    }

    function recognizeSpeech() {
        return new Promise((resolve, reject) => {
            const recognition = new webkitSpeechRecognition();
            recognition.lang = 'en-US';
            
            recognition.onresult = (event) => {
                resolve(event.results[0][0].transcript);
            };
            
            recognition.onerror = (event) => {
                reject(new Error(`Recognition error: ${event.error}`));
            };
            
            recognition.start();
        });
    }

    async function processQuery(query) {
        const response = await fetch('/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'API request failed');
        }
        
        const data = await response.json();
        return data.response;
    }

    function speakResponse(text) {
        const utterance = new SpeechSynthesisUtterance(text);
        window.speechSynthesis.speak(utterance);
    }

    function addMessage(sender, text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender.toLowerCase()}`;
        msgDiv.innerHTML = `<strong>${sender}:</strong> ${text}`;
        chatHistory.appendChild(msgDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
});