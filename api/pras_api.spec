# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['run_pras.py'],
    pathex=['.'],  # directory that contains this spec (api/)
    binaries=[],
    datas=[
        ('db', 'db'),                                   # read-only inside onefile bundle
        ('uploads', 'uploads'),                         # read-only inside onefile bundle (see note below)
        ('pdf_output', 'pdf_output'),                   # read-only inside onefile bundle (see note below)
        ('../src/assets/fonts', 'src/assets/fonts'),
        ('img_assets/seal_no_border.png', 'img_assets'),
        ('../.env', '.'),                               # optional; consider using real env vars in prod
        ('db/pras_sql_script.sql', 'db'),
        ('services/smtp_service/templates', 'api/services/smtp_service/templates'),
    ],
    hiddenimports=['aiosqlite'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='pras_api',
    console=True,
    upx=True,
)
