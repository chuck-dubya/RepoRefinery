import requests
import logging
from datetime import datetime

# Initialize logging
logging.basicConfig(level=logging.INFO)


def api_request(url, headers, method="get", json_data=None):
    """
    Sends an API request with error handling and returns the response object.

    Args:
        url (str): The API endpoint URL.
        headers (dict): The headers for authentication and content type.
        method (str): HTTP method, e.g., "get", "post", "delete", etc.
        json_data (dict, optional): JSON data to send with the request.

    Returns:
        Response: The Response object if successful, otherwise None.
    """
    try:
        response = requests.request(method, url, headers=headers, json=json_data)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logging.error(f"API request error for {method.upper()} {url}: {e}")
        return None


def get_branches(base_url, headers):
    """Fetches all branches from the repository."""
    url = f"{base_url}/branches"
    response = api_request(url, headers)
    try:
        return response.json() if response else []
    except ValueError as e:
        logging.error(f"Failed to parse branch data: {e}")
        return []


def delete_branch(base_url, headers, branch_name):
    """Deletes a specified branch."""
    url = f"{base_url}/git/refs/heads/{branch_name}"
    response = api_request(url, headers, method="delete")
    if response and response.status_code == 204:
        logging.info(f"Deleted branch: {branch_name}")
    else:
        logging.warning(f"Failed to delete branch: {branch_name}")


def close_pull_request(base_url, headers, pr_number):
    """Closes a pull request with the specified pull request number."""
    url = f"{base_url}/pulls/{pr_number}"
    response = api_request(url, headers, method="patch", json_data={"state": "closed"})
    if response and response.status_code == 200:
        logging.info(f"Closed pull request #{pr_number}")
    else:
        logging.warning(f"Failed to close pull request #{pr_number}")


def get_tags(base_url, headers):
    """Fetches all tags from the repository."""
    url = f"{base_url}/tags"
    response = api_request(url, headers)
    try:
        return response.json() if response else []
    except ValueError as e:
        logging.error(f"Failed to parse tag data: {e}")
        return []


def delete_tag(base_url, headers, tag_name):
    """Deletes a specified tag."""
    url = f"{base_url}/git/refs/tags/{tag_name}"
    response = api_request(url, headers, method="delete")
    if response and response.status_code == 204:
        logging.info(f"Deleted tag: {tag_name}")
    else:
        logging.warning(f"Failed to delete tag: {tag_name}")


def fetch_commit_date_from_url(url, headers):
    """
    Fetches the commit date from a specific commit URL.

    Args:
        url (str): The commit URL to fetch the date from.
        headers (dict): Authorization headers for API access.

    Returns:
        datetime: The commit date if available, else None.
    """
    response = api_request(url, headers)
    if response:
        try:
            commit_date_str = (
                response.json().get("commit", {}).get("committer", {}).get("date")
            )
            if commit_date_str:
                return datetime.strptime(commit_date_str, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError as e:
            logging.error(f"Failed to parse commit date: {e}")
    logging.warning(f"Could not retrieve commit date for URL: {url}")
    return None


def get_old_branches(base_url, headers, cutoff_date):
    """
    Identifies branches with no recent commits (older than cutoff date) and deletes them.

    Args:
        base_url (str): The base API URL for the repository.
        headers (dict): Authorization headers for API access.
        cutoff_date (datetime): Date to determine branch staleness.

    Logs:
        Information about each branch deleted or skipped due to recency.
    """
    branches = get_branches(base_url, headers)
    old_branches = []

    for branch in branches:
        branch_name = branch.get("name")
        commit_url = branch.get("commit", {}).get("url")

        if commit_url:
            commit_date = fetch_commit_date_from_url(commit_url, headers)
            if commit_date and commit_date < cutoff_date:
                delete_branch(base_url, headers, branch_name)
                old_branches.append(branch_name)
            else:
                logging.info(
                    f"Branch '{branch_name}' is recent (last commit date: {commit_date})"
                )
        else:
            logging.warning(f"Skipping branch '{branch_name}' - no commit URL found.")

    if old_branches:
        logging.info(f"Deleted old branches: {', '.join(old_branches)}")
    else:
        logging.info("No old branches found.")
