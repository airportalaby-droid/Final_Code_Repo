from git import Repo
import os
import shutil

def clone_repo(url, folder="repo"):
    # old folder remove pannum
    if os.path.exists(folder):
        shutil.rmtree(folder)

    Repo.clone_from(url, folder)
    print("✅ Repo cloned successfully")