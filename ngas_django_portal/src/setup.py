from setuptools import setup, find_packages

setup(
    name = "ngas_portal",
    version = "1.0",
    url = 'http://icrargit.icrar.org/ngas_portal',
    license = 'BSD',
    description = "The Django version of the ngas portal",
    author = 'Simon King',
    packages = find_packages('portal'),
    package_dir = {'': 'portal'},
    install_requires = ['setuptools'],
)


