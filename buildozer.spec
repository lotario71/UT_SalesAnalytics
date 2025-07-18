[app]
title = UT_SalesAnalytics
package.name = utsalesanalytics
package.domain = org.umbrellaweb
source.dir = .
source.include_exts = py,txt,png,jpg,kv,atlas

# buildozer.spec
requirements = python3,kivy==2.3.1,kivymd,matplotlib,requests,pandas,lxml
python_version = 3.11


# Enable PythonService support
android.add_services = true

version = 1.0.0
