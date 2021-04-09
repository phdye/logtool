#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Usage:
 script [options] [ <file> ]


Options:
 -a, --append            append the output
 -c, --command <command> run command rather than interactive shell
 -p, --python            Use a Python shell as the terminal command
 -e, --return            return exit code of the child process
 -v, --verbose           print additional details
 -q, --quiet             be quiet -- superceeds verbose
 -d, --debug             print debugging details -- superceeds quiet
 -V, --version           output version information and exit
 -h, --help              display this help and exit

"""

# -f, --flush             run flush after each write
#     --force             use output file even when it is a link
# -t, --timing[=<file>]   output timing data to stderr (or to FILE)

# ------------------------------------------------------------------------------

import sys
import os
import time

import shlex

from docopt import docopt

from plumbum import local
from plumbum.commands.processes import ProcessExecutionError

from logtool import version

from logtool.multiplex import MULTIPLEX

from prettyprinter import cpprint as pp

# ------------------------------------------------------------------------------

# As setuptools' entry point passes nothing, argv must default to sys.argv main
# to work.  Do not use sys.argv inside main since that would break unit tests.


def main(argv=sys.argv):

    return perform(configure(parse_arguments(argv[1:])))

# ------------------------------------------------------------------------------


def parse_arguments(argv):

    if '--debug' in argv:
        print('')
        print("raw argv:  '%s'" % ("' '".join(argv)))
        print('')

    args = docopt(__doc__, argv, version=version, options_first=True)

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
        shell_command = ';' in lexed_command
        if not shell_command:
            command = lexed_command.pop(0)
            try:
                cfg.command = local.get(command)
                cfg.argv = lexed_command
            except BaseException:
                shell_command = True
        if shell_command:
            cfg.command = local.get('bash', 'sh')
            cfg.argv = ['-c', command_string]

    if not cfg.command:
        if 'SHELL' in os.environ:
            command = os.environ['SHELL']
            try:
                cfg.command = local.get(command)
            except BaseException:
                cfg.command = local.get('bash', 'sh')

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

    # script = open ( cfg.filename, cfg.mode )

    # def read(fd):
    #     data = os.read(fd, 1024)
    #     script.write(data)
    #     return data

    if not cfg.quiet:
        sys.stdout.write('Script started, file is %s\n' % cfg.filename)
        sys.stdout.flush()
        # script.write(('Script started on %s\n' % time.asctime()).encode())
        with open(cfg.filename, cfg.mode) as f:
            f.write(('Script started on %s\n' % time.asctime()).encode())

    # pty.spawn ( cfg.shell, read )

    try:
        cfg.command[cfg.argv] & MULTIPLEX(keep=False, outputs=[cfg.filename])
        return 0
    except ProcessExecutionError as e:
        print(e.stdout)
        print(e.stderr)
        sys.stdout.flush()
        return e.retcode

    if not cfg.quiet:
        # script.write(('Script done on %s\n' % time.asctime()).encode())
        with open(cfg.filename, 'a') as f:
            f.write(('Script done on %s\n' % time.asctime()).encode())
        sys.stdout.write('Script done, file is %s\n' % cfg.filename)
        sys.stdout.flush()

    return 0


# ------------------------------------------------------------------------------

if __name__ == '__main__':
    exit(main(sys.argv))

# ------------------------------------------------------------------------------
