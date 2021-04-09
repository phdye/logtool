# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
# from setuptools.command.develop import develop
from setuptools.command.install import install

import re

package_name = 'logtool'
with open(f"{package_name}/__init__.py", 'rb') as f:
    _version = re.search('^__version__\s*=\s*"(.*)"', f.read(), re.M ).group(1)

with open("README.rst", 'rb') as f:
    _long_description = f.read().decode("utf-8")

from logtool.version import __version__

class InstallCommandWrapper(install):
    """Installer command wrapper.  Allows for pre-install and post-install actions."""

    def run(self):
        #
        # PUT YOUR PRE-INSTALL SCRIPT HERE or CALL A FUNCTION
        # ...
        #
        install.run(self)
        #
        # PUT YOUR POST-INSTALL SCRIPT HERE or CALL A FUNCTION
        # ...
        #
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


setup(
    name = package_name,
    version=__version__,
    # description = "logging tools -- pscript, log, logts",
    description="logging tools -- log, logts",
    author='Philip H. Dye',
    author_email='philip@phd-solutions.com',
    packages=find_packages(exclude=[ 'tests', 't', 'src', 's', 'aaa', 'log', 'snapshot' ]),
    url='https://github.com/philip-h-dye/logtool',
    requires=['plumbum', 'dateparser', 'docopt'],
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    cmdclass={
        # 'develop': PostDevelopCommand,
        'install': InstallCommand,
    },
    entry_points='''
        [console_scripts]
            logts    = logtool.logts:main '''  # !/usr/bin/env python3
    '''
            log      = logtool.log:main '''  # !/usr/bin/env python3
    '''
            pscript  = logtool.pscript:main	'''  # !/usr/bin/env python3
    '''
        ''',
)
