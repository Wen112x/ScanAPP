# -*- coding: utf-8 -*-
import os

# Request code para identificar el resultado de ZXing
ZXING_REQUEST_CODE = 49374


class AndroidBarcodeScanner:
    def __init__(self):
        self.is_android = False
        self.scan_callback = None

        try:
            from jnius import autoclass
            self.is_android = True
            self.Intent = autoclass('android.content.Intent')
            self.PythonActivity = autoclass('org.kivy.android.PythonActivity')

            # Registrar callback para recibir el resultado de ZXing
            try:
                from android.activity import bind as activity_bind
                activity_bind(on_activity_result=self._on_activity_result)
            except ImportError:
                print("android.activity not available")

        except ImportError:
            print("Not running on Android - barcode scanner simulated")

    def scan_from_camera(self, callback=None):
        """Escanear código de barras con ZXing Barcode Scanner.

        callback(barcode, error=None) se llama cuando llega el resultado.
        Si ZXing no está instalado, callback recibe error con el mensaje.
        """
        if not self.is_android:
            result = self._simulate_scan()
            if callback:
                callback(result)
            return

        self.scan_callback = callback
        try:
            intent = self.Intent("com.google.zxing.client.android.SCAN")
            intent.putExtra("SCAN_MODE", "ALL_BARCODE_MODE")
            activity = self.PythonActivity.mActivity
            activity.startActivityForResult(intent, ZXING_REQUEST_CODE)
        except Exception as e:
            print(f"Error starting ZXing: {e}")
            if callback:
                callback(None, error=(
                    "ZXing Barcode Scanner no está instalado.\n"
                    "Instálalo gratis desde Play Store o usa la entrada manual."
                ))

    def _on_activity_result(self, request_code, result_code, intent):
        """Recibe el resultado de la actividad ZXing."""
        if request_code != ZXING_REQUEST_CODE:
            return
        RESULT_OK = -1
        cb = self.scan_callback
        self.scan_callback = None
        if cb is None:
            return
        if result_code == RESULT_OK and intent is not None:
            try:
                barcode = intent.getStringExtra("SCAN_RESULT")
                cb(barcode)
            except Exception as e:
                print(f"Error reading scan result: {e}")
                cb(None)
        else:
            # El usuario canceló el escaneo
            cb(None)

    def scan_from_image(self, _image_path):
        """Escanear código de barras desde imagen (no implementado en Android)."""
        return self._simulate_scan()

    def _simulate_scan(self):
        """Simulación para pruebas en escritorio."""
        return "123456789012"
