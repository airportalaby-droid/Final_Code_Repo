import streamlit as st
from core.repo_loader import RepoLoader
from core.scanner import scan_repo
from agent.agent import generate_fix
import os
import difflib

EXT_TO_LANG = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript", ".java": "java",
    ".go": "go", ".c": "c", ".cpp": "cpp", ".php": "php", ".rb": "ruby",
}

def _get_lang(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1]
    return EXT_TO_LANG.get(ext, "text")

# ── Session state init ────────────────────────────────────────────────────────
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'results' not in st.session_state:
    st.session_state.results = []
if 'files' not in st.session_state:
    st.session_state.files = []
if 'fixes' not in st.session_state:
    # Cache: key = (vuln_type, snippet, model) → fix dict
    st.session_state.fixes = {}

st.set_page_config(page_title="CodeSentinel 🛡️", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;700;800&family=JetBrains+Mono:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif !important;
    }
    
    code, pre, .stCodeBlock {
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    @keyframes fadeInDown {
        0% { opacity: 0; transform: translateY(-25px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes backgroundPan {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes pulseGlow {
        0% { box-shadow: 0 0 10px rgba(0, 240, 255, 0.3); }
        50% { box-shadow: 0 0 25px rgba(0, 240, 255, 0.6); }
        100% { box-shadow: 0 0 10px rgba(0, 240, 255, 0.3); }
    }
    
    .hero-container {
        animation: fadeInDown 0.8s ease-out forwards;
        text-align: center;
        margin-top: -1rem;
    }
    
    .hero-title {
        font-weight: 800;
        font-size: 4.5rem;
        background: linear-gradient(135deg, #00C2FF, #7000FF, #00D4FF, #00C2FF);
        background-size: 300% 300%;
        animation: backgroundPan 8s ease infinite;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
        padding-bottom: 0px;
        line-height: 1.1;
        letter-spacing: -2px;
    }
    
    .hero-subtitle {
        font-size: 1.4rem;
        font-weight: 400;
        color: #718096;
        margin-top: 8px;
        margin-bottom: 2rem;
        opacity: 0;
        animation: fadeInDown 0.8s ease-out 0.2s forwards;
    }
    
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
        border: 1px solid rgba(0, 0, 0, 0.05);
        border-radius: 16px;
        padding: 1.5rem 1.75rem;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        animation: fadeInDown 0.6s ease-out forwards;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-8px) scale(1.02);
        background: #ffffff;
        border-color: rgba(0, 240, 255, 0.6);
        box-shadow: 0 10px 30px -10px rgba(0, 200, 255, 0.25);
    }
    
    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(90deg, #00D4FF, #7000FF);
        color: #FFFFFF;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1.5rem;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        transition: all 0.3s ease;
        animation: pulseGlow 3s infinite;
        white-space: nowrap;
        width: 100%;
    }
    
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        transform: translateY(-3px) scale(1.03);
        background: linear-gradient(90deg, #7000FF, #00D4FF);
    }
    
    .stTextInput input, .stSelectbox > div > div {
        background: rgba(0, 0, 0, 0.02) !important;
        border: 1px solid rgba(0, 0, 0, 0.08) !important;
        color: #1A202C !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput input:focus, .stSelectbox > div > div:focus-within {
        border-color: #00D4FF !important;
        box-shadow: 0 0 10px rgba(0, 240, 255, 0.2) !important;
    }

    .line-badge {
        display: inline-block;
        background: rgba(112, 0, 255, 0.12);
        color: #7000FF;
        border-radius: 6px;
        padding: 1px 8px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-left: 6px;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .conf-bar-wrap {
        background: #eee;
        border-radius: 999px;
        height: 8px;
        width: 100%;
        margin-top: 4px;
        margin-bottom: 12px;
    }
    .conf-bar-fill {
        height: 8px;
        border-radius: 999px;
        background: linear-gradient(90deg, #00D4FF, #7000FF);
        transition: width 0.6s ease;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.header("⚙️ System Config")
st.sidebar.markdown("Configure the behavior of your CodeSentinel Subsystem.")
selected_model = st.sidebar.selectbox("🧠 Primary Compute Node (LLM)", ["qwen3", "mistral"], index=0)
ALL_SUPPORTED_EXTS = [".py", ".js", ".java", ".ts", ".go", ".c", ".cpp", ".php", ".rb"]
selected_exts = st.sidebar.multiselect("📂 Analyzed File Extensions", ALL_SUPPORTED_EXTS, default=ALL_SUPPORTED_EXTS)
st.sidebar.write("---")
st.sidebar.info("Ensure the local Ollama daemon is active.")

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-container"><div class="hero-title">CodeSentinel</div><div class="hero-subtitle">Security Fabric &amp; Remediation Engine</div></div>', unsafe_allow_html=True)
st.write("---")

# ── Input Row ─────────────────────────────────────────────────────────────────
# URL and Branch on the same row, Analyze button on its own full-width row below
col1, col2 = st.columns([3, 1])
with col1:
    repo_url = st.text_input("Repository URL", placeholder="https://github.com/username/repository", label_visibility="collapsed")
with col2:
    branch = st.text_input("Branch", placeholder="main / master (optional)", label_visibility="collapsed")

analyze_btn = st.button("🚀 Analyze Repository", use_container_width=True, type="primary")

# ── Analysis trigger ──────────────────────────────────────────────────────────
if analyze_btn and repo_url:
    st.session_state.analysis_complete = False
    st.session_state.results = []
    st.session_state.files = []
    st.session_state.fixes = {}  # clear cached fixes for new repo

    manager = RepoLoader()

    with st.status("Analyzing Repository...", expanded=True) as status:
        try:
            if os.path.exists(os.path.abspath(repo_url)):
                path = os.path.abspath(repo_url)
                manager.repo_path = path
                status.write(f"Loading local directory: `{path}`")
            else:
                status.write("Cloning repository...")
                path = manager.clone_repo(repo_url, branch=branch)
        except Exception as e:
            status.update(label="Error loading repository", state="error")
            st.error(f"Failed to access repository: {str(e)}")
            st.stop()

        status.write("Detecting file extensions in the repository...")
        detected_exts = manager.detect_extensions()

        if detected_exts:
            scan_exts = detected_exts
            status.write(f"Auto-detected extensions: `{', '.join(detected_exts)}`")
        else:
            scan_exts = selected_exts
            status.write(f"No supported extensions detected, using selected: `{', '.join(selected_exts)}`")

        status.write("Parsing and scanning source files...")
        files = manager.get_source_files(valid_exts=scan_exts)
        results = scan_repo(files)

        st.session_state.files = files
        st.session_state.results = results
        st.session_state.analysis_complete = True

        status.update(label=f"Analysis Complete — {len(results)} issue(s) found", state="complete")

    st.write("---")

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.analysis_complete:
    files = st.session_state.files
    results = st.session_state.results

    high_sev  = sum(1 for v in results if getattr(v, "severity", "LOW").upper() == "HIGH")
    med_sev   = sum(1 for v in results if getattr(v, "severity", "LOW").upper() == "MEDIUM")
    low_sev   = len(results) - high_sev - med_sev

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Files Scanned 📂", len(files))
    m2.metric("Total Vulnerabilities 🛡️", len(results))
    m3.metric("High Severity 🚨", high_sev)
    m4.metric("Medium/Low Severity ⚠️", med_sev + low_sev)

    st.write("---")

    colA, colB = st.columns([3, 1])
    with colA:
        st.subheader("🛠️ Vulnerability Report & Remediation")
    with colB:
        report_md = f"# CodeSentinel Report\n\n"
        report_md += f"**Files Scanned:** `{len(files)}`\n\n"
        report_md += f"**Total Vulnerabilities:** `{len(results)}`\n\n"
        for v in results:
            sev = getattr(v, "severity", "LOW")
            lang = _get_lang(v.file_path)
            report_md += f"### {v.vulnerability_type} — `{os.path.basename(v.file_path)}` (Line {v.line_number})\n"
            report_md += f"- **File:** `{v.file_path}`\n- **Severity:** `{sev}`\n\n"
            report_md += f"**Vulnerable Code:**\n```{lang}\n{v.code_snippet}\n```\n\n---\n"
        st.download_button(
            label="📄 Export Report (.md)",
            data=report_md,
            file_name="codesentinel_report.md",
            mime="text/markdown",
            type="secondary",
            use_container_width=True,
        )

    if len(results) == 0:
        st.success("Hooray! No vulnerabilities detected in the scanned files. 🎉")

    VULNERABILITY_EXPLANATIONS = {
        "Code Injection (eval)": (
            "The `eval()` function executes arbitrary Python expressions from a string at runtime. "
            "If an attacker controls the input passed to `eval()`, they can execute any Python code on the server — "
            "including reading files, deleting data, or establishing reverse shells. "
            "**How to fix:** Remove `eval()` entirely and replace it with safe alternatives such as `ast.literal_eval()` "
            "for parsing data literals, or use explicit conditional logic instead of dynamically evaluated code."
        ),
        "Code Injection (exec)": (
            "The `exec()` function runs arbitrary Python statements from a string. "
            "If user-controlled data reaches `exec()`, an attacker can run any code on your server with full privileges. "
            "**How to fix:** Eliminate `exec()` and restructure the logic using dictionaries, factory patterns, "
            "or plugin architectures that don't require dynamic code execution."
        ),
        "Command Injection": (
            "The code passes a string directly to a system shell via `os.system()` or `subprocess` with `shell=True`. "
            "If any part of that string comes from user input, an attacker can inject additional shell commands "
            "(e.g., `; rm -rf /`) to take full control of the operating system. "
            "**How to fix:** Use `subprocess.run()` with a list of arguments instead of a single string, "
            "and set `shell=False` (the default). This ensures arguments are passed directly to the executable "
            "without shell interpretation."
        ),
        "Dynamic Import": (
            "Using `__import__()` to dynamically load modules at runtime can allow an attacker to import "
            "arbitrary modules if the module name comes from untrusted input. "
            "**How to fix:** Use explicit `import` statements for known modules, or validate the module name "
            "against a strict allowlist before calling `__import__()`."
        ),
        "Unsafe Deserialization": (
            "The `pickle.load()` / `pickle.loads()` functions deserialize Python objects from a byte stream. "
            "A maliciously crafted pickle payload can execute arbitrary code during deserialization, "
            "leading to full remote code execution. "
            "**How to fix:** Never unpickle data from untrusted sources. Use safe serialization formats "
            "like JSON, or use `hmac` signatures to verify pickle integrity before loading."
        ),
        "YAML Injection": (
            "Using `yaml.load()` without a safe Loader can execute arbitrary Python objects embedded in YAML files. "
            "**How to fix:** Always use `yaml.safe_load()` instead of `yaml.load()`, or explicitly set "
            "`Loader=yaml.SafeLoader` to prevent code execution during YAML parsing."
        ),
        "SQL Injection": (
            "The code constructs SQL queries by directly embedding user input into the query string using "
            "f-strings, string formatting, or concatenation. An attacker can manipulate the input to alter "
            "the SQL logic — for example, injecting `' OR '1'='1` to bypass authentication or `'; DROP TABLE users;--` "
            "to delete data. "
            "**How to fix:** Use parameterized queries (placeholders) instead of string formatting. "
            "For example, replace `cursor.execute(f\"SELECT * FROM users WHERE id = '{user_id}'\")` with "
            "`cursor.execute(\"SELECT * FROM users WHERE id = %s\", (user_id,))`. This separates data from SQL logic."
        ),
        "XSS Vulnerability": (
            "Cross-Site Scripting (XSS) occurs when user-supplied content is rendered directly into HTML "
            "without sanitization. An attacker can inject malicious JavaScript that executes in other users' "
            "browsers, stealing cookies, session tokens, or redirecting to phishing sites. "
            "**How to fix:** Always escape or sanitize user input before rendering it in HTML templates. "
            "Use `render_template()` with Jinja2 auto-escaping instead of `render_template_string()` with concatenation."
        ),
        "Hardcoded Credentials": (
            "The code contains a password or credential value written directly in the source code as a plain-text string. "
            "Anyone with access to the repository can read these credentials and use them to access your systems. "
            "**How to fix:** Move credentials to environment variables (e.g., `os.environ['DB_PASSWORD']`) "
            "or a secrets manager. Use a `.env` file locally with `python-dotenv`, and never commit secrets to version control."
        ),
        "Hardcoded API Key": (
            "An API key is embedded directly in the source code. If the code is pushed to a public repository, "
            "attackers can extract the key and abuse the associated service. "
            "**How to fix:** Store API keys in environment variables or a secure vault. "
            "Use `os.getenv('API_KEY')` to read them at runtime, and add `.env` to your `.gitignore`."
        ),
        "Hardcoded Secret": (
            "A secret value (such as a signing key, encryption key, or token) is hardcoded in the source code. "
            "**How to fix:** Use environment variables or a dedicated secrets management service to store secrets. "
            "Rotate any secrets that have already been committed to version control."
        ),
        "Insecure HTTP Connection": (
            "The code uses an `http://` URL instead of `https://`. Data sent over plain HTTP is transmitted in "
            "clear text and can be intercepted or modified by attackers through man-in-the-middle attacks. "
            "**How to fix:** Replace all `http://` URLs with `https://` to encrypt data in transit using TLS."
        ),
        "Assertion Bypass": (
            "The code uses `assert False` which can be bypassed entirely when Python is run with the `-O` "
            "(optimize) flag, as all assert statements are stripped in optimized mode. "
            "**How to fix:** Use explicit `raise` statements (e.g., `raise RuntimeError('...')`) instead of "
            "`assert` for security-critical checks that must always execute."
        ),
    }

    # ── Vulnerability cards ───────────────────────────────────────────────────
    for i, vuln in enumerate(results):
        severity = getattr(vuln, "severity", "LOW").upper()
        sev_icon = "🚨" if severity == "HIGH" else "⚠️" if severity == "MEDIUM" else "ℹ️"
        expander_title = (
            f"{sev_icon} [{severity}] {vuln.vulnerability_type}  "
            f"— {os.path.basename(vuln.file_path)}  (Line {vuln.line_number})"
        )

        with st.expander(expander_title, expanded=(i == 0)):
            st.markdown(
                f"**File:** `{vuln.file_path}` "
                f"<span class='line-badge'>Line {vuln.line_number}</span>",
                unsafe_allow_html=True,
            )

            explanation = VULNERABILITY_EXPLANATIONS.get(vuln.vulnerability_type)
            if explanation:
                st.info(f"📖 **What is this error?** {explanation}")

            vuln_col, fix_col = st.columns(2)

            with vuln_col:
                st.markdown("##### 🐞 Vulnerable Code")
                lang = _get_lang(vuln.file_path)
                st.code(vuln.code_snippet, language=lang)

            with fix_col:
                st.markdown("##### ✨ Remediation")

                # Build a cache key so we don't re-run the LLM on every Streamlit rerender
                cache_key = (vuln.vulnerability_type, vuln.code_snippet, selected_model)

                if cache_key not in st.session_state.fixes:
                    # Show button to trigger generation (avoids running ALL fixes at once)
                    if st.button(f"⚡ Generate Secure Fix", key=f"gen_{i}"):
                        with st.spinner(f"Generating fix using `{selected_model}`..."):
                            result = generate_fix(
                                vuln.vulnerability_type,
                                vuln.code_snippet,
                                model_name=selected_model,
                            )
                            st.session_state.fixes[cache_key] = result
                        st.rerun()
                    else:
                        st.caption("Click the button above to generate an AI-powered fix.")
                else:
                    suggestion = st.session_state.fixes[cache_key]

                    if suggestion is None:
                        st.error("Failed to generate fix. Please try again.")
                    elif isinstance(suggestion, dict):
                        if "error" in suggestion:
                            st.error(suggestion["error"])
                        else:
                            # Rationale
                            st.markdown(f"**Rationale:** {suggestion.get('rationale', '')}")

                            # Confidence bar
                            conf = suggestion.get("confidence", 0)
                            bar_color = (
                                "#00c853" if conf >= 80
                                else "#ffd600" if conf >= 50
                                else "#d50000"
                            )
                            st.markdown(
                                f"**Confidence Score:** `{conf}/100`"
                                f"<div class='conf-bar-wrap'>"
                                f"<div class='conf-bar-fill' style='width:{conf}%; background: "
                                f"linear-gradient(90deg, {bar_color}, #7000FF);'></div></div>",
                                unsafe_allow_html=True,
                            )

                            # Diff viewer
                            st.markdown("##### 🔍 Code Diff Viewer")
                            fixed_code = suggestion.get("fixed_code", vuln.code_snippet)
                            diff_html = difflib.HtmlDiff().make_table(
                                vuln.code_snippet.splitlines(),
                                fixed_code.splitlines(),
                                fromdesc="Vulnerable Code",
                                todesc="Secure Fix",
                            )
                            diff_html_styled = f"""<style>
                                body {{margin: 0;}}
                                table {{width: 100%; font-size: 13px; font-family: monospace; border-collapse: collapse;}}
                                td, th {{padding: 4px; border: 1px solid #ddd;}}
                                .diff_header {{background-color: #f0f0f0; min-width: 20px;}}
                                .diff_next {{display: none;}}
                                .diff_add {{background-color: #d4edda;}}
                                .diff_sub {{background-color: #f8d7da;}}
                            </style>{diff_html}"""
                            st.components.v1.html(diff_html_styled, scrolling=True, height=250)

                            # Download patch
                            patch_lang = _get_lang(vuln.file_path)
                            patch_content = (
                                f"# Fix for {vuln.vulnerability_type}\n\n"
                                f"**Rationale:** {suggestion.get('rationale', '')}\n\n"
                                f"**Secure Code:**\n```{patch_lang}\n{fixed_code}\n```"
                            )
                            st.download_button(
                                label="💾 Download Fix Patch",
                                data=patch_content,
                                file_name=f"fix_for_{os.path.basename(vuln.file_path)}.md",
                                mime="text/markdown",
                                key=f"dl_patch_{i}",
                                use_container_width=True,
                            )
                    else:
                        st.success(str(suggestion), icon="💡")