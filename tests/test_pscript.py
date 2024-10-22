import io
import pytest
from unittest.mock import patch
from contextlib import redirect_stdout, redirect_stderr
from tempfile import NamedTemporaryFile

import docopt

from logtool.pscript import main as pscript
from .common import redirect_stdin, empty_pipe

def test_pscript_command_quiet():
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdin(empty_pipe()):
        with redirect_stdout(stdout):
            with redirect_stderr(stderr):
                assert pscript(["pscript", "--quiet","--command", "echo Hello"]) == 0
    assert stdout.getvalue() == "Hello\n"
    assert stderr.getvalue() == ""

def test_pscript_command_normal():
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdin(empty_pipe()):
        with redirect_stdout(stdout):
            with redirect_stderr(stderr):
                assert pscript(["pscript","--command", "echo Hello"]) == 0
    # print(stdout.getvalue())
    print('...')
    stdout = stdout.getvalue().split('\n')
    assert len(stdout) == 4
    assert stdout[0].startswith("Script started")
    assert stdout[1] == "Hello"
    assert stdout[2].startswith("Script done")
    assert stderr.getvalue() == ""

def test_pscript_invalid_args():
    argv = ["pscript", "--invalid"]
    with pytest.raises(SystemExit):
        pscript(argv)

def test_pscript_append_mode():
    tmp_name = None
    with NamedTemporaryFile(mode='w', delete=False) as tmp_file:
        tmp_name = tmp_file.name
        print(f"{tmp_name = }")
        print("Hello ", end='', file=tmp_file)
    
    stdout = io.StringIO()
    stderr = io.StringIO()
    argv = ["pscript", "--quiet", "--append", "--command", "echo World", tmp_name]
    # argv = ["pscript", "--append", "--command", "echo World", tmp_name]
    with redirect_stdin(empty_pipe()):
        if True: # with redirect_stdout(stdout):
            with redirect_stderr(stderr):
                assert pscript(argv) == 0
    # assert stdout.getvalue() == "World\n"
    assert stderr.getvalue() == ""

    with open(tmp_name, 'r') as fp:
        assert fp.read() == "Hello World\n"

