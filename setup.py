import os

from setuptools import setup, find_packages


DESC = open(os.path.join(os.path.dirname(__file__), 'README')).read()

META = {
    #'name': '',
    #'url': 'https://github.com/FND/',
    #'version': VERSION,
    #'description': '',
    'long_description': DESC,
    #'license': 'LICENSE',
    #'author': AUTHOR,
    #'author_email': '',
    'maintainer': 'FND',
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


#setup(**META)
