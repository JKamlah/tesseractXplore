from itertools import chain

from setuptools import setup, find_packages

from tesseractXplore import __version__

extras_require = {
    'app': ['kivy>=1.11', 'kivymd~=0.104.1', 'kivy-garden.contextmenu', 'pygments'],
    'dev': [
        'black',
        'kivy_examples',
        'memory_profiler',
        'prettyprinter',
        'pytest',
        'Sphinx>=3.0',
        'sphinx-rtd-theme',
        'sphinxcontrib-apidoc',
    ],
}
extras_require['all'] = list(chain.from_iterable(extras_require.values()))
extras_require['app-win'] = ['pypiwin32', 'kivy_deps.sdl2', 'kivy_deps.gstreamer', 'kivy_deps.angle']
extras_require['all-win'] = extras_require['all'] + extras_require['app-win']

# To install kivy dev version on python 3.8:
# pip install kivy[base] kivy_examples --pre --extra-index-url https://kivy.org/downloads/simple/

setup(
    name='tesseractXplore',
    version=__version__,
    packages=find_packages(),
    install_requires=[
        'appdirs',
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
            'tesseractXplore-app=tesseractXplore.app.app:main',
        ],
    }
)
