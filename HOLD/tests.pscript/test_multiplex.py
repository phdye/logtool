import sys
import os
import io
import pytest
from unittest.mock import MagicMock, patch, mock_open

from logtool.multiplex import MULTIPLEX
import subprocess

from plumbum import local

from .common import redirect_stdin, empty_pipe


def test_multiplex_initialization():
    """Test that MULTIPLEX initializes with correct attributes."""
    mplex = MULTIPLEX(retcode=0, buffered=True, keep=True, append=False, timeout=None, outputs=[])
    assert mplex.retcode == 0
    assert mplex.buffered is True
    assert mplex.keep is True
    assert mplex.append is False
    assert mplex.timeout is None
    assert mplex.outputs == []


def test_multiplex_run_command():
    """Test that MULTIPLEX correctly runs a command."""

    message = "Hello World !"

    # Instantiate MULTIPLEX and run a command
    with redirect_stdin(empty_pipe()):
        echo = local['/bin/echo']
        (return_code, stdout, stderr) = echo[message] & MULTIPLEX()

    assert stdout == f"{message}\n"
    assert stderr == ""
    assert return_code == 0


def test_multiplex_command_failure():
    """Test that MULTIPLEX handles command failure gracefully."""

    with redirect_stdin(empty_pipe()):
        (return_code, stdout, stderr) = local['/bin/false'] & MULTIPLEX(retcode=1)

    assert stdout == ""
    assert stderr == ""
    assert return_code == 1


def test_multiplex_keyboard_interrupt():
    """Test that MULTIPLEX handles keyboard interrupts gracefully."""
    
    mplex = MULTIPLEX(retcode=None)

    def rand_core__keyboard_interrupt(self, *args):
        raise KeyboardInterrupt        
    setattr(mplex, 'rand_core', rand_core__keyboard_interrupt)

    with redirect_stdin(empty_pipe()):
        (return_code, stdout, stderr) = local['/bin/echo'] & mplex
        assert stdout == ""
        assert stderr == ""
        assert return_code == 1

