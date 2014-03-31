# -*- mode: python -*-
a = Analysis(['easyleed//trunk/run-gui.py'],
             pathex=['/home/salopaasi/Documents/Moo/pyinstaller-2.0'],
             hiddenimports=[],
             hookspath=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name=os.path.join('dist', 'EasyLEED'),
          debug=False,
          strip=None,
          upx=True,
          console=True , icon='easyleed/doc/source/_static/eicon.ico')
