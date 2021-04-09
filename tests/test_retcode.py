import unittest

from plumbum import local
from plumbum import local, RETCODE

class Test_Plumbum_RetCode ( unittest.TestCase ) :

    def test_background ( self ) :
        # Returns 1, since target cannot be touched
        retcode = local['touch']['/root/test'] & RETCODE
        self.assertEqual ( retcode, 1 )

    def test_background ( self ) :
        # Returns 1, since target cannot be touched
        retcode = local['touch']['/root/test'] & RETCODE(FG=True)
        self.assertEqual ( retcode, 1 )

