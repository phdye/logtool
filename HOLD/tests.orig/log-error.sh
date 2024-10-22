#!/bin/bash

PYTHONPATH=".:${PYTHONPATH}"

log='python logtool/log.py'
# log=$( which log )

( set -x ; exit-code ${log} log/err exit-code touch /root/no-such-file )

