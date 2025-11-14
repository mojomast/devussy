"""Unit tests for GitManager."""

import gc
import shutil
import tempfile
from pathlib import Path

import pytest
from git import Repo

from src.git_manager import GitManager


@pytest.fixture
def temp_repo():
    """Create a temporary Git repository for testing."""
    tmpdir = tempfile.mkdtemp()
    try:
        repo_path = Path(tmpdir)
        # Initialize repository
        Repo.init(repo_path)
        # Configure git user for commits
        repo = Repo(repo_path)
        with repo.config_writer() as git_config:
            git_config.set_value("user", "name", "Test User")
            git_config.set_value("user", "email", "test@example.com")
        yield repo_path
    finally:
        # Force garbage collection to release file handles
        gc.collect()
        # Try to remove temp directory, ignore errors on Windows
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass


@pytest.fixture
def git_manager(temp_repo):
    """Create a GitManager instance with a temporary repository."""
    return GitManager(temp_repo)


def test_init_with_valid_repo(temp_repo):
    """Test GitManager initialization with a valid repository."""
    manager = GitManager(temp_repo)
    assert manager.is_repo()
    assert manager.repo_path == temp_repo


def test_init_without_repo():
    """Test GitManager initialization without a Git repository."""
    tmpdir = tempfile.mkdtemp()
    try:
        manager = GitManager(Path(tmpdir))
        assert not manager.is_repo()
    finally:
        gc.collect()
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass


def test_is_repo(git_manager):
    """Test is_repo() method."""
    assert git_manager.is_repo()


def test_commit_changes_with_new_file(git_manager, temp_repo):
    """Test committing a new file."""
    # Create a test file
    test_file = temp_repo / "test.txt"
    test_file.write_text("test content")

    # Commit the file
    git_manager.commit_changes("test: add test file", files=["test.txt"])

    # Verify commit was created
    repo = git_manager.repo
    assert len(list(repo.iter_commits())) == 1
    commit = list(repo.iter_commits())[0]
    assert commit.message == "test: add test file"


def test_commit_changes_all_files(git_manager, temp_repo):
    """Test committing all changes without specifying files."""
    # Create multiple test files
    (temp_repo / "file1.txt").write_text("content 1")
    (temp_repo / "file2.txt").write_text("content 2")

    # Commit all files
    git_manager.commit_changes("test: add multiple files")

    # Verify commit was created with all files
    repo = git_manager.repo
    commit = list(repo.iter_commits())[0]
    assert commit.message == "test: add multiple files"
    # Check that both files are in the commit
    assert "file1.txt" in commit.stats.files
    assert "file2.txt" in commit.stats.files


def test_commit_changes_no_changes(git_manager, temp_repo, caplog):
    """Test committing when there are no changes."""
    # Create and commit a file first
    test_file = temp_repo / "test.txt"
    test_file.write_text("test content")
    git_manager.commit_changes("test: initial commit")

    # Try to commit again with no changes
    git_manager.commit_changes("test: no changes")

    # Verify only one commit exists
    repo = git_manager.repo
    assert len(list(repo.iter_commits())) == 1


def test_create_branch(git_manager, temp_repo):
    """Test creating a new branch."""
    # Create an initial commit first (needed for HEAD to exist)
    (temp_repo / "test.txt").write_text("test")
    git_manager.commit_changes("test: initial commit")

    # Now create the branch
    git_manager.create_branch("feature-branch")

    # Verify branch was created
    repo = git_manager.repo
    assert "feature-branch" in [head.name for head in repo.heads]


def test_merge_branch(git_manager, temp_repo):
    """Test merging branches."""
    # Create initial commit on main
    (temp_repo / "main.txt").write_text("main content")
    git_manager.commit_changes("test: main commit")

    # Create and checkout feature branch
    git_manager.create_branch("feature")
    repo = git_manager.repo
    repo.heads.feature.checkout()

    # Add commit to feature branch
    (temp_repo / "feature.txt").write_text("feature content")
    git_manager.commit_changes("test: feature commit")

    # Merge feature into main
    git_manager.merge_branch("master", "feature")

    # Verify merge was successful
    assert git_manager.get_current_branch() == "master"
    assert (temp_repo / "feature.txt").exists()


