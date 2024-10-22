#!/usr/bin/env python3

import sys

from logtool.multiplex import MULTIPLEX
import subprocess

from plumbum import local

def example():

    echo = local['echo']

    (status, stdout, stderr) = echo["Hello"] & MULTIPLEX(outputs=['test.out'])

    if len(stdout) > 0 and stdout[-1] != '\n':
        stdout += "<missing-end-of-line>\n"

    if len(stderr) > 0 and stdout[-1] != '\n':
        stderr += "<missing-end-of-line>\n"

    print(f"[stdout]\n{stdout}- - - -")
    print(f"[stderr]\n{stderr}- - - -")
    print(f"[status]\n{status = }\n- - - -")

if __name__ == "__main__":
    example()
