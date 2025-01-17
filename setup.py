

from setuptools import setup

setup(
    name='rediska',
    version='1.0',
    py_modules=['rediska'],
    entry_points={
        'console_scripts': [
            'rediska=rediska:main',
        ],
    },
)
