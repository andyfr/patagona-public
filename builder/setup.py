
import os, pip

# from pip.req import parse_requirements

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

install_reqs = pip.req.parse_requirements('requirements.txt', session=pip.download.PipSession())

requirements = [str(ir.req) for ir in install_reqs if ir is not None]

setup(name             = 'builder',
      version          = '0.1',
      author           = 'Patagona GmbH',
      author_email     = 'developers@gmail.com',
      description      = 'builder for dockerizable projects',
      license          = None,
      keywords         = "utility docker administration",
      url              = 'https://github.com/andyfr/infrastructure',
      packages         = ['builder'],
      install_requires = requirements,
      long_description = read('README.rst'),
      classifiers      = [],
      entry_points     = {'console_scripts': ['builder=builder.cli:run']}
)
