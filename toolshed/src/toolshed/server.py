from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INTERNAL_ERROR, INVALID_PARAMS

import subprocess
import os
import requests
from bs4 import BeautifulSoup
from html2text import html2text

mcp = FastMCP("ToolShed")


@mcp.tool()
def code_search(pattern: str, directory: str = ".") -> str:
    """
    Use ripgrep (rg) to find patterns across the codebase.

    Args:
        pattern: The regex pattern or text to search for.
        directory: The directory to search in (defaults to the current directory).

    Returns:
        The text output from ripgrep.
    """
    try:
        if not os.path.exists(directory):
            raise ValueError(f"Directory does not exist: {directory}")

        result = subprocess.run(
            ["rg", "--line-number", "--heading", pattern, directory],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            return result.stdout
        elif result.returncode == 1:
            return f"No matches found for pattern: '{pattern}' in directory: '{directory}'"
        else:
            raise McpError(
                ErrorData(
                    INTERNAL_ERROR,
                    f"ripgrep error (code {result.returncode}): {result.stderr}"
                )
            )

    except FileNotFoundError:
        # rg is not installed or not in PATH
        raise McpError(
            ErrorData(
                INTERNAL_ERROR,
                "ripgrep ('rg') is not installed or not available in PATH."
            )
        )
    except ValueError as e:
        raise McpError(ErrorData(INVALID_PARAMS, str(e))) from e
    except Exception as e:
        if isinstance(e, McpError):
            raise e
        raise McpError(ErrorData(INTERNAL_ERROR, f"Unexpected error: {str(e)}")) from e


@mcp.tool()
def github_context(owner: str, repo: str, branch: str) -> str:
    """
    Fetch recent PR descriptions and issue comments for a given branch using the GitHub API.

    Args:
        owner: The repository owner (e.g., 'block').
        repo: The repository name (e.g., 'goose').
        branch: The branch name.

    Returns:
        A formatted string with the PR title, body, and recent comments.
    """
    try:
        headers = {"Accept": "application/vnd.github.v3+json"}
        # Check if an auth token is in the environment
        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"token {github_token}"

        # 1. Fetch Pull Requests from this branch
        pulls_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
        params = {"head": f"{owner}:{branch}", "state": "all"}

        pr_response = requests.get(pulls_url, headers=headers, params=params, timeout=15)

        if pr_response.status_code == 404:
            raise ValueError(f"Repository {owner}/{repo} not found or access denied.")
        elif pr_response.status_code != 200:
            raise McpError(
                ErrorData(
                    INTERNAL_ERROR,
                    f"GitHub API error fetching PRs. HTTP status code: {pr_response.status_code}"
                )
            )

        prs = pr_response.json()
        if not prs:
            return f"No pull requests found for branch: '{branch}' in repository '{owner}/{repo}'."

        # Select the most recent PR
        pr = prs[0]
        pr_number = pr.get("number")
        pr_title = pr.get("title", "No Title")
        pr_body = pr.get("body", "No Description")

        # 2. Fetch comments for this PR
        comments_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
        comments_response = requests.get(comments_url, headers=headers, timeout=15)

        output = [
            f"Pull Request #{pr_number}: {pr_title}",
            "=" * 50,
            f"Description:\n{pr_body or 'No description provided.'}",
            "\n" + "=" * 50,
            "Comments:"
        ]

        if comments_response.status_code == 200:
            comments = comments_response.json()
            if not comments:
                output.append("No comments found.")
            else:
                for idx, comment in enumerate(comments[-5:], start=1):
                    user = comment.get("user", {}).get("login", "Unknown")
                    body = comment.get("body", "")
                    output.append(f"\n--- Comment {idx} by {user} ---\n{body}")
        else:
            output.append(f"[Warning: Failed to fetch comments. HTTP {comments_response.status_code}]")

        return "\n".join(output)

    except ValueError as e:
        raise McpError(ErrorData(INVALID_PARAMS, str(e))) from e
    except requests.exceptions.RequestException as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"GitHub Request error: {str(e)}")) from e
    except Exception as e:
        if isinstance(e, McpError):
            raise e
        raise McpError(ErrorData(INTERNAL_ERROR, f"Unexpected error: {str(e)}")) from e


@mcp.tool()
def fetch_docs(source: str) -> str:
    """
    Pull content from a local file (e.g. docs folder) or a specified URL.

    Args:
        source: A local file path or a URL starting with http:// or https://.

    Returns:
        The text content of the file or parsed markdown from the URL.
    """
    try:
        if source.startswith("http://") or source.startswith("https://"):
            # Fetch from URL
            response = requests.get(source, timeout=15)
            if response.status_code != 200:
                raise McpError(
                    ErrorData(
                        INTERNAL_ERROR,
                        f"Failed to fetch URL. HTTP status code: {response.status_code}"
                    )
                )

            # Use BeautifulSoup to get the text, converting HTML to Markdown
            # This is a basic conversion, for better results html2text is used
            soup = BeautifulSoup(response.text, "html.parser")

            # Simple heuristic: if there's an article or main tag, prefer that
            content_elem = soup.find("main") or soup.find("article") or soup.find("body") or soup

            markdown_text = html2text(str(content_elem))
            return markdown_text
        else:
            # Read from local file
            if not os.path.exists(source):
                raise ValueError(f"Local file does not exist: {source}")

            with open(source, "r", encoding="utf-8") as f:
                return f.read()

    except ValueError as e:
        raise McpError(ErrorData(INVALID_PARAMS, str(e))) from e
    except requests.exceptions.RequestException as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"Request error: {str(e)}")) from e
    except Exception as e:
        if isinstance(e, McpError):
            raise e
        raise McpError(ErrorData(INTERNAL_ERROR, f"Unexpected error: {str(e)}")) from e
