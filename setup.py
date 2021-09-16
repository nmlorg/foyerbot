import setuptools


setuptools.setup(
    name='foyerbot',
    version='0.0.1',
    author='Daniel Reed',
    author_email='nmlorg@gmail.com',
    description='https://t.me/foyerbot',
    url='https://github.com/nmlorg/foyerbot',
    packages=setuptools.find_packages(include=('foyerbot', 'foyerbot.*')),
    python_requires='>=3.5',
    install_requires=[
        'ntelebot',
    ])
