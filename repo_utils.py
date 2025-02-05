import git
import os
import re
import uuid
import json
import shutil
import chardet
import stat
import time
import concurrent.futures
from typing import Dict

def delete_directory(repo_clone_path: str) -> None:
    """Safely delete a directory with retries and permission handling"""
    if not os.path.exists(repo_clone_path):
        return

    # Handle Windows file locking
    def on_error(func, path, exc_info):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    for _ in range(3):  # Retry up to 3 times
        try:
            shutil.rmtree(repo_clone_path, onerror=on_error)
            print(f"Successfully deleted: {repo_clone_path}")
            return
        except Exception as e:
            print(f"Error deleting directory: {str(e)}")
            time.sleep(0.5)
    
    raise RuntimeError(f"Failed to delete directory after 3 attempts: {repo_clone_path}")

def get_reponame(repo_url: str) -> str:
    """Extract repository name and branch from URL"""
    repo_url = repo_url.rstrip('/')
    parts = repo_url.split('/')
    username = parts[3]
    reponame = parts[4]

    if len(parts) > 5 and parts[5] == 'tree':
        branchname = parts[6]
        return f"{username}+{reponame}+{branchname}"
    return f"{username}+{reponame}"

def clone_github_repo(repo_url: str, clone_path: str) -> None:
    """Clone a GitHub repository with branch support"""
    try:
        repo_url = repo_url.rstrip('/')
        pattern = re.compile(r'^https://github\.com/([^/]+)/([^/]+)(/tree/([^/]+))?$')
        match = pattern.match(repo_url)

        if not match:
            raise ValueError("Invalid GitHub URL format")

        username, reponame, _, branchname = match.groups()
        base_repo_url = f"https://github.com/{username}/{reponame}.git"

        if not os.path.exists(clone_path):
            os.makedirs(clone_path)

        if branchname:
            git.Repo.clone_from(base_repo_url, clone_path, branch=branchname)
        else:
            git.Repo.clone_from(base_repo_url, clone_path)

        print(f"Successfully cloned to {clone_path}")
    except Exception as e:
        raise RuntimeError(f"Cloning failed: {str(e)}")

def is_valid_repolink(repolink: str) -> bool:
    """Validate GitHub repository URL format"""
    pattern = re.compile(
        r'^https://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(/tree/[a-zA-Z0-9_.-]+)?/?$'
    )
    return bool(pattern.match(repolink))

def process_file(file_path: str, clone_path: str) -> tuple:
    """Process individual files with encoding detection"""
    relative_path = os.path.relpath(file_path, clone_path)
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            
            if not raw_data:
                return (relative_path, "")

            if file_path.endswith('.ipynb'):
                try:
                    content = json.loads(raw_data)
                    cell_sources = [
                        ''.join(cell.get('source', ''))
                        for cell in content.get('cells', [])
                        if cell.get('cell_type') in ('markdown', 'code')
                    ]
                    return (relative_path, '\n'.join(cell_sources))
                except json.JSONDecodeError:
                    return (relative_path, "Invalid notebook format")

            # Detect encoding for text files
            encoding = chardet.detect(raw_data)['encoding']
            if encoding:
                return (relative_path, raw_data.decode(encoding))
            
            return (relative_path, "Binary file (not shown)")

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return (relative_path, f"File processing error: {str(e)}")

def create_file_content_dict(clone_path: str) -> Dict[str, str]:
    """Create a dictionary of file contents using parallel processing"""
    file_content_dict = {}
    files_to_process = []

    for root, _, files in os.walk(clone_path):
        if '/.git' in root:
            continue
        for file in files:
            file_path = os.path.join(root, file)
            files_to_process.append(file_path)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(process_file, fp, clone_path): fp 
            for fp in files_to_process
        }
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                path, content = result
                file_content_dict[path] = content

    return file_content_dict

def get_default_branch_code(repo_url: str) -> Dict[str, str]:
    """Clone and process default branch for comparison"""
    base_url = repo_url.split('/tree/')[0]
    unique_id = uuid.uuid4().hex
    clone_path = f"./repo/default_branch_{unique_id}"
    
    try:
        print(f"Cloning default branch to {clone_path}")
        clone_github_repo(base_url, clone_path)
        return create_file_content_dict(clone_path)
    except Exception as e:
        raise RuntimeError(f"Default branch clone failed: {str(e)}")
    finally:
        delete_directory(clone_path)