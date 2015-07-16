
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

setup(name             = "shopwarecli",
      author           = "Aljosha Friemann",
      author_email     = "aljosha.friemann@gmail.com",
      license          = "",
      version          = "0.0.1",
      description      = "",
      url              = "",
      keywords         = [],
      # download_url     = "",
      install_requires = requirements,
      long_description = read('README.rst'),
      classifiers      = [],
      packages         = ["shopwarecli"],
      entry_points     = {'console_scripts': ['shopwarecli=shopwarecli.cli:run']}
)
