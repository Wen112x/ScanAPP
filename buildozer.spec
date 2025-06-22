[app]

# (str) Title of your application
title = 库存管理系统

# (str) Package name
package.name = inventoryapp

# (str) Package domain (needed for android/ios packaging)
package.domain = org.scanapp

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,txt

# (str) Application versioning (method 1)
version = 1.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy==2.1.0,kivymd==1.1.1,pillow==9.5.0,requests,anthropic,plyer,pyjnius,sqlite3

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (list) Permissions
android.permissions = CAMERA, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, INTERNET

# (list) Android addons
android.add_src = 

# (str) Bootstrap to use for android builds
android.bootstrap = sdl2

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (str) Android NDK version to use
android.ndk = 25b

# (int) Android SDK version to use
android.sdk = 31

# (list) Android application meta-data to set (key=value format)
android.meta_data = com.google.android.gms.vision.DEPENDENCIES=barcode

# (list) Android library project to add (will be added to project.properties)
# android.library_references = @aar/com.google.android.gms:play-services-vision:20.1.3

# (str) Android logcat filters to use
android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a libpymodules.so
android.copy_libs = 1

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) The format used to package the app for release mode (aab or apk).
android.release_artifact = apk

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1