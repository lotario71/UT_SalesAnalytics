[app]
title = UT_SalesAnalytics
package.name = utsalesanalytics
package.domain = org.umbrellaweb

source.dir = .
source.include_exts = py,kv,png,jpg,txt,json

# Main Python file
entrypoint = main.py

orientation = portrait

version = 1.0.0

requirements = python3,kivy==2.3.0,kivymd==1.2.0,requests,pandas,matplotlib

# uncomment if you use internet or save files
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE

fullscreen = 1

[buildozer]
log_level = 2
warn_on_root = 0

[android]
android.api = 34
android.ndk = 25b
