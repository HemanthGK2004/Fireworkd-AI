# Fireworks AI Web Application

This is a Flask-based web application that integrates with the Fireworks AI API to provide chat functionality, essay generation, and text analysis tools.

## Features

### AI Chat Assistant
- Interactive chat with Fireworks AI's Mixtral 8x7B model
- Conversation history management
- Markdown support for code blocks, links, and formatting

### Essay Generator
- Generate well-structured essays on any topic
- Customize essay length (short, medium, long, extended)
- Choose writing style (academic, informative, persuasive, creative, technical)
- Select tone (neutral, optimistic, critical, conversational, authoritative)
- Option to include references and citations
- Export essays to PDF

### Text Analysis Tools
- Document summarization
- Sentiment analysis
- Support for multiple file formats (TXT, PDF, DOCX, MD)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd fireworks_ai_web_app
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Set up your Fireworks AI API key:
   - The current code uses a fixed API key for demonstration purposes
   - For production, replace it with an environment variable:
   ```python
   # In app.py
   API_KEY = os.environ.get("FIREWORKS_API_KEY", "your_default_key")
   ```

5. Run the application:
```bash
python app.py
```

The application will be available at http://localhost:5000

## Project Structure

```
fireworks_ai_web_app/
│
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
│
├── static/
│   └── script.js       # Frontend JavaScript
│
├── templates/
│   └── index.html      # Main HTML template
│
└── uploads/            # Directory for uploaded files
```

## Usage

### Chat
1. Go to the Chat tab
2. Type your message in the input field
3. Press Enter or click Send

### Essay Generation
1. Go to the Essay Generator tab
2. Enter the essay topic
3. Select desired length, style, and tone
4. Click "Generate Essay"
5. Wait for the essay to be generated
6. Download the essay as PDF or copy the text

### Text Analysis
1. Go to the Text Tools tab
2. Paste text or upload a document
3. Choose the analysis method (summarize or sentiment analysis)
4. View and copy the results

## Security Notes

- This application uses server-side sessions for user management
- API keys should be stored as environment variables in production
- File uploads are restricted to specific file types and size limits
- All uploaded and generated files are automatically cleaned up after 24 hours

## Dependencies

- Flask: Web framework
- Requests: HTTP client for API calls
- FPDF: PDF generation
- PyPDF2: PDF parsing
- python-docx: DOCX parsing
- Bootstrap 5: Frontend UI framework
- Font Awesome: Icons

## License

[MIT License](LICENSE)