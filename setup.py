from setuptools import find_packages, setup

setup(
    name='fine_art_scrapper',
    packages=find_packages(exclude=['tests', 'tests.*']),
    setup_requires=['wheel'],
    version="0.1",
    description='Artisme',
    author=''
)
