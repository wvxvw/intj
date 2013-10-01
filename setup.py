from setuptools import setup
from setuptools import find_packages

setup(name             = 'walla-test-assignment',
      version          = '0.0.1',
      author           = 'Oleg Sivokon',
      author_email     = 'olegsivokon@gmail.com',
      packages         = find_packages(),
      license          = 'LICENSE',
      url              = 'http://wvxvw.github.io/walla-test-assignment',
      description      = 'A toy social network site.',
      long_description = open('README.org').read(),
      install_requires = ['tornado >=  3.1.1'])
