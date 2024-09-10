# -*- coding: utf-8 -*-
import setuptools
from pathlib import Path

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


def read(filename, encoding='utf-8'):
    """read file contents"""

    fullpath = Path(__file__).resolve().parent / filename

    with fullpath.open() as fh:
        contents = fh.read().strip()
    return contents

def get_package_version():
    about = {}
    with open(Path(__file__).resolve().parent / 'fstpy' / '__init__.py', 'r', encoding='utf-8') as f:
        exec(f.read(), about)
    return about['__version__']


setuptools.setup(
    name="fstpy", # Replace with your own username
    version=get_package_version(),
    author="Sebastien Fortier",
    author_email="sebastien.fortier@canada.ca",
    description="High level pandas interface to fstd files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.science.gc.ca/CMDS/fstpy",
    project_urls={
        "Bug Tracker": "https://gitlab.science.gc.ca/CMDS/fstpy/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU License",
        "Operating System :: OS Linux",
    ],
    install_requires=[
        'pandas>=1.2.4','numpy>=1.19.5','dask>=2021.8.0','fstd2nc-deps >= 0.20200304.0', 'cmcdict >= 1.0.8'
    ],
    packages=setuptools.find_packages(exclude='test'),
    include_package_data=True,
    python_requires='>=3.6',
    package_data = {
    'fstpy': ['csv/*'],
  },
)
