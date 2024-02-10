import unittest
import tempfile
import os
import shutil
from pathlib import Path
from datetime import datetime

from plumbum import local, RETCODE

from tests.common import LogTool_TestCase

#------------------------------------------------------------------------------

tmp_dir_obj = tempfile.TemporaryDirectory()
tmp_dir = Path ( tmp_dir_obj.name )

writable_tmp_dir = os.access( tmp_dir, os.W_OK )

def slurp(file, raw = False):
    with open(file, "r", newline=('' if raw else None)) as f:
        contents = f.read()
    return contents
    
def get_files(startpath):
    collected = [ ]
    for root, dirs, files in os.walk(startpath):
        dir = root # [len(startpath)]
        for file in files :            
            collected.append ( os.path.join ( dir, file ) )
    return collected

#------------------------------------------------------------------------------

class Test_Case ( LogTool_TestCase ) :

    # Verify symlinks
    # Caveat -- won't work if too close to midnight such that 'logts' runs before
    # midnight and verify occurs after midnight.

    # <b>/latest.txt => <date>/latest.txt , etc.
    # <b>/utmost.dat -> <date>/utmost.dat , etc.

    def verify_link ( self, dir, subdir, link_name, target_name ) :

        link = dir / link_name

        self.files_expected.append( str(link) )

        self.assertTrue(os.path.lexists(link), f"Symlink '{link}' is missing")
        self.assertTrue(os.path.islink(link), f"Symlink '{link}' is invalid.  It is not a symlink.")

        target = Path ( os.readlink( link ) )

        self.assertEqual ( len(target.parts), 2,
                           f"Symlink '{link}', expected target to have 2 parts <subdir>/<file> but target is '{target}'")

        self.assertEqual ( target.parts[0], subdir,
                           f"Symlink '{link}', expected target subdir '{subdir}, found '{target.parts[0]}'")
        self.assertEqual ( target.parts[1], target_name,
                           f"Symlink '{link}', expected target file '{target_name}, found '{target.parts[1]}'")

    #--------------------------------------------------------------------------

    def verify_file ( self, what, dir, name ) :
        file = dir / name
        self.files_expected.append( str(file) )
        self.assertTrue(os.path.exists(file), f"{what} file '{file}' does not exist")
        self.assertTrue(os.path.isfile(file), f"{what} file '{file}' is not a regular file")

    #--------------------------------------------------------------------------

    @unittest.skipUnless ( writable_tmp_dir, f"temporary dir '{tmp_dir.name}' is not writable" )
    def test_logts ( self ) :

        program = 'echo'
        message = "a b c"
        retcode = local['scripts/logts'][ '-b', tmp_dir, 'echo', message ] & RETCODE
        self.assertEqual ( retcode, 0 )

        record = True
        if record :
            dest = Path("log/record/ts")
            dest.mkdir(parents=True, exist_ok=True)

        #----------------------------------------------------------------------

        self.files_expected = [ ]

        files_found = sorted ( get_files ( tmp_dir ) )

        # Save details for manual analyis
        if record :
            with (dest / 'files-found').open("w") as f :
                f.write(f"files : {len(files_found)}\n")
                for file in files_found :
                    f.write(f"{file}\n")
                    if os.path.islink(file) :
                        f.write(f"  link target = {os.readlink(file)}\n")

        #----------------------------------------------------------------------

        utmost_name = 'utmost.dat'
        latest_name = 'latest.txt'

        date = datetime.today().strftime('%Y-%m-%d')
        
        self.verify_link ( tmp_dir, date, utmost_name, utmost_name )
        self.verify_link ( tmp_dir, date, latest_name, latest_name )

        #----------------------------------------------------------------------

        date_dir = tmp_dir / date

        timestamps = list(date_dir.glob('??-??-??'))

        self.assertEqual(len(timestamps), 1,
                               f"In {date_dir.name}, expected 1 timestamp, but found {len(timestamps)}")

        time = timestamps[0].parts[-1]

        if record :
            with (dest / 'links').open("w") as f :
                f.write("\n".join([ str(x) for x in timestamps]) + "\n")
                f.write(str(date_dir) + "\n")
                f.write(time + "\n")

        #----------------------------------------------------------------------

        raw_name = 'raw.dat'
        text_name = 'out.txt'

        self.verify_link ( date_dir, time, utmost_name, raw_name )
        self.verify_link ( date_dir, time, latest_name, text_name )
        
        timestamp_dir = date_dir / time

        self.verify_file ( "Raw", timestamp_dir, raw_name )
        self.verify_file ( "Text", timestamp_dir, text_name )
        
        #----------------------------------------------------------------------

        self.files_expected = sorted(self.files_expected)

        self.assertListEqual ( files_found, self.files_expected,
                               f"Set of files found does not match expected" )

        #----------------------------------------------------------------------

        # Verify the raw file contents

        utmost_file = tmp_dir / utmost_name
        contents = slurp( utmost_file, raw = True )
        lines = contents.split('\n')
        lines = lines[1:-2]
        contents = "\n".join(lines) + "\n"

        self.assertEqual ( contents, f"\r\n{message}\r\n\r\n\n" )

        #----------------------------------------------------------------------

        # Verify the text file contents

        latest_file = tmp_dir / latest_name
        contents = slurp( latest_file, raw = True )
        lines = contents.split('\n')
        lines = lines[1:-2]
        contents = "\n".join(lines) + "\n"

        # self.assertEqual ( contents, f"\n{message}\n\n\n" )
        self.assertEqual ( body, f"+ {program} {message}\n\n{message}\n\n\n" )

        #----------------------------------------------------------------------

        # Save details for manual analyis

        if record :

            with (dest / 'files-expected').open("w") as f :
                f.write ( "\n".join(self.files_expected) + "\n" )

            with (dest / 'output.txt').open("w") as f :
                f.write(f"file:  {latest_file}\n")
                f.write(f"lines: {len(lines)}\n")
                f.write ( contents )

    def test_writable_tmp_dir ( self ) :
        self.assertTrue ( writable_tmp_dir )

    #--------------------------------------------------------------------------

    # @unittest.skipUnless ( writable_tmp_dir, f"temporary dir '{tmp_dir.name}' is not writable" )
    def SKIP_test_logts ( self ) :
        message = "a b c"
        retcode = local['scripts/logts'][ '-b', tmp_dir.name, 'echo', message ] & RETCODE
        self.assertEqual ( retcode, 0 )

        files = get_files ( tmp_dir.name )
        latest = files[0] # Should be <tmpdir>/latest.txt

        self.assertEqual ( file, os.path.join( tmp_dir.name, 'latest.txt' ) )

        Path("log/test/ts").mkdir(parents=True, exist_ok=True)

        with open("log/test/ts/files.txt", "w") as f :
            f.write(f"files : {len(files)}\n")
            # f.write(f"bytes : {len(contents)}\n")
            f.write("\n".join(files) + "\n")

        contents = slurp(file)
        lines = contents.split('\n')
        lines = lines[1:-2]
        contents = "\n".join(lines) + "\n"

        with open("log/test/ts/output.txt", "w") as f :
            f.write(f"file:  {file}\n")
            f.write(f"lines: {len(lines)}\n")
            f.write ( contents )
        
        self.assertEqual ( contents, f"\n{message}\n\n\n" )

#------------------------------------------------------------------------------
