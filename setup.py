import os.path
import sys
import warnings

from setuptools import find_packages, setup

if sys.version_info < (2, 7):
    raise NotImplementedError(
        """\n
###########################################################
# mp-auth does not support python versions older than 2.7 #
###########################################################"""
    )

# single source of truth for package version
version_ns = {}
with open(os.path.join("mp_auth", "version.py")) as f:
    exec(f.read(), version_ns)

setup(
    name="mp-auth",
    version=version_ns["__version__"],
    description="Multiprovider Authentication",
    long_description=open("README.md").read(),
    author="Globus Team",
    author_email="lukasz@uchicago.edu",
    url="https://github.com/fair-research/mp_auth",
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=[
        "cryptography>=2.3.1",
        "PyJWT>=1.4.0",
        "requests>=2.0.0,<3.0.0",
        "django>=2.0",
        "django-rest-framework>=3.8.0",
    ],
    extras_require={
        # empty extra included to support older installs
        # the development extra is for SDK developers only
        "development": [
        ],
    },
    include_package_data=True,
    keywords=["oauth2", "jwt", "authentication", "django"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Communications :: File Sharing",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
