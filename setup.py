#!/usr/bin/env python
from distutils.core import setup
from django_forms import get_version


def read_files(*filenames):
    """
    Output the contents of one or more files to a single concatenated string.

    """
    output = []
    for filename in filenames:
        f = open(filename)
        try:
            output.append(f.read())
        finally:
            f.close()
    return '\n'.join(output)


setup(
    name='easy-thumbnails',
    version=get_version(join='-'),
    description='Django forms API designed to provide full form control to '
        'template designers.',
    long_description=read_files('README'),
    author='Chris Beaven',
    author_email='smileychris@gmail.com',
    platforms=['any'],
    packages=[
        'django_forms',
    ],
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
