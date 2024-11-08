import argparse
from datetime import datetime, timedelta
import requests
import base64
import subprocess

# Define the cutoff date for old branches (e.g., branches with no commits in the last 6 months)
OLD_BRANCH_CUTOFF_DAYS = 180
cutoff_date = datetime.now() - timedelta(days=OLD_BRANCH_CUTOFF_DAYS)


def get_old_branches(base_url, headers):
    url = f"{base_url}/branches"
    response = requests.get(url, headers=headers)
    old_branches = []

    if response.status_code == 200:
        branches = response.json()
        for branch in branches:
            branch_name = branch["name"]
            # Get the last commit date of the branch
            commit_url = branch["commit"]["url"]
            commit_response = requests.get(commit_url, headers=headers)

            if commit_response.status_code == 200:
                commit_data = commit_response.json()
                commit_date = datetime.strptime(
                    commit_data["commit"]["committer"]["date"], "%Y-%m-%dT%H:%M:%SZ"
                )

                # Check if the last commit date is older than the cutoff date
                if commit_date < cutoff_date:
                    old_branches.append((branch_name, commit_date.strftime("%Y-%m-%d")))
                    # Call delete_branch to delete the old branch
                    delete_branch(base_url, headers, branch_name)
            else:
                print(
                    f"Failed to fetch commit info for branch {branch_name}: {commit_response.text}"
                )

        if old_branches:
            print("Deleted old branches (not updated in the last 6 months):")
            for branch_name, date in old_branches:
                print(f"Branch: {branch_name}, Last Commit Date: {date}")
        else:
            print("No old branches found to delete.")
    else:
        print(f"Failed to fetch branches: {response.text}")


def delete_branch(base_url, headers, branch_name):
    url = f"{base_url}/git/refs/heads/{branch_name}"
    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        print(f"Deleted branch: {branch_name}")
    else:
        print(f"Failed to delete branch {branch_name}: {response.text}")


def archive_repository(base_url, headers):
    url = base_url
    response = requests.patch(url, headers=headers, json={"archived": True})
    if response.status_code == 200:
        print("Repository archived successfully.")
    else:
        print(f"Failed to archive repository: {response.text}")


def list_large_files(repo_path, file_size_threshold=5):
    """
    Lists large files in the repository history. Requires a local clone.
    Args:
        repo_path (str): Path to the local clone of the repository.
        file_size_threshold (int): Minimum file size (in MB) to be listed.
    """
    print(f"Finding files larger than {file_size_threshold} MB in the repository...")

    try:
        # Run git rev-list and git cat-file to find large files
        result = subprocess.run(
            [
                "git",
                "-C",
                repo_path,
                "rev-list",
                "--objects",
                "--all",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        # Get the list of all objects (files) and sizes
        large_files = []
        for line in result.stdout.splitlines():
            object_hash, filename = line.split(maxsplit=1)
            size_result = subprocess.run(
                ["git", "-C", repo_path, "cat-file", "-s", object_hash],
                capture_output=True,
                text=True,
                check=True,
            )

            # Convert size to MB and check against threshold
            size_in_mb = int(size_result.stdout.strip()) / (1024 * 1024)
            if size_in_mb > file_size_threshold:
                large_files.append((filename, f"{size_in_mb:.2f} MB"))

        # Print results
        if large_files:
            print("Large files in the repository:")
            for filename, size in large_files:
                print(f"{filename}: {size}")
        else:
            print("No large files found above the threshold.")

    except subprocess.CalledProcessError as e:
        print(f"Error while finding large files: {e}")


def delete_file(base_url, headers, file_path, branch="main"):
    url = f"{base_url}/contents/{file_path}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        sha = response.json()["sha"]
        delete_response = requests.delete(
            url,
            headers=headers,
            json={
                "message": f"Removing obsolete file {file_path}",
                "sha": sha,
                "branch": branch,
            },
        )
        if delete_response.status_code == 200:
            print(f"Deleted file: {file_path}")
        else:
            print(f"Failed to delete file {file_path}: {delete_response.text}")
    else:
        print(f"File {file_path} not found.")


def update_gitignore(base_url, headers):
    gitignore_content = """
    # Ignore Python bytecode
    __pycache__/
    *.py[cod]

    # Ignore OS files
    .DS_Store
    Thumbs.db

    # Ignore IDE configs
    .idea/
    .vscode/
    *.swp
    """
    encoded_content = base64.b64encode(gitignore_content.encode()).decode("utf-8")
    url = f"{base_url}/contents/.gitignore"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        sha = response.json()["sha"]
        response = requests.put(
            url,
            headers=headers,
            json={
                "message": "Updating .gitignore",
                "content": encoded_content,
                "sha": sha,
            },
        )
    else:
        response = requests.put(
            url,
            headers=headers,
            json={
                "message": "Creating .gitignore",
                "content": encoded_content,
            },
        )
    if response.status_code in (200, 201):
        print(".gitignore updated successfully.")
    else:
        print(f"Failed to update .gitignore: {response.text}")


def main():
    # Argument parsing
    parser = argparse.ArgumentParser(description="GitHub repository cleanup tool.")
    parser.add_argument("token", help="Your GitHub personal access token.")
    parser.add_argument(
        "owner", help="The GitHub repository owner (username or organization)."
    )
    parser.add_argument("repo", help="The GitHub repository name.")
    parser.add_argument(
        "--repo_path", help="Path to the local clone of the repository", default="."
    )

    args = parser.parse_args()

    # Set up GitHub API URL and headers
    base_url = f"https://api.github.com/repos/{args.owner}/{args.repo}"
    headers = {
        "Authorization": f"token {args.token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Identify and delete old branches
    get_old_branches(base_url, headers)

    # List large files (requires local clone of the repository)
    list_large_files(args.repo_path)

    # Update .gitignore
    update_gitignore(base_url, headers)


if __name__ == "__main__":
    main()
