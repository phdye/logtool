# -*- coding: utf-8 -*-
import sys
from setuptools import setup, find_packages
# from setuptools.command.develop import develop
from setuptools.command.install import install as InstallCommand
from setuptools.command.test import test as TestCommand

import re

#------------------------------------------------------------------------------

package_name = 'logtool'

init = f"{package_name}/__init__.py"

with open(init, 'r') as f:
    # _version = re.search('^__version__\s*=\s*"(.*)"', f.read(), re.M ).group(1)
    # contents = f.read()
    # print(contents, file=sys.stderr)
    # results = re.search('^__version__\s*=\s*"(.*)"', contents, re.M )
    # print(results, file=sys.stderr)
    # _version = results.group(1)
    contents = f.readlines()
    prefix = '__version__='
    __version__ = None
    for line in contents:
        line = line.strip().replace(' ','')
        if line.startswith(prefix):
            __version__ = line[len(prefix)+1:-1]
    if not __version__:
        raise ValueError(f"setup.py:  can't get version from '{init}'")

with open("README.rst", 'rb') as f:
    _long_description = f.read().decode("utf-8")

#------------------------------------------------------------------------------

class InstallCommandWrapper(InstallCommand):
    """Installer command wrapper.  Allows for pre-install and post-install actions."""

    def run(self):
        # PUT YOUR PRE-INSTALL SCRIPT HERE or CALL A FUNCTION
        InstallCommand.run(self)
        # PUT YOUR POST-INSTALL SCRIPT HERE or CALL A FUNCTION
        import os
        sym_target = 'logts'
        sym_name = 'log-ts'
        # Do nothing if 'logts' hasn't been created yet (i.e. 'bdist_wheel').
        if os.path.exists ( os.path.join(self.install_scripts, sym_target) ) :
            print("Create symlink '{}' to '{}' in '{}'.".format(
                sym_name, sym_target, self.install_scripts))
            sym_link = os.path.join(self.install_scripts, sym_name)
            if os.path.exists(sym_link):
                if os.path.islink(sym_link):
                    os.unlink(sym_link)
                else:
                    raise ValueError(
                        "'{}' exists and is not a symlink".format(sym_link))
            os.symlink(sym_target, sym_link)

#------------------------------------------------------------------------------

setup(
    name = package_name,
    version=__version__,
    description="logging tools -- log, logts",
    author='Philip H. Dye',
    author_email='philip@phd-solutions.com',
    # packages=find_packages(exclude=[ 'tests', 't', 'src', 's', 'aaa', 'log', 'snapshot' ]),
    packages=['logtool'],
    url='https://github.com/philip-h-dye/logtool',
    requires=['plumbum', 'dateparser', 'docopt', 'prettyprinter'],
    tests_require=["pytest", "pytest-runner"],
    cmdclass={
        # 'develop': PostDevelopCommand,
        'install': InstallCommandWrapper,
        # 'test' : PyTest,
    },
    entry_points='''
        [console_scripts]
            logts    = logtool.logts:main
            log      = logtool.log:main
        ''',
)
