#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
usage: log [options] <log-file> <command> [ <argv> ... ]

Log <command>'s output to <log-file> and STDOUT.

Create the logfile starting with the command line to be executed.

After the command has completed, the <log-file> is striped of ANSI
and other non-text controls leaving text easily worked with text
tools (grep, sed, emacs, vi).  Specify '--raw' to retain the
non-text controls in <log-file>.  Alternarively, specify
'--keep-raw <raw-file>' to get text only in <log-file> and
retain the raw outout in <raw-file>.  This is often done to
permit more meaningfil perusal of logs containing ANSI colors
highlighting points of interest or error conditions.

Positional arguments :
  <log-file>     destination for <command>'s STDOUT and STDERR
  <command>      command to execute (if '-', read from STDIN).

Optional arguments :
  -a, --append   If <log-file> already exists, append to it.
  -x, --no-show  Do not print or log the command line.
  -q, --quiet    Quiet script meta output (command still shown).
  -v, --verbose  Show additional details.
  -d, --debug    Show debugging details.
  -h, --help     Show this help message and exit.
  -V, --version  Show program version and exit.

  -r, --raw      Do not strip ANSI and other non-text controls from
                 <log-file>.

  --raw-file <raw-file>
                 Retain unfiltered output in <log-raw>.  Implies '--raw'.

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

from prettyprinter import cpprint as pp
from logtool import __version__
import sys
import os

from docopt import docopt

# NOTE:  CYGWIN primary broken /bin/script in a recent (late '18) release of
#        util-linux removed it (albiet temporarily).  I had to track down an
#        old release of util-linix to get my personal tools working.
from plumbum import RETCODE
from plumbum.commands.processes import ProcessExecutionError
from plumbum.cmd import raw_to_text

pscript = False
# from logtool import pscript

if not pscript:
    from plumbum.cmd import script

# from logtool.fgx import FGX

# ------------------------------------------------------------------------------

# As setuptools' entry point passes nothing, argv must default to sys.argv main
# to work.  Do not use sys.argv inside main since that would break unit tests.

def main(argv=sys.argv):

    return perform(configure(parse_arguments(argv[1:])))

# ------------------------------------------------------------------------------


def perform(cfg):

    if cfg.command == '-':
        if cfg.argv:
            print("log:  no arguments permitted after '-' (read from STDIN).")
            exit(1)
        cfg.command = '/bin/cat'
        # cfg.argv = ['>', '/dev/null'] # Prevent line duplication
        cfg.argv = []

    command_line = ' '.join([cfg.command] + cfg.argv)

    argv = [
        '--return',
        '--flush',
        '--command',
        'echo ; %s ; status=$? ; echo ; exit ${status}' %
        (command_line),
        cfg.logfile]

    if cfg.debug and pscript:
        argv.insert(0, '--debug')     # only if python verison of script
    elif cfg.quiet:
        argv.insert(0, '--quiet')
    elif cfg.verbose and pscript:
        argv.insert(0, '--verbose')   # only if python verison of script
    if cfg.show or cfg.append:
        argv.insert(0, '--append')    # applies to script

    if cfg.show:
        if cfg.verbose:
            print("+ script '{}'".format("' '".join(argv)))
        else:
            print("+ " + command_line)
        with open(cfg.logfile, cfg.mode) as f:
            print(f"+ {command_line}\n", file=f)
        sys.stdout.flush()

    # DEBUG: print ( "+ script '{}'".format ( "' '".join(argv) ))
    # DEBUG: sys.stdout.flush()

    try:

        # retcode = pscript.main ( argv )
        chain = script[argv]
        retcode = script[argv] & RETCODE(FG=True)
        if cfg.debug:
            print('log:  retcode = {}'.format(str(retcode)))
        if not cfg.raw :
            if cfg.verbose:
                print('-- converting raw output to text using raw-to-text')
            raw_file = cfg.logfile + '.raw'
            txt_file = cfg.logfile + '.txt'
            convert_retcode = ( ( raw_to_text['-'] < cfg.logfile ) > txt_file ) & RETCODE(FG=True)
            if convert_retcode == 0:
                os.rename(cfg.logfile, raw_file)
                os.rename(txt_file, cfg.logfile)
            else :
                print("*** raw to text conversion failed, raw logfile unchanged.")
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
        'argv',
        'append',
        'command',
        'debug',
        'logDir',
        'logfile',
        'mode',
        'quiet',
        'raw',
        'rawfile',
        'show',
        'verbose',
        )

    def __init__(self):
        self.argv = []
        self.append = False
        self.command = None
        self.debug = False
        self.logDir = None
        self.logfile = None
        self.mode = None
        self.quiet = False
        self.raw = False
        self.rawfile = None
        self.show = True
        self.verbose = False

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

    cfg.rawfile = args['--raw-file']

    cfg.raw = args['--raw'] or cfg.rawfile

    cfg.raw = args['--raw']

    cfg.show = not args['--no-show']

    cfg.mode = 'a' if cfg.append else 'w' # only applies to reporting the command

    # print(f": append  = '{cfg.append}'")
    # print(f": mode    = '{cfg.mode}'")

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

    args = docopt(__doc__, argv, version=__version__, options_first=True)

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
