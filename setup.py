from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='food_finder',
    version='0.1',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'food_finder = src.main:main'
        ]
    },
    install_requires=required,
)
