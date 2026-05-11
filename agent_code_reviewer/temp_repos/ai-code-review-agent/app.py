import streamlit as st
from src.engine import StaticAnalysisEngine

st.set_page_config(page_title='Static Analysis AI Agent')
st.title('Static Analysis Engine — Vulnerability Detection')

repo_input = st.text_input('Repository URL or local path', '')
ollama_url = st.text_input('Ollama URL (optional, e.g., http://127.0.0.1:11434)', '')

if ollama_url:
    import os
    os.environ['OLLAMA_URL'] = ollama_url

if st.button('Run Analysis'):
    if not repo_input:
        st.error('Provide a repository URL or local path.')
    else:
        st.info('Starting analysis — this may take a moment.')
        engine = StaticAnalysisEngine()
        try:
            result = engine.analyze_repo(repo_input)
        except Exception as e:
            st.error(f'Analysis failed: {e}')
        else:
            findings = result.get('findings', [])
            st.success(f'Found {len(findings)} potential issues')
            for idx, f in enumerate(findings, 1):
                with st.expander(f"{idx}. {f['type']} — {f['file']}:{f['line']}"):
                    st.write('**Message:**', f['message'])
                    st.write('**Snippet:**', f.get('snippet',''))
                    st.write('**Confidence:**', f.get('confidence'))
                    llm = f.get('llm_suggestion', {})
                    st.write('**Suggestion:**', llm.get('text', f.get('suggestion')))
                    st.write('**Suggestion confidence:**', llm.get('confidence'))
            st.download_button('Download JSON', data=str(result), file_name='findings.json')
