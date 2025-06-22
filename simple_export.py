# -*- coding: utf-8 -*-
import csv
import os
from datetime import datetime

def export_to_csv(delivery_note_name, items):
    """Export delivery note to CSV (Android compatible)"""
    try:
        filename = f"delivery_note_{delivery_note_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Get app's external files directory on Android
        try:
            from jnius import autoclass
            Environment = autoclass('android.os.Environment')
            context = autoclass('org.kivy.android.PythonActivity').mActivity
            external_path = context.getExternalFilesDir(None).toString()
            filepath = os.path.join(external_path, filename)
        except:
            # Fallback for desktop
            filepath = filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow(['条码', '商品名称', '单价', '数量', '状态'])
            
            # Data rows
            for item in items:
                writer.writerow([
                    item[2] or '',  # barcode
                    item[3] or '',  # name  
                    item[4] or 0,   # price
                    item[5] or 0,   # quantity
                    item[6] or 'unchecked'  # status
                ])
        
        return filepath
        
    except Exception as e:
        print(f"Export error: {e}")
        return None