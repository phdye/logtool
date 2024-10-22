#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Usage:
  pscript [options] <file>

Options:
 -a, --append            Append the output
 -c, --command <command> Run command rather than interactive shell
 -p, --python            Use a Python shell as the terminal command
 -e, --return            Return exit code of the child process
 -v, --verbose           Print additional details
 -q, --quiet             Be quiet -- superceeds verbose
 -d, --debug             Print debugging details -- superceeds quiet
 -V, --version           Output version information and exit
 -h, --help              Display this help and exit
 -t, --time              Prefix each line with elapsed time
 -w, --wallclock         Prefix each line with local time of day
 -f, --flush             run flush after each write (DEFAULT)
"""

#     --force             use output file even when it is a link

# ------------------------------------------------------------------------------

import sys
import os
import time

import shlex

from docopt import docopt

from plumbum import local
from plumbum.commands.processes import ProcessExecutionError

from logtool import __version__

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

    args = docopt(__doc__, argv, version=__version__, options_first=True)

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
    __slots__ = ('args', 'filename', 'append', 'mode', 'command', 'argv',
                 'return_', 'python', 'quiet', 'verbose', 'debug')


def configure(args):

    cfg = ActionConfig()
    cfg.args = args
    cfg.command = None
    cfg.argv = []
    cfg.filename = 'typescript'
    cfg.append = args['--append']
    cfg.return_ = args['--return']
    cfg.debug = args['--debug']
    cfg.quiet = args['--quiet'] if not cfg.debug else False

    # cfg.verbose = ( args['--verbose'] if not cfg.quiet else False ) \
    #               if not cfg.debug else True

    cfg.verbose = cfg.debug or (args['--verbose'] if not cfg.quiet else False)

    if args['<file>']:
        cfg.filename = args['<file>']

    cfg.mode = 'ab' if cfg.append else 'wb'

    # option -p: use a Python shell as the terminal command

    if args['--python']:

        cfg.command = local.get(sys.executable)

    elif args['--command']:

        command_string = args['--command']
        lexed_command = list(
            shlex.shlex(
                command_string,
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
        cfg.argv = ['-c', '--', command_string]

    if not cfg.command:
        if 'SHELL' in os.environ:
            command = os.environ['SHELL']
            try:
                cfg.command = local.get(command)
                cfg.argv = ['-c', '--', command_string]
            except BaseException:
                pass

    if not cfg.command:
        cfg.command = local.get('bash', 'sh')
        cfg.argv = ['-c', '--', command_string]
        
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

    if not cfg.quiet:
        sys.stdout.write(f"Script started, output log file is '{cfg.filename}'.\n")
        sys.stdout.flush()
        with open(cfg.filename, cfg.mode) as f:
            f.write(('Script started on %s\n' % time.asctime()).encode())

    retcode = 0
    result = 'done'
    try:
        chain = cfg.command[cfg.argv]
        # Elapsed time ?
        if cfg.args['--time']:
            chain |= ttee['-uxt']
        # Time of day ?
        if cfg.args['--wallclock']:
            chain |= ttee['-uxc']
        outputs = [cfg.filename] if cfg.filename else []
        chain & MULTIPLEX(append=True, binary=binary, keep=False, outputs=outputs])
    except ProcessExecutionError as e:
        print(f"[stdout]\n{e.stdout}\n- - - - -")
        print(f"[stderr]\n{e.stdout}\n- - - - -")
        sys.stdout.flush()
        retcode = e.retcode
        result = 'error'

    if not cfg.quiet:
        with open(cfg.filename, 'a') as f:
            f.write((f'Script {result} on %s\n' % time.asctime()))
        sys.stdout.write(f'Script {result}, file is %s\n' % cfg.filename)
        sys.stdout.flush()

    return retcode


# ------------------------------------------------------------------------------

if __name__ == '__main__':
    exit(main(sys.argv))

# ------------------------------------------------------------------------------
