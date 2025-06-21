# -*- coding: utf-8 -*-
import cv2
from pyzbar import pyzbar
import numpy as np
from PIL import Image

class BarcodeScanner:
    def __init__(self):
        self.camera = None
    
    def scan_from_camera(self, callback=None):
        """从摄像头扫描条形码"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            return None
        
        found_codes = []
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 检测条形码
                barcodes = pyzbar.decode(frame)
                
                for barcode in barcodes:
                    # 提取条形码数据
                    barcode_data = barcode.data.decode('utf-8')
                    barcode_type = barcode.type
                    
                    # 绘制条形码边框
                    (x, y, w, h) = barcode.rect
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    
                    # 显示条形码数据
                    text = f"{barcode_data} ({barcode_type})"
                    cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
                    if barcode_data not in found_codes:
                        found_codes.append(barcode_data)
                        if callback:
                            callback(barcode_data)
                        cap.release()
                        cv2.destroyAllWindows()
                        return barcode_data
                
                # 显示帧
                cv2.imshow('条形码扫描器 - 按ESC退出', frame)
                
                # 按ESC退出
                if cv2.waitKey(1) & 0xFF == 27:
                    break
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
        
        return None
    
    def scan_from_image(self, image_path):
        """从图像文件扫描条形码"""
        try:
            # 读取图像
            image = cv2.imread(image_path)
            if image is None:
                return []
            
            # 转换为灰度
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 解码条形码
            barcodes = pyzbar.decode(gray)
            
            found_codes = []
            for barcode in barcodes:
                barcode_data = barcode.data.decode('utf-8')
                found_codes.append(barcode_data)
            
            return found_codes
        
        except Exception as e:
            print(f"扫描图像时出错: {str(e)}")
            return []
    
    def validate_barcode(self, barcode):
        """验证条形码格式"""
        if not barcode:
            return False
        
        # EAN-13 (13位数字)
        if len(barcode) == 13 and barcode.isdigit():
            return self._validate_ean13(barcode)
        
        # EAN-8 (8位数字)
        if len(barcode) == 8 and barcode.isdigit():
            return self._validate_ean8(barcode)
        
        # UPC-A (12位数字)
        if len(barcode) == 12 and barcode.isdigit():
            return self._validate_upca(barcode)
        
        # 其他格式（Code 128, Code 39等）
        return len(barcode) > 0
    
    def _validate_ean13(self, barcode):
        """验证EAN-13条形码"""
        try:
            digits = [int(d) for d in barcode[:-1]]
            check_digit = int(barcode[-1])
            
            odd_sum = sum(digits[::2])
            even_sum = sum(digits[1::2])
            total = odd_sum + even_sum * 3
            
            calculated_check = (10 - (total % 10)) % 10
            return calculated_check == check_digit
        except:
            return False
    
    def _validate_ean8(self, barcode):
        """验证EAN-8条形码"""
        try:
            digits = [int(d) for d in barcode[:-1]]
            check_digit = int(barcode[-1])
            
            odd_sum = sum(digits[::2])
            even_sum = sum(digits[1::2])
            total = odd_sum * 3 + even_sum
            
            calculated_check = (10 - (total % 10)) % 10
            return calculated_check == check_digit
        except:
            return False
    
    def _validate_upca(self, barcode):
        """验证UPC-A条形码"""
        try:
            digits = [int(d) for d in barcode[:-1]]
            check_digit = int(barcode[-1])
            
            odd_sum = sum(digits[::2])
            even_sum = sum(digits[1::2])
            total = odd_sum * 3 + even_sum
            
            calculated_check = (10 - (total % 10)) % 10
            return calculated_check == check_digit
        except:
            return False