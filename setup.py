#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='chat-union',
    version='2.0.0',
    description='高性能的多平台通讯通道集成系统，支持微信、SMS、Email、Discord、Slack、Telegram等多种通讯平台',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Chat-Union Team',
    author_email='1633797949@qq.com',
    url='https://github.com/yourusername/chat-union',
    packages=find_packages(exclude=['tests*', 'docs*', 'examples*']),
    include_package_data=True,
    python_requires='>=3.8',
    install_requires=[
        'fastapi>=0.104.1',
        'uvicorn>=0.24.0',
        'websockets>=12.0',
        'pydantic>=2.5.0',
        'pydantic-settings>=2.1.0',
        'python-dotenv>=1.0.0',
        'httpx>=0.25.2',
    ],
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-asyncio>=0.21.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Communications :: Chat',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    keywords='chat union wechat discord slack telegram sms email multi-platform communication',
    entry_points={
        'console_scripts': [
            'chat-union=backend.main:main',
        ],
    },
)
