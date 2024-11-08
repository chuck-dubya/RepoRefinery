# RepoCleaner

RepoCleaner is a Python tool designed to help manage and clean up GitHub repositories. It automates tasks such as removing stale branches, cleaning up duplicate files, identifying large files, and optimizing `.gitignore` files. This project includes modules for interacting with the GitHub API and utilities for managing files within the repository.

## Features

- **Branch Cleanup**: Identify and delete branches that haven't been updated in the last 6 months.
- **Duplicate File Detection**: Find and optionally remove duplicate files in the repository.
- **Large File Detection**: Identify files exceeding a specified size threshold.
- **Gitignore Optimization**: Automatically add common, recommended entries to the `.gitignore` file.

## Requirements

- Python 3.7 or higher
- `requests` library for making API requests to GitHub.

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/repo-cleaner.git
    cd repo-cleaner
    ```

2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Set up your GitHub API token as an environment variable:

    ```bash
    export GITHUB_TOKEN='your_github_token'
    ```

## Project Structure

```
repo-cleaner/
├── repo_cleaner.py        # Main script for running cleanup tasks
├── github_api.py          # Contains functions for interacting with the GitHub API
├── file_utils.py          # File management utilities (e.g., duplicate detection, .gitignore optimization)
├── README.md              # Project documentation
├── .gitignore             # Exclusions for version control
└── requirements.txt       # Python dependencies
```

## Usage

Run `repo_cleaner.py` with the necessary arguments to clean up a specified GitHub repository.

### Basic Commands

- **Removing stale branches**:

    ```bash
    python repo_cleaner.py <github_token> <owner> <repo> --delete_stale_branches
    ```

- **Finding and removing duplicate files**:

    ```bash
    python repo_cleaner.py <github_token> <owner> <repo> --delete_duplicates
    ```

- **Identifying large files** (default threshold is 5MB):

    ```bash
    python repo_cleaner.py <github_token> <owner> <repo> --size_threshold 5
    ```

- **Optimizing the `.gitignore` file**:

    ```bash
    python repo_cleaner.py <github_token> <owner> <repo> --optimize_gitignore
    ```

### Arguments

- `--repo_path`: Path to the local clone of the repository.
- `--delete_duplicates`: Delete duplicate files found in the repository.
- `--size_threshold`: Size in MB to identify large files (default is 5).
- `--log_level`: Set logging level (e.g., `INFO`, `DEBUG`).

### Example

```bash
python repo_cleaner.py ghp_yourGithubToken username my-repo --repo_path "./my-local-repo" --delete_duplicates --size_threshold 10 --log_level DEBUG
```

## Modules

- **repo_cleaner.py**: The main script to execute cleanup tasks.
- **github_api.py**: Contains functions to interact with GitHub's REST API for branch management, tag deletion, and commit data retrieval.
- **file_utils.py**: Utility functions to detect large files, identify duplicates, and manage `.gitignore` entries.

## Contributing

Contributions are welcome! If you would like to add new features, fix bugs, or improve documentation, please feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Acknowledgements

This project was inspired by the need for efficient repository maintenance and cleanup automation.
