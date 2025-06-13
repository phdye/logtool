#!/usr/bin/env python3

"""
Usage:
    err [options] <command> [<arg>...]

Options:
    -a, --append   Append to errors rather than overwriting it.
    --no-clean     Keep ./.errors.{raw,txt}, after .txt copied to /dn/.
    -h, --help     Show this usage and exit.
    --version      Show version and exit.
"""

import sys
import os
import shlex
import shutil
import subprocess
try:
    from shlex import quote as _quote
except ImportError:  # Python < 3.3
    from pipes import quote as _quote

def shlex_join(split_command):
    """Fallback implementation of shlex.join for Python < 3.8."""
    return ' '.join(_quote(arg) for arg in split_command)

from .vendor.raw_to_text import raw_to_text
from .vendor.docopt import docopt

DESTINATION = "/dn/errors.txt"
ERRORS_RAW = ".errors.raw"
ERRORS_TXT = ".errors.txt"

def main():
    check_dependencies()

    args = docopt(__doc__, options_first=True)
    command = args["<command>"]
    command_args = args["<arg>"] or []

    # print(args)

    if not command:
        print("Error: No command provided.", file=sys.stderr)
        sys.exit(1)

    full_command = [command] + command_args

    # print("Running command in terminal session: {0}".format(shlex_join(full_command)))
    rc = run_command_and_capture_errors(full_command)

    convert_raw_to_text(ERRORS_RAW, ERRORS_TXT)

    copy_to_destination(args, ERRORS_TXT, DESTINATION)

    if not args['--no-clean']:
        os.unlink(ERRORS_RAW)
        os.unlink(ERRORS_TXT)

    print("\nLog '{0}'".format(DESTINATION))
    # print("Process completed successfully.")

    sys.exit(rc)

def _which(cmd):
    """shutil.which backport for Python < 3.3."""
    if hasattr(shutil, "which"):
        return shutil.which(cmd)
    paths = os.environ.get("PATH", os.defpath).split(os.pathsep)
    for path in paths:
        full = os.path.join(path, cmd)
        if os.path.isfile(full) and os.access(full, os.X_OK):
            return full
    return None


def check_dependencies():
    """Ensure required dependencies exist."""
    missing = []
    for cmd in ["script"]:
        if _which(cmd) is None:
            missing.append(cmd)

    if missing:
        print("Error: Missing required command(s): {0}".format(
            ", ".join(missing)
        ), file=sys.stderr)
        sys.exit(1)

def run_command_and_capture_errors(command):
    """Runs a command in a script(1) session and captures stderr."""
    command_str = shlex_join(command)
    script_command = ["script", "-q", "-c", "set -x && {0}".format(command_str), ERRORS_RAW]
    try:
        if hasattr(subprocess, "run"):
            completed = subprocess.run(script_command, check=True)
            return completed.returncode
        else:
            ret = subprocess.call(script_command)
            if ret != 0:
                raise subprocess.CalledProcessError(ret, script_command)
            return ret
    except subprocess.CalledProcessError as e:
        print("Error executing command: {0}".format(e), file=sys.stderr)
        sys.exit(1)

def convert_raw_to_text(input_file, output_file):
    """Converts the raw error file into readable text."""
    with open(input_file, "r") as in_file, open(output_file, "w") as out_file:
        raw_to_text(in_file, out_file)

def copy_to_destination(ctx, source_file, dest_path):
    """Copies the processed error text file to the specified destination file"""
    # os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    try:
        mode = "a" if ctx['--append'] else "w"
        with open(dest_path, mode) as dest_file:
            with open(source_file, "r") as src_file:
                dest_file.write( src_file.read() + "\n" )
        action = "appended" if ctx['--append'] else "copied"
        # print("File {0} to {1}".format(action, dest_path))
    except subprocess.CalledProcessError as e:
        print("Error copying text fi to {0} : {1}".format(dest_path, e), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

