import argparse
from datetime import datetime, timedelta
import requests
import base64

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
            else:
                print(
                    f"Failed to fetch commit info for branch {branch_name}: {commit_response.text}"
                )

        print("Old branches (not updated in the last 6 months):")
        for branch_name, date in old_branches:
            print(f"Branch: {branch_name}, Last Commit Date: {date}")
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


def list_large_files():
    print(
        "Review large files in your repository using tools like git-filter-repo or BFG Repo-Cleaner manually."
    )


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

    args = parser.parse_args()

    # Set up GitHub API URL and headers
    base_url = f"https://api.github.com/repos/{args.owner}/{args.repo}"
    headers = {
        "Authorization": f"token {args.token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Example usage of each function
    get_old_branches(base_url, headers)
    # Uncomment to delete an old branch (replace 'old_branch_name' with actual branch name)
    # delete_branch(base_url, headers, "old_branch_name")

    # Uncomment to archive the repository
    # archive_repository(base_url, headers)

    # List large files (manual)
    list_large_files()

    # Delete a specific file (uncomment and replace with file path)
    # delete_file(base_url, headers, "path/to/obsolete/file.txt")

    # Update .gitignore
    update_gitignore(base_url, headers)


if __name__ == "__main__":
    main()
