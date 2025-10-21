"""Git integration wrapper for DevPlan Orchestrator."""

import logging
from pathlib import Path
from typing import List, Optional

from git import GitCommandError, InvalidGitRepositoryError, Repo

logger = logging.getLogger(__name__)


class GitManager:
    """Manage Git operations for automatic commits and version control."""

    def __init__(self, repo_path: Optional[Path] = None):
        """
        Initialize GitManager with optional repository path.

        Args:
            repo_path: Path to Git repository. Defaults to current directory.

        Raises:
            InvalidGitRepositoryError: If repo_path is not a valid Git repository.
        """
        self.repo_path = repo_path or Path.cwd()
        try:
            self.repo = Repo(self.repo_path)
            logger.debug(f"Initialized GitManager for repository: {self.repo_path}")
        except InvalidGitRepositoryError:
            logger.warning(f"Not a git repository: {self.repo_path}")
            self.repo = None

    def is_repo(self) -> bool:
        """
        Check if the current path is a valid Git repository.

        Returns:
            bool: True if valid Git repository, False otherwise.
        """
        return self.repo is not None and not self.repo.bare

    def commit_changes(self, message: str, files: Optional[List[str]] = None) -> None:
        """
        Commit changes to the repository.

        Args:
            message: Commit message.
            files: List of file paths to stage. If None, stages all changes.

        Raises:
            InvalidGitRepositoryError: If not a valid Git repository.
            GitCommandError: If Git command fails.
        """
        if not self.is_repo():
            raise InvalidGitRepositoryError(
                f"Cannot commit: {self.repo_path} is not a valid Git repository"
            )

        try:
            # Stage files
            if files:
                logger.debug(f"Staging specific files: {files}")
                self.repo.index.add(files)
            else:
                logger.debug("Staging all changes")
                # Stage all modified and new files
                self.repo.git.add(A=True)

            # Check if there are changes to commit (handle new repo without HEAD)
            try:
                has_staged_changes = bool(self.repo.index.diff("HEAD"))
            except Exception:
                # No HEAD yet (empty repo), check if index has entries
                has_staged_changes = len(self.repo.index.entries) > 0

            if not has_staged_changes and not self.repo.untracked_files:
                logger.info("No changes to commit")
                return

            # Commit changes
            commit = self.repo.index.commit(message)
            logger.info(f"Created commit {commit.hexsha[:7]}: {message}")

        except GitCommandError as e:
            logger.error(f"Git commit failed: {e}")
            raise

    def create_branch(self, name: str) -> None:
        """
        Create a new branch.

        Args:
            name: Name of the branch to create.

        Raises:
            InvalidGitRepositoryError: If not a valid Git repository.
            GitCommandError: If branch creation fails.
        """
        if not self.is_repo():
            raise InvalidGitRepositoryError(
                f"Cannot create branch: {self.repo_path} is not a valid Git repository"
            )

        try:
            new_branch = self.repo.create_head(name)
            logger.info(f"Created branch: {name}")
            return new_branch
        except GitCommandError as e:
            logger.error(f"Failed to create branch {name}: {e}")
            raise

    def merge_branch(self, base: str, feature: str) -> None:
        """
        Merge feature branch into base branch.

        Args:
            base: Name of the base branch to merge into.
            feature: Name of the feature branch to merge from.

        Raises:
            InvalidGitRepositoryError: If not a valid Git repository.
            GitCommandError: If merge fails.
        """
        if not self.is_repo():
            raise InvalidGitRepositoryError(
                f"Cannot merge: {self.repo_path} is not a valid Git repository"
            )

        try:
            # Checkout base branch
            self.repo.heads[base].checkout()
            logger.debug(f"Checked out base branch: {base}")

            # Merge feature branch
            self.repo.git.merge(feature)
            logger.info(f"Merged {feature} into {base}")

        except GitCommandError as e:
            logger.error(f"Failed to merge {feature} into {base}: {e}")
            raise

    def tag_release(self, tag: str, message: Optional[str] = None) -> None:
        """
        Create a Git tag for release versioning.

        Args:
            tag: Tag name (e.g., "v1.0.0", "handoff-phase-5").
            message: Optional tag message for annotated tags.

        Raises:
            InvalidGitRepositoryError: If not a valid Git repository.
            GitCommandError: If tag creation fails.
        """
        if not self.is_repo():
            raise InvalidGitRepositoryError(
                f"Cannot create tag: {self.repo_path} is not a valid Git repository"
            )

        try:
            if message:
                # Create annotated tag
                self.repo.create_tag(tag, message=message)
                logger.info(f"Created annotated tag: {tag} with message: {message}")
            else:
                # Create lightweight tag
                self.repo.create_tag(tag)
                logger.info(f"Created lightweight tag: {tag}")

        except GitCommandError as e:
            logger.error(f"Failed to create tag {tag}: {e}")
            raise

    def init_repository(self, initial_commit_message: str = "Initial commit") -> None:
        """
        Initialize a new Git repository.

        Args:
            initial_commit_message: Message for the initial commit.

        Raises:
            GitCommandError: If initialization fails.
        """
        try:
            if self.is_repo():
                logger.warning(f"Repository already initialized at {self.repo_path}")
                return

            # Initialize repository
            self.repo = Repo.init(self.repo_path)
            logger.info(f"Initialized Git repository at {self.repo_path}")

            # Create initial commit if there are files
            if list(self.repo_path.glob("*")):
                self.repo.git.add(A=True)
                self.repo.index.commit(initial_commit_message)
                logger.info(f"Created initial commit: {initial_commit_message}")

        except GitCommandError as e:
            logger.error(f"Failed to initialize repository: {e}")
            raise

    def add_remote(self, name: str, url: str) -> None:
        """
        Add a remote repository.

        Args:
            name: Remote name (e.g., "origin").
            url: Remote URL.

        Raises:
            InvalidGitRepositoryError: If not a valid Git repository.
            GitCommandError: If adding remote fails.
        """
        if not self.is_repo():
            raise InvalidGitRepositoryError(
                f"Cannot add remote: {self.repo_path} is not a valid Git repository"
            )

        try:
            self.repo.create_remote(name, url)
            logger.info(f"Added remote {name}: {url}")
        except GitCommandError as e:
            logger.error(f"Failed to add remote {name}: {e}")
            raise

    def push(self, remote: str = "origin", branch: Optional[str] = None) -> None:
        """
        Push commits to remote repository.

        Args:
            remote: Remote name (default: "origin").
            branch: Branch name to push. If None, pushes current branch.

        Raises:
            InvalidGitRepositoryError: If not a valid Git repository.
            GitCommandError: If push fails.
        """
        if not self.is_repo():
            raise InvalidGitRepositoryError(
                f"Cannot push: {self.repo_path} is not a valid Git repository"
            )

        try:
            if branch:
                self.repo.git.push(remote, branch)
                logger.info(f"Pushed {branch} to {remote}")
            else:
                self.repo.git.push(remote)
                logger.info(f"Pushed to {remote}")

        except GitCommandError as e:
            logger.error(f"Failed to push to {remote}: {e}")
            raise

    def get_current_branch(self) -> Optional[str]:
        """
        Get the name of the current branch.

        Returns:
            str: Current branch name, or None if not in a repository.
        """
        if not self.is_repo():
            return None

        try:
            return self.repo.active_branch.name
        except TypeError:
            # Detached HEAD state
            logger.warning("Repository is in detached HEAD state")
            return None

    def has_uncommitted_changes(self) -> bool:
        """
        Check if there are uncommitted changes.

        Returns:
            bool: True if there are uncommitted changes, False otherwise.
        """
        if not self.is_repo():
            return False

        # Check for staged changes (handle repos without HEAD)
        try:
            if self.repo.index.diff("HEAD"):
                return True
        except Exception:
            # No HEAD yet, check if index has entries
            if len(self.repo.index.entries) > 0:
                return True

        # Check for unstaged changes
        if self.repo.index.diff(None):
            return True

        # Check for untracked files
        if self.repo.untracked_files:
            return True

        return False
