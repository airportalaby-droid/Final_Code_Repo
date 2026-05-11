from dataclasses import dataclass
from typing import Optional

@dataclass
class RepoVulnerability:
    file_path: str
    line_number: int
    code_snippet: str
    vulnerability_type: str
    severity: str = "LOW"
    
    def to_dict(self):
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "vulnerability_type": self.vulnerability_type,
            "severity": self.severity
        }
