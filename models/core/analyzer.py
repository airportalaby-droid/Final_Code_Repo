import tree_sitter_python as tspython
from tree_sitter import Language, Parser

class ASTAnalyzer:
    def __init__(self):
        lang = Language(tspython.language())
        self.parser = Parser(lang)
        
        # We store rules as tuples: (name, severity, query_string)
        self.rules = [
            ("Dangerous Command Execution", "HIGH", lang.query("""
                (call
                    function: (identifier) @func_name
                    (#match? @func_name "^(eval|exec)$")) @dangerous_call
            """)),
            ("Unsafe OS Command", "HIGH", lang.query("""
                (call
                    function: (attribute
                        object: (identifier) @obj
                        attribute: (identifier) @attr)
                    (#match? @obj "os")
                    (#match? @attr "^(system|popen|spawn)$")) @os_call
            """)),
            ("Hardcoded Secret", "MEDIUM", lang.query("""
                (assignment
                    left: (identifier) @var_name
                    right: (string) @value)
                (#match? @var_name ".*(password|secret|key|token|api).*")
            """)),
            ("SQL Injection", "CRITICAL", lang.query("""
                (call
                    function: (attribute
                        attribute: (identifier) @method)
                    arguments: (argument_list) @args)
                (#match? @method "execute")
            """))
        ]
    
    def analyze_file(self, file_path):
        results = []
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                
            tree = self.parser.parse(content)
            source_lines = content.decode('utf-8', errors='ignore').split('\n')
            
            for rule_name, severity, query in self.rules:
                for match in query.matches(tree.root_node):
                    for node in match[1]:
                        line_idx = node.start_point[0]
                        code_line = source_lines[line_idx].strip() if line_idx < len(source_lines) else ""
                        
                        results.append({
                            "file_path": file_path,
                            "line_number": line_idx + 1,
                            "code_snippet": code_line,
                            "vulnerability_type": rule_name,
                            "severity": severity
                        })
                        
        except Exception as e:
            # Silently catch for now so one bad file doesn't crash the scanner
            pass
            
        return results
