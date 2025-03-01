import os
from flask import Flask, render_template, request, jsonify, send_file, session
import requests
import json
import datetime
import tempfile
from fpdf import FPDF
import textwrap
import uuid
from werkzeug.utils import secure_filename
import threading
import time

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'md'}
API_KEY = "fw_3ZV3je3RsJbgBZHkigLEpPQS"  # Replace with environment variable in production

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.secret_key = os.urandom(24)

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Store active chat sessions
active_sessions = {}
# Store generated PDFs for download
generated_files = {}

class FireworksAIChatbot:
    def __init__(self, api_key, session_id=None):
        self.api_key = api_key
        self.api_url = "https://api.fireworks.ai/inference/v1/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.conversation_history = []
        self.session_id = session_id or str(uuid.uuid4())
        
    def add_message(self, role, content):
        """Add a message to the conversation history."""
        self.conversation_history.append({"role": role, "content": content})
        return {"role": role, "content": content}
    
    def create_prompt(self):
        """Create a formatted prompt from conversation history."""
        formatted_messages = []
        
        for msg in self.conversation_history:
            if msg["role"] == "user":
                formatted_messages.append(f"Human: {msg['content']}")
            else:
                formatted_messages.append(f"Assistant: {msg['content']}")
        
        return "\n".join(formatted_messages) + "\nAssistant:"
    
    def get_response(self, model_id="accounts/fireworks/models/mixtral-8x7b-instruct"):
        """Get a response from the Fireworks AI API."""
        prompt = self.create_prompt()
        
        payload = {
            "model": model_id,
            "prompt": prompt,
            "max_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            assistant_response = result.get("choices", [{}])[0].get("text", "").strip()
            
            # Add the assistant's response to conversation history
            self.add_message("assistant", assistant_response)
            
            return assistant_response
        
        except requests.exceptions.RequestException as e:
            error_msg = f"Error: {str(e)}"
            self.add_message("assistant", error_msg)
            return error_msg

    def generate_essay(self, topic, length="medium", style="academic", tone="neutral", 
                      model_id="accounts/fireworks/models/mixtral-8x7b-instruct", 
                      references=True, stream=False, callback=None):
        """Generate an essay on a given topic with streaming support."""
        # Define length in word count
        length_mapping = {
            "short": "500-750 words",
            "medium": "1000-1500 words",
            "long": "2000-2500 words",
            "extended": "3000-3500 words"
        }
        
        # Define style descriptions
        style_mapping = {
            "academic": "formal academic writing with proper citations and scholarly language",
            "informative": "clear, educational content with a balanced perspective",
            "persuasive": "convincing arguments with supporting evidence",
            "creative": "engaging and descriptive language with narrative elements",
            "technical": "detailed technical analysis with industry-specific terminology"
        }
        
        # Define tone options
        tone_mapping = {
            "neutral": "balanced and objective",
            "optimistic": "positive and hopeful",
            "critical": "analytical and questioning",
            "conversational": "friendly and accessible",
            "authoritative": "confident and expert"
        }
        
        word_count = length_mapping.get(length.lower(), "1000-1500 words")
        writing_style = style_mapping.get(style.lower(), "formal academic writing")
        writing_tone = tone_mapping.get(tone.lower(), "balanced and objective")
        
        reference_text = ""
        if references:
            reference_text = """
6. Include a 'References' or 'Works Cited' section at the end using appropriate citation format
7. Cite reliable sources to support key points"""
        
        prompt = f"""Please write a well-structured essay on the topic: "{topic}".
        
Length: {word_count}
Style: {writing_style}
Tone: {writing_tone}

The essay should include:
1. An engaging introduction with a clear thesis statement
2. Well-developed body paragraphs with logical transitions
3. Supporting evidence and examples
4. A thoughtful conclusion that summarizes key points
5. Proper paragraph structure and organization{reference_text}

Please structure the essay with a title and clear section headings."""

        # If not streaming, use the regular API call
        if not stream:
            payload = {
                "model": model_id,
                "prompt": prompt,
                "max_tokens": 4000,
                "temperature": 0.7,
                "top_p": 0.9
            }
            
            try:
                response = requests.post(self.api_url, headers=self.headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                essay_text = result.get("choices", [{}])[0].get("text", "").strip()
                
                return essay_text
            
            except requests.exceptions.RequestException as e:
                return f"Error generating essay: {str(e)}"
        
        # For streaming, we use a separate API endpoint and process chunk by chunk
        else:
            stream_url = "https://api.fireworks.ai/inference/v1/completions"
            
            payload = {
                "model": model_id,
                "prompt": prompt,
                "max_tokens": 4000,
                "temperature": 0.7,
                "top_p": 0.9,
                "stream": True
            }
            
            full_text = ""
            
            try:
                response = requests.post(stream_url, headers=self.headers, json=payload, stream=True)
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        try:
                            line_text = line.decode('utf-8')
                            if line_text.startswith('data: '):
                                json_str = line_text[6:]  # Remove 'data: ' prefix
                                if json_str.strip() == '[DONE]':
                                    break
                                
                                chunk_data = json.loads(json_str)
                                chunk_text = chunk_data.get('choices', [{}])[0].get('text', '')
                                
                                if chunk_text:
                                    full_text += chunk_text
                                    if callback:
                                        callback(chunk_text, full_text)
                        except Exception as e:
                            print(f"Error processing chunk: {str(e)}")
                
                return full_text
            
            except requests.exceptions.RequestException as e:
                error_msg = f"Error streaming essay: {str(e)}"
                if callback:
                    callback(error_msg, error_msg)
                return error_msg
    
    def export_to_pdf(self, content, filename=None):
        """Export content to a PDF file."""
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"essay_{timestamp}.pdf"
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Add title
        pdf.set_font("Arial", "B", 16)
        
        # Try to extract title from content
        lines = content.split('\n')
        title = "Generated Essay"
        for line in lines[:5]:  # Check first few lines for title
            if line and not line.startswith('#') and len(line) < 100:
                title = line.strip()
                break
        
        pdf.cell(0, 10, title, ln=True, align='C')
        pdf.ln(5)
        
        # Add content
        pdf.set_font("Arial", "", 12)
        
        # Process the content
        text = content
        # Remove the title from the content if found
        if title in text and title != "Generated Essay":
            text = text.replace(title, "", 1)
        
        # Format markdown headers
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            if line.startswith('# '):
                formatted_lines.append(f"\n{line[2:]}\n")
                pdf.set_font("Arial", "B", 14)
            elif line.startswith('## '):
                formatted_lines.append(f"\n{line[3:]}\n")
                pdf.set_font("Arial", "B", 13)
            elif line.startswith('### '):
                formatted_lines.append(f"\n{line[4:]}\n")
                pdf.set_font("Arial", "B", 12)
            else:
                formatted_lines.append(line)
                pdf.set_font("Arial", "", 12)
        
        text = '\n'.join(formatted_lines)
        
        # Add text with wrapping
        for line in text.split('\n'):
            wrapped_text = textwrap.fill(line, width=80) if line else ""
            if wrapped_text:
                pdf.multi_cell(0, 10, wrapped_text)
            else:
                pdf.ln(5)  # Add some space for empty lines
        
        # Add footer with date
        pdf.set_y(-15)
        pdf.set_font("Arial", "I", 8)
        current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pdf.cell(0, 10, f"Generated on {current_date}", 0, 0, 'C')
        
        # Save the PDF
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        pdf.output(output_path)
        return output_path
    
    def chat(self, user_input):
        """Process user input and return chatbot response."""
        self.add_message("user", user_input)
        return self.get_response()
    
    def summarize_document(self, text, model_id="accounts/fireworks/models/mixtral-8x7b-instruct"):
        """Summarize the provided text."""
        prompt = f"""Please provide a comprehensive summary of the following text. 
Include the key points, main arguments, and important details.

Text to summarize:
{text[:4000]}  # Truncate if too long

Summary:"""

        payload = {
            "model": model_id,
            "prompt": prompt,
            "max_tokens": 1000,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            summary = result.get("choices", [{}])[0].get("text", "").strip()
            
            return summary
        
        except requests.exceptions.RequestException as e:
            return f"Error generating summary: {str(e)}"
    
    def analyze_sentiment(self, text, model_id="accounts/fireworks/models/mixtral-8x7b-instruct"):
        """Analyze the sentiment of the provided text."""
        prompt = f"""Please analyze the sentiment of the following text. Categorize it as positive, negative, or neutral, and provide a brief explanation of your analysis including key emotional indicators and tone.

Text to analyze:
{text[:2000]}  # Truncate if too long

Sentiment analysis:"""

        payload = {
            "model": model_id,
            "prompt": prompt,
            "max_tokens": 500,
            "temperature": 0.3,
            "top_p": 0.9
        }
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            analysis = result.get("choices", [{}])[0].get("text", "").strip()
            
            return analysis
        
        except requests.exceptions.RequestException as e:
            return f"Error analyzing sentiment: {str(e)}"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_file_content(file_path):
    """Read and return file content based on extension."""
    ext = file_path.rsplit('.', 1)[1].lower()
    
    if ext == 'txt' or ext == 'md':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    elif ext == 'pdf':
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
    elif ext == 'docx':
        try:
            import docx
            doc = docx.Document(file_path)
            text = []
            for para in doc.paragraphs:
                text.append(para.text)
            return '\n'.join(text)
        except Exception as e:
            return f"Error reading DOCX: {str(e)}"
    return "Unsupported file format"

# Clean up old files periodically
def cleanup_old_files():
    while True:
        time.sleep(3600)  # Run every hour
        current_time = time.time()
        # Clean up files older than 24 hours
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(filepath):
                file_time = os.path.getmtime(filepath)
                if current_time - file_time > 24 * 3600:
                    try:
                        os.remove(filepath)
                        print(f"Removed old file: {filename}")
                    except Exception as e:
                        print(f"Error removing file {filename}: {str(e)}")

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

# Routes
@app.route('/')
def index():
    # Create a new session if one doesn't exist
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        active_sessions[session['session_id']] = FireworksAIChatbot(API_KEY, session['session_id'])
    
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    if session['session_id'] not in active_sessions:
        active_sessions[session['session_id']] = FireworksAIChatbot(API_KEY, session['session_id'])
    
    chatbot = active_sessions[session['session_id']]
    chatbot.add_message("user", message)
    response = chatbot.get_response()
    
    return jsonify({'response': response})

@app.route('/essay', methods=['POST'])
def generate_essay():
    data = request.json
    topic = data.get('topic', '')
    length = data.get('length', 'medium')
    style = data.get('style', 'academic')
    tone = data.get('tone', 'neutral')
    references = data.get('references', True)
    
    if not topic:
        return jsonify({'error': 'Topic is required'}), 400
    
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    if session['session_id'] not in active_sessions:
        active_sessions[session['session_id']] = FireworksAIChatbot(API_KEY, session['session_id'])
    
    chatbot = active_sessions[session['session_id']]
    essay = chatbot.generate_essay(topic, length, style, tone, references=references)
    
    # Generate a PDF file
    filename = f"essay_{session['session_id']}_{uuid.uuid4().hex[:8]}.pdf"
    pdf_path = chatbot.export_to_pdf(essay, filename)
    
    # Store the filename for download
    file_id = uuid.uuid4().hex
    generated_files[file_id] = pdf_path
    
    return jsonify({
        'essay': essay, 
        'file_id': file_id,
        'message': 'Essay generated successfully'
    })

@app.route('/download/<file_id>', methods=['GET'])
def download_file(file_id):
    if file_id not in generated_files:
        return "File not found", 404
    
    filepath = generated_files[file_id]
    filename = os.path.basename(filepath)
    
    return send_file(filepath, as_attachment=True, download_name=filename)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Read the file content
        content = read_file_content(filepath)
        
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': filename,
            'content': content[:2000] + '...' if len(content) > 2000 else content
        })
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/summarize', methods=['POST'])
def summarize():
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    if session['session_id'] not in active_sessions:
        active_sessions[session['session_id']] = FireworksAIChatbot(API_KEY, session['session_id'])
    
    chatbot = active_sessions[session['session_id']]
    summary = chatbot.summarize_document(text)
    
    return jsonify({'summary': summary})

@app.route('/analyze-sentiment', methods=['POST'])
def analyze_sentiment():
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    if session['session_id'] not in active_sessions:
        active_sessions[session['session_id']] = FireworksAIChatbot(API_KEY, session['session_id'])
    
    chatbot = active_sessions[session['session_id']]
    analysis = chatbot.analyze_sentiment(text)
    
    return jsonify({'analysis': analysis})

@app.route('/clear-chat', methods=['POST'])
def clear_chat():
    if 'session_id' in session and session['session_id'] in active_sessions:
        # Create a new chatbot instance
        active_sessions[session['session_id']] = FireworksAIChatbot(API_KEY, session['session_id'])
    
    return jsonify({'message': 'Chat history cleared'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)