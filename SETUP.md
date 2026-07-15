# 🚀 Quick Start Guide

## Option 1: Local Installation (Recommended)

### Step 1: Install Ollama
1. Visit [ollama.ai](https://ollama.ai)
2. Download for Windows
3. Run the installer

### Step 2: Pull Model
Open Command Prompt and run:
```bash
ollama pull llama3
```

### Step 3: Start Server
```bash
ollama serve
```

### Step 4: Run App
Open a new terminal:
```bash
cd D:\MyMimoProject\resume-matcher
pip install -r requirements.txt
streamlit run app.py
```

## Option 2: Cloud API (Alternative)

If you prefer using a cloud API instead of local Ollama:

1. Get an API key from [OpenAI](https://platform.openai.com) or [Together AI](https://together.ai)
2. Modify `app.py` to use the API instead of Ollama
3. Set your API key as environment variable

## Troubleshooting

### Ollama won't start
- Try running as Administrator
- Check if port 11434 is in use
- Restart your computer after installation

### Model not found
```bash
ollama list
ollama pull llama3
```

### PDF extraction fails
- Ensure PDF is not password-protected
- Try converting to TXT format

## System Requirements
- Windows 10/11
- 8GB RAM minimum (16GB recommended)
- 10GB free disk space for model