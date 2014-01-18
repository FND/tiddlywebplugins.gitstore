import os

from setuptools import setup, find_packages


# XXX: these should go into the package's __init__
VERSION = '0.6.4'
AUTHOR = 'FND'
LICENSE = 'BSD'

DESC = os.path.join(os.path.dirname(__file__), 'README')
DESC = ''.join(line for line in open(DESC)
        if not line.startswith('[![build status](http')) # XXX: fugly hack

META = {
    'name': 'tiddlywebplugins.gitstore',
    'url': 'https://github.com/FND/tiddlywebplugins.gitstore',
    'version': VERSION,
    'description': 'TiddlyWeb store implementation using Git',
    'long_description': DESC,
    'license': LICENSE,
    'author': AUTHOR,
    'packages': find_packages(exclude=['test']),
    'namespace_packages': ['tiddlywebplugins'],
    'platforms': 'Posix; MacOS X; Windows',
    'include_package_data': False,
    'zip_safe': False,
    'install_requires': ['tiddlyweb>=1.4.0', 'tiddlywebplugins.utils',
            'dulwich'],
    'extras_require': {
        'testing': ['pytest', 'wsgi-intercept', 'httplib2'],
        'coverage': ['figleaf', 'coverage']
    }
}


if __name__ == '__main__':
    setup(**META)
