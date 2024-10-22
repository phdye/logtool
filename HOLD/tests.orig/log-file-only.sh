#!/bin/bash

PYTHONPATH=".:${PYTHONPATH}"

# log='python logtool/log.py'
log=$( which log )

log_file=foo-bar.log

rm -f ${log_file}

# opt=--verbose
opt=--debug
( set -x ; exit-code ${log} ${opt} ${log_file} "( set -x ; \; exit-code touch ${log_file} )" )
