[app]
title = UT_SalesAnalytics
package.name = utsalesanalytics
package.domain = org.umbrellaweb

source.dir = .
source.include_exts = py,txt,png,jpg,kv,atlas

requirements = python3,kivy,kivymd,requests,pandas,matplotlib,cython

version = 1.0.0

# Forzar versiones Android correctas:
android.api = 33
android.ndk = 25b
android.build_tools_version = 33.0.0

# (list) Permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
# orientation = portrait

# (str) Entry point, default is main.py
# entrypoint = main.py

# Otros ajustes por defecto (no toques)
