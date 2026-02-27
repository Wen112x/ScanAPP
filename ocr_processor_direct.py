# -*- coding: utf-8 -*-
"""
OCR处理器 - 直接HTTP版本
使用requests直接调用Claude API，无需anthropic库
"""

import base64
import json
import os
import re
import requests
from kivy.storage.jsonstore import JsonStore

DEFAULT_MODEL = "claude-sonnet-4-6"

class OCRProcessor:
    def __init__(self, api_key, model=None):
        """
        初始化OCR处理器
        Args:
            api_key: Claude API密钥
            model:   Claude模型ID (默认 claude-sonnet-4-6)
        """
        self.api_key = api_key
        self.model = model or DEFAULT_MODEL
        self.api_url = "https://api.anthropic.com/v1/messages"

        # 验证API密钥格式
        if not api_key or not api_key.startswith('sk-ant-'):
            print("⚠️ 警告: API密钥格式可能不正确")
    
    def encode_image_to_base64(self, image_path):
        """将图像编码为base64"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"❌ 图像编码失败: {e}")
            raise
    
    def extract_delivery_note_data(self, image_paths, progress_callback=None):
        """
        从送货单图像中提取数据 - 逐张处理以避免输出限制
        Args:
            image_paths: 图像文件路径列表
            progress_callback: 进度回调函数 callback(current, total, message)
        Returns:
            提取的数据列表
        """
        if not self.api_key:
            raise Exception("未设置API密钥")
        
        extracted_data = []
        total_images = len(image_paths)
        
        for index, image_path in enumerate(image_paths, 1):
            try:
                filename = os.path.basename(image_path)
                progress_msg = f"正在处理图像 {index}/{total_images}: {filename}"
                print(f"🔄 {progress_msg}")
                
                # 通知进度
                if progress_callback:
                    progress_callback(index, total_images, progress_msg)
                
                # 编码图像
                base64_image = self.encode_image_to_base64(image_path)
                
                # 构建请求数据
                headers = {
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01"
                }
                
                payload = {
                    "model": self.model,
                    "max_tokens": 3000,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/jpeg",
                                        "data": base64_image
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": """分析这张送货单图像并提取所有表格数据。

重要：只返回有效的JSON格式，格式如下：

{
  "headers": ["列1", "列2", "列3"],
  "rows": [
    ["值1", "值2", "值3"],
    ["值1", "值2", "值3"]
  ]
}

规则：
- 提取所有可见的列
- 包含所有数据行
- 对引号和特殊字符使用正确的JSON转义
- JSON前后不要包含任何其他文本
- 确保所有字符串都正确引用
- 不要使用尾随逗号

只返回JSON。"""
                                }
                            ]
                        }
                    ]
                }
                
                # 发送请求
                api_progress_msg = f"发送到Claude API处理图像 {index}/{total_images}..."
                print(f"📡 {api_progress_msg}")
                if progress_callback:
                    progress_callback(index, total_images, api_progress_msg)
                    
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=90  # 增加超时时间给Sonnet 4
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if 'content' in result and len(result['content']) > 0:
                        response_text = result['content'][0]['text']
                        print(f"✅ Claude响应: {response_text[:200]}...")
                        
                        # 解析JSON响应
                        table_data = self._parse_response(response_text)
                        if table_data:
                            extracted_data.append(table_data)
                            success_msg = f"✅ 图像 {index}/{total_images} 处理完成"
                            print(success_msg)
                            if progress_callback:
                                progress_callback(index, total_images, success_msg)
                        else:
                            error_msg = f"⚠️ 图像 {index}/{total_images} 未提取到数据"
                            print(error_msg)
                            if progress_callback:
                                progress_callback(index, total_images, error_msg)
                    else:
                        print("❌ API响应格式异常")
                else:
                    error_msg = f"API请求失败: {response.status_code}"
                    try:
                        error_detail = response.json()
                        if 'error' in error_detail:
                            error_msg += f" - {error_detail['error'].get('message', '')}"
                    except:
                        error_msg += f" - {response.text[:200]}"
                    
                    print(f"❌ {error_msg}")
                    raise Exception(error_msg)
                    
            except Exception as e:
                error_msg = f"❌ 图像 {index}/{total_images} 处理失败: {str(e)}"
                print(error_msg)
                if progress_callback:
                    progress_callback(index, total_images, error_msg)
                continue
        
        # Progreso final
        final_msg = f"🎉 处理完成！成功提取 {len(extracted_data)} 个表格，总计 {total_images} 张图像"
        print(final_msg)
        if progress_callback:
            progress_callback(total_images, total_images, final_msg)
        
        return extracted_data
    
    def _parse_response(self, response_text):
        """解析Claude的响应文本"""
        try:
            # 尝试提取JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group()
                
                # 清理JSON
                json_text = self._clean_json(json_text)
                
                try:
                    json_data = json.loads(json_text)
                    if 'headers' in json_data and 'rows' in json_data:
                        print(f"✅ 成功解析表格，列数: {len(json_data['headers'])}, 行数: {len(json_data['rows'])}")
                        return json_data
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析错误: {e}")
                    # 尝试修复数据
                    salvaged_data = self._salvage_data(response_text)
                    if salvaged_data:
                        return salvaged_data
            
            print("❌ 未找到有效的JSON数据")
            return None
            
        except Exception as e:
            print(f"❌ 响应解析失败: {e}")
            return None
    
    def _clean_json(self, json_text):
        """清理JSON格式问题"""
        # 移除尾随逗号
        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
        
        # 移除控制字符
        json_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_text)
        
        return json_text
    
    def _salvage_data(self, response_text):
        """尝试从损坏的响应中提取数据"""
        try:
            # 查找headers模式
            headers_match = re.search(r'"headers":\s*\[(.*?)\]', response_text, re.DOTALL)
            rows_match = re.search(r'"rows":\s*\[(.*?)\]\s*\}', response_text, re.DOTALL)
            
            if headers_match and rows_match:
                headers_text = headers_match.group(1)
                rows_text = rows_match.group(1)
                
                # 提取headers
                headers = re.findall(r'"([^"]*)"', headers_text)
                
                # 提取rows
                rows = []
                row_matches = re.findall(r'\[(.*?)\]', rows_text)
                for row_match in row_matches:
                    values = re.findall(r'"([^"]*)"', row_match)
                    if values:
                        rows.append(values)
                
                if headers and rows:
                    print(f"🔧 数据修复成功，列数: {len(headers)}, 行数: {len(rows)}")
                    return {
                        "headers": headers,
                        "rows": rows
                    }
        except Exception as e:
            print(f"❌ 数据修复失败: {e}")
            
        return None

# 配置管理类
class OCRConfig:
    """管理OCR配置的工具类"""
    
    def __init__(self):
        self.config_store = JsonStore('ocr_config.json')
    
    def save_api_key(self, api_key):
        """保存API密钥"""
        existing_model = self.get_model()
        self.config_store.put('api', api_key=api_key, model=existing_model or DEFAULT_MODEL)
        print("✅ API密钥已保存")

    def save_model(self, model):
        """保存模型ID"""
        existing_key = self.get_api_key() or ''
        self.config_store.put('api', api_key=existing_key, model=model)
        print(f"✅ 模型已保存: {model}")

    def save_config(self, api_key, model):
        """同时保存API密钥和模型"""
        self.config_store.put('api', api_key=api_key, model=model)
        print(f"✅ 配置已保存 (模型: {model})")

    def get_api_key(self):
        """获取API密钥"""
        try:
            return self.config_store.get('api')['api_key']
        except KeyError:
            return None

    def get_model(self):
        """获取模型ID"""
        try:
            return self.config_store.get('api').get('model') or DEFAULT_MODEL
        except KeyError:
            return DEFAULT_MODEL

    def has_api_key(self):
        """检查是否已设置API密钥"""
        api_key = self.get_api_key()
        return api_key is not None and api_key.strip() != ""