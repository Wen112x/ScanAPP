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

    def scan_from_mlkit(self, image_path, callback):
        """Escanear código de barras desde imagen con ML Kit (in-app, sin salir).

        Ejecuta el escaneo en un hilo de fondo y llama a
        callback(barcode) o callback(None, error=mensaje) en el hilo de Kivy.
        """
        import threading

        if not self.is_android:
            # En escritorio, simular resultado
            callback(self._simulate_scan())
            return

        def _scan():
            try:
                from jnius import autoclass

                BitmapFactory = autoclass('android.graphics.BitmapFactory')
                InputImage = autoclass('com.google.mlkit.vision.common.InputImage')
                BarcodeScanning = autoclass('com.google.mlkit.vision.barcode.BarcodeScanning')
                Tasks = autoclass('com.google.android.gms.tasks.Tasks')

                bitmap = BitmapFactory.decodeFile(image_path)
                if bitmap is None:
                    from kivy.clock import Clock
                    Clock.schedule_once(
                        lambda _dt: callback(None, error="无法读取图像文件")
                    )
                    return

                image = InputImage.fromBitmap(bitmap, 0)
                scanner = BarcodeScanning.getClient()
                task = scanner.process(image)

                # Bloquear hasta que ML Kit termine (hilo de fondo, es seguro)
                result = Tasks.await_(task)
                barcode_list = result.toArray()

                from kivy.clock import Clock
                if barcode_list and len(barcode_list) > 0:
                    value = barcode_list[0].getRawValue()
                    Clock.schedule_once(lambda _dt: callback(value))
                else:
                    Clock.schedule_once(
                        lambda _dt: callback(None, error="没有检测到条码\n请靠近商品并重试")
                    )

            except Exception as e:
                print(f"ML Kit scan error: {e}")
                from kivy.clock import Clock
                Clock.schedule_once(lambda _dt: callback(None, error=f"扫描错误: {e}"))

        threading.Thread(target=_scan, daemon=True).start()

    def _simulate_scan(self):
        """Simulación para pruebas en escritorio."""
        return "123456789012"
