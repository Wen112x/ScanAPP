# -*- coding: utf-8 -*-
"""
OCR处理器 - Android版本
通过HTTP连接到PC服务器进行OCR处理
"""

import requests
import json
import os
from kivy.storage.jsonstore import JsonStore

class OCRProcessorAndroid:
    def __init__(self, server_url=None):
        """
        初始化Android OCR处理器
        Args:
            server_url: 服务器地址，如 http://192.168.1.100:5000
        """
        self.server_url = server_url
        self.config_store = JsonStore('ocr_config.json')
        
        # 如果没有提供服务器地址，尝试从配置中读取
        if not self.server_url:
            try:
                self.server_url = self.config_store.get('server')['url']
            except KeyError:
                self.server_url = None
        
        print(f"OCR处理器初始化 - 服务器: {self.server_url}")
    
    def set_server_url(self, url):
        """设置服务器地址并保存到配置"""
        self.server_url = url
        # 保存到本地配置
        self.config_store.put('server', url=url)
        print(f"服务器地址已设置: {url}")
    
    def get_server_url(self):
        """获取当前服务器地址"""
        return self.server_url
    
    def test_connection(self):
        """测试与服务器的连接"""
        if not self.server_url:
            return False, "未设置服务器地址"
        
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    ocr_available = data.get('ocr_available', False)
                    return True, f"连接成功 - OCR功能: {'可用' if ocr_available else '不可用'}"
                else:
                    return False, "服务器状态异常"
            else:
                return False, f"服务器响应错误: {response.status_code}"
        except requests.exceptions.ConnectTimeout:
            return False, "连接超时 - 请检查服务器地址和网络连接"
        except requests.exceptions.ConnectionError:
            return False, "连接失败 - 请确保服务器正在运行且在同一网络"
        except Exception as e:
            return False, f"连接测试失败: {str(e)}"
    
    def extract_delivery_note_data(self, image_paths):
        """
        向服务器发送图像进行OCR处理
        Args:
            image_paths: 图像文件路径列表
        Returns:
            提取的数据列表
        """
        if not self.server_url:
            raise Exception("未设置服务器地址")
        
        if not image_paths:
            return []
        
        try:
            # 准备上传的文件
            files = []
            for i, image_path in enumerate(image_paths):
                if not os.path.exists(image_path):
                    print(f"⚠️ 文件不存在: {image_path}")
                    continue
                
                # 打开文件准备上传
                file_obj = open(image_path, 'rb')
                files.append(('images', (f'image_{i}.jpg', file_obj, 'image/jpeg')))
            
            if not files:
                return []
            
            print(f"📡 发送 {len(files)} 张图像到服务器进行OCR处理...")
            
            # 发送POST请求到服务器
            response = requests.post(
                f"{self.server_url}/ocr",
                files=files,
                timeout=60  # 60秒超时
            )
            
            # 关闭文件
            for _, (_, file_obj, _) in files:
                file_obj.close()
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    data = result.get('data', [])
                    print(f"✅ OCR处理成功，获得 {len(data)} 个表格")
                    return data
                else:
                    error_msg = result.get('error', '未知错误')
                    print(f"❌ OCR处理失败: {error_msg}")
                    raise Exception(f"OCR处理失败: {error_msg}")
            else:
                error_msg = f"服务器错误 {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', error_msg)
                except:
                    pass
                print(f"❌ 服务器响应错误: {error_msg}")
                raise Exception(f"服务器响应错误: {error_msg}")
                
        except requests.exceptions.ConnectTimeout:
            raise Exception("请求超时 - OCR处理时间过长")
        except requests.exceptions.ConnectionError:
            raise Exception("连接失败 - 请确保服务器正在运行")
        except Exception as e:
            print(f"❌ OCR请求异常: {e}")
            raise Exception(f"OCR请求失败: {str(e)}")
    
    def is_available(self):
        """检查OCR功能是否可用"""
        if not self.server_url:
            return False
        
        try:
            success, _ = self.test_connection()
            return success
        except:
            return False

# 兼容性函数 - 保持与原来OCRProcessor相同的接口
class OCRProcessor:
    """兼容性类 - 保持与桌面版相同的接口"""
    
    def __init__(self, api_key_or_server_url):
        """
        初始化OCR处理器
        Args:
            api_key_or_server_url: 在Android上，这应该是服务器URL
        """
        # 在Android上，我们忽略api_key，使用server_url
        if api_key_or_server_url and api_key_or_server_url.startswith('http'):
            self.processor = OCRProcessorAndroid(api_key_or_server_url)
        else:
            # 尝试使用默认配置
            self.processor = OCRProcessorAndroid()
    
    def extract_delivery_note_data(self, image_paths):
        """提取送货单数据"""
        return self.processor.extract_delivery_note_data(image_paths)
    
    def set_server_url(self, url):
        """设置服务器地址"""
        self.processor.set_server_url(url)
    
    def test_connection(self):
        """测试连接"""
        return self.processor.test_connection()
    
    def is_available(self):
        """检查是否可用"""
        return self.processor.is_available()