"""Tests for the MkDocs plugin."""

import os
from unittest.mock import MagicMock, patch

import pytest
from mkdocs.config.defaults import MkDocsConfig

from markdown_exec.mkdocs_plugin import MarkdownExecPlugin, MarkdownExecPluginConfig


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


def test_plugin_init():
    """Test plugin initialization."""
    plugin = MarkdownExecPlugin()
    assert plugin.original_env_vars == {}


def test_auto_exec_list(plugin, mkdocs_config):
    """Test auto_exec with a list value."""
    # Set up plugin config
    plugin.config = MarkdownExecPluginConfig(auto_exec=["python", "bash"])

    # Save original environment
    original_auto_exec = os.environ.get("MARKDOWN_EXEC_AUTO")

    try:
        # Run on_config
        with patch("markdown_exec.mkdocs_plugin.ansi_ok", True):
            plugin.on_config(mkdocs_config)

        # Check that environment variable was set correctly
        assert os.environ["MARKDOWN_EXEC_AUTO"] == "python,bash"

        # Run on_post_build to restore environment
        plugin.on_post_build(config=mkdocs_config)

        # Check that environment variable was restored
        if original_auto_exec is None:
            assert "MARKDOWN_EXEC_AUTO" not in os.environ
        else:
            assert os.environ["MARKDOWN_EXEC_AUTO"] == original_auto_exec

    finally:
        # Clean up
        if original_auto_exec is None:
            os.environ.pop("MARKDOWN_EXEC_AUTO", None)
        else:
            os.environ["MARKDOWN_EXEC_AUTO"] = original_auto_exec


def test_auto_exec_string(plugin, mkdocs_config):
    """Test auto_exec with a string value."""
    # Set up plugin config
    plugin.config = MarkdownExecPluginConfig(auto_exec="python,bash")

    # Save original environment
    original_auto_exec = os.environ.get("MARKDOWN_EXEC_AUTO")

    try:
        # Run on_config
        with patch("markdown_exec.mkdocs_plugin.ansi_ok", True):
            plugin.on_config(mkdocs_config)

        # Check that environment variable was set correctly
        assert os.environ["MARKDOWN_EXEC_AUTO"] == "python,bash"

        # Run on_post_build to restore environment
        plugin.on_post_build(config=mkdocs_config)

        # Check that environment variable was restored
        if original_auto_exec is None:
            assert "MARKDOWN_EXEC_AUTO" not in os.environ
        else:
            assert os.environ["MARKDOWN_EXEC_AUTO"] == original_auto_exec

    finally:
        # Clean up
        if original_auto_exec is None:
            os.environ.pop("MARKDOWN_EXEC_AUTO", None)
        else:
            os.environ["MARKDOWN_EXEC_AUTO"] = original_auto_exec


def test_auto_exec_none(plugin, mkdocs_config):
    """Test auto_exec with None value (default)."""
    # Set up plugin config
    plugin.config = MarkdownExecPluginConfig(auto_exec=None)

    # Save original environment
    original_auto_exec = os.environ.get("MARKDOWN_EXEC_AUTO")

    try:
        # Set a test value to ensure it's not changed
        if original_auto_exec is None:
            os.environ["MARKDOWN_EXEC_AUTO"] = "test"
            test_value = "test"
        else:
            test_value = original_auto_exec

        # Run on_config
        with patch("markdown_exec.mkdocs_plugin.ansi_ok", True):
            plugin.on_config(mkdocs_config)

        # Check that environment variable was not changed
        assert os.environ["MARKDOWN_EXEC_AUTO"] == test_value

        # Run on_post_build to restore environment
        plugin.on_post_build(config=mkdocs_config)

        # Check that environment variable was restored
        if original_auto_exec is None:
            assert "MARKDOWN_EXEC_AUTO" not in os.environ
        else:
            assert os.environ["MARKDOWN_EXEC_AUTO"] == original_auto_exec

    finally:
        # Clean up
        if original_auto_exec is None:
            os.environ.pop("MARKDOWN_EXEC_AUTO", None)
        else:
            os.environ["MARKDOWN_EXEC_AUTO"] = original_auto_exec
