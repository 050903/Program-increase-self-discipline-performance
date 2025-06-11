# build_app_v2.spec - Dành riêng cho performance_app_v2.py

# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Phiên bản này chỉ cần file config.json
data_files = [
    ('config.json', '.')
]

a = Analysis(
    ['performance_app_v2.py'],  # Tên file Python của phiên bản v2
    pathex=[],
    binaries=[],
    datas=data_files,
    hiddenimports=[
        # Các thư viện cần thiết cho v2
        'Pillow', 
        'seaborn', 
        'matplotlib',
        'pandas'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TroLyKyLuat_v2',  # Đặt tên khác để phân biệt
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # Ẩn cửa sổ console đen
    icon='logo.ico'          # Sử dụng icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TroLyKyLuat_v2'   # Tên thư mục output trong 'dist'
)