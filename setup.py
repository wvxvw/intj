from setuptools import setup
from setuptools import find_packages

setup(name             = 'intj',
      version          = '0.0.1',
      author           = 'Oleg Sivokon',
      author_email     = 'olegsivokon@gmail.com',
      packages         = find_packages(),
      license          = 'LICENSE',
      url              = 'https://github.com/wvxvw/intj',
      description      = 'A toy social network site.',
      long_description = open('README.org').read(),
      install_requires = ['tornado >=  3.1.1', 'py2neo >= 1.6.0',
                          'httpstream >= 1.0.9', 'bcrypt >= 1.0.2'])
