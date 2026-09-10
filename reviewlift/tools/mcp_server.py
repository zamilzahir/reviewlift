"""Real MCP server exposing a get_diff tool, backed by the GitHub API.
Run standalone with: python3 -m reviewlift.tools.mcp_server
Connects to Claude Code / Cursor / any MCP client via stdio.
"""

import os
import re

import requests
from mcp.server.fastmcp import FastMCP

GITHUB_API_BASE = "https://api.github.com"
PR_ID_PATTERN = re.compile(r"^([\w.-]+)/([\w.-]+)#(\d+)$")
PR_URL_PATTERN = re.compile(
    r"^https?://(?:www\.)?github\.com/([\w.-]+)/([\w.-]+)/pull/(\d+)/?"
)

mcp = FastMCP("reviewlift-github")


def _parse_pr_id(pr_id: str) -> tuple[str, str, str]:
    """Accepts either a full GitHub PR URL or the short owner/repo#number form."""
    cleaned = pr_id.strip()

    url_match = PR_URL_PATTERN.match(cleaned)
    if url_match:
        return url_match.groups()

    match = PR_ID_PATTERN.match(cleaned)
    if not match:
        raise ValueError(
            f"'{pr_id}' isn't a valid PR id. Expected format: owner/repo#number "
            f"(e.g. zamilzahir/buggy-calculator#1)"
        )
    return match.groups()


@mcp.tool()
def get_diff(pr_id: str) -> str:
    """Fetch the real unified diff for a public GitHub pull request.

    Args:
        pr_id: PR identifier in 'owner/repo#number' format,
               e.g. 'zamilzahir/buggy-calculator#1'
    """
    owner, repo, number = _parse_pr_id(pr_id)
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{number}"
    headers = {"Accept": "application/vnd.github.v3.diff"}

    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.get(url, headers=headers, timeout=15)
    except requests.RequestException as e:
        raise RuntimeError(f"Could not reach GitHub: {e}") from e

    if response.status_code == 404:
        raise ValueError(f"PR not found: {pr_id}. Check it's correct and public.")
    if response.status_code == 403:
        raise RuntimeError("GitHub rate limit hit. Add GITHUB_TOKEN to .env.")
    response.raise_for_status()
    return response.text


@mcp.tool()
def list_hunks(diff: str) -> list[str]:
    """Split a diff into individual file hunks. Currently returns the whole
    diff as one hunk — per-file splitting is a possible next step."""
    return [diff]


if __name__ == "__main__":
    mcp.run(transport="stdio")