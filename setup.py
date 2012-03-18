#!/usr/bin/env python3
# encoding: utf-8

classifiers = [
    'License :: OSI Approved :: BSD License',
    'Operating System :: Linux',
]

kw = {
    'name'                 : 'motionwol',
    'version'              : '0.1-never',

    'description'          : 'motion wake on lan',
    'long_description'     : '',

    'author'               : 'Georgi Valkov',
    'author_email'         : 'georgi.t.valkov@gmail.com',

    'license'              : 'New BSD License',

    'keywords'             : '',
    'classifiers'          : classifiers,
    'url'                  : 'https://github.com/gvalkov/motion-wol',

    'packages'             : ['motionwol'],
    'install_requires'     : [],
    'entry_points'         : {
        'console_scripts'  : ['motion-wol = motionwol.main:main']
    },

    'zip_safe'             : True,
}

from setuptools import setup
setup(**kw)
