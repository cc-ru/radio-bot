#!/usr/bin/env python3

from setuptools import find_packages, setup

setup(
    name='radio-bot',
    version='0.0.1',
    long_description='Radio bot',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['irc',
                      'python-mpd2'],
    entry_points={
        'console_scripts': [
            'radio-bot=radiobot:main'
        ]
    }
)
