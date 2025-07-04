import sys
import os
import tempfile
import shutil
import unittest
from contextlib import _RedirectStream
from pathlib import Path

import pytest

from logtool.vendor.miniplumbum import local, RETCODE, BG
from prettyprinter import cpprint as pp

code_snippet_ansi = 'tests/code-snippet.ansi'
code_snippet_text = 'tests/code-snippet.txt'

class redirect_stdin(_RedirectStream):
    _stream = "stdin"

def empty_pipe():
    read_fd, write_fd = os.pipe()
    os.close(write_fd)
    return os.fdopen(read_fd, 'r')

@pytest.mark.usefixtures("class_setup")
class LogTool_TestCase ( unittest.TestCase ):

    def setUp ( self ) :
        self.logtool_init_for_session()

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

    def X_log_common ( self, command, raw = False ) :
        print(f"test {command} : raw = {raw}")
        
    def log_common ( self, command, raw = False ) :

        if self.retain :
            self.tmp_dir = self.tmp_dir / command / f"raw={raw}"
            if self.tmp_dir.exists() :
                shutil.rmtree(self.tmp_dir)
            self.makedirs( self.tmp_dir )
            
        if self.record :
            extension = 'raw' if raw else 'txt'
            self.recordName = 'ts' if command == 'logts' else command
            self.commonDir = Path(os.path.join ( self.record_base, self.recordName, 'common' ))
            shutil.rmtree( self.commonDir, ignore_errors=True)
            self.makedirs( self.commonDir )

        program = 'cat'
        file_name = "tests/code-snippet.ansi"
        if command == 'log':
            tmp_file_obj = tempfile.TemporaryFile(dir = self.tmp_dir)
            out_file = tmp_file_obj.name
            # WEIRD:  on alpine, out_file is merely an integer ?
            # Perhaps a musl issue ?
            if not isinstance(out_file, str):
                out_file = str(tmp_file_obj)
            raw_file = out_file if raw else out_file + '.raw' 
            args = [ out_file, program, file_name ]
            if raw :
                args.insert(0, '--raw')
        elif command == 'logts':
            if raw :
                raise ValueError(f"raw=True is not applicable when command ='{command}'") 
            # yes, a bit contrived to keep as much in common as feasible
            txt_file = self.tmp_dir / 'latest.txt'
            raw_file = self.tmp_dir / 'utmost.dat'
            out_file = raw_file if raw else txt_file
            args = [ '-b', str(self.tmp_dir), program, file_name ]
        else:
            raise ValueError(f"Unrecognized command name '{command}' -- please resolve.") 

        if self.record :
            with (self.commonDir / 'command' ).open('w') as f :
                print(f"+ {command} " + " ".join(args), file=f)

        command = local[f"scripts/{command}-runner"][args]

        if self.record :
            listing = self.commonDir / 'listing'
            with listing.open('w') as f:
                f.write(str(command)+"\n\n")

        (retcode, stdout, stderr) = command.run(retcode=None)

        if retcode != 0:
            print("\n***\n*** Error Occurred\n***")
            print(f"[stdout]\n{stdout}\n")
            print(f"[stderr]\n{stderr}\n")
            print(f"[error]\nexit code = {retcode}\n")
            
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
        self.assertEqual ( lines[0], f"+ {program} {file_name}",
                           "Line 1 should be the command'" )
        # Form 1 : Script started, file is <log-file>
        # Form 2 : Script started on 2021-03-20 17:51:07-04:00 [TERM="screen" TTY="/dev/pty9" COLUMNS="131" LINES="39"]
        self.assertRegex ( lines[2], 'Script started',
                           "Line 3 should be the script of the 'script' recording.")

        # Form 1 : Script done, file is <log-file>
        # Form 2 : Script done on 2021-03-20 17:51:07-04:00 [COMMAND_EXIT_CODE="0"]
        # self.assertRegex ( lines[-2], 'Script done',
        #                   "The second to last line should be marked as the end of the 'script' recording.")
        self.assertRegex ( lines[-2], 'Script done',
                           "The second to last line should be marked as the end of the 'script' recording.")
        self.assertEqual ( lines[-1], '', "The last line should be blank." )
        # For the comparision, ommit the 'Script ...' lines and their following blank lines.
        lines = lines[0:2] + lines[4:-2]

        self.assertEqual( lines[0], f"+ {program} {file_name}")
        self.assertEqual( lines[1], "")
        self.assertEqual( lines[-1], "")

        lines = lines[2:-1]
        if False:
            print("[body]")
            for line in lines:
                sys.stdout.write(line+'\n')
            print("- - - - -")
            del lines[1]
            del lines[1]
        body = '\n'.join(lines) + '\n'

        # print(f"[body]\n{body}\n= = = = =")

        if raw :
            snippet_body = slurp(code_snippet_ansi)
        else :
            snippet_body = slurp(code_snippet_text)

        if False:
            lines = snippet_body.split('\n')
            print("[snippet]")
            for line in lines:
                sys.stdout.write(line+'\n')
            print("- - - - -")
            # del lines[1]
            # del lines[1]
            snippet_body = '\n'.join(lines)

        self.assertEqual ( body, snippet_body )

#------------------------------------------------------------------------------

def slurp(file, raw = False):
    with open(file, "r") as f:
        # , newline=('' if raw else None)) as f:
        # , newline=('\r\n' if raw else None)) as f:
        contents = f.read()
    return contents

#------------------------------------------------------------------------------
