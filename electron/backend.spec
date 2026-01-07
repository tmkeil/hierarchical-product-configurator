# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Alle Python-Dateien und Dependencies sammeln
a = Analysis(
    ['../database/api.py'],
    pathex=['../database'],
    binaries=[
        # Python DLL explizit hinzufügen für Systeme ohne Python
        ('C:\\Program Files\\Python313\\python313.dll', '.'),
    ],
    datas=[
        ('../database/schema.sql', '.'),
        # .env nicht nötig - Environment Variables werden von Electron gesetzt
    ],
    hiddenimports=[
        # FastAPI & Uvicorn Core
        'fastapi',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.wsproto_impl',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.server',
        'uvicorn.config',
        'uvicorn.main',
        
        # Starlette & Dependencies
        'starlette',
        'starlette.routing',
        'starlette.middleware',
        'starlette.middleware.cors',
        'starlette.applications',
        'starlette.responses',
        'starlette.exceptions',
        
        # Pydantic
        'pydantic',
        'pydantic.v1',
        'pydantic_core',
        
        # Authentication
        'jose',
        'jwt',
        'passlib',
        'passlib.handlers',
        'passlib.handlers.bcrypt',
        'bcrypt',
        
        # Standard Library
        'sqlite3',
        'multipart',
        'python_multipart',
        'email.mime',
        'email.mime.multipart',
        'email.mime.text',
        
        # dotenv
        'dotenv',
        
        # Excel
        'openpyxl',
        'openpyxl.styles',
        
        # Azure (optional but included)
        'azure.storage.blob',
        'azure.core',
        'azure.identity',
        
        # System
        'zoneinfo',
        
        # HTTP & Encodings
        'h11',
        'httptools',
        'websockets',
        'anyio',
        'click',
        'typing_extensions',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # True für Debugging, False für Production
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
