try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Garbo- a garbage collector for the clouds',
    'author': 'Nati Cohen',
    'url': 'https://github.com/natict/garbo',
    'download_url': '',
    'author_email': 'nocoot at gmail',
    'version': '0.1',
    'install_requires': ['boto'],
    'packages': ['garbo'],
    'scripts': [],
    'name': 'garbo'
}

setup(**config)
