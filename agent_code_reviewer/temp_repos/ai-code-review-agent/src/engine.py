import os
from typing import List, Dict
from pathlib import Path
from .parser import parse_file
from .detectors import run_detectors
from .llm import suggest_fix_with_llm

try:
    from git import Repo, GitCommandError
    GITPYTHON_AVAILABLE = True
except Exception:
    Repo = None
    GitCommandError = Exception
    GITPYTHON_AVAILABLE = False


class StaticAnalysisEngine:
    def __init__(self, workdir: str = None):
        self.workdir = workdir or os.getcwd()

    def _clone_repo(self, repo_url: str, target: str) -> str:
        if not GITPYTHON_AVAILABLE:
            raise RuntimeError('gitpython not installed; cannot clone remote repositories. Install gitpython or provide a local path.')
        try:
            Repo.clone_from(repo_url, target)
            return target
        except GitCommandError as e:
            raise RuntimeError(f"Git clone failed: {e}")

    def analyze_repo(self, repo: str) -> Dict[str, List[Dict]]:
        # repo can be a local path or a remote URL
        target = repo
        tmp = False
        if repo.startswith('http://') or repo.startswith('https://') or repo.endswith('.git'):
            target = os.path.join(self.workdir, 'tmp_repo')
            if os.path.exists(target):
                # simple cleanup
                import shutil
                shutil.rmtree(target)
            self._clone_repo(repo, target)
            tmp = True

        findings = []
        for root, _, files in os.walk(target):
            for f in files:
                if f.endswith(('.py', '.js', '.jsx', '.ts', '.html', '.php')):
                    path = os.path.join(root, f)
                    try:
                        with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
                            src = fh.read()
                    except Exception:
                        continue
                    parsed = parse_file(path, src)
                    issues = run_detectors(path, parsed)
                    for issue in issues:
                        # ask LLM for suggestion
                        suggestion = suggest_fix_with_llm(issue, src)
                        issue['llm_suggestion'] = suggestion
                    findings.extend(issues)

        if tmp:
            import shutil
            shutil.rmtree(target)

        return {"repo": repo, "findings": findings}


if __name__ == '__main__':
    import sys
    repo = sys.argv[1] if len(sys.argv) > 1 else '.'
    engine = StaticAnalysisEngine()
    out = engine.analyze_repo(repo)
    import json
    print(json.dumps(out, indent=2))
