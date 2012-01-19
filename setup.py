from setuptools import find_packages, setup

# description = ''
# with open('README.rst') as f:
#     description = f.read()

setup(name="python-search-benchmark",
      version='dev',
      description='',
      long_description='',
      packages=find_packages(),
      license='MIT',
      platforms='any',
      install_requires=[
        "xappy",
        "whoosh",
        "xodb",
        ],
      )
