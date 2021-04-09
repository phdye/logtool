import unittest

from plumbum import local
from plumbum import local, RETCODE

class Test_Plumbum_RetCode ( unittest.TestCase ) :

    def test_background ( self ) :
        # Returns 1, since target cannot be touched
        retcode = local['touch']['/root/test'] & RETCODE
        self.assertEqual ( retcode, 1 )

    def test_background ( self ) :
        # Returns 1, since target cannot be touched as parents do not exist
        retcode = local['touch']['/foo/bar/baz'] & RETCODE(FG=True)
        self.assertEqual ( retcode, 1 )

