from typing import Dict, Any
from .engine import StaticAnalysisEngine
from .llm import suggest_fix_with_llm


class ReviewOrchestrator:
    def __init__(self, workdir: str = None):
        self.engine = StaticAnalysisEngine(workdir)

    def run_review(self, repo: str) -> Dict[str, Any]:
        result = self.engine.analyze_repo(repo)
        findings = result.get('findings', [])
        # Build a simple human-readable summary
        summary_lines = []
        for f in findings:
            summary_lines.append(f"{f['type']} in {f['file']}:{f['line']} - {f['message']}")
        summary = '\n'.join(summary_lines)

        # Optionally ask LLM to create an executive summary
        exec_summary = suggest_fix_with_llm({'type': 'Summary', 'message': 'Provide a short executive summary of findings', 'snippet': summary}, summary)

        return {
            'repo': repo,
            'count': len(findings),
            'findings': findings,
            'executive_summary': exec_summary,
        }


if __name__ == '__main__':
    orch = ReviewOrchestrator()
    out = orch.run_review('samples')
    import json
    print(json.dumps(out, indent=2))
