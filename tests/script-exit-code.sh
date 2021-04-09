#!/bin/bash

PYTHONPATH=".:${PYTHONPATH}"

script=$( which script )
# script="python3 logtool/pscript.py"

script_file=log/script-output.txt

rm -f ${script_file}

( set -x ; exit-code ${script} --return --command "exit-code touch /root/no-such-file" ${script_file} )

# rm -f ${script_file}

# Expected Output :
# + exit-code /usr/bin/script --return --command 'exit-code touch /root/no-such-file' log/script-output.txt
# Script started, file is log/script-output.txt
# touch: cannot touch '/root/no-such-file': Permission denied
# + exit 1
# Script done, file is log/script-output.txt
# + exit 1
