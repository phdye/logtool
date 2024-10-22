import pytest
from unittest.mock import patch, mock_open
from logtool.log import main

@patch("logtool.log.subprocess.run")
def test_log_executes_command(mock_run):
    mock_run.return_value.returncode = 0
    argv = ["log", "-a", "test.log", "echo", "Hello"]

    with patch("logtool.log.docopt") as mock_docopt:
        mock_docopt.return_value = {
            "<log-file>": "test.log",
            "<command>": "echo",
            "<argv>": ["Hello"],
        }
        assert main(argv) == 0  # Verify successful execution

    mock_run.assert_called_once_with(
        ["echo", "Hello"], stdout=mock_open(), stderr=mock_open()
    )

def test_log_with_timestamps(mocker):
    # Mock file opening
    mocker.patch("logtool.log.open", mock_open())
    argv = ["log", "-t", "test.log", "echo", "Hello"]
    
    with patch("logtool.log.docopt") as mock_docopt:
        mock_docopt.return_value = {
            "<log-file>": "test.log",
            "--time": True,
            "<command>": "echo",
            "<argv>": ["Hello"],
        }
        assert main(argv) == 0

def test_log_invalid_command():
    argv = ["log", "--invalid"]
    with pytest.raises(SystemExit):
        main(argv)
