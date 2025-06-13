import sys
import argparse
try:
    from typing import TextIO
except ImportError:  # Python < 3.5
    TextIO = None  # type: ignore


def raw_to_text(in_fp: TextIO, out_fp: TextIO, chunk_size: int = 8192, partial_flush_threshold: int = 0) -> None:
    """
    Convert raw terminal output into cleaned plain text, respecting partial
    ANSI/OSC sequences, backspaces, carriage returns, and tabs, with minimal
    memory usage.

    :param in_fp: input stream
    :param out_fp: output stream
    :param chunk_size: how many bytes to read per chunk (default 8192)
    :param partial_flush_threshold: if > 0, flush line if it grows beyond this length
    """

    NORMAL, ESC, CSI, OSC = 0, 1, 2, 3
    state = NORMAL
    escape_buf = ""

    line = []        # Full line buffer
    line_len = 0     # Number of valid characters
    col = 0          # Cursor column
    carriage_return_mode = False  # If True, we truncate leftover after overwriting

    # Create local references for micro-optimizations
    in_fp_read = in_fp.read
    out_fp_write = out_fp.write
    line_clear = line.clear
    line_extend = line.extend
    line_append = line.append

    def flush_line():
        nonlocal line, line_len
        if line_len > 0:
            out_fp_write(''.join(line[:line_len]).expandtabs())
        out_fp_write("\n")
        line_clear()
        line_len = 0

    while True:
        chunk = in_fp_read(chunk_size)
        if not chunk:
            break

        for ch in chunk:
            if state == NORMAL:
                if ch == '\x1B':
                    state = ESC
                    escape_buf = ch
                elif ch == '\b':
                    # Backspace
                    if col > 0:
                        col -= 1
                        line_len = min(line_len, col)
                elif ch == '\r':
                    # Carriage return: move cursor to start, enable CR mode
                    col = 0
                    carriage_return_mode = True
                elif ch == '\n':
                    # New line
                    flush_line()
                    col = 0
                    carriage_return_mode = False
                else:
                    # Overwrite or append character
                    if col < len(line):
                        line[col] = ch
                    else:
                        # Extend with spaces if there's a gap
                        line_extend([' '] * (col - len(line)))
                        line_append(ch)
                    col += 1
                    # If carriage_return_mode is True, after each char,
                    # we truncate the leftover
                    if carriage_return_mode:
                        line_len = col
                    else:
                        line_len = max(line_len, col)

            elif state == ESC:
                escape_buf += ch
                if ch == '[':
                    state = CSI
                elif ch == ']':
                    state = OSC
                else:
                    state = NORMAL
            elif state == CSI:
                escape_buf += ch
                if '@' <= ch <= '~':
                    state = NORMAL
            elif state == OSC:
                escape_buf += ch
                # replaced endswith with direct indexing as requested
                if ch == '\\' and len(escape_buf) >= 2 and escape_buf[-2] == '\x1B':
                    state = NORMAL
                elif ch == '\x07':
                    state = NORMAL

        # If partial flushing is enabled, check after each chunk
        if partial_flush_threshold > 0 and line_len >= partial_flush_threshold:
            flush_line()
            col = 0
            carriage_return_mode = False

    # Flush any partial line
    if line_len > 0:
        out_fp_write(''.join(line[:line_len]).expandtabs())


if __name__ == '__main__':

    # Moved main() here to prevent duplicate top-level name issue with pyonetrue

    def main(argv=sys.argv):
        parser = argparse.ArgumentParser(argv=argv, description="raw-to-text converter")
        parser.add_argument("-s", "--chunksize", type=int, default=8192,
                            help="Number of bytes per read chunk")
        parser.add_argument("-l", "--large", type=int, default=0,
                            help="Partial flush threshold for very large lines (0=off)")
        args = parser.parse_args()

        raw_to_text(sys.stdin, sys.stdout,
                    chunk_size=args.chunksize,
                    partial_flush_threshold=args.large)

    exit(main(argv=sys.argv))

#
