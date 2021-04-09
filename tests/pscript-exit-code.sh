#!/bin/bash

PYTHONPATH=".:${PYTHONPATH}"

# script=$( which script )
script="python3 logtool/pscript.py"

script_file=log/pscript-output.txt

rm -f ${script_file}

( set -x ; exit-code ${script} --return --command "exit-code touch /root/no-such-file" ${script_file} ) 

# rm -f ${script_file}

# Expected Output :
# + exit-code python logtool/pscript.py --return --command 'exit-code touch /root/no-such-file' log/pscript-output.txt
# Script started, file is log/pscript-output.txt
# touch: cannot touch '/root/no-such-file': Permission denied
# + exit 1
# Script done, file is log/pscript-output.txt
# + exit 1
