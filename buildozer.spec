# -*- coding: utf-8 -*-
# Buildozer — Sales Analytics Android (SOAP + conta seed).
# Compilar: buildozer -v android debug
# APK en: bin/salesanalytics-2.2.7-arm64-v8a-debug.apk

[app]
title = Sales Analytics
package.name = salesanalytics
package.domain = com.umbrellatravel

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json,ttf
# Incluir seed conta/PE y fuente de graficas; excluir temporales y backups
source.include_patterns = data/*.json,assets/*
source.exclude_patterns = BACKUP/*,APK/*,Hello_World/*,__pycache__/*,chart_*.png,.buildozer/*,bin/*

version = 2.2.7

# Python 3.11: hostpython3 y python3 DEBEN coincidir (si no, p4a usa 3.14 y rompe Kivy).
requirements = hostpython3==3.11.10,python3==3.11.10,kivy==2.3.0,kivymd==1.2.0,requests,urllib3,charset-normalizer,idna,certifi,pillow,pyjnius,android,openssl,sqlite3

# Solo vertical: las graficas llenan el hueco en portrait
orientation = portrait
fullscreen = 0

# Xiaomi 14T y moviles modernos: solo arm64
android.archs = arm64-v8a
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 35
android.minapi = 26
android.ndk = 25b
android.accept_sdk_license = True
android.presplash_color = #111827

# Recetas locales (freetype por SourceForge; evita 502 de savannah.gnu.org)
p4a.local_recipes = ./p4a-recipes

# Icono (opcional)
# icon.filename = %(source.dir)s/assets/icon.png

[buildozer]
log_level = 2
warn_on_root = 1
