import os
import tempfile
import shutil

from pathlib import Path
from dataclasses import dataclass

import pytest


from prettyprinter import cpprint as pp


def pytest_addoption(parser):
    parser.addoption("--retain", action="store_true", help="retain output files")
    parser.addoption("--record", action="store_true", help="record test stats")

@dataclass
class LogToolTestConfig:
    retain          : bool      = None
    tmp_dir_obj     : object    = None
    tmp_dir_base    : str	= None
    record          : bool      = None
    record_base     : str	= None

@pytest.fixture(scope='session')
def session_setup(pytestconfig):
    
    cfg = LogToolTestConfig()
    cfg.retain = pytestconfig.getoption("--retain")
    cfg.record = pytestconfig.getoption("--record")

    def makedirs ( path, mode = 0o770, exist_ok = True ):
        os.makedirs ( path, mode, exist_ok = exist_ok )

    def assert_OS_Access ( self, target, access ) :
        self.assert_OS_Path_Exists ( target )
        self.assertTrue ( os.access ( target, 0 ),
                          f"Existing '{target}' is not {access} accessible.")

    if cfg.retain :
        cfg.tmp_dir_base = Path(os.path.join('log', 'retain'))
        shutil.rmtree(cfg.tmp_dir_base, ignore_errors=True)
        makedirs(cfg.tmp_dir_base)
    else :
        cfg.tmp_dir_obj = tempfile.TemporaryDirectory()
        cfg.tmp_dir_base = Path ( cfg.tmp_dir_obj.name )

    if cfg.record :
        cfg.record_base = Path(os.path.join('log', 'record'))
        shutil.rmtree(cfg.record_base, ignore_errors=True)
        makedirs(cfg.record_base)

    def setup_closure ( self ) :
        # print("\n: setting up a test")
        self.retain         = cfg.retain
        self.tmp_dir        = cfg.tmp_dir_base
        self.record         = cfg.record
        self.record_base    = cfg.record_base
        ALL_OK = os.R_OK | os.W_OK | os.X_OK
        assert_OS_Access ( self, self.tmp_dir, ALL_OK )
        if cfg.record :
            assert_OS_Access ( self, self.record_base, ALL_OK )

    return setup_closure

@pytest.fixture(scope="class")
def class_setup(request, session_setup):
    request.cls.logtool_init_for_session = session_setup

#
