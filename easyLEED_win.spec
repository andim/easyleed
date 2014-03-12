# -*- mode: python -*-
a = Analysis(['easyleed\\trunk\\run-gui.py'],
             pathex=['C:\\Users\\Salopaasi\\My Documents\\pyinstaller-pyinstaller-275d4c9\\easeh'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='easeh.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False )