def test_tag_release_lightweight(git_manager, temp_repo):
    """Test creating a lightweight tag."""
    # Create a commit first
    (temp_repo / "test.txt").write_text("test")
    git_manager.commit_changes("test: add file")

    # Create tag
    git_manager.tag_release("v1.0.0")

    # Verify tag was created
    repo = git_manager.repo
    assert "v1.0.0" in [tag.name for tag in repo.tags]


def test_tag_release_annotated(git_manager, temp_repo):
    """Test creating an annotated tag."""
    # Create a commit first
    (temp_repo / "test.txt").write_text("test")
    git_manager.commit_changes("test: add file")

    # Create annotated tag
    git_manager.tag_release("v2.0.0", "Release version 2.0.0")

    # Verify tag was created
    repo = git_manager.repo
    assert "v2.0.0" in [tag.name for tag in repo.tags]
    tag = repo.tags["v2.0.0"]
    assert tag.tag.message == "Release version 2.0.0"


def test_init_repository():
    """Test initializing a new repository."""
    tmpdir = tempfile.mkdtemp()
    try:
        repo_path = Path(tmpdir)
        manager = GitManager(repo_path)

        # Repository should not exist yet
        assert not manager.is_repo()

        # Initialize repository
        manager.init_repository("Initial commit")

        # Verify repository was initialized
        assert manager.is_repo()
    finally:
        # Force cleanup
        gc.collect()
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass


def test_add_remote(git_manager):
    """Test adding a remote repository."""
    git_manager.add_remote("origin", "https://github.com/test/test.git")

    # Verify remote was added
    repo = git_manager.repo
    assert "origin" in [remote.name for remote in repo.remotes]
    assert repo.remotes.origin.url == "https://github.com/test/test.git"


def test_get_current_branch(git_manager, temp_repo):
    """Test getting the current branch name."""
    # Create initial commit (needed for active branch)
    (temp_repo / "test.txt").write_text("test")
    git_manager.commit_changes("test: add file")

    # Default branch should be master or main
    current_branch = git_manager.get_current_branch()
    assert current_branch in ["master", "main"]


def test_has_uncommitted_changes(git_manager, temp_repo):
    """Test checking for uncommitted changes."""
    # Initially no changes
    assert not git_manager.has_uncommitted_changes()

    # Create a file - should have uncommitted changes
    (temp_repo / "test.txt").write_text("test")
    assert git_manager.has_uncommitted_changes()

    # Commit the file - no more uncommitted changes
    git_manager.commit_changes("test: add file")
    assert not git_manager.has_uncommitted_changes()

    # Modify the file - should have uncommitted changes again
    (temp_repo / "test.txt").write_text("modified")
    assert git_manager.has_uncommitted_changes()


def test_commit_changes_not_a_repo():
    """Test committing changes when not in a Git repository."""
    tmpdir = tempfile.mkdtemp()
    try:
        manager = GitManager(Path(tmpdir))

        with pytest.raises(Exception):
            manager.commit_changes("test: should fail")
    finally:
        gc.collect()
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass


def test_create_branch_not_a_repo():
    """Test creating branch when not in a Git repository."""
    tmpdir = tempfile.mkdtemp()
    try:
        manager = GitManager(Path(tmpdir))

        with pytest.raises(Exception):
            manager.create_branch("feature")
    finally:
        gc.collect()
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass


def test_tag_release_not_a_repo():
    """Test creating tag when not in a Git repository."""
    tmpdir = tempfile.mkdtemp()
    try:
        manager = GitManager(Path(tmpdir))

        with pytest.raises(Exception):
            manager.tag_release("v1.0.0")
    finally:
        gc.collect()
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass
