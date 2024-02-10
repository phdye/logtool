import unittest
import tempfile
import os
import shutil
from pathlib import Path
from datetime import datetime

from plumbum import local, RETCODE

from tests.common import LogTool_TestCase

#------------------------------------------------------------------------------

class Test_Case ( LogTool_TestCase ) :

    def test_ts_text_default ( self ) :
        self.log_common ( 'logts', raw = False )

    # fails, '--raw' only applicable to 'log'
    def SKIP_test_ts_raw ( self ) :
        self.log_common ( 'logts', raw = True )

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

#------------------------------------------------------------------------------
