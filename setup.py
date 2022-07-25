from setuptools import setup

import easycpp


with open('requirements.txt') as f:
    requirements = f.read().splitlines()


with open('README.rst', 'r') as rm:
    readme = rm.read()


packages = [
    'easycpp'
]


setup(
    name='easycpp',
    author=easycpp.__author__,
    version=easycpp.__version__,
    description='A Python module to easily use code from C++ in Python.',
    long_description=readme,
    long_description_content_type='text/x-rst',
    include_package_data=True,
    install_requires=requirements,
    python_requires='>=3.6.0',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
        'Typing :: Typed',
    ]
)

