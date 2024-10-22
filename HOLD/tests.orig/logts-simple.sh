#!/bin/bash

logger='python logtool/logts.py'
# logger=$( which logts )

log_base=log/simple

file=log/foo-bar.baz

rm -f ${file}

PYTHONPATH=".:${PYTHONPATH}"

( set -x ; exit-code ${logger} -b ${log_base} exit-code touch ${file} )

rm -f ${file}

#
