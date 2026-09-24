# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path(SPEC).resolve().parent
frontend_dist = project_root / "frontend" / "dist"


analysis = Analysis(
    [
        str(project_root / "run_server.py"),
    ],
    pathex=[
        str(project_root),
    ],
    binaries=[],
    datas=[
        (
            str(frontend_dist),
            "frontend/dist",
        ),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

python_archive = PYZ(analysis.pure)

executable = EXE(
    python_archive,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="SkySwallowServer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)

application = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    name="SkySwallowTools",
)
