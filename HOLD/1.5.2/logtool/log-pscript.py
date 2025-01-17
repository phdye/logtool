#!/usr/bin/env python3

"""
usage: log [options] <log-file> <command> [ <argv> ... ]

Log <command>'s output to <log-file> and STDOUT.

Create the logfile starting with the command line to be executed.

Positional arguments :
  <log-file>     destination for <command>'s STDOUT and STDERR
  <command>      command to execute

Optional arguments :
  -a, --append   If <log-file> already exists, append to it.
  -n, --no-show  Do not print or log the command line.
  -q, --quiet    Quiet script meta output.
  -v, --verbose  Show additional details.
  -d, --debug    Show debugging details.
  -h, --help     Show this help message and exit.
  -V, --version  Show program version and exit.

NOT YET IMPLEMENTED :
X -s, --silent   Silence STDOUT.  Output only to <log-file> (-q -n).
"""

# _x_script_usage = """
# Usage:
#  {,p}script [options] [file]
#
# Options:
# ✓-a, --append            append the output
# ✓-c, --command <command> run command rather than interactive shell
# ✓-e, --return            return exit code of the child process
# ✓-q, --quiet             be quiet
#
# docopt provided :
#  -V, --version           output version information and exit
#  -h, --help              display this help and exit
#
# NOT IMPLEMENTED YET :
#  -f, --flush             run flush after each write
#      --force             use output file even when it is a link
#  -t, --timing[=<file>]   output timing data to stderr (or to FILE)
# """

import sys
import os

from docopt import docopt

# NOTE:  CYGWIN primary broken /bin/script in a recent (late '18) release of
#        util-linux removed it (albiet temporarily).  I had to track down an
#        old release of util-linix to get my personal tools working.

# from plumbum import RETCODE
from plumbum.commands.processes import ProcessExecutionError
# from plumbum.cmd import script

from logtool import version

from logtool import pscript

# from logtool.fgx import FGX

from prettyprinter import cpprint as pp

# ------------------------------------------------------------------------------

# As setuptools' entry point passes nothing, argv must default to sys.argv main
# to work.  Do not use sys.argv inside main since that would break unit tests.


def main(argv=sys.argv):

    return perform(configure(parse_arguments(argv[1:])))

# ------------------------------------------------------------------------------


def perform(cfg):

    command_line = ' '.join([cfg.command] + cfg.argv)
    cfg.argv = [
        '--return',
        '--append',
        '--command',
        'echo ; %s ; status=$? ; echo ; exit ${status}' %
        (command_line),
        cfg.logfile]

    if cfg.debug:
        cfg.argv.insert(0, '--debug')
    elif cfg.quiet:
        cfg.argv.insert(0, '--quiet')
    elif cfg.verbose:
        cfg.argv.insert(0, '--verbose')
    if cfg.append:
        cfg.argv.insert(0, '--append')

    if cfg.show:
        if cfg.verbose:
            print("+ script '{}'".format("' '".join(cfg.argv)))
        else:
            print("+ " + command_line)
        with open(cfg.logfile, cfg.mode) as f:
            print('+ ' + command_line, file=f)
        sys.stdout.flush()

    try:

        retcode = pscript.main(cfg.argv)
        if cfg.debug:
            print('log:  retcode = {}'.format(str(retcode)))
        return retcode

    except ProcessExecutionError as e:

        sys.stdout.flush()
        print('log:  ProcessExecutionError')
        print('log:  exception retcode = %s' % (str(e.retcode)))
        print('log:  exception stdout')
        print(e.stdout)
        print('log:  exception stderr')
        print(e.stderr)
        print('log:  done')
        print('')
        sys.stdout.flush()
        return e.retcode

# ------------------------------------------------------------------------------


class ActionConfig (object):

    __slots__ = (
        'logDir',
        'logfile',
        'command',
        'append',
        'mode',
        'argv',
        'debug',
        'quiet',
        'verbose',
        'show')

    def __init__(self):
        self.logDir = None
        self.logfile = None
        self.append = False
        self.mode = 'w'
        self.command = None
        self.argv = []
        self.debug = False
        self.verbose = False
        self.quiet = False
        self.show = True

# ------------------------------------------------------------------------------


def configure(args):

    cfg = ActionConfig()

    cfg.debug = args['--debug']

    # debug overrides quiet
    cfg.quiet = args['--quiet'] if not cfg.debug else False

    # quiet overrides verbose
    cfg.verbose = args['--verbose'] if not cfg.quiet else False

    cfg.logfile = args['<log-file>']

    cfg.append = args['--append']

    cfg.mode = 'a' if cfg.append else 'w'

    cfg.logDir = os.path.dirname(cfg.logfile) or '.'
    if not os.path.isdir(cfg.logDir):
        raise ValueError(
            "Logfile directory does not exist:  '{}'".format(
                cfg.logDir))

    cfg.command = args['<command>']
    cfg.argv = args['<argv>']

    return cfg

# ------------------------------------------------------------------------------


def parse_arguments(argv):

    args = docopt(__doc__, argv, version=version, options_first=True)

    if args['--verbose']:
        print("+ log '" + "' '".join(sys.argv) + "'")
        print('')
        print('parsed :')
        pp(args)
        print('')

    return args

# ------------------------------------------------------------------------------


if __name__ == '__main__':
    exit(main(sys.argv))

# ------------------------------------------------------------------------------
