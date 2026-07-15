# 🎯 Resume Matcher - AI Job Fit Analyzer

An AI-powered resume analysis tool that compares your resume against job descriptions and provides detailed fit scoring, skill gap analysis, and improvement recommendations.

## ✨ Features

- **Fit Score Analysis**: Get a 0-100% match score between resume and job description
- **Strengths Identification**: Highlights areas where your resume aligns well
- **Skill Gap Analysis**: Identifies missing skills and experiences
- **Actionable Recommendations**: Specific improvements to enhance your resume
- **ATS Optimization**: Keywords and formatting tips for Applicant Tracking Systems
- **Analysis History**: Track all your past analyses
- **Export Reports**: Download analysis as Markdown files

## 🛠️ Tech Stack

- **Python** - Core language
- **Streamlit** - Interactive web UI
- **Ollama** - Local LLM inference (no API costs!)
- **PyMuPDF** - PDF text extraction
- **Llama 3** - AI model for analysis

## 📋 Prerequisites

1. **Install Ollama**
   - Visit [ollama.ai](https://ollama.ai) and install for your OS

2. **Pull a model**
   ```bash
   ollama pull llama3
   ```

3. **Start Ollama server**
   ```bash
   ollama serve
   ```

## 🚀 Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd resume-matcher

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

## 📖 Usage

1. Open your browser to `http://localhost:8501`
2. Upload your resume (PDF or TXT format)
3. Upload the job description (PDF or TXT format)
4. Click "Analyze Match"
5. View your fit score and detailed analysis
6. Download the report for your records

## 📁 Supported Formats

- **PDF** - Automatic text extraction
- **TXT** - Plain text files

## 🔒 Privacy

- **100% Local**: All processing happens on your machine
- **No API Keys**: Uses Ollama for local inference
- **No Data Storage**: Files are not stored or transmitted
- **Open Source**: Full transparency

## 📊 Score Interpretation

| Score | Rating | Description |
|-------|--------|-------------|
| 80-100% | Excellent | Strong match, minimal changes needed |
| 60-79% | Good | Good match, some improvements recommended |
| 40-59% | Fair | Moderate match, significant improvements needed |
| 0-39% | Poor | Weak match, major revisions required |

## 🛠️ Troubleshooting

**Cannot connect to Ollama:**
- Ensure `ollama serve` is running in a separate terminal
- Check if port 11434 is available

**Model not found:**
- Run `ollama pull llama3` to download the model
- Check available models with `ollama list`

**PDF extraction fails:**
- Ensure the PDF is not password-protected
- Try converting to TXT format

## 📄 License

MIT License - Feel free to use and modify for your needs.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io)
- Powered by [Ollama](https://ollama.ai) and [Llama 3](https://ollama.ai/library/llama3)
- PDF parsing by [PyMuPDF](https://pymupdf.readthedocs.io)