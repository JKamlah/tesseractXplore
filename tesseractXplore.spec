from os.path import abspath
from kivymd import hooks_path as kivymd_hooks_path
from PyInstaller.compat import is_win, is_linux, is_darwin

PROJECT_NAME = 'tesseractXplore'

if is_win:
    # Define platform-specific dependencies
    binaries = []
    hiddenimports = ['win32timezone']
    kivy_bins = [Tree(p) for p in (sdl2.dep_bins + angle.dep_bins)]

    a = Analysis(
    [f'{PROJECT_NAME}\\app\\app.py'],
    pathex=[abspath('.')],
    binaries=binaries,
    datas=[
        ('assets\\metadata\\*.yml' , 'assets\\metadata'),
        ('assets\\fonts\\*.ttf' , 'assets\\fonts'),
        ('assets\\*.png' , 'assets'),
	    ('assets\\*.ico' , 'assets'),
        ('kv\\*.kv', 'kv'),
        ('venv\\Lib\\site-packages\\kivy_garden\\contextmenu\\*', 'kivy_garden\\contextmenu'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[kivymd_hooks_path],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
    )
    pyz = PYZ(a.pure, a.zipped_data, cipher=None)
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=PROJECT_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=True,
    )
    coll = COLLECT(
        exe,
        Tree(f'{PROJECT_NAME}\\'),
        a.binaries,
        a.zipfiles,
        a.datas,
        *kivy_bins,
        name=PROJECT_NAME,
        strip=False,
        upx=True,
        upx_exclude=[],
    )

else:
    # Define platform-specific dependencies
    binaries = []
    hiddenimports = []

    a = Analysis(
        [f'{PROJECT_NAME}/app/app.py'],
        pathex=[abspath('.')],
        binaries=binaries,
        datas=[
            ('assets/metadata/*.yml' , 'assets/metadata'),
            ('assets/fonts/*.ttf' , 'assets/fonts'),
            ('assets/*.png' , 'assets'),
            ('assets/*.ico' , 'assets'),
            ('kv/*.kv', 'kv'),
            ('/venv/lib/python3.8/site-packages/kivy_garden/contextmenu/*', 'kivy_garden/contextmenu'),
            ('/venv/lib/python3.8/site-packages/kivy/*', 'kivy'),
        ],
        hiddenimports=hiddenimports,
        hookspath=[kivymd_hooks_path],
        win_no_prefer_redirects=False,
        win_private_assemblies=False,
        cipher=None,
        noarchive=False,
    )
    pyz = PYZ(a.pure, a.zipped_data, cipher=None)
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=PROJECT_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=True,
    )
    coll = COLLECT(
        exe,
        Tree(f'{PROJECT_NAME}/'),
        a.binaries,
        a.zipfiles,
        a.datas,
        name=PROJECT_NAME,
        strip=False,
        upx=True,
        upx_exclude=[],
    )
