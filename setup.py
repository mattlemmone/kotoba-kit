from setuptools import setup, find_packages

setup(
    name="kotobakit",
    version="0.1.0",
    description="KotobaKit - Japanese TTS and Anki Card Creator",
    author="Matt Lemmone",
    author_email="",
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
) 