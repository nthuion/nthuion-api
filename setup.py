import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()

requires = [
    'itsdangerous',
    'psycopg2',
    'pyramid',
    'pyramid_debugtoolbar',
    'pyramid_tm',
    'redis',
    'requests',
    'SQLAlchemy',
    'transaction',
    'uwsgi',
    'voluptuous',
    'zope.sqlalchemy',
]

tests_require = [
    'hypothesis',
    'pytest',  # includes virtualenv
    'pytest-cov',
    'WebTest >= 1.3.1',  # py3 compat
]

docs_require = [
    'sphinx',
    'sphinx_rtd_theme',
    'sphinxcontrib-httpdomain',
]

setup(
    name='nthuion',
    version='0.0',
    description='nthuion',
    long_description=README,
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author='',
    author_email='',
    url='',
    keywords='web wsgi bfg pylons pyramid',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    extras_require={
        'testing': tests_require,
        'docs': docs_require
    },
    install_requires=requires,
    entry_points="""\
    [paste.app_factory]
    main = nthuion:main
    [console_scripts]
    initialize_nthuion_db = nthuion.scripts.initializedb:main
    popularity-decay = nthuion.scripts.popularity_decay:main
    flush-traffic = nthuion.scripts.flush_traffic:main
    """,
)
