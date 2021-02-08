from itertools import chain

from setuptools import setup, find_packages

from tesseractXplore import __version__

extras_require = {  # noqa
    'app': ['kivy',
            'KivyMD @ git://github.com/kivymd/KivyMD.git@29e07fe094522bb2aad5a0f3ce311f65c7b2a869#egg=KivyMD',
            'kivy-garden.contextmenu',
            'pygments'],
    'build': ['coveralls', 'twine', 'wheel'],
    'dev': [
        'black==20.8b1',
        'flake8',
        'isort',
        'mypy',
        'pre-commit',
        'pytest>=5.0',
        'pytest-cov',
        'kivy_examples',
        'memory_profiler',
        'prettyprinter',
        'Sphinx~=3.2.1',
        'sphinx-rtd-theme',
        'sphinxcontrib-apidoc',
    ],
}
extras_require['all'] = list(chain.from_iterable(extras_require.values()))
extras_require['app-win'] = [
    'pypiwin32',
    'kivy_deps.sdl2',
    'kivy_deps.angle']
extras_require['all-win'] = extras_require['all'] + extras_require['app-win']


# To install kivy dev version on python 3.8:
# pip install kivy[base] kivy_examples --pre --extra-index-url https://kivy.org/downloads/simple/

setup(
    name='tesseractXplore',
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'appdirs',
        'python-dateutil',
        'attrs',
        'click-help-colors',
        'pillow>=7.0',
        'pyexiv2',
        'pyyaml',
        'lxml',
        'requests',
        'xmltodict',
    ],
    extras_require=extras_require,
    entry_points={
        'gui_scripts': [
            'tesseractXplore=tesseractXplore.app.app:main',
        ],
    }
)
