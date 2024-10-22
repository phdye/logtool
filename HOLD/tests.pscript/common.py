import os

from contextlib import _RedirectStream

class redirect_stdin(_RedirectStream):
    _stream = "stdin"

def empty_pipe():
    read_fd, write_fd = os.pipe()
    os.close(write_fd)
    return os.fdopen(read_fd, 'r')

