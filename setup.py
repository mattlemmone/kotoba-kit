from setuptools import setup, find_packages

setup(
    name="kotobakit",
    version="0.1.0",
    description="KotobaKit - Japanese TTS and Anki Card Creator",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "argparse>=1.4.0",
    ],
    entry_points={
        "console_scripts": [
            "kotobakit=kotobakit:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
) 