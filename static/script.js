// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const typingIndicator = document.getElementById('typing-indicator');
const clearChatBtn = document.getElementById('clear-chat-btn');

// Essay Generator Elements
const essayTopic = document.getElementById('essay-topic');
const essayLength = document.getElementById('essay-length');
const essayStyle = document.getElementById('essay-style');
const essayTone = document.getElementById('essay-tone');
const includeReferences = document.getElementById('include-references');
const generateEssayBtn = document.getElementById('generate-essay-btn');
const essayGenerationProgress = document.getElementById('essay-generation-progress');
const essayResultContainer = document.getElementById('essay-result-container');
const essayResult = document.getElementById('essay-result');
const downloadEssayBtn = document.getElementById('download-essay-btn');
const copyEssayBtn = document.getElementById('copy-essay-btn');

// Text Tools Elements
const textInput = document.getElementById('text-input');
const fileUpload = document.getElementById('file-upload');
const summarizeBtn = document.getElementById('summarize-btn');
const summaryResultContainer = document.getElementById('summary-result-container');
const summaryResult = document.getElementById('summary-result');
const copySummaryBtn = document.getElementById('copy-summary-btn');
const analyzeSentimentBtn = document.getElementById('analyze-sentiment-btn');
const sentimentResultContainer = document.getElementById('sentiment-result-container');
const sentimentResult = document.getElementById('sentiment-result');
const copySentimentBtn = document.getElementById('copy-sentiment-btn');

// Store current download file ID
let currentFileId = null;

function addMessage(content, isUser = false) {
    // Create a new message element
    const messageDiv = document.createElement('div');
    const messageClass = isUser ? 'user-message' : 'assistant-message'; // Determine message class based on sender
    messageDiv.className = `message ${messageClass}`;
    
    // Create a container for the message and action buttons
    const containerDiv = document.createElement('div');
    containerDiv.className = 'message-container position-relative';
    
    // Add text content
    const contentP = document.createElement('p');
    contentP.className = 'mb-0';
    contentP.innerHTML = formatMessage(content);
    
    // Add action buttons for assistant messages if the message is from the assistant
    if (!isUser) {
        const actionButtons = document.createElement('div');
        actionButtons.className = 'action-buttons';
        
        const copyBtn = document.createElement('button');
        copyBtn.className = 'btn btn-sm btn-outline-secondary';
        copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
        copyBtn.title = 'Copy to clipboard';
        copyBtn.onclick = () => copyToClipboard(content);
        
        actionButtons.appendChild(copyBtn);
        containerDiv.appendChild(actionButtons);
    }
    
    containerDiv.appendChild(contentP);
    messageDiv.appendChild(containerDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function formatMessage(text) {
    // Basic markdown-like formatting
    // Convert code blocks
    text = text.replace(/```(\w+)?\n([\s\S]*?)\n```/g, '<pre class="bg-light p-2 mt-2 mb-2 rounded"><code>$2</code></pre>');
    
    // Convert inline code
    text = text.replace(/`([^`]+)`/g, '<code class="bg-light px-1 rounded">$1</code>');
    
    // Convert links
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    
    // Convert bold
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // Convert italics
    text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    
    // Convert newlines to <br>
    text = text.replace(/\n/g, '<br>');
    
    return text;
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!');
    }).catch(err => {
        console.error('Error copying text: ', err);
        showToast('Failed to copy to clipboard', true);
    });
}

function showToast(message, isError = false) {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast align-items-center ${isError ? 'bg-danger' : 'bg-success'} text-white border-0 position-fixed bottom-0 end-0 m-3`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Initialize and show the toast
    const bsToast = new bootstrap.Toast(toast, { autohide: true, delay: 3000 });
    bsToast.show();
    
    // Remove the element after it's hidden
    toast.addEventListener('hidden.bs.toast', () => {
        document.body.removeChild(toast);
    });
}

function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;
    
    addMessage(message, true);
    chatInput.value = '';
    
    // Show typing indicator while waiting for response
    typingIndicator.style.display = 'block';
    
    // Send the user message to the server for processing
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
    })
    .then(response => response.json())
    .then(data => {
        // Hide typing indicator
        typingIndicator.style.display = 'none';
        
        // Add response message
        addMessage(data.response);
    })
    .catch(error => {
        console.error('Error:', error);
        typingIndicator.style.display = 'none';
        addMessage('Error: Unable to get response. Please try again later.');
    });
}

