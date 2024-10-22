#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Usage:  logts [options] <command> [ <argv> ... ]

  Log the output of <command> to <base>/<date>/<time>.txt
  and also pipe its output to STDOUT.

Log Destination Options:

  -b <base>, --base <base>  MANDATORY - fatal error if not specified.
                  Place dated log directories under <base>.
                    * dirname(<base>) must exist
                    * basename(<base>) will be created if necessary
                    * <base>/<date> will be created if necessary
                    * output to <base>/<date>/<time>.txt

  -c, --clean     [DEFAULT = True] -- actually, always forced True.
                  Create time directory level to hold raw (vt102, ANSI,
                  color, etc) and clean (simply text) output.
                    * <base>/<date>/<time> will be created
                    * raw output to <base>/<date>/<time>/raw.dat
                    * clean text to <base>/<date>/<time>/out.txt
                  !!!
                  !!! To reenable this option, you must sort out the
                  !!! non-clean code paths in the arrange_the_log_logs
                  !!! and arrange_the_log_links.
                  !!!

  -p <p>, --prefix
                  Prefix the log file with file string <p>.

  --ts <ts>       Use <ts> for the timestamp.  Useful to link multiple
                  stages of a process by an overall starting timestamp.

  --ref <file>    As with '--ts', but use <file>'s last modification
                  time for timestamp, '--ref' superceeds '--ts'.

Log Output Options:

  -t, --time     Prefix each line with elapsed time.

  -w, --wallclock  Prefix each line with local time of day.

  -v, --verbose   Print a bit more detail about the actions being taken.
                  - Superceeded by '--quiet'

  -q, --quiet     Print less, keep quiet.
                  - Superceeds '--verbose', superceeded by '--debug'.

  -d, --debug     Show debugging details.
                  - Superceeds '--quiet'
                  - Implies '--verbose'

  -n, --no-show   Do not print or log the command line.

  -a, --append    If the target log file already exists, append to it
                  -- applicable when '--ts' or '--ref' are specified.

General Options:

  --help          Print this usage informatsion to STDERR and exit.

  --version       Print program version to STDERR and exit.

NOT IMPLEMENTED YET :

X -s, --silent    Print nothing unless an error occurs.

