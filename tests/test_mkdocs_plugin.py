"""Tests for the MkDocs plugin."""

import os
from unittest.mock import patch

import pytest
from mkdocs.config.defaults import MkDocsConfig

from markdown_exec import MarkdownExecPlugin, MarkdownExecPluginConfig


@pytest.fixture
def plugin():
    """Return a plugin instance."""
    return MarkdownExecPlugin()


@pytest.fixture
def mkdocs_config():
    """Return a MkDocs config."""
    config = MkDocsConfig()
    config["markdown_extensions"] = ["pymdownx.superfences"]
    config["config_file_path"] = "/path/to/mkdocs.yml"
    config["mdx_configs"] = {}
    return config


@pytest.fixture
def env_cleanup():
    """Save and restore environment variables."""
    original_auto_exec = os.environ.get("MARKDOWN_EXEC_AUTO")
    original_config_dir = os.environ.get("MKDOCS_CONFIG_DIR")

    yield

    # Restore original environment
    if original_auto_exec is None:
        os.environ.pop("MARKDOWN_EXEC_AUTO", None)
    else:
        os.environ["MARKDOWN_EXEC_AUTO"] = original_auto_exec

    if original_config_dir is None:
        os.environ.pop("MKDOCS_CONFIG_DIR", None)
    else:
        os.environ["MKDOCS_CONFIG_DIR"] = original_config_dir


@pytest.mark.parametrize(
    "auto_exec_value, expected_env_value",
    [
        (["python", "bash"], "python,bash"),
        ("python,bash", "python,bash"),
        (None, None),
    ],
)
def test_auto_exec_config(
    plugin, mkdocs_config, env_cleanup, auto_exec_value, expected_env_value
):
    """Test auto_exec configuration with different values."""
    # Set up plugin config
    plugin.config = MarkdownExecPluginConfig()
    plugin.config.load_dict({"auto_exec": auto_exec_value})

    # For None case, set a test value to ensure it's not changed
    if auto_exec_value is None:
        os.environ["MARKDOWN_EXEC_AUTO"] = "test"
        expected_env_value = "test"

    # Run on_config
    with patch("markdown_exec._internal.mkdocs_plugin._ansi_ok", True):
        plugin.on_config(mkdocs_config)

    # Check that environment variable was set correctly
    assert os.environ["MARKDOWN_EXEC_AUTO"] == expected_env_value

    # Run on_post_build to restore environment
    plugin.on_post_build(config=mkdocs_config)

    # Check that environment variable was restored
    if "MARKDOWN_EXEC_AUTO" in os.environ:
        assert os.environ["MARKDOWN_EXEC_AUTO"] == "test"


def test_auto_exec_preserves_existing_env(plugin, mkdocs_config, env_cleanup):
    """Test that existing environment variables are preserved and restored."""
    # Set initial environment variables
    os.environ["MARKDOWN_EXEC_AUTO"] = "initial,value"
    os.environ["MKDOCS_CONFIG_DIR"] = "/initial/path"

    # Set up plugin config
    plugin.config = MarkdownExecPluginConfig()
    plugin.config.load_dict({"auto_exec": ["python", "bash"]})

    # Run on_config
    with patch("markdown_exec._internal.mkdocs_plugin._ansi_ok", True):
        plugin.on_config(mkdocs_config)

    # Check that environment variables were updated
    assert os.environ["MARKDOWN_EXEC_AUTO"] == "python,bash"
    assert os.environ["MKDOCS_CONFIG_DIR"] == os.path.dirname(
        mkdocs_config["config_file_path"]
    )

    # Run on_post_build to restore environment
    plugin.on_post_build(config=mkdocs_config)

    # Check that environment variables were restored
    assert os.environ["MARKDOWN_EXEC_AUTO"] == "initial,value"
    assert os.environ["MKDOCS_CONFIG_DIR"] == "/initial/path"


