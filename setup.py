import os

from setuptools import setup, find_packages


# XXX: these should go into the package's __init__
VERSION = '0.1.1'
AUTHOR = 'FND'
LICENSE = 'BSD'

DESC = open(os.path.join(os.path.dirname(__file__), 'README')).read()
DESC = "\n".join(line for line in DESC.splitlines()
        if not line.startswith("[![build status](http")) # XXX: fugly hack

META = {
    'name': 'tiddlywebplugins.gitstore',
    'url': 'https://github.com/FND/tiddlywebplugins.gitstore',
    'version': VERSION,
    'description': 'TiddlyWeb store implementation using Git',
    'long_description': DESC,
    'license': 'BSD',
    'author': AUTHOR,
    'packages': find_packages(exclude=['test']),
    'platforms': 'Posix; MacOS X; Windows',
    'include_package_data': False,
    'zip_safe': False,
    'install_requires': ['tiddlyweb>=1.4.0', 'tiddlywebplugins.utils',
            'dulwich'],
    'extras_require': {
        'testing': ['pytest'],
        'coverage': ['figleaf', 'coverage']
    }
}


if __name__ == '__main__':
    setup(**META)
