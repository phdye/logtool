#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Usage:
  pscript [options] [<file>]

Options:
  -a, --append            Append the output
  -c, --command <command> Run command rather than interactive shell
  -p, --python            Use a Python shell as the terminal command
  -e, --return            Return exit code of the child process
  -v, --verbose           Print additional details
  -q, --quiet             Be quiet -- superceeds verbose
  -d, --debug             Print debugging details -- superceeds quiet
  -t, --time              Prefix each line with elapsed time
  -w, --wallclock         Prefix each line with local time of day
  -x, --show              Show the command line to be exectuted.
  -V, --version           Output version information and exit
  -h, --help              Display this help and exit
 """

# -f, --flush             run flush after each write
#     --force             use output file even when it is a link

# ------------------------------------------------------------------------------

import sys
import os
import time

import shlex

from docopt import docopt

from plumbum import local
from plumbum.commands.processes import ProcessExecutionError

from logtool import __version__ as version

from logtool.multiplex import MULTIPLEX

from prettyprinter import cpprint as pp

ttee = local['ttee']

# ------------------------------------------------------------------------------

# As setuptools' entry point passes nothing, argv must default to sys.argv main
# to work.  Do not use sys.argv inside main since that would break unit tests.


def main(argv=sys.argv):

    return perform(configure(parse_arguments(argv[1:])))

# ------------------------------------------------------------------------------


def parse_arguments(argv):

    # pp(argv)
    # sys.stdout.flush()

    if '--debug' in argv:
        print('')
        print("raw argv:  '%s'" % ("' '".join(argv)))
        print('')

    args = docopt(__doc__, argv, version=version, options_first=True)

    # pp(args)
    # sys.stdout.flush()

    if args['--debug']:
        print("+ log '" + "' '".join(sys.argv) + "'")
        print('')
        print('parsed :')
        pp(args)
        print('')

    return args

# ------------------------------------------------------------------------------

# Derived directly from https://docs.python.org/3.2/library/pty.html.
# Functionally equivalent.


class ActionConfig (object):
    __slots__ = ('args', 'filename', 'append', 'mode', 
                 'command_string', 'command', 'argv',
                 'return_', 'python', 'show', 'quiet',
                 'verbose', 'debug')


def configure(args):

    cfg = ActionConfig()
    cfg.args = args
    cfg.command = None
    cfg.argv = []
    cfg.filename = args['<file>']
    cfg.append = args['--append']
    cfg.return_ = args['--return']
    cfg.show = args['--show']
    cfg.debug = args['--debug']
    cfg.quiet = args['--quiet'] if not cfg.debug else False
    cfg.verbose = cfg.debug or (args['--verbose'] if not cfg.quiet else False)
    cfg.mode = 'ab' if cfg.append else 'wb'

    # option -p: use a Python shell as the terminal command
    if args['--python']:

        cfg.command = local.get(sys.executable)

    elif args['--command']:

        cfg.command_string = args['--command']
        lexed_command = list(
            shlex.shlex(
                cfg.command_string,
                punctuation_chars=True))
        if cfg.debug:
            print('lexed_command:  ', end='')
            pp(lexed_command)
            sys.stdout.flush()
        # Always assume it is a shell command
        # re_shellop = re.compile(r'<>;()+-*/^=!'
        # shell_command = re_shellop.match(lexed_command) ...
        # if not shell_command: ...
        #     command = lexed_command.pop(0) ...
        #     try: ...
        #         cfg.command = local.get(command) ...
        #         cfg.argv = lexed_command ...
        #     except BaseException: ...
        #         shell_command = True ...
        # if shell_command: ...
        cfg.command = local.get('bash', 'sh')
        cfg.argv = ['-c', '--', cfg.command_string]

    if not cfg.command:
        if 'SHELL' in os.environ:
            command = os.environ['SHELL']
            try:
                cfg.command = local.get(command)
                cfg.argv = ['-c', '--', cfg.command_string]
            except BaseException:
                pass

    if not cfg.command:
        cfg.command = local.get('bash', 'sh')
        cfg.argv = ['-c', '--', cfg.command_string]
        
    if cfg.debug:
        print('')
        print('command:  ', end='')
        pp(cfg.command)
        print('')
        print("cfg.argv:  '%s'" % ("' '".join(cfg.argv)))
        print('')
        sys.stdout.flush()

    return cfg

# ------------------------------------------------------------------------------

# Derived directly from https://docs.python.org/3.2/library/pty.html.  Only
# minor changes made to adapt to argument handling and program configuration.


def perform(cfg):

    file_info = ''

    if not cfg.quiet:
        if cfg.filename:
            file_info = f", file is {cfg.filename}"
        print(f'Script started{file_info}')
        sys.stdout.flush()
        if cfg.filename:
            with open(cfg.filename, cfg.mode) as f:
                f.write(('Script started at %s\n' % time.asctime()).encode())
            cfg.mode = 'ab'

    if cfg.show:
        print(f'+ {cfg.command_string}')
        sys.stdout.flush()
        if cfg.filename:
            with open(cfg.filename, cfg.mode) as f:
                f.write(f'+ {cfg.command_string}\n'.encode())
            cfg.mode = 'ab'

    try:
        chain = cfg.command[cfg.argv]
        # Time of day ?
        if cfg.args['--wallclock']:
            chain |= ttee['-uxc']
        # Elapsed time ?
        if cfg.args['--time']:
            chain |= ttee['-uxt']
        append = cfg.mode != 'w'
        outputs = [cfg.filename] if cfg.filename else []
        chain & MULTIPLEX(append=append, outputs=outputs, keep=False)
        # , buffered=False)
    except ProcessExecutionError as e:
        print(e.stdout)
        print(e.stderr)
        sys.stdout.flush()
        return e.retcode

    if not cfg.quiet:
        # script.write(('Script done at %s\n' % time.asctime()).encode())
        if cfg.filename:
            with open(cfg.filename, 'ab') as f:
                f.write(('Script done on %s\n' % time.asctime()).encode())
        print(f'Script done{file_info}')
        sys.stdout.flush()

    return 0


# ------------------------------------------------------------------------------

if __name__ == '__main__':
    exit(main(sys.argv))

# ------------------------------------------------------------------------------
