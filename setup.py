# -*- coding: utf-8 -*-
# setup.py ---
#

from distutils.core import setup
from setuptools import find_packages

setup(name='Humongolus',
      version='1.0.6',
      author='Christopher Coté',
      packages=find_packages(),
      zip_safe=False,
      install_requires=['pymongo==2.8'],
      include_package_data=True,
      )

#
# setup.py ends here
