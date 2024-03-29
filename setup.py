from itertools import chain

from setuptools import setup, find_packages

from tesseractXplore import __version__

extras_require = {  # noqa
    'app': ['cython',
            'kivy',
            'kivy-garden.contextmenu',
            'pygments'],
    'build': ['coveralls', 'twine', 'wheel'],
}
extras_require['all'] = list(chain.from_iterable(extras_require.values()))
extras_require['app-win'] = [
    'pypiwin32',
    'kivy_deps.sdl2',
    'kivy_deps.angle']
extras_require['all-win'] = extras_require['all'] + extras_require['app-win']
extras_require['dev'] = [
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
        'sphinxcontrib-apidoc']
extras_require['all-win-dev'] = extras_require['all-win'] + extras_require['dev']
extras_require['all-dev'] = extras_require['all'] + extras_require['dev']


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
        'pyyaml',
        'lxml',
        'requests',
        'xmltodict',
        'cython',
        'kivy',
        'kivy-garden.contextmenu',
        'pygments',
        'KivyMD @ git+https://github.com/kivymd/KivyMD.git@ad75c6b4c5ff7d1f5534bf7360017d4e84fb6de1#egg=KivyMD',
    ],
    extras_require=extras_require,
    entry_points={
        'gui_scripts': [
            'tesseractXplore=tesseractXplore.app.app:main',
        ],
    }
)
