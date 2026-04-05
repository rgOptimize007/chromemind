import subprocess
from agents.logger import LoggerAgent

class GitAgentError(Exception):
    pass

class GitAgent:
    @staticmethod
    def _run_cmd(cmd: list[str]) -> str:
        try:
            result = subprocess.run(cmd, check=True, text=True, capture_output=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            LoggerAgent.log("git_agent", "cmd_failed", "error", {"cmd": " ".join(cmd), "error": e.stderr})
            raise GitAgentError(f"Git command failed: {e.stderr}")

    @staticmethod
    def checkout_feature_branch(branch_name: str) -> None:
        """Checks out a feature branch from main."""
        LoggerAgent.log("git_agent", "checkout_branch", "info", {"branch": branch_name})
        GitAgent._run_cmd(["git", "checkout", "main"])
        GitAgent._run_cmd(["git", "pull", "origin", "main"])
        
        # Check if branch exists
        try:
            GitAgent._run_cmd(["git", "checkout", "-b", branch_name])
        except GitAgentError:
            GitAgent._run_cmd(["git", "checkout", branch_name])

    @staticmethod
    def commit_changes(message: str) -> None:
        """Stages all changes and commits them with a meaningful message."""
        LoggerAgent.log("git_agent", "commit_changes", "info", {"message": message})
        GitAgent._run_cmd(["git", "add", "."])
        
        # Check if there are changes to commit
        status = GitAgent._run_cmd(["git", "status", "--porcelain"])
        if not status:
            LoggerAgent.log("git_agent", "no_changes", "info")
            return
            
        GitAgent._run_cmd(["git", "commit", "-m", message])

    @staticmethod
    def push_and_squash_if_needed(branch_name: str, threshold: int = 3) -> None:
        """Pushes to remote. Squashes if local commits exceed threshold."""
        LoggerAgent.log("git_agent", "push_check", "info", {"branch": branch_name})
        
        # Count commits ahead of main
        commit_count_str = GitAgent._run_cmd(["git", "rev-list", "--count", f"main..{branch_name}"])
        commit_count = int(commit_count_str) if commit_count_str.isdigit() else 0
        
        if commit_count > threshold:
            LoggerAgent.log("git_agent", "squashing_commits", "info", {"count": commit_count})
            GitAgent._run_cmd(["git", "reset", "--soft", f"HEAD~{commit_count}"])
            GitAgent._run_cmd(["git", "commit", "-m", f"Squashed {commit_count} commits into one for PR"])
            
        # Push to remote
        try:
            GitAgent._run_cmd(["git", "push", "-u", "origin", branch_name])
        except GitAgentError as e:
            if "fetch first" in str(e) or "non-fast-forward" in str(e):
                LoggerAgent.log("git_agent", "push_rejected", "error")
                raise GitAgentError("Push rejected, fetch and merge required.")
            raise e

    @staticmethod
    def check_pr_conflicts(pr_number: str) -> bool:
        """
        Uses GitHub CLI (or MCP if configured via orchestrator) to check for conflicts.
        Returns True if conflicts exist.
        """
        LoggerAgent.log("git_agent", "check_pr_conflicts", "info", {"pr": pr_number})
        try:
            # We assume `gh` CLI is available in the environment to check PR status.
            # In an MCP context, the orchestrator would query the MCP directly, 
            # but standardizing here abstracts the interface.
            output = GitAgent._run_cmd(["gh", "pr", "view", pr_number, "--json", "mergeable"])
            if '"mergeable":"CONFLICTING"' in output:
                LoggerAgent.log("git_agent", "pr_conflict_detected", "error", {"pr": pr_number})
                return True
            return False
        except Exception as e:
            LoggerAgent.log("git_agent", "gh_cli_error", "warn", {"error": str(e)})
            return False
