#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("HISTORY.md") as history_file:
    history = history_file.read()

install_requires = [
    'typing-extensions>=4.12.0; python_version<"3.10"',
]

tests_require = [
    "pytest>=3.4.2",
    "pytest-cov>=2.6.0",
]

development_requires = [
    # general
    "bumpversion>=0.5.3",
    "pip>=9.0.1",
    "watchdog>=0.8.3",
    # docs
    "m2r>=0.2.0",
    "Sphinx>=1.7.1",
    "sphinx_rtd_theme>=0.2.4",
    "autodocsumm>=0.1.10",
    # style check
    "black>=24.4.2",
    "isort>=4.3.4",
    # fix style issues
    "autoflake>=1.2",
    "autopep8>=1.4.3",
    # distribute on PyPI
    "twine>=1.10.0",
    "wheel>=0.30.0",
    # Advanced testing
    "coverage>=4.5.1",
    "tox>=2.9.1",
]

setup(
    author="Micah Smith",
    author_email="micahjsmith@gmail.com",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    description="Stack log messages",
    extras_require={
        "test": tests_require,
        "dev": development_requires + tests_require,
    },
    install_package_data=True,
    install_requires=install_requires,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords="stacklog",
    name="stacklog",
    packages=find_packages(include=["stacklog", "stacklog.*"]),
    python_requires=">=3.8,<3.13",
    test_suite="tests",
    tests_require=tests_require,
    url="https://github.com/micahjsmith/stacklog",
    version="2.0.0",
    zip_safe=False,
)
