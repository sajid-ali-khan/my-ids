#!/usr/bin/env python3
"""
Setup script for IDS CLI package
Installation Methods (choose one):
  1. pipx install .           (recommended, auto venv handling)
  2. python3 -m venv venv && source venv/bin/activate && pip install .
  3. bash install.sh          (Linux, auto venv handling)
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read long description from README
root_dir = Path(__file__).parent
readme_file = root_dir / 'README.md'
long_description = ""

if readme_file.exists():
    with open(readme_file, 'r', encoding='utf-8') as f:
        long_description = f.read()

setup(
    name='ids-tool',
    version='1.0.0',
    description='Network Intrusion Detection System with Web Dashboard and CLI',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/sajid-ali-khan/my-ids',
    license='MIT',
    
    packages=find_packages(),
    
    include_package_data=True,
    package_data={
        'ids_api': [],
        'ids_core': [],
        'ids_cli': [],
    },
    
    # Package data files to include
    data_files=[
        ('web', [
            'web/index.html',
            'web/style.css',
            'web/script.js',
        ]),
        ('model', []),  # Model directory (user will populate)
    ],
    
    python_requires='>=3.8',
    
    install_requires=[
        'numpy>=2.0.0',
        'pandas>=3.0.0',
        'scikit-learn>=1.6.0',
        'scapy>=2.7.0',
        'joblib>=1.5.0',
        'flask>=2.3.0',
        'flask-cors>=4.0.0',
        'requests>=2.30.0',
        'click>=8.0.0',
    ],
    
    entry_points={
        'console_scripts': [
            'ids-cli=ids_cli.cli:main',
        ],
    },
    
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Networking :: Monitoring',
        'Topic :: Security',
    ],
    
    keywords='ids intrusion-detection network-security dashboard monitoring',
    
    project_urls={
        'Bug Reports': 'https://github.com/sajid-ali-khan/my-ids/issues',
        'Documentation': 'https://github.com/sajid-ali-khan/my-ids#readme',
        'Source': 'https://github.com/sajid-ali-khan/my-ids',
    },
)
