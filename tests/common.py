import sys	# only for early exit when debuging
import os
import tempfile
import shutil
import unittest
import pytest

from pathlib import Path

from plumbum import local, RETCODE, BG

#------------------------------------------------------------------------------

@pytest.fixture()
def _record(pytestconfig):
    # return pytestconfig.getoption("record")
    _x_record = pytestconfig.getoption("record")
    with open('x-record', 'w') as f :
        print(f"record = {record}")
    return _x_record

@pytest.fixture()
def _retain(pytestconfig):
    return pytestconfig.getoption("retain")

#------------------------------------------------------------------------------

class LogTool_TestCase ( unittest.TestCase ):

    def setUp ( self ) :

        if _retain :
            self.tmp_dir = Path('log/retain')
            shutil.rmtree(self.tmp_dir, ignore_errors=True)
            self.makedirs(self.tmp_dir)
        else :
            self.tmp_dir_obj = tempfile.TemporaryDirectory()
            self.tmp_dir = Path ( self.tmp_dir_obj.name )
        self.assert_OS_Access ( self.tmp_dir, os.R_OK | os.W_OK | os.X_OK )
        self.record = _record
        if self.record :
            self.recordBase = os.path.join('log', 'record')
            self.makedirs ( self.recordBase )

    def assert_OS_Path_Exists ( self, target ) :
        self.assertTrue ( os.path.exists ( target ),
                          f"Expected path '{target}' does not exist.")

    def assert_OS_Access ( self, target, access ) :
        self.assert_OS_Path_Exists ( target )
        self.assertTrue ( os.access ( target, 0 ),
                          f"Existing '{target}' is not {access} accessible.")

    def makedirs ( self, path, mode = 0o770, exist_ok = True ):
        os.makedirs ( path, mode, exist_ok = exist_ok )
        self.assert_OS_Access ( path, os.R_OK | os.W_OK | os.X_OK )
        
    #--------------------------------------------------------------------------

    # command			: log vs logts
    # record destination	: 'log' vs 'ts'	  		-- derivable
    # file extenstion, log only	: 'txt' vs 'raw'		-- derivable
    # output destination	: log : a file name known
    #				: ts  : a file name constructed -- derivable
    
    def log_common ( self, command, raw = False ) :

        if self.record :
            extension = 'raw' if raw else 'txt'
            self.recordName = 'ts' if command == 'logts' else command
            self.commonDir = Path(os.path.join ( self.recordBase, self.recordName, 'common' ))
            shutil.rmtree( self.commonDir, ignore_errors=True)
            self.makedirs( self.commonDir )

        program = 'echo'
        message = "a b c"
        if command == 'log':
            tmp_file_obj = tempfile.TemporaryFile(dir = self.tmp_dir)
            out_file = tmp_file_obj.name
            raw_file = out_file if raw else out_file + '.raw' 
            args = [ out_file, program, message ]
            if raw :
                args.insert(0, '--raw')
        else :
            if raw :
                raise ValueError(f"raw=True is not applicable when command ='{command}'") 
            # yes, a bit contrived to keep as much in common as feasible
            txt_file = self.tmp_dir / 'latest.txt'
            raw_file = self.tmp_dir / 'utmost.dat'
            out_file = raw_file if raw else txt_file
            args = [ '-b', str(self.tmp_dir), program, message ]

        if self.record :
            with (self.commonDir / 'command' ).open('w') as f :
                print(f"+ {command} " + " ".join(args), file=f)

        command = local[f"scripts/{command}"][args]

        if self.record :
            listing = self.commonDir / 'listing'
            with listing.open('w') as f:
                f.write(str(command)+"\n\n")

        retcode = command & RETCODE

        if self.record :
            with listing.open('a') as f:
                f.write(f"+ ls {str(self.tmp_dir)}\n\n")
                ( local['ls'][str(self.tmp_dir)] >> str(listing) ) & BG

        contents = slurp(out_file, raw=True)
        lines = contents.split('\n')

        if self.record :
            with (self.commonDir / f"output.{extension}").open('w') as f :
                f.write(f"lines : {len(lines)}\n")
                f.write(f"bytes : {len(contents)}\n")
                f.write(contents)

        self.assertEqual ( retcode, 0 )
        self.assertEqual ( lines[0], f"+ {program} {message}",
                           "Line 1 should be the command'" )
        # Form 1 : Script started, file is <log-file>
        # Form 2 : Script started on 2021-03-20 17:51:07-04:00 [TERM="screen" TTY="/dev/pty9" COLUMNS="131" LINES="39"]
        self.assertRegex ( lines[2], 'Script started',
                           "Line 3 should be the script of the 'script' recording.")
        
        # Form 1 : Script done, file is <log-file>
        # Form 2 : Script done on 2021-03-20 17:51:07-04:00 [COMMAND_EXIT_CODE="0"]
        self.assertRegex ( lines[-2], 'Script done',
                           "The second to last line should be marked as the end of the 'script' recording.")
        self.assertRegex ( lines[-2], 'Script done',
                           "The second to last line should be marked as the end of the 'script' recording.")
        self.assertEqual ( lines[-1], '', "The last line should be blank." )
        # For the comparision, ommit the 'Script ...' lines and their following blank lines.
        lines = lines[0:2] + lines[4:-2]

        body = "\n".join(lines) + "\n"
        if raw :
            self.assertEqual ( body, f"+ {program} {message}\n\n{message}\r\n\r\n\n" )
        else :
            self.assertEqual ( body, f"+ {program} {message}\n\n{message}\n\n\n" )
            
        # return ( program, message, "\n".join(lines) + "\n" )

#------------------------------------------------------------------------------

def slurp(file, raw = False):
    with open(file, "r", newline=('' if raw else None)) as f:
        contents = f.read()
    return contents

#------------------------------------------------------------------------------
