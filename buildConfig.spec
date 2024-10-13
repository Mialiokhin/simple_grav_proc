# pyinstaller buildConfig.spec

# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['rasterio', 'rasterio.sample', 'rasterio._io', 'rasterio.enums', 'rasterio.crs', 'tabulate', 'contextily', 'contextily.place', 'contextily.tile', 'mercantile', 'cartopy', 'cartopy.crs', 'cartopy.io.img_tiles', 'cartopy.io.shapereader', 'cartopy.feature', 'geopandas', 'geopandas.io.file', 'geopandas.datasets', 'fiona', 'fiona.ogrext', 'fiona._shim', 'fiona._env', 'shapely', 'shapely.geometry', 'shapely.geos', 'shapely.ops', 'pyproj', 'pyproj._proj', 'pyproj.crs', 'statsmodels.api', 'statsmodels.formula.api', 'matplotlib.backends.backend_tkagg', 'matplotlib.backends.backend_agg', 'matplotlib.backends.backend_pdf', 'matplotlib.pyplot', 'matplotlib.dates', 'matplotlib.patches', 'seaborn', 'PIL', 'PIL._imagingtk', 'networkx', 'folium', 'mapclassify', 'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog', 'tkinter.simpledialog', 'tkinter.scrolledtext', 'components.survey_data_tab', 'components.ties_tab', 'components.vg_tab', 'grav_proc.calculations', 'grav_proc.reports', 'grav_proc.plots', 'grav_proc.loader', 'grav_proc.vertical_gradient'],
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
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
