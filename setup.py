from distutils.core import setup

setup(
    name="supermoto",
    version="1.2.2",
    description='Helpers for "moto" tests',
    author="Ville M. Vainio",
    author_email="ville.vainio@basware.com",
    url="https://github.com/vivainio/supermoto",
    packages=["supermoto"],
    package_data={
        "supermoto": ["py.typed"],
    },
    install_requires=[],
)
