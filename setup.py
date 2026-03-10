import os
import setuptools


def read(fname):
    return open(
        os.path.join(os.path.dirname(__file__), fname), encoding="utf-8"
        ).read()


setuptools.setup(
    name='grepbydate',
    version='0.0.0',
    setup_requires=[],
    scripts=[
        'grepbydate/bin/__init__.py'],
    entry_points={
        'console_scripts': [
            'grepbydate=grepbydate.bin:main'
            ],
        },
    packages=setuptools.find_packages(),
    package_data={},
    license='GPLv3',
    author='Pablo Fernández Rodríguez',
    url='https://github.com/pafernanr/grepbydate',
    keywords='sysadmin',
    description="Show events from log files converting input date formats to a unique format: '%Y-%m-%d %H:%M:%S'.",
    long_description_content_type='text/markdown',
    long_description=read("README.md"),
    classifiers=[
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    )
