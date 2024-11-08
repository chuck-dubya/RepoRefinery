import os
import hashlib
import logging
import subprocess


def list_large_files(repo_path, size_threshold_mb=5):
    """
    Lists large files in the repository history based on a specified size threshold.

    Args:
        repo_path (str): Path to the repository.
        size_threshold_mb (int): File size threshold in MB.

    Returns:
        list of tuples: [(filename, size)], where size is formatted as "X.XX MB" for files exceeding the threshold.
    """
    logging.info(f"Scanning for files larger than {size_threshold_mb} MB...")
    large_files = []
    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "rev-list", "--objects", "--all"],
            capture_output=True,
            text=True,
            check=True,
        )
        for line in result.stdout.splitlines():
            parts = line.split(maxsplit=1)
            if len(parts) < 2:
                continue
            object_hash, filename = parts
            size_result = subprocess.run(
                ["git", "-C", repo_path, "cat-file", "-s", object_hash],
                capture_output=True,
                text=True,
                check=True,
            )
            size_mb = int(size_result.stdout.strip()) / (1024 * 1024)
            if size_mb > size_threshold_mb:
                large_files.append((filename, f"{size_mb:.2f} MB"))
    except subprocess.CalledProcessError as e:
        logging.error(f"Error retrieving large files in repository: {e}")
    return large_files


def remove_duplicate_files(repo_path, delete_duplicates=True):
    """
    Identifies duplicate files in the specified directory, optionally deleting them.

    Args:
        repo_path (str): Path to the directory to scan.
        delete_duplicates (bool): If True, delete duplicate files found.

    Returns:
        list of str: Paths of duplicate files identified.
    """
    logging.info("Scanning for duplicate files...")
    file_hashes = {}
    duplicates = []
    error_files = []

    for root, _, files in os.walk(repo_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            try:
                file_hash = hash_file(file_path)
                if file_hash in file_hashes:
                    duplicates.append(file_path)
                    if delete_duplicates:
                        os.remove(file_path)
                        logging.info(f"Deleted duplicate file: {file_path}")
                    else:
                        logging.info(
                            f"Found duplicate: {file_path} (same as {file_hashes[file_hash]})"
                        )
                else:
                    file_hashes[file_hash] = file_path
            except IOError as e:
                logging.warning(f"Could not read file {file_path}: {e}")
                error_files.append(file_path)

    if duplicates and not delete_duplicates:
        logging.info("Duplicate files found but not removed.")
    elif not duplicates:
        logging.info("No duplicate files found.")

    if error_files:
        logging.warning(f"Some files could not be processed: {', '.join(error_files)}")

    return duplicates


def hash_file(file_path):
    """
    Generates an MD5 hash for a file to identify duplicates.

    Args:
        file_path (str): Path to the file to hash.

    Returns:
        str: MD5 hash of the file content, or None if the file cannot be opened.
    """
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except IOError as e:
        logging.error(f"Error hashing file {file_path}: {e}")
        return None


def optimize_gitignore(repo_path):
    """
    Optimizes the .gitignore file by adding patterns for common temporary files, OS-specific files, and IDE files.

    Args:
        repo_path (str): Path to the local repository.
    """
    gitignore_path = os.path.join(repo_path, ".gitignore")

    # Patterns for common temporary files, OS-specific files, and IDE files
    common_patterns = [
        # OS-specific
        "*.DS_Store",  # macOS Finder files
        "Thumbs.db",  # Windows Explorer thumbnail cache
        # IDE-specific
        ".vscode/",  # VSCode
        ".idea/",  # IntelliJ/Android Studio
        "*.iml",  # IntelliJ module files
        "*.suo",  # Visual Studio Solution User Options
        "*.user",  # Visual Studio User file
        "*.sln.docstates",  # Visual Studio solution explorer states
        # Python
        "*.pyc",
        "*.pyo",
        "__pycache__/",
        "*.pyd",
        "*.pdb",
        "*.egg-info/",
        # Node.js
        "node_modules/",
        "npm-debug.log*",
        "yarn-debug.log*",
        "yarn-error.log*",
        # Logs and temporary files
        "*.log",
        "*.tmp",
        "*.bak",
        "*.swp",
        "*.swo",
    ]

    # Read existing .gitignore entries to avoid duplicates
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            existing_patterns = set(line.strip() for line in f if line.strip())
    else:
        existing_patterns = set()

    # Add missing patterns to .gitignore
    new_patterns = [
        pattern for pattern in common_patterns if pattern not in existing_patterns
    ]
    if new_patterns:
        with open(gitignore_path, "a") as f:
            f.write("\n# Optimized entries added by optimize_gitignore\n")
            for pattern in new_patterns:
                f.write(f"{pattern}\n")
                logging.info(f"Added '{pattern}' to .gitignore")

        logging.info("Optimization complete: new entries added to .gitignore.")
    else:
        logging.info("No new entries needed. .gitignore is already optimized.")
