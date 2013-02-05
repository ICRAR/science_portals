from setuptools import setup, find_packages

setup(
    name = "ngas_portal",
    version = "0.3",
    url = 'http://icrargit.icrar.org/ngas_portal',
    license = 'LGPL',
    description = "The Django version of the ngas portal",
    author = 'Simon King',
    packages = find_packages('src/portal'),
    package_dir = {'': 'src/portal'},
    install_requires = ['setuptools'],
)


