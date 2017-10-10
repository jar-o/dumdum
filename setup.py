"""
dumdum
-------------

Create fake HTTP servers with simple stanzas.
"""
from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(
    name='dumdum',
    version='0.1.5',
    url='http://www.github.com/jar-o/dumdum/',
    license='MIT',
    author='James Robson',
    author_email='dumdumpy@googlegroups.com',
    description='Easily create dummy HTTP servers',
    long_description=readme(),
    py_modules=['dumdum'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'pyparsing'
    ],
    scripts=['bin/dumdum'],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    test_suite='test_dumdum'
)
