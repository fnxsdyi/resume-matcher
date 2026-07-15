import streamlit as st
import requests
import fitz  # PyMuPDF for PDF parsing
import json
import re
import os
from datetime import datetime
from typing import Dict, List, Optional

# ── Config File ──────────────────────────────────────────────────────────────
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    """Load saved config from file"""
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_config(data):
    """Save config to file"""
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Resume Matcher - AI Job Fit Analyzer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
    }
    .score-high { color: #28a745; }
    .score-medium { color: #ffc107; }
    .score-low { color: #dc3545; }
    div[data-testid="stExpander"] {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ── Session State ────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "current_result" not in st.session_state:
    st.session_state.current_result = None

# ── Helper Functions ─────────────────────────────────────────────────────────
def extract_pdf_text(file) -> str:
    """Extract text from PDF file"""
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def get_text_from_file(file) -> str:
    """Extract text from uploaded file (PDF or TXT)"""
    if file.type == "application/pdf":
        return extract_pdf_text(file)
    else:
        return file.read().decode("utf-8")

def parse_fit_score(response: str) -> Optional[int]:
    """Extract fit score from LLM response - looks for the actual Fit Score line"""
    # First, try to find the specific Fit Score line with a percentage
    lines = response.split('\n')
    for line in lines:
        line_lower = line.lower()
        if 'fit score' in line_lower or '匹配分数' in line_lower or '匹配度' in line_lower:
            # Look for a percentage pattern on this line (e.g., "95%" or "95")
            match = re.search(r'(\d{1,3})\s*%', line)
            if match:
                score = int(match.group(1))
                if 10 <= score <= 100:  # Ignore obviously wrong scores like 1%
                    return score
            # Also try just a number if no percentage sign
            match = re.search(r':\s*(\d{2,3})\b', line)
            if match:
                score = int(match.group(1))
                if 10 <= score <= 100:
                    return score
    
    # Fallback: look for patterns like "**Fit Score**: 95%"
    patterns = [
        r'[Ff]it\s*[Ss]core\s*[:\s]*(\d{2,3})\s*%',
        r'[Ss]core\s*[:\s]*(\d{2,3})\s*%',
        r'(\d{2,3})\s*%\s*(?:match|fit|匹配)',
    ]
    for pattern in patterns:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            score = int(match.group(1))
            if 10 <= score <= 100:
                return score
    
    return None

def get_score_color(score: int) -> str:
    """Get color based on score"""
    if score >= 70:
        return "#28a745"
    elif score >= 40:
        return "#ffc107"
    else:
        return "#dc3545"

def get_score_label(score: int) -> str:
    """Get label based on score"""
    if score >= 80:
        return "Excellent Match"
    elif score >= 60:
        return "Good Match"
    elif score >= 40:
        return "Fair Match"
    else:
        return "Poor Match"

def call_llm(provider: str, prompt: str, config: dict) -> str:
    """Call LLM based on provider"""
    if provider == "Ollama":
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": config.get("model", "llama3"), "prompt": prompt, "stream": False},
            timeout=120
        )
        return response.json().get("response", "No response from model.")
    
    elif provider in ["OpenAI", "Together AI", "API2D"]:
        base_url = config.get("base_url", "https://api.openai.com/v1")
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json"
        }
        data = {
            "model": config.get("model", "gpt-4o-mini"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 4000
        }
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=120
        )
        result = response.json()
        return result.get("choices", [{}])[0].get("message", {}).get("content", "No response from model.")
    
    else:
        raise ValueError(f"Unknown provider: {provider}")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/3d-fluency/94/bullseye.png", width=80)
    st.title("Resume Matcher")
    st.caption("AI-Powered Job Fit Analyzer")
    
    st.divider()
    
    # Provider selection
    saved = load_config()
    st.subheader("🔧 AI Provider")
    provider = st.selectbox(
        "Select Provider",
        ["Ollama (Local)", "OpenAI", "Together AI", "API2D"],
        index=["Ollama (Local)", "OpenAI", "Together AI", "API2D"].index(saved.get("provider", "API2D")),
        key="provider_select",
        help="Choose your AI backend"
    )
    
    config = {}
    
    if provider == "Ollama (Local)":
        provider_key = "Ollama"
        model = st.selectbox(
            "Select Model",
            ["llama3", "llama3.1", "mistral", "codellama"],
            index=0
        )
        config = {"model": model}
        
        st.info("""
        **Setup:**
        1. Install [Ollama](https://ollama.ai)
        2. Run: `ollama serve`
        3. Pull model: `ollama pull llama3`
        """)
    
    elif provider == "OpenAI":
        provider_key = "OpenAI"
        api_key = st.text_input("OpenAI API Key", type="password", value=saved.get("api_key", ""))
        model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0)
        config = {
            "api_key": api_key,
            "base_url": "https://api.openai.com/v1",
            "model": model
        }
    
    elif provider == "Together AI":
        provider_key = "Together AI"
        api_key = st.text_input("Together AI API Key", type="password", value=saved.get("api_key", ""))
        model = st.selectbox("Model", ["meta-llama/Llama-3-70b-chat-hf", "meta-llama/Llama-3-8b-chat-hf", "mistralai/Mixtral-8x7B-Instruct-v0.1"], index=0)
        config = {
            "api_key": api_key,
            "base_url": "https://api.together.xyz/v1",
            "model": model
        }
    
    elif provider == "API2D":
        provider_key = "API2D"
        api_key = st.text_input("API2D API Key", type="password", value=saved.get("api_key", ""))
        base_url = st.text_input("Base URL", value=saved.get("base_url", "https://oa.api2d.net"))
        model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0)
        config = {
            "api_key": api_key,
            "base_url": base_url,
            "model": model
        }
    
    # Save config when API key is provided
    if api_key if provider != "Ollama (Local)" else False:
        save_config({
            "provider": provider,
            "api_key": api_key,
            "base_url": config.get("base_url", ""),
        })
    
    st.divider()
    
    # History
    st.subheader("📜 History")
    if st.session_state.history:
        st.write(f"Total analyses: {len(st.session_state.history)}")
        if st.button("Clear History"):
            st.session_state.history = []
            st.rerun()
    else:
        st.caption("No history yet")

# ── Main Content ─────────────────────────────────────────────────────────────
st.title("🎯 Resume & Job Matcher")
st.caption("Upload your resume and job description to get AI-powered fit analysis")

# Tabs
tab1, tab2, tab3 = st.tabs(["📄 Analysis", "📊 Results", "📜 History"])

# ── Tab 1: Analysis ──────────────────────────────────────────────────────────
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Resume")
        resume_file = st.file_uploader(
            "Upload Resume",
            type=["pdf", "txt"],
            key="resume",
            help="Supports PDF and TXT formats"
        )
        if resume_file:
            st.success(f"✅ Loaded: {resume_file.name}")
    
    with col2:
        st.subheader("Job Description")
        job_file = st.file_uploader(
            "Upload Job Description",
            type=["pdf", "txt"],
            key="job",
            help="Supports PDF and TXT formats"
        )
        if job_file:
            st.success(f"✅ Loaded: {job_file.name}")
    
    st.divider()
    
    # Analysis button
    if st.button("🔍 Analyze Match", type="primary", use_container_width=True):
        if resume_file and job_file:
            # Check if API key is needed
            if provider_key in ["OpenAI", "Together AI", "API2D"] and not config.get("api_key"):
                st.error("❌ Please enter your API key in the sidebar.")
                st.stop()
            
            with st.spinner(f"🤖 AI ({provider}) is analyzing your resume vs job description..."):
                # Extract text
                resume_text = get_text_from_file(resume_file)
                job_text = get_text_from_file(job_file)
                
                # Create prompt
                prompt = f"""
You are an expert career consultant and ATS (Applicant Tracking System) specialist.

Analyze the following resume against the job description and provide:

1. **Fit Score** (0-100%): How well does this resume match the job requirements?

2. **Key Strengths**: List 3-5 specific areas where the resume aligns well with the job.

3. **Skill Gaps**: List specific skills or experiences mentioned in the job description that are missing from the resume.

4. **Recommendations**: Provide 5 specific, actionable improvements to make the resume better fit this job.

5. **ATS Optimization**: Suggest keywords from the job description that should be added to the resume.

6. **Overall Assessment**: A brief summary paragraph.

Format your response in clear Markdown with headers and bullet points.

---

RESUME:
{resume_text[:3000]}

---

JOB DESCRIPTION:
{job_text[:3000]}
"""
                
                try:
                    output = call_llm(provider_key, prompt, config)
                    
                    # Parse score
                    score = parse_fit_score(output)
                    
                    # Store result
                    result = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "resume_name": resume_file.name,
                        "job_name": job_file.name,
                        "score": score,
                        "analysis": output,
                        "provider": provider,
                        "model": config.get("model", "unknown")
                    }
                    
                    st.session_state.current_result = result
                    st.session_state.history.append(result)
                    
                    st.success("✅ Analysis complete! Check the Results tab.")
                    
                except requests.exceptions.ConnectionError:
                    if provider_key == "Ollama":
                        st.error("❌ Cannot connect to Ollama. Please ensure `ollama serve` is running.")
                    else:
                        st.error("❌ Cannot connect to API. Please check your API key and network.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("⚠️ Please upload both Resume and Job Description.")

# ── Tab 2: Results ───────────────────────────────────────────────────────────
with tab2:
    if st.session_state.current_result:
        result = st.session_state.current_result
        
        # Score display
        if result["score"] is not None:
            score = result["score"]
            color = get_score_color(score)
            label = get_score_label(score)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown(f"""
                <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, {color}22, {color}11); border-radius: 15px; border: 2px solid {color}">
                    <h1 style="color: {color}; margin: 0; font-size: 64px;">{score}%</h1>
                    <p style="color: {color}; margin: 5px 0 0 0; font-size: 18px; font-weight: bold;">{label}</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()
        
        # Metadata
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Resume", result["resume_name"])
        with col2:
            st.metric("Job Description", result["job_name"])
        with col3:
            st.metric("Provider", result["provider"])
        with col4:
            st.metric("Model", result["model"])
        
        st.divider()
        
        # Full analysis
        st.subheader("📋 Detailed Analysis")
        st.markdown(result["analysis"])
        
        # Download
        st.divider()
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.download_button(
                "📥 Download Report",
                data=result["analysis"],
                file_name=f"resume_match_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True
            )
    else:
        st.info("📊 No analysis results yet. Upload files and click Analyze in the Analysis tab.")

# ── Tab 3: History ───────────────────────────────────────────────────────────
with tab3:
    if st.session_state.history:
        st.subheader(f"📜 Analysis History ({len(st.session_state.history)} records)")
        
        for i, record in enumerate(reversed(st.session_state.history)):
            with st.expander(
                f"{'🟢' if record['score'] and record['score'] >= 60 else '🟡' if record['score'] and record['score'] >= 40 else '🔴'} "
                f"{record['resume_name']} → {record['job_name']} "
                f"({'N/A' if not record['score'] else str(record['score']) + '%'}) "
                f"- {record['timestamp']}"
            ):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Resume:** {record['resume_name']}")
                    st.write(f"**Job:** {record['job_name']}")
                with col2:
                    st.write(f"**Score:** {'N/A' if not record['score'] else str(record['score']) + '%'}")
                    st.write(f"**Provider:** {record.get('provider', 'Unknown')}")
                
                st.divider()
                st.markdown(record["analysis"])
    else:
        st.info("📜 No analysis history yet. Complete an analysis to see it here.")