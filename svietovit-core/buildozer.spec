[app]
title = Śviętovit (szkielet)
package.name = svietovitcore
package.domain = org.aplikacje
source.dir = .
source.include_exts = py,ttf,png,json
source.exclude_dirs = tests,bin,.buildozer,__pycache__,tools,.github,i18n
version = 1.0.0
requirements = python3,kivy==2.3.1,pyjnius
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/presplash.png
orientation = portrait
fullscreen = 0
android.permissions =
android.api = 34
android.ndk = 25b
android.ndk_api = 24
p4a.branch = v2024.01.21
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True
# Zapytanie o silnik mowy (chiński kurs czyta znaki na głos).
android.extra_manifest_xml = ./android_queries.xml
android.presplash_color = #16171B

[buildozer]
log_level = 2
warn_on_root = 1
