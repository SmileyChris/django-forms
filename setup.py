#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='django-forms',
    version='0.1',
    description='Django forms API designed to provide full form control to '
        'template designers.',
    long_description=open('README.rst').read(),
    author='Chris Beaven',
    author_email='smileychris@gmail.com',
    platforms=['any'],
    install_requires=['django-ttag'],
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