"""

# -------------------------------------------------------------------:----------

from __future__ import print_function

import sys
import os

from time import localtime, strftime
from dataclasses import dataclass

import dateparser

from plumbum import local

from pprint import PrettyPrinter
pp = PrettyPrinter(indent=4).pprint
pp8 = PrettyPrinter(indent=8).pprint

from docopt import docopt

from logtool import __version__, log

# ------------------------------------------------------------------------------

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H-%M-%S"

TS_FORMAT = "%H:%M:%S"

# ------------------------------------------------------------------------------

# As setuptools' entry point passes nothing, argv must default to sys.argv main
# to work.  Do not use sys.argv inside main since that would break unit tests.

def main(argv=sys.argv):

    return perform(configure(parse_arguments(argv[1:])))

# ------------------------------------------------------------------------------

def perform(cfg):

    # print(f"{cfg}")

    command_line = ' '.join([cfg.command] + cfg.argv)

    # Leave 'log' to report the command
    if False : # not cfg.quiet:
        print('')
        print("+ " + command_line)
        print('')
        with open(cfg.log_file, cfg.mode) as f:
            print('+ ' + command_line, file=f)
            print('', file=f)
        sys.stdout.flush()

    # log <log-file> <command> ...

    xfg = log.ActionConfig()
    xfg.debug = cfg.debug
    xfg.verbose = cfg.verbose
    xfg.quiet = cfg.quiet
    xfg.logDir = cfg.log_dir
    xfg.logfile = cfg.log_file
    xfg.mode = 'w' if cfg.quiet else 'a'
    xfg.show = cfg.show
    xfg.command = cfg.command
    xfg.raw = True
    xfg.argv = cfg.argv
    xfg.time = cfg.time
    xfg.wallclock = cfg.wallclock

    try:
        retcode = log.perform(xfg)
        if xfg.debug:
            print('')
            print(
                'log:  retcode = {} (as received by logts)'.format(
                    str(retcode)))
        arrange_the_log_files(cfg)
        return retcode
    except Exception as e:
        if xfg.debug:
            print('logts:  RAISE : retcode = ?')
        print('')
        arrange_the_log_files(cfg)
        raise e

# ------------------------------------------------------------------------------


def arrange_the_log_files(cfg):

    if not os.path.exists(cfg.log_file):
        return False

    link_name = 'latest.txt'
    link_raw = 'utmost.dat'

    if cfg.clean and cfg.raw_name is not None:

        # log-dir : raw-to-text < %raw_file% > %text_file%

        raw_file = cfg.log_file
        cfg.log_file = os.path.join(cfg.log_dir, cfg.text_name)
        rawtotext = local['raw-to-text']
        # ((grep["world"] < sys.stdin) > "tmp.txt")()
        ((rawtotext[""] < raw_file) > cfg.log_file)()
        if not os.path.exists(cfg.log_file):
            raise ValueError("raw to text conversion failed.  Text-only log " +
                             "'%s' does not exist." % (cfg.log_file))
        # Script done, file is log/build/2019-03-30/02-28-52/raw.dat
        # ....... text file is log/build/2019-03-30/02-28-52/out.txt
        if not cfg.quiet:
            print("And the text file is %s" % (cfg.log_file))

        arrange_the_log_links(cfg, cfg.raw_name, link_raw)
        arrange_the_log_links(cfg, cfg.text_name, link_name)

# ------------------------------------------------------------------------------


def arrange_the_log_links(cfg, file_name, link_name):

    if cfg.clean and cfg.raw_name is not None:

        # date-dir : <d>/latest.txt -> <time>/out.txt

        symlink = os.path.join(cfg.log_date_dir, link_name)
        if os.path.lexists(symlink):
            os.unlink(symlink)
        os.symlink(os.path.join(cfg.time_string, file_name), symlink)
        if cfg.verbose:
            print(". created symlink '{}'".format(symlink))

        # date-dir : <d>/utmost.dat -> <time>/raw.dat

        symlink = os.path.join(cfg.log_date_dir, link_name)
        if os.path.lexists(symlink):
            os.unlink(symlink)
        os.symlink(os.path.join(cfg.time_string, file_name), symlink)
        if cfg.verbose:
            print(". created symlink '{}'".format(symlink))

    else:

        # log-dir  ; nothing, it does not exist
        # date-dir : <d>/latest.txt -> <time>.txt
        symlink = os.path.join(cfg.log_date_dir, link_name)
        if os.path.lexists(symlink):
            os.unlink(symlink)
        os.symlink(os.path.join(cfg.time_string, cfg.raw_name), symlink)
        if cfg.verbose:
            print(". created symlink '{}'".format(symlink))

    # log-base : <b>/latest.txt -> <date>/latest.txt
    symlink = os.path.join(cfg.log_base, link_name)
    if os.path.lexists(symlink):
        os.unlink(symlink)
    os.symlink(os.path.join(cfg.date_string, link_name), symlink)
    if not cfg.quiet:
        print(". created symlink '{}'".format(symlink))
        print('')

# ------------------------------------------------------------------------------

@dataclass
class ActionConfig (object):
    log_base : str = None
    log_date_dir : str = None
    log_dir : str = None
    log_name : str = None
    log_file : str = None
    log_prefix : str = None
    append : bool = False
    mode : bool = False
    date_string : str = None
    time_string : str = None
    time_stamp : str = None
    command : str = None
    argv : str = None
    debug : bool = False
    quiet : bool = False
    verbose : bool = False
    show : bool = False
    clean : bool = False
    raw_name : str = None
    text_name : str = None

# ------------------------------------------------------------------------------


def configure(args):

    cfg = ActionConfig()

    cfg.debug = args['--debug']

    # debug overrides quiet
    cfg.quiet = args['--quiet'] if not cfg.debug else False

    # quiet overrides verbose
    cfg.verbose = args['--verbose'] if not cfg.quiet else False

    cfg.show = not args['--no-show']

    cfg.log_base = args['--base']

    if not os.path.isdir(os.path.dirname(cfg.log_base)):
        pass  # error

    # set time_stamp
    if args['--ref'] is not None:
        ts = os.path.getmtime(args['--ref'])
    elif args['--ts'] is not None:
        ts = dateparser.parse(date_string=args['--ts'])
    else:
        ts = None
    cfg.time_stamp = localtime(ts)

    cfg.time_string = strftime(TIME_FORMAT, cfg.time_stamp)

    cfg.log_prefix = args['--prefix'] if args['--prefix'] is not None else ''

    cfg.clean = args['--clean']
    # every lower level will be created if needed
    cfg.date_string = strftime(DATE_FORMAT, cfg.time_stamp)
    cfg.log_dir = [cfg.log_base, cfg.date_string]
    cfg.log_date_dir = os.path.join(* cfg.log_dir)
    if cfg.clean:
        cfg.log_dir = os.path.join(cfg.log_date_dir, cfg.time_string)
        cfg.raw_name = cfg.log_prefix + 'raw.dat'
        cfg.text_name = cfg.log_prefix + 'out.txt'
        cfg.log_name = cfg.raw_name
        os.environ['LOGTS_LOG_DIR'] = cfg.log_dir
    else:
        cfg.log_dir = cfg.log_date_dir
        cfg.log_name = cfg.log_prefix + cfg.time_string + '.txt'

    os.makedirs(cfg.log_dir, exist_ok=True)

    cfg.log_file = os.path.join(cfg.log_dir, cfg.log_name)

    cfg.time = args['--time']

    cfg.wallclock = args['--wallclock']

    cfg.append = args['--append']

    cfg.mode = 'a' if cfg.append else 'w'

    cfg.command = args['<command>']
    cfg.argv = args['<argv>']

    return cfg

# ------------------------------------------------------------------------------

def parse_arguments(argv):

    if False:  # not quiet and verbose : # '--verbose' in argv :
        print("+ [logts] '" + "' '".join(argv) + "'")

    # pp(argv) ; sys.stdout.flush()

    args = docopt(__doc__, argv, version=__version__, options_first=True)

    # pp(args) ; sys.stdout.flush()

    if args['--base'] is None:
        print('')
        print('Error: < base > missing.  '
              + ' Please specify a log file base directory.')
        print('')
        print('Usage:  logts [options] <command> [ <argv> ... ]')
        print('')
        exit(1)

    if args['--debug']:
        print("+ logts '" + "' '".join(argv) + "'")
        print('')
        print('parsed args :')
        pp(args)
        print('')

    args['--clean'] = True  # !!! always true for now

    return args

# ------------------------------------------------------------------------------


if __name__ == '__main__':
    retcode = main(sys.argv)
    if '--debug' in sys.argv:
        print('logts:  retcode = {}'.format(str(retcode)))
    exit(retcode)


# ------------------------------------------------------------------------------
