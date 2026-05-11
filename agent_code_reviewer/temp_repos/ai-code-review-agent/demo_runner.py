import json
from src.engine import StaticAnalysisEngine

if __name__ == '__main__':
    engine = StaticAnalysisEngine()
    result = engine.analyze_repo('samples')
    print(json.dumps(result, indent=2))
