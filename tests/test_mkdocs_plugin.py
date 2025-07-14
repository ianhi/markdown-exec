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
    plugin.config = MarkdownExecPluginConfig(auto_exec=auto_exec_value)

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
    plugin.config = MarkdownExecPluginConfig(auto_exec=["python", "bash"])

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
