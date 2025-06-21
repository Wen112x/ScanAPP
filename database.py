# -*- coding: utf-8 -*-
import sqlite3
import sys
import pandas as pd
from datetime import datetime
import os

class DatabaseManager:
    def __init__(self, db_path="inventory.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create delivery notes table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS delivery_notes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        total_items INTEGER DEFAULT 0
                    )
                ''')
                
                # Create items table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        delivery_note_id INTEGER,
                        barcode TEXT,
                        name TEXT NOT NULL,
                        unit_price REAL,
                        quantity INTEGER,
                        status TEXT DEFAULT 'unchecked',
                        FOREIGN KEY (delivery_note_id) REFERENCES delivery_notes (id)
                    )
                ''')
                
                conn.commit()
                print("Database initialized successfully")
        except Exception as e:
            print(f"Database initialization error: {e}")
            sys.exit(1)
    
    def create_delivery_note(self, name):
        """创建新的送货单"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO delivery_notes (name) VALUES (?)",
                (name,)
            )
            conn.commit()
            return cursor.lastrowid
    
    def add_item(self, delivery_note_id, barcode, name, unit_price, quantity):
        """添加商品到送货单"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO items (delivery_note_id, barcode, name, unit_price, quantity)
                VALUES (?, ?, ?, ?, ?)
            ''', (delivery_note_id, barcode, name, unit_price, quantity))
            
            item_id = cursor.lastrowid
            conn.commit()
            return item_id
    
    def update_delivery_note_count(self, delivery_note_id):
        """Update the total items count for a delivery note"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE delivery_notes 
                SET total_items = (
                    SELECT COUNT(*) FROM items WHERE delivery_note_id = ?
                )
                WHERE id = ?
            ''', (delivery_note_id, delivery_note_id))
            
            conn.commit()
    
    def fix_all_delivery_note_counts(self):
        """Fix the item count for all delivery notes"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all delivery notes
            cursor.execute("SELECT id FROM delivery_notes")
            delivery_notes = cursor.fetchall()
            
            for note in delivery_notes:
                delivery_note_id = note[0]
                
                # Count items for this delivery note
                cursor.execute("SELECT COUNT(*) FROM items WHERE delivery_note_id = ?", (delivery_note_id,))
                actual_count = cursor.fetchone()[0]
                
                # Update count for this delivery note
                cursor.execute('''
                    UPDATE delivery_notes 
                    SET total_items = ?
                    WHERE id = ?
                ''', (actual_count, delivery_note_id))
            
            conn.commit()
    
    def get_delivery_notes(self):
        """获取所有送货单"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM delivery_notes ORDER BY date_created DESC")
            return cursor.fetchall()
    
    def get_items_by_delivery_note(self, delivery_note_id):
        """根据送货单ID获取商品"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM items WHERE delivery_note_id = ?",
                (delivery_note_id,)
            )
            return cursor.fetchall()
    
    def search_item_by_barcode(self, delivery_note_id, barcode):
        """根据条形码搜索商品"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM items 
                WHERE delivery_note_id = ? AND barcode = ?
            ''', (delivery_note_id, barcode))
            return cursor.fetchone()
    
    def update_item_status(self, item_id, status):
        """更新商品状态 (unchecked, correct, incorrect)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE items SET status = ? WHERE id = ?",
                (status, item_id)
            )
            conn.commit()
    
    def export_to_excel(self, delivery_note_id, file_path):
        """导出送货单数据到Excel"""
        with sqlite3.connect(self.db_path) as conn:
            # 获取送货单信息
            delivery_note = pd.read_sql_query(
                "SELECT * FROM delivery_notes WHERE id = ?",
                conn, params=(delivery_note_id,)
            )
            
            # 获取商品信息
            items = pd.read_sql_query(
                "SELECT barcode, name, unit_price, quantity, status FROM items WHERE delivery_note_id = ?",
                conn, params=(delivery_note_id,)
            )
            
            # 创建Excel文件
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                delivery_note.to_excel(writer, sheet_name='送货单信息', index=False)
                items.to_excel(writer, sheet_name='商品清单', index=False)
            
            return True
    
    def delete_delivery_note(self, delivery_note_id):
        """删除送货单及其所有商品"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM items WHERE delivery_note_id = ?", (delivery_note_id,))
            cursor.execute("DELETE FROM delivery_notes WHERE id = ?", (delivery_note_id,))
            conn.commit()