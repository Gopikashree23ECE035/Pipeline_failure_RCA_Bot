import requests
import logging

logger = logging.getLogger(__name__)

class GitHubService:
    def __init__(self, token=None, repo=None):
        self.token = token
        self.repo = repo
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def is_configured(self):
        return bool(self.token and self.repo)

    def fetch_recent_commits(self, limit=5):
        """
        Fetches recent commits and their diff details from the GitHub repository.
        """
        if not self.is_configured():
            logger.error("GitHub integration not fully configured. Missing token or repo.")
            raise ValueError("GitHub token and repo must be configured")

        url = f"https://api.github.com/repos/{self.repo}/commits"
        params = {"per_page": limit}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to fetch commits from GitHub (Status {response.status_code}): {response.text}")
                raise RuntimeError(f"GitHub API Error: {response.text}")
                
            commits_list = response.json()
            detailed_commits = []
            
            for c in commits_list[:limit]:
                sha = c.get("sha")
                commit_details = self.fetch_commit_detail(sha)
                if commit_details:
                    detailed_commits.append(commit_details)
                else:
                    # Fallback to basic info if detail fetch failed
                    detailed_commits.append({
                        "commit_id": sha,
                        "author": c.get("commit", {}).get("author", {}).get("name", "Unknown"),
                        "date": c.get("commit", {}).get("author", {}).get("date", ""),
                        "message": c.get("commit", {}).get("message", ""),
                        "changed_files": [],
                        "diff_summary": "Diff details unavailable."
                    })
            return detailed_commits

        except Exception as e:
            logger.error(f"Error connecting to GitHub API: {str(e)}")
            raise e

    def fetch_commit_detail(self, sha):
        """
        Fetches detailed information for a specific commit, including list of changed files and diffs.
        """
        url = f"https://api.github.com/repos/{self.repo}/commits/{sha}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return None
                
            data = response.json()
            changed_files = []
            diffs = []
            
            for file_info in data.get("files", []):
                filename = file_info.get("filename")
                changed_files.append(filename)
                
                patch = file_info.get("patch", "")
                if patch:
                    diffs.append(f"--- a/{filename}\n+++ b/{filename}\n{patch}")
            
            return {
                "commit_id": sha,
                "author": data.get("commit", {}).get("author", {}).get("name", "Unknown"),
                "date": data.get("commit", {}).get("author", {}).get("date", ""),
                "message": data.get("commit", {}).get("message", ""),
                "changed_files": changed_files,
                "diff_summary": "\n\n".join(diffs)
            }
        except Exception as e:
            logger.error(f"Error fetching commit details for {sha}: {str(e)}")
            return None
