import argparse
import logging
import os
from datetime import datetime, timedelta
from utils.github_api import (
    get_old_branches,
    get_tags,
    delete_tag,
)
from utils.file_utils import (
    list_large_files,
    optimize_gitignore,
    remove_duplicate_files,
)


def get_github_token(token_arg):
    """Retrieves the GitHub token from argument or environment variable and logs a warning if not available."""
    token = token_arg or os.getenv("GITHUB_TOKEN")
    if not token:
        logging.warning(
            "GitHub token not provided. Please provide it as an argument or set it as an environment variable."
        )
    return token


def main():
    parser = argparse.ArgumentParser(description="GitHub repository cleanup tool.")
    parser.add_argument("token", help="Your GitHub personal access token.")
    parser.add_argument(
        "owner", help="The GitHub repository owner (username or organization)."
    )
    parser.add_argument("repo", help="The GitHub repository name.")
    parser.add_argument(
        "--repo_path", help="Path to the local clone of the repository", default="."
    )
    parser.add_argument(
        "--delete_duplicates", action="store_true", help="Delete duplicate files"
    )
    parser.add_argument(
        "--size_threshold", type=int, default=5, help="File size threshold in MB"
    )
    parser.add_argument(
        "--log_level",
        type=str,
        default="INFO",
        help="Set the logging level (e.g., DEBUG, INFO)",
    )

    args = parser.parse_args()

    # Set up logging level based on the log_level argument
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Set up GitHub API headers and URL
    token = get_github_token(args.token)
    base_url = f"https://api.github.com/repos/{args.owner}/{args.repo}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Task 1: Find and delete old branches
    logging.info("Finding and deleting old branches...")
    cutoff_date = datetime.now() - timedelta(days=180)
    get_old_branches(base_url, headers, cutoff_date)

    # Task 2: Close stale pull requests
    logging.info("Checking for stale pull requests...")
    # Logic to retrieve and close stale PRs would go here (similar to old branches logic)

    # Task 3: Delete unused tags
    logging.info("Deleting unused tags...")
    tags = get_tags(base_url, headers)
    for tag in tags:
        tag_name = tag["name"]
        tag_date = datetime.strptime(
            tag["commit"]["commit"]["committer"]["date"], "%Y-%m-%dT%H:%M:%SZ"
        )
        if tag_date < cutoff_date:
            delete_tag(base_url, headers, tag_name)

    # Task 4: List large files
    large_files = list_large_files(
        args.repo_path, size_threshold_mb=args.size_threshold
    )
    if large_files:
        logging.info("Large files found in the repository:")
        for file, size in large_files:
            logging.info(f"{file}: {size}")
    else:
        logging.info("No large files found above the threshold.")

    # Task 5: Remove duplicate files
    remove_duplicate_files(args.repo_path, delete_duplicates=args.delete_duplicates)

    # Use it in your cleanup tasks
    optimize_gitignore(args.repo_path)

    # Final summary log
    logging.info("Repository cleanup completed.")


if __name__ == "__main__":
    main()
