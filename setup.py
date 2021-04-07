from distutils.core import setup

setup(name='supermoto',
      version='1.0.0',
      description='Helpers for "moto" tests',
      author='Ville M. Vainio',
      author_email='ville.vainio@basware.com',
      url='https://github.com/vivainio/supermoto',
      packages=['supermoto'],
      install_requires=[],
      entry_points = {
        'console_scripts': [
            'supermoto = supermoto.supermoto:main'
        ]
      }
     )
