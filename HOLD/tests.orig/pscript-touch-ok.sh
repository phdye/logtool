#!/bin/bash

PYTHONPATH=".:${PYTHONPATH}"

# script=$( which script )
script="python3 logtool/pscript.py"

script_file=log/pscript-output.txt
touch_file=${script_file}

#------------------------------------------------------------------------------

rm -f ${script_file}

( set -x ; ${script} --return --command "( set -x ; touch ${touch_file} )" ${script_file} ) 

exit_code=$?
if [ ${exit_code} -eq 0 ] ; then
    echo "Success:  exit code is 0"
else
    echo "*** Error :  exit code is ${exit_code} -- EXPECTED 0"
fi

# rm -f ${script_file}

#------------------------------------------------------------------------------

# Expected Output :
# + python3 logtool/pscript.py --return --command '( set -x ; touch log/pscript-output.txt )' log/pscript-output.txt
# Script started, file is log/pscript-output.txt
# + touch log/pscript-output.txt
# Success:  exit code is 0
