import os.path
from setuptools import setup, find_packages


# single source of truth for package version
version_ns = {}
with open(os.path.join('mp_auth', '__init__.py')) as f:
    exec(f.read(), version_ns)

install_requires = []
with open('requirements.txt') as reqs:
    for line in reqs.readlines():
        req = line.strip()
        if not req or req.startswith('#'):
            continue
        install_requires.append(req)


setup(name='multi-provider-auth',
      version=version_ns['__version__'],
      description='Add Multi-provider auth for various providers',
      long_description=open('README.md').read(),
      author='Globus Team',
      author_email='support@globus.org',
      packages=find_packages(),
      install_requires=install_requires,
      include_package_data=True,
      keywords=['globus', 'django'],
      license='apache 2.0',
      classifiers=[
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Apache Software License',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Topic :: Communications :: File Sharing',
          'Topic :: Internet :: WWW/HTTP',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      )
