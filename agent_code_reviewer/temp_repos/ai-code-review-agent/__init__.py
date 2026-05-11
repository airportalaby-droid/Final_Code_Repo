from ingestion.clone_repo import clone_repo
from ingestion.file_filter import get_code_files
from ingestion.reader import read_files

def fetch_and_prepare(repo_url):
    clone_repo(repo_url)                 # clone
    files = get_code_files("repo")       # filter
    data = read_files(files)             # read
    return data