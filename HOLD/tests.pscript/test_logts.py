import pytest
from unittest.mock import patch, mock_open, MagicMock
from logtool.logts import main

@patch("logtool.logts.subprocess.run")
def test_logts_creates_timestamped_log(mock_run):
    mock_run.return_value.returncode = 0
    argv = ["logts", "--time", "--base", "/tmp", "echo", "Hello"]

    with patch("logtool.logts.docopt") as mock_docopt:
        mock_docopt.return_value = {
            "--time": True,
            "--base": "/tmp",
            "<command>": "echo",
            "<argv>": ["Hello"],
        }
        assert main(argv) == 0

    mock_run.assert_called_once_with(
        ["echo", "Hello"], stdout=MagicMock(), stderr=MagicMock()
    )

@patch("os.makedirs")
def test_logts_creates_directory(mock_makedirs, mocker):
    mocker.patch("logtool.logts.open", mock_open())
    argv = ["logts", "--time", "--base", "/tmp", "echo", "Hello"]

    with patch("logtool.logts.docopt") as mock_docopt:
        mock_docopt.return_value = {
            "--time": True,
            "--base": "/tmp",
            "<command>": "echo",
            "<argv>": ["Hello"],
        }
        main(argv)

    mock_makedirs.assert_called_once_with("/tmp", exist_ok=True)

def test_logts_missing_base():
    argv = ["logts", "--time", "echo", "Hello"]
    with pytest.raises(SystemExit):
        main(argv)
