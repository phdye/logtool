import unittest
import tempfile
import os

from tests.common import LogTool_TestCase

#------------------------------------------------------------------------------

class Test_Case ( LogTool_TestCase ) :
    
    def test_log_text_default ( self ) :
        self.log_common ( 'log' )

    def test_log_text_explicit ( self ) :
        self.log_common ( 'log', raw = False )

    def test_log_raw ( self ) :
        self.log_common ( 'log', raw = True )

    def X_test_log_stdin ( self ) :
        ( program, message, body ) = self.log_common('txt')
        self.assertEqual ( body, f"+ {program} {message}\n\n{message}\n\n\n" )

#