// Essay generation
function generateEssay() {
    const topic = essayTopic.value.trim();
    if (!topic) {
        showToast('Please enter an essay topic', true);
        return;
    }
    
    // Show progress
    essayGenerationProgress.style.display = 'block';
    essayResultContainer.style.display = 'none';
    generateEssayBtn.disabled = true;
    
    // Prepare data to send to the server
    const data = {
        topic: topic,
        length: essayLength.value,
        style: essayStyle.value,
        tone: essayTone.value,
        references: includeReferences.checked
    };
    
    // Send request
    fetch('/essay', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
        // Hide the progress indicator after receiving the response
        essayGenerationProgress.style.display = 'none';
        generateEssayBtn.disabled = false;
        
        if (data.error) {
            showToast(data.error, true);
            return;
        }
        
        // Display the generated essay result
        essayResult.textContent = data.essay;
        essayResultContainer.style.display = 'block';
        
        // Store file ID for download
        currentFileId = data.file_id;
    })
    .catch(error => {
        console.error('Error:', error);
        essayGenerationProgress.style.display = 'none';
        generateEssayBtn.disabled = false;
        showToast('Error generating essay. Please try again later.', true);
    });
}

function downloadEssay() {
    if (!currentFileId) {
        showToast('No essay file available', true);
        return;
    }
    
    window.location.href = `/download/${currentFileId}`;
}

// File upload handling
function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    fetch('/upload', {
        method: 'POST',
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showToast(data.error, true);
            return;
        }
        
        textInput.value = data.content;
        showToast(`File "${data.filename}" uploaded successfully`);
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error uploading file', true);
    });
}

// Text summarization
function summarizeText() {
    const text = textInput.value.trim();
    if (!text) {
        showToast('Please enter or upload text to summarize', true);
        return;
    }
    
    summarizeBtn.disabled = true;
    summarizeBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Summarizing...';
    
    fetch('/summarize', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
    })
    .then(response => response.json())
    .then(data => {
        summarizeBtn.disabled = false;
        summarizeBtn.innerHTML = '<i class="fas fa-compress-alt"></i> Summarize Text';
        
        if (data.error) {
            showToast(data.error, true);
            return;
        }
        
        summaryResult.innerHTML = formatMessage(data.summary);
        summaryResultContainer.style.display = 'block';
    })
    .catch(error => {
        console.error('Error:', error);
        summarizeBtn.disabled = false;
        summarizeBtn.innerHTML = '<i class="fas fa-compress-alt"></i> Summarize Text';
        showToast('Error summarizing text', true);
    });
}

// Sentiment analysis
function analyzeSentiment() {
    const text = textInput.value.trim();
    if (!text) {
        showToast('Please enter or upload text to analyze', true);
        return;
    }
    
    analyzeSentimentBtn.disabled = true;
    analyzeSentimentBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Analyzing...';
    
    fetch('/analyze-sentiment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
    })
    .then(response => response.json())
    .then(data => {
        analyzeSentimentBtn.disabled = false;
        analyzeSentimentBtn.innerHTML = '<i class="fas fa-chart-bar"></i> Analyze Sentiment';
        
        if (data.error) {
            showToast(data.error, true);
            return;
        }
        
        sentimentResult.innerHTML = formatMessage(data.analysis);
        sentimentResultContainer.style.display = 'block';
    })
    .catch(error => {
        console.error('Error:', error);
        analyzeSentimentBtn.disabled = false;
        analyzeSentimentBtn.innerHTML = '<i class="fas fa-chart-bar"></i> Analyze Sentiment';
        showToast('Error analyzing sentiment', true);
    });
}

// Clear the chat history on the server
function clearChat() {
    fetch('/clear-chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        chatMessages.innerHTML = '';
        addMessage('Chat history cleared. How can I help you today?');
        showToast('Chat history cleared');
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error clearing chat history', true);
    });
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Chat events
    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    clearChatBtn.addEventListener('click', clearChat);
    
    // Essay generator events
    generateEssayBtn.addEventListener('click', generateEssay);
    downloadEssayBtn.addEventListener('click', downloadEssay);
    copyEssayBtn.addEventListener('click', () => {
        copyToClipboard(essayResult.textContent);
    });
    
    // Text tools events
    fileUpload.addEventListener('change', handleFileUpload);
    summarizeBtn.addEventListener('click', summarizeText);
    copySummaryBtn.addEventListener('click', () => {
        copyToClipboard(summaryResult.textContent);
    });
    analyzeSentimentBtn.addEventListener('click', analyzeSentiment);
    copySentimentBtn.addEventListener('click', () => {
        copyToClipboard(sentimentResult.textContent);
    });
});

// Initialize tooltips