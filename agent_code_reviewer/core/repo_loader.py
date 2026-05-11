import os
from typing import List
from pathlib import Path


class RepoLoader:
    def __init__(self):
        self.repo_path = None
        self.temp_dir = "./temp_repos"

    def clone_repo(self, repo_url: str, branch: str = None) -> str:
        try:
            import git
        except ImportError:
            raise RuntimeError(
                "GitPython failed to initialize. Make sure 'git' is installed "
                "and available on your system PATH.\n"
                "Download git from: https://git-scm.com/downloads"
            )

        os.makedirs(self.temp_dir, exist_ok=True)
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        path = os.path.join(self.temp_dir, repo_name)

        if os.path.exists(path):
            try:
                repo = git.Repo(path)
                repo.remotes.origin.pull()
            except Exception:
                pass  # Use existing local copy if pull fails (e.g. offline)
        else:
            repo = git.Repo.clone_from(repo_url, path)

        if branch:
            repo.git.checkout(branch)

        self.repo_path = path
        return path
    
    def get_source_files(self, valid_exts: List[str]) -> List[str]:
        if not self.repo_path:
            return []
        
        files = []
        for root, _, filenames in os.walk(self.repo_path):
            for filename in filenames:
                if any(filename.endswith(ext) for ext in valid_exts):
                    files.append(os.path.join(root, filename))
        
        # Filter out common non-source directories
        excluded_dirs = ['node_modules', '__pycache__', '.git', 'venv', 'env', '.venv']
        filtered_files = [
            f for f in files 
            if not any(excluded in f for excluded in excluded_dirs)
        ]
        
        return filtered_files

    def detect_extensions(self) -> List[str]:
        """Auto-detect which supported file extensions exist in the repo."""
        if not self.repo_path:
            return []
        
        SUPPORTED_EXTS = {".py", ".js", ".java", ".ts", ".go", ".c", ".cpp", ".php", ".rb"}
        excluded_dirs = {'node_modules', '__pycache__', '.git', 'venv', 'env', '.venv'}
        found_exts = set()
        
        for root, dirs, filenames in os.walk(self.repo_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            for filename in filenames:
                ext = os.path.splitext(filename)[1]
                if ext in SUPPORTED_EXTS:
                    found_exts.add(ext)
        
        return sorted(found_exts)
