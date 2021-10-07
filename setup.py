import setuptools


setuptools.setup(
    name='foyerbot',
    version='0.0.3',
    author='Daniel Reed',
    author_email='nmlorg@gmail.com',
    description='https://t.me/foyerbot',
    url='https://github.com/nmlorg/foyerbot',
    packages=setuptools.find_packages(include=('foyerbot', 'foyerbot.*')),
    python_requires='>=3.6',
    install_requires=[
        'captcha',
        'ntelebot >= 0.4.1',
    ])
