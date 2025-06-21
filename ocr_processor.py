# -*- coding: utf-8 -*-
import base64
import json
import re
from anthropic import Anthropic

class OCRProcessor:
    def __init__(self, api_key):
        self.client = Anthropic(api_key=api_key)
    
    def encode_image_to_base64(self, image_path):
        """Encode image to base64 for Claude API"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def extract_delivery_note_data(self, image_paths):
        """Extract all table data from delivery note images using Claude Vision"""
        extracted_data = []
        
        for image_path in image_paths:
            try:
                # Encode image directly (no preprocessing needed for Claude)
                base64_image = self.encode_image_to_base64(image_path)
                
                # Build request to Claude
                message = self.client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=2000,
                    messages=[
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
                                    "text": """Analyze this delivery note image and extract ALL table data. 

IMPORTANT: Return ONLY valid JSON in this exact format:

{
  "headers": ["Column1", "Column2", "Column3"],
  "rows": [
    ["value1", "value2", "value3"],
    ["value1", "value2", "value3"]
  ]
}

Rules:
- Extract ALL columns you can see
- Include ALL rows of data
- Use proper JSON escaping for quotes and special characters
- Do not include any text before or after the JSON
- Ensure all strings are properly quoted
- Do not use trailing commas

Return the JSON only."""
                                }
                            ]
                        }
                    ]
                )
                
                # Parse response
                response_text = message.content[0].text
                print(f"Claude response: {response_text}")
                
                # Try to extract and clean JSON
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group()
                    
                    # Clean up common JSON issues
                    json_text = self._clean_json(json_text)
                    
                    try:
                        json_data = json.loads(json_text)
                        if 'headers' in json_data and 'rows' in json_data:
                            # Store original table data for column mapping
                            extracted_data.append(json_data)
                    except json.JSONDecodeError as e:
                        print(f"JSON parse error: {e}")
                        print(f"Problematic JSON: {json_text[:200]}...")
                        # Try to salvage data manually
                        salvaged_data = self._salvage_data(response_text)
                        if salvaged_data:
                            extracted_data.append(salvaged_data)
                
            except Exception as e:
                print(f"Error processing image {image_path}: {str(e)}")
                continue
        
        return extracted_data
    
    def _clean_json(self, json_text):
        """Clean common JSON formatting issues"""
        # Remove any trailing commas before closing brackets
        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
        
        # Fix unescaped quotes in strings
        json_text = re.sub(r'([^\\])"([^"]*)"([^,}\]:])', r'\1"\2"\3', json_text)
        
        # Remove any control characters
        json_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_text)
        
        return json_text
    
    def _salvage_data(self, response_text):
        """Try to salvage data from malformed response"""
        try:
            # Look for headers pattern
            headers_match = re.search(r'"headers":\s*\[(.*?)\]', response_text, re.DOTALL)
            rows_match = re.search(r'"rows":\s*\[(.*?)\]\s*\}', response_text, re.DOTALL)
            
            if headers_match and rows_match:
                headers_text = headers_match.group(1)
                rows_text = rows_match.group(1)
                
                # Extract headers
                headers = re.findall(r'"([^"]*)"', headers_text)
                
                # Extract rows - this is more complex
                rows = []
                # Find all row arrays
                row_matches = re.findall(r'\[(.*?)\]', rows_text)
                for row_match in row_matches:
                    # Extract values from each row
                    values = re.findall(r'"([^"]*)"', row_match)
                    if values:
                        rows.append(values)
                
                if headers and rows:
                    return {
                        "headers": headers,
                        "rows": rows
                    }
        except Exception as e:
            print(f"Data salvage failed: {e}")
            
        return None
    
    def _convert_table_to_items(self, table_data):
        """Convert table data to item format expected by the application"""
        items = []
        headers = [h.lower().strip() for h in table_data.get('headers', [])]
        rows = table_data.get('rows', [])
        
        # Try to map headers to expected fields
        header_mapping = {}
        for i, header in enumerate(headers):
            if any(keyword in header for keyword in ['código', 'code', 'barcode', '条码']):
                header_mapping['barcode'] = i
            elif any(keyword in header for keyword in ['nombre', 'name', 'product', '产品', '商品']):
                header_mapping['name'] = i
            elif any(keyword in header for keyword in ['precio', 'price', 'cost', '价格']):
                header_mapping['unit_price'] = i
            elif any(keyword in header for keyword in ['cantidad', 'quantity', 'qty', '数量']):
                header_mapping['quantity'] = i
        
        # Process each row
        for row in rows:
            if len(row) > 0:
                item = {
                    'barcode': row[header_mapping.get('barcode', 0)] if header_mapping.get('barcode', 0) < len(row) else '',
                    'name': row[header_mapping.get('name', 1)] if header_mapping.get('name', 1) < len(row) else '',
                    'unit_price': row[header_mapping.get('unit_price', 2)] if header_mapping.get('unit_price', 2) < len(row) else 0,
                    'quantity': row[header_mapping.get('quantity', 3)] if header_mapping.get('quantity', 3) < len(row) else 1
                }
                items.append(item)
        
        return items
    
    def validate_extracted_data(self, items):
        """验证提取的数据"""
        validated_items = []
        
        for item in items:
            # 清理和验证数据
            validated_item = {
                'barcode': str(item.get('barcode', '')).strip() if item.get('barcode') else '',
                'name': str(item.get('name', '')).strip() if item.get('name') else '未知商品',
                'unit_price': self._parse_price(item.get('unit_price')),
                'quantity': self._parse_quantity(item.get('quantity'))
            }
            
            # 只添加有效的商品（至少有名称）
            if validated_item['name'] and validated_item['name'] != '未知商品':
                validated_items.append(validated_item)
        
        return validated_items
    
    def _parse_price(self, price):
        """解析价格"""
        if price is None:
            return 0.0
        
        try:
            # 移除货币符号和空格
            price_str = str(price).replace('¥', '').replace('$', '').replace(',', '').strip()
            return float(price_str)
        except (ValueError, TypeError):
            return 0.0
    
    def _parse_quantity(self, quantity):
        """解析数量"""
        if quantity is None:
            return 1
        
        try:
            return int(float(str(quantity)))
        except (ValueError, TypeError):
            return 1