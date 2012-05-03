# setup.py ---
#

from distutils.core import setup
from setuptools import find_packages

setup(name='Humongolus',
      version='1.0',
      author='entone',
      packages=find_packages(),
      zip_safe=False,
      requires=['pymongo'],
      include_package_data=True,
      )

#
# setup.py ends here
