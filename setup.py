from setuptools import find_packages, setup
from databricks_jobs import __version__

setup(
    name='fine_art_scrapper',
    packages=find_packages(exclude=['tests', 'tests.*']),
    setup_requires=['wheel'],
    version=__version__,
    description='Artisme',
    author=''
)
