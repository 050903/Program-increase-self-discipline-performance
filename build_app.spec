# build_app.spec

# -*- mode: python ; coding: utf-8 -*-
import os

# --- TỰ ĐỘNG XÁC ĐỊNH THƯ MỤC GỐC ---
# Dòng này lấy đường dẫn đến thư mục chứa chính file .spec này
# Đảm bảo nó luôn tìm thấy các file khác dù bạn chạy lệnh từ đâu
SPEC_DIR = os.path.dirname(os.path.abspath(__file__))

# --- TẠO DANH SÁCH CÁC FILE DỮ LIỆU ---
# Tạo một danh sách các file cần được copy vào ứng dụng.
# os.path.join sẽ tạo ra đường dẫn đúng cho mọi hệ điều hành.
data_files = [
    (os.path.join(SPEC_DIR, 'config.json'), '.'),
    (os.path.join(SPEC_DIR, 'secrets.json'), '.'),
    (os.path.join(SPEC_DIR, 'logo.png'), '.'),
    (os.path.join(SPEC_DIR, 'logo.ico'), '.')
]

block_cipher = None

a = Analysis(
    ['performance_app_v2.py'],  # Tên file Python chính
    pathex=[],
    binaries=[],
    datas=data_files, # <-- Sử dụng danh sách file đã được tạo ở trên
    hiddenimports=[
        'Pillow', 
        'seaborn', 
        'google.generativeai', # Chỉ định rõ ràng hơn
        'matplotlib',
        'pandas', # Matplotlib đôi khi cần pandas
        'tkinter',
        'datetime',
        'threading'
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
    name='TroLyKyLuat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Ẩn cửa sổ dòng lệnh màu đen
    icon=os.path.join(SPEC_DIR, 'logo.ico') # <-- Dùng đường dẫn tuyệt đối
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TroLyKyLuat'
)