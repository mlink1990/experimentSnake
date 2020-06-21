# -*- coding: utf-8 -*-
"""
Created on Sat Mar 14 19:50:04 2015

@author: User
"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Experiment Snake',
    'author': 'Timothy Harrison',
    'author_email': 'harrison@physik.uni-bonn.de',
    'version': '1.0',
    'install_requires': ['enthough.traits.api', 'enthough.traits.ui.api', 'pyface'],
    'packages': ['experimentSnake'],
    'scripts': [],
    'name': 'experimentSnake'
}

setup(**config)