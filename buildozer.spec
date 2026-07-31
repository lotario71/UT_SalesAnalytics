# -*- coding: utf-8 -*-
"""
Buildozer — Sales Analytics Android (SOAP + conta seed).
Compilar en Linux/WSL o GitHub Actions:
  cd "Version Android"
  buildozer -v android debug
APK en: bin/salesanalytics-2.2.3-arm64-v8a-debug.apk
"""

[app]
title = Sales Analytics
package.name = salesanalytics
package.domain = com.umbrellatravel

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json
# Incluir seed conta/PE; excluir temporales y backups
source.include_patterns = data/*.json,assets/*
source.exclude_patterns = BACKUP/*,APK/*,Hello_World/*,__pycache__/*,chart_*.png,.buildozer/*,bin/*

version = 2.2.3

requirements = python3,kivy==2.3.0,kivymd==1.2.0,requests,urllib3,charset-normalizer,idna,certifi,pandas,numpy,matplotlib,pillow,pyjnius,android,openssl,sqlite3

orientation = portrait
fullscreen = 0

# Xiaomi 14T y moviles modernos: solo arm64
android.archs = arm64-v8a
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 26
android.ndk = 25b
android.accept_sdk_license = True
android.presplash_color = #111827

# Icono (opcional)
# icon.filename = %(source.dir)s/assets/icon.png

[buildozer]
log_level = 2
warn_on_root = 1
