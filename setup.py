# -*- coding: utf-8 -*-
# @Time : 2021/9/8 15:17
# @Author : Ben
# @Email : dengjiabin@bluemoon.com.cn
DEFINE_VERSION = '0.0.1'
from setuptools import setup, find_packages

requireList = [
    'lz4==3.1.3',
    'requests==2.25.1',
]

setup(
    name='bmai_easy_rpc',
    version=DEFINE_VERSION,
    description='一个基于python的简单高效RPC框架',
    author='DengJiaBin',
    author_email = 'dengjiabin@bluemoon.com.cn',
    platforms=["all"],
    install_requires=requireList,
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    keywords='bmai_easy_rpc',
    packages=find_packages(),
    include_package_data=True,
    entry_points = {
        'console_scripts' : [
            'rpc=bmai_easy_rpc.cli.entry:main'
        ]
    }
)

