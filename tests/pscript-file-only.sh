#!/bin/bash

PYTHONPATH=".:${PYTHONPATH}"

# script=$( which script )
script="python logtool/pscript.py"

script_file=log/script-output.txt
touch_file=log/script-touch.txt

rm -f ${script_file} ${touch_file}

command="echo ; ( set -x ; exit-code touch ${touch_file} ) ; status=$? ; echo ; exit ${status}"

opt="--debug"
( set -x ; exit-code ${script} ${opt} --command "${command}" ${script_file} )
