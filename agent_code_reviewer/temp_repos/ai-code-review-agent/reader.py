import os

def get_code_files(path):
    code_files = []

    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith((".py", ".js", ".java")):
                full_path = os.path.join(root, file)
                code_files.append(full_path)

    return code_files