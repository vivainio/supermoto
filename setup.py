from pathlib import Path

from setuptools import setup

long_description = Path("README.md").read_text(encoding="utf-8")

setup(
    name="supermoto",
    version="1.5.0",
    description='Helpers for "moto" tests, and other AWS test resource setup',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Ville M. Vainio",
    author_email="ville.vainio@basware.com",
    url="https://github.com/vivainio/supermoto",
    license="MIT",
    license_files=["LICENSE"],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Testing",
        "Intended Audience :: Developers",
    ],
    python_requires=">=3.7",
    packages=["supermoto"],
    package_data={
        "supermoto": ["py.typed"],
    },
    install_requires=[],
)