def test_dynamic_environment_variable_reading(plugin, mkdocs_config, env_cleanup):
    """Test that environment variables are read dynamically, not at import time.
    
    This test ensures that the fix for the timing issue works correctly:
    - Environment variables are read when validator/formatter functions are called
    - Not when the module is imported
    """
    from markdown_exec._internal.main import get_auto_exec_languages, validator
    
    # Initially, no auto-exec environment variable
    os.environ.pop("MARKDOWN_EXEC_AUTO", None)
    
    # Should return empty list when no env var is set
    assert get_auto_exec_languages() == []
    
    # Test validator with no auto-exec - should not execute python
    result = validator("python", {}, {}, {}, None)
    assert result is False
    
    # Now set the environment variable (simulating what the plugin does)
    os.environ["MARKDOWN_EXEC_AUTO"] = "python,bash"
    
    # Should now return the languages
    assert get_auto_exec_languages() == ["python", "bash"]
    
    # Test validator with auto-exec - should execute python
    result = validator("python", {}, {}, {}, None)
    assert result is True
    
    # Test that explicit exec="off" overrides auto-exec
    result = validator("python", {"exec": "off"}, {}, {}, None)
    assert result is False
    
    # Test that explicit exec="1" works regardless of auto-exec
    os.environ.pop("MARKDOWN_EXEC_AUTO", None)  # Remove auto-exec
    
    # Even without auto-exec, exec="1" should enable execution
    result = validator("python", {"exec": "1"}, {}, {}, None)
    assert result is True


def test_plugin_sets_environment_before_validation(plugin, mkdocs_config, env_cleanup):
    """Test that the plugin sets the environment variable before validation occurs."""
    from markdown_exec._internal.main import get_auto_exec_languages
    
    # Clear any existing environment variable
    os.environ.pop("MARKDOWN_EXEC_AUTO", None)
    
    # Initially should be empty
    assert get_auto_exec_languages() == []
    
    # Configure plugin with auto_exec
    plugin.config = MarkdownExecPluginConfig()
    plugin.config.load_dict({"auto_exec": ["python", "bash", "sh"]})
    
    # Run on_config - this should set the environment variable
    with patch("markdown_exec._internal.mkdocs_plugin._ansi_ok", True):
        plugin.on_config(mkdocs_config)
    
    # Now the environment variable should be set and readable
    assert get_auto_exec_languages() == ["python", "bash", "sh"]
    
    # Test with string value
    plugin.config.load_dict({"auto_exec": "python"})
    plugin.on_config(mkdocs_config)
    assert get_auto_exec_languages() == ["python"]


def test_auto_exec_end_to_end_workflow(plugin, mkdocs_config, env_cleanup):
    """Test the complete auto-exec workflow from config to validation."""
    from markdown_exec._internal.main import validator
    
    # Clear environment
    os.environ.pop("MARKDOWN_EXEC_AUTO", None)
    
    # Step 1: Configure the plugin
    plugin.config = MarkdownExecPluginConfig()
    plugin.config.load_dict({"auto_exec": ["python", "bash"]})
    
    # Step 2: Run on_config to set up the environment
    with patch("markdown_exec._internal.mkdocs_plugin._ansi_ok", True):
        plugin.on_config(mkdocs_config)
    
    # Step 3: Test that validation now works correctly
    
    # Python should auto-execute
    result = validator("python", {}, {}, {}, None)
    assert result is True
    
    # Bash should auto-execute
    result = validator("bash", {}, {}, {}, None)
    assert result is True
    
    # Console should NOT auto-execute (not in the list)
    result = validator("console", {}, {}, {}, None)
    assert result is False
    
    # Python with exec="off" should NOT execute (explicit override)
    result = validator("python", {"exec": "off"}, {}, {}, None)
    assert result is False
    
    # Console with exec="1" should execute (explicit enable)
    result = validator("console", {"exec": "1"}, {}, {}, None)
    assert result is True
    
    # Step 4: Test cleanup
    plugin.on_post_build(config=mkdocs_config)
    
    # Environment should be restored (no auto-exec)
    from markdown_exec._internal.main import get_auto_exec_languages
    assert get_auto_exec_languages() == []
