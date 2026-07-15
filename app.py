import streamlit as st
import requests
import fitz  # PyMuPDF for PDF parsing
import json
import re
import os
from datetime import datetime
from typing import Dict, List, Optional

# ── Translations ─────────────────────────────────────────────────────────────
T = {
    "zh": {
        "title": "🎯 简历 & 职位匹配器",
        "subtitle": "上传简历和职位描述，获取 AI 驱动的匹配分析",
        "sidebar_title": "简历匹配器",
        "sidebar_caption": "AI 驱动的职位匹配分析工具",
        "provider": "AI 服务商",
        "api_key": "API Key",
        "base_url": "Base URL",
        "model": "模型",
        "history": "历史记录",
        "history_count": "共 {n} 条分析记录",
        "clear_history": "清空历史",
        "no_history": "暂无历史记录",
        "tab_analysis": "📄 分析",
        "tab_results": "📊 结果",
        "tab_history": "📜 历史",
        "resume": "简历",
        "job_desc": "职位描述",
        "upload_resume": "上传简历",
        "upload_job": "上传职位描述",
        "upload_help": "支持 PDF 和 TXT 格式",
        "loaded": "✅ 已加载: {name}",
        "analyze": "🔍 开始分析",
        "analyzing": "🤖 AI ({provider}) 正在分析简历与职位描述...",
        "analysis_done": "✅ 分析完成！请查看结果标签页。",
        "error_api_key": "❌ 请在侧边栏输入 API Key",
        "error_connect": "❌ 无法连接到 API，请检查 API Key 和网络。",
        "error_ollama": "❌ 无法连接到 Ollama，请确保 `ollama serve` 正在运行。",
        "error_generic": "❌ 错误: {error}",
        "warning_upload": "⚠️ 请上传简历和职位描述。",
        "resume_file": "简历",
        "job_file": "职位描述",
        "provider_label": "服务商",
        "model_label": "模型",
        "detailed_analysis": "📋 详细分析",
        "download_report": "📥 下载报告",
        "no_results": "📊 暂无分析结果。请在分析标签页上传文件并点击分析。",
        "history_title": "📜 分析历史（{n} 条记录）",
        "history_resume": "简历:",
        "history_job": "职位:",
        "history_score": "分数:",
        "history_provider": "服务商:",
        "no_history_detail": "📜 暂无分析历史。完成一次分析后即可查看。",
        "score_excellent": "优秀匹配",
        "score_good": "良好匹配",
        "score_fair": "一般匹配",
        "score_poor": "较差匹配",
        "ollama_setup": """
**配置步骤:**
1. 安装 [Ollama](https://ollama.ai)
2. 运行: `ollama serve`
3. 拉取模型: `ollama pull llama3`
""",
    },
    "en": {
        "title": "🎯 Resume & Job Matcher",
        "subtitle": "Upload your resume and job description to get AI-powered fit analysis",
        "sidebar_title": "Resume Matcher",
        "sidebar_caption": "AI-Powered Job Fit Analyzer",
        "provider": "AI Provider",
        "api_key": "API Key",
        "base_url": "Base URL",
        "model": "Model",
        "history": "History",
        "history_count": "Total {n} analyses",
        "clear_history": "Clear History",
        "no_history": "No history yet",
        "tab_analysis": "📄 Analysis",
        "tab_results": "📊 Results",
        "tab_history": "📜 History",
        "resume": "Resume",
        "job_desc": "Job Description",
        "upload_resume": "Upload Resume",
        "upload_job": "Upload Job Description",
        "upload_help": "Supports PDF and TXT formats",
        "loaded": "✅ Loaded: {name}",
        "analyze": "🔍 Analyze Match",
        "analyzing": "🤖 AI ({provider}) is analyzing your resume vs job description...",
        "analysis_done": "✅ Analysis complete! Check the Results tab.",
        "error_api_key": "❌ Please enter your API key in the sidebar.",
        "error_connect": "❌ Cannot connect to API. Please check your API key and network.",
        "error_ollama": "❌ Cannot connect to Ollama. Please ensure `ollama serve` is running.",
        "error_generic": "❌ Error: {error}",
        "warning_upload": "⚠️ Please upload both Resume and Job Description.",
        "resume_file": "Resume",
        "job_file": "Job Description",
        "provider_label": "Provider",
        "model_label": "Model",
        "detailed_analysis": "📋 Detailed Analysis",
        "download_report": "📥 Download Report",
        "no_results": "📊 No analysis results yet. Upload files and click Analyze in the Analysis tab.",
        "history_title": "📜 Analysis History ({n} records)",
        "history_resume": "Resume:",
        "history_job": "Job:",
        "history_score": "Score:",
        "history_provider": "Provider:",
        "no_history_detail": "📜 No analysis history yet. Complete an analysis to see it here.",
        "score_excellent": "Excellent Match",
        "score_good": "Good Match",
        "score_fair": "Fair Match",
        "score_poor": "Poor Match",
        "ollama_setup": """
**Setup:**
1. Install [Ollama](https://ollama.ai)
2. Run: `ollama serve`
3. Pull model: `ollama pull llama3`
""",
    },
}

def t(key: str, **kwargs) -> str:
    """Get translated text"""
    lang = st.session_state.get("lang", "en")
    text = T.get(lang, T["en"]).get(key, T["en"].get(key, key))
    return text.format(**kwargs) if kwargs else text

# ── Config File ──────────────────────────────────────────────────────────────
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_config(data):
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
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 10px; }
    div[data-testid="stExpander"] { border: 1px solid #e0e0e0; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ── Session State ────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "current_result" not in st.session_state:
    st.session_state.current_result = None
if "lang" not in st.session_state:
    # Auto-detect from Streamlit query params or default to English
    st.session_state.lang = "en"

# ── Helper Functions ─────────────────────────────────────────────────────────
def extract_pdf_text(file) -> str:
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def get_text_from_file(file) -> str:
    if file.type == "application/pdf":
        return extract_pdf_text(file)
    else:
        return file.read().decode("utf-8")

def parse_fit_score(response: str) -> Optional[int]:
    lines = response.split('\n')
    for line in lines:
        line_lower = line.lower()
        if any(kw in line_lower for kw in ['fit score', '匹配分数', '匹配度', '匹配评分']):
            match = re.search(r'(\d{1,3})\s*%', line)
            if match:
                score = int(match.group(1))
                if 10 <= score <= 100:
                    return score
            match = re.search(r':\s*(\d{2,3})\b', line)
            if match:
                score = int(match.group(1))
                if 10 <= score <= 100:
                    return score
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
    if score >= 70: return "#28a745"
    elif score >= 40: return "#ffc107"
    else: return "#dc3545"

def get_score_label(score: int) -> str:
    if score >= 80: return t("score_excellent")
    elif score >= 60: return t("score_good")
    elif score >= 40: return t("score_fair")
    else: return t("score_poor")

def call_llm(provider: str, prompt: str, config: dict) -> str:
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
        response = requests.post(f"{base_url}/chat/completions", headers=headers, json=data, timeout=120)
        result = response.json()
        return result.get("choices", [{}])[0].get("message", {}).get("content", "No response from model.")
    else:
        raise ValueError(f"Unknown provider: {provider}")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/3d-fluency/94/bullseye.png", width=80)
    st.title(t("sidebar_title"))
    st.caption(t("sidebar_caption"))
    
    st.divider()
    
    # Language switcher
    lang = st.radio("Language / 语言", ["en", "zh"], index=0 if st.session_state.lang == "en" else 1, horizontal=True, key="lang_radio")
    if lang != st.session_state.lang:
        st.session_state.lang = lang
        st.rerun()
    
    st.divider()
    
    # Provider selection
    saved = load_config()
    st.subheader(f"🔧 {t('provider')}")
    provider = st.selectbox(
        t("provider"),
        ["Ollama (Local)", "OpenAI", "Together AI", "API2D"],
        index=["Ollama (Local)", "OpenAI", "Together AI", "API2D"].index(saved.get("provider", "API2D")),
        key="provider_select",
    )
    
    config = {}
    api_key = ""
    
    if provider == "Ollama (Local)":
        provider_key = "Ollama"
        model = st.selectbox(t("model"), ["llama3", "llama3.1", "mistral", "codellama"], index=0)
        config = {"model": model}
        st.info(t("ollama_setup"))
    elif provider == "OpenAI":
        provider_key = "OpenAI"
        api_key = st.text_input("OpenAI API Key", type="password", value=saved.get("api_key", ""))
        model = st.selectbox(t("model"), ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0)
        config = {"api_key": api_key, "base_url": "https://api.openai.com/v1", "model": model}
    elif provider == "Together AI":
        provider_key = "Together AI"
        api_key = st.text_input("Together AI API Key", type="password", value=saved.get("api_key", ""))
        model = st.selectbox(t("model"), ["meta-llama/Llama-3-70b-chat-hf", "meta-llama/Llama-3-8b-chat-hf", "mistralai/Mixtral-8x7B-Instruct-v0.1"], index=0)
        config = {"api_key": api_key, "base_url": "https://api.together.xyz/v1", "model": model}
    elif provider == "API2D":
        provider_key = "API2D"
        api_key = st.text_input("API2D API Key", type="password", value=saved.get("api_key", ""))
        base_url = st.text_input(t("base_url"), value=saved.get("base_url", "https://oa.api2d.net"))
        model = st.selectbox(t("model"), ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0)
        config = {"api_key": api_key, "base_url": base_url, "model": model}
    
    if api_key and provider != "Ollama (Local)":
        save_config({"provider": provider, "api_key": api_key, "base_url": config.get("base_url", "")})
    
    st.divider()
    st.subheader(f"📜 {t('history')}")
    if st.session_state.history:
        st.write(t("history_count", n=len(st.session_state.history)))
        if st.button(t("clear_history")):
            st.session_state.history = []
            st.rerun()
    else:
        st.caption(t("no_history"))

# ── Main Content ─────────────────────────────────────────────────────────────
st.title(t("title"))
st.caption(t("subtitle"))

tab1, tab2, tab3 = st.tabs([t("tab_analysis"), t("tab_results"), t("tab_history")])

# ── Tab 1: Analysis ──────────────────────────────────────────────────────────
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(t("resume"))
        resume_file = st.file_uploader(t("upload_resume"), type=["pdf", "txt"], key="resume", help=t("upload_help"))
        if resume_file:
            st.success(t("loaded", name=resume_file.name))
    with col2:
        st.subheader(t("job_desc"))
        job_file = st.file_uploader(t("upload_job"), type=["pdf", "txt"], key="job", help=t("upload_help"))
        if job_file:
            st.success(t("loaded", name=job_file.name))
    
    st.divider()
    
    if st.button(t("analyze"), type="primary", use_container_width=True):
        if resume_file and job_file:
            if provider_key in ["OpenAI", "Together AI", "API2D"] and not config.get("api_key"):
                st.error(t("error_api_key"))
                st.stop()
            
            with st.spinner(t("analyzing", provider=provider)):
                resume_text = get_text_from_file(resume_file)
                job_text = get_text_from_file(job_file)
                
                lang_instruction = "Please respond in Chinese." if st.session_state.lang == "zh" else "Please respond in English."
                
                prompt = f"""
You are an expert career consultant and ATS specialist.

Analyze the following resume against the job description and provide:

1. **Fit Score** (0-100%): How well does this resume match the job requirements?

2. **Key Strengths**: List 3-5 specific areas where the resume aligns well with the job.

3. **Skill Gaps**: List specific skills or experiences mentioned in the job description that are missing from the resume.

4. **Recommendations**: Provide 5 specific, actionable improvements to make the resume better fit this job.

5. **ATS Optimization**: Suggest keywords from the job description that should be added to the resume.

6. **Overall Assessment**: A brief summary paragraph.

{lang_instruction}
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
                    score = parse_fit_score(output)
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
                    st.success(t("analysis_done"))
                except requests.exceptions.ConnectionError:
                    st.error(t("error_ollama") if provider_key == "Ollama" else t("error_connect"))
                except Exception as e:
                    st.error(t("error_generic", error=str(e)))
        else:
            st.warning(t("warning_upload"))

# ── Tab 2: Results ───────────────────────────────────────────────────────────
with tab2:
    if st.session_state.current_result:
        result = st.session_state.current_result
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
        
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric(t("resume_file"), result["resume_name"])
        with col2: st.metric(t("job_file"), result["job_name"])
        with col3: st.metric(t("provider_label"), result["provider"])
        with col4: st.metric(t("model_label"), result["model"])
        
        st.divider()
        st.subheader(t("detailed_analysis"))
        st.markdown(result["analysis"])
        
        st.divider()
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.download_button(
                t("download_report"),
                data=result["analysis"],
                file_name=f"resume_match_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True
            )
    else:
        st.info(t("no_results"))

# ── Tab 3: History ───────────────────────────────────────────────────────────
with tab3:
    if st.session_state.history:
        st.subheader(t("history_title", n=len(st.session_state.history)))
        for i, record in enumerate(reversed(st.session_state.history)):
            score_str = 'N/A' if not record['score'] else str(record['score']) + '%'
            icon = '🟢' if record['score'] and record['score'] >= 60 else '🟡' if record['score'] and record['score'] >= 40 else '🔴'
            with st.expander(f"{icon} {record['resume_name']} → {record['job_name']} ({score_str}) - {record['timestamp']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**{t('history_resume')}** {record['resume_name']}")
                    st.write(f"**{t('history_job')}** {record['job_name']}")
                with col2:
                    st.write(f"**{t('history_score')}** {score_str}")
                    st.write(f"**{t('history_provider')}** {record.get('provider', 'Unknown')}")
                st.divider()
                st.markdown(record["analysis"])
    else:
        st.info(t("no_history_detail"))
