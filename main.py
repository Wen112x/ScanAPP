# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.config import Config
# Configuración para Android - solo en desktop
import platform
if platform.system() == 'Windows' or platform.system() == 'Linux':
    # Solo configurar ventana en desktop
    Config.set('graphics', 'width', '360')
    Config.set('graphics', 'height', '640')
    Config.set('graphics', 'resizable', False)

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import OneLineListItem, ThreeLineListItem, MDList
from kivymd.uix.dialog import MDDialog
from kivymd.uix.card import MDCard
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.navigationdrawer import MDNavigationDrawer
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.progressbar import MDProgressBar
from plyer import camera, filechooser
import os
import threading
import sqlite3
from database import DatabaseManager
from ocr_processor import OCRProcessor

# Import appropriate barcode scanner
try:
    from android_barcode import AndroidBarcodeScanner as BarcodeScanner
    print("Using Android barcode scanner")
except ImportError:
    try:
        from barcode_scanner import BarcodeScanner
        print("Using desktop barcode scanner")
    except ImportError:
        BarcodeScanner = None
        print("No barcode scanner available")

class MainScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'main'
        
        # Main layout
        main_layout = MDBoxLayout(orientation='vertical')
        
        # Top toolbar
        toolbar = MDTopAppBar(
            title="库存管理系统",
            elevation=10,
        )
        main_layout.add_widget(toolbar)
        
        # Content area
        content = MDBoxLayout(
            orientation='vertical',
            padding=20,
            spacing=20
        )
        
        # Welcome label
        welcome_label = MDLabel(
            text="欢迎使用库存管理系统",
            theme_text_color="Primary",
            size_hint_y=None,
            height=50,
            halign="center"
        )
        content.add_widget(welcome_label)
        
        # Navigation buttons
        nav_button = MDRaisedButton(
            text="管理送货单",
            size_hint_y=None,
            height=60
        )
        nav_button.bind(on_release=self.go_to_delivery_notes)
        content.add_widget(nav_button)
        
        main_layout.add_widget(content)
        self.add_widget(main_layout)
    
    def go_to_delivery_notes(self, instance):
        self.manager.current = 'delivery_notes'

class DeliveryNotesScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'delivery_notes'
        
        # Main layout
        main_layout = MDBoxLayout(orientation='vertical')
        
        # Top toolbar
        toolbar = MDTopAppBar(
            title="送货单管理",
            left_action_items=[["arrow-left", lambda x: self.go_back()]],
            right_action_items=[["plus", lambda x: self.create_new_delivery_note()]],
            elevation=10,
        )
        main_layout.add_widget(toolbar)
        
        # Delivery note list
        self.delivery_list = MDList()
        scroll = MDScrollView()
        scroll.add_widget(self.delivery_list)
        main_layout.add_widget(scroll)
        
        self.add_widget(main_layout)
        self.refresh_delivery_notes()
    
    @property
    def db(self):
        """Get the shared database instance from the app"""
        return App.get_running_app().db
    
    def go_back(self):
        self.manager.current = 'main'
    
    def create_new_delivery_note(self):
        """创建新的送货单"""
        text_field = MDTextField(
            hint_text="输入送货单名称",
            helper_text="请输入送货单名称",
            helper_text_mode="on_focus"
        )
        
        dialog = MDDialog(
            title="创建新送货单",
            type="custom",
            content_cls=text_field,
            buttons=[
                MDFlatButton(
                    text="取消"
                ),
                MDRaisedButton(
                    text="创建"
                ),
            ],
        )
        # Bind button events
        dialog.buttons[0].bind(on_release=lambda x: dialog.dismiss())
        dialog.buttons[1].bind(on_release=lambda x: self.save_new_delivery_note(text_field.text, dialog))
        dialog.open()
    
    def save_new_delivery_note(self, name, dialog):
        if name and name.strip():
            self.db.create_delivery_note(name.strip())
            self.refresh_delivery_notes()
            dialog.dismiss()
    
    def refresh_delivery_notes(self):
        self.delivery_list.clear_widgets()
        notes = self.db.get_delivery_notes()
        
        for note in notes:
            # Create a card with delivery note info and delete button
            card = MDCard(
                padding=10,
                size_hint_y=None,
                height=80,
                spacing=10,
                elevation=2
            )
            card.bind(on_release=lambda x, note_id=note[0]: self.open_delivery_note(note_id))
            
            # Horizontal layout for content and delete button
            content_layout = MDBoxLayout(orientation='horizontal', spacing=10)
            
            # Info layout (left side)
            info_layout = MDBoxLayout(orientation='vertical', size_hint_x=0.85)
            info_layout.add_widget(MDLabel(
                text=note[1], 
                theme_text_color="Primary",
                font_style="H6",
                size_hint_y=0.4
            ))
            info_layout.add_widget(MDLabel(
                text=f"创建时间: {note[2]}",
                theme_text_color="Secondary", 
                font_style="Caption",
                size_hint_y=0.3
            ))
            info_layout.add_widget(MDLabel(
                text=f"商品数量: {note[3]}",
                theme_text_color="Secondary",
                font_style="Caption", 
                size_hint_y=0.3
            ))
            
            # Delete button (right side)
            delete_btn = MDIconButton(
                icon="delete",
                size_hint_x=0.15,
                theme_icon_color="Custom",
                icon_color=[1, 0.2, 0.2, 1]
            )
            delete_btn.bind(on_release=lambda x, note_id=note[0]: self.delete_delivery_note(note_id))
            
            content_layout.add_widget(info_layout)
            content_layout.add_widget(delete_btn)
            card.add_widget(content_layout)
            self.delivery_list.add_widget(card)
    
    def open_delivery_note(self, note_id):
        app = App.get_running_app()
        app.current_delivery_note_id = note_id
        self.manager.current = 'delivery_detail'
    
    def delete_delivery_note(self, note_id):
        """删除送货单并确认"""
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton, MDRaisedButton
        
        dialog = MDDialog(
            title="删除送货单",
            text="确定要删除此送货单吗？所有相关商品也将被删除。",
            buttons=[
                MDFlatButton(
                    text="取消"
                ),
                MDRaisedButton(
                    text="删除"
                ),
            ],
        )
        # Bind delete dialog buttons
        dialog.buttons[0].bind(on_release=lambda x: dialog.dismiss())
        dialog.buttons[1].bind(on_release=lambda x: self.confirm_delete(note_id, dialog))
        dialog.open()
    
    def confirm_delete(self, note_id, dialog):
        """执行实际删除"""
        try:
            # Delete associated items first
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM items WHERE delivery_note_id = ?", (note_id,))
                cursor.execute("DELETE FROM delivery_notes WHERE id = ?", (note_id,))
                conn.commit()
            
            self.refresh_delivery_notes()
            dialog.dismiss()
        except Exception as e:
            print(f"删除送货单时出错: {e}")
            dialog.dismiss()

class DeliveryDetailScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'delivery_detail'
        
        # Main layout
        main_layout = MDBoxLayout(orientation='vertical')
        
        # Top toolbar
        toolbar = MDTopAppBar(
            title="送货单详情",
            left_action_items=[["arrow-left", lambda x: self.go_back()]],
            right_action_items=[
                ["camera", lambda x: self.scan_delivery_note()],
                ["file-excel", lambda x: self.export_to_excel()]
            ],
            elevation=10,
        )
        main_layout.add_widget(toolbar)
        
        # Loading overlay
        self.loading_layout = MDBoxLayout(
            orientation='vertical',
            spacing=20,
            padding=50,
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            opacity=0
        )
        
        self.loading_spinner = MDSpinner(size_hint=(None, None), size=(46, 46))
        loading_label = MDLabel(
            text="正在处理图像...",
            theme_text_color="Primary",
            halign="center"
        )
        
        self.loading_layout.add_widget(self.loading_spinner)
        self.loading_layout.add_widget(loading_label)
        
        # Items list
        self.items_list = MDList()
        scroll = MDScrollView()
        scroll.add_widget(self.items_list)
        
        # Add loading overlay and items list to main layout
        content_layout = MDBoxLayout()
        content_layout.add_widget(scroll)
        content_layout.add_widget(self.loading_layout)
        
        main_layout.add_widget(content_layout)
        self.add_widget(main_layout)
        
        # Initialize variables
        self.photo_count = 0
        self.collected_images = []
    
    @property
    def db(self):
        """Get the shared database instance from the app"""
        return App.get_running_app().db
    
    def on_enter(self):
        # Clear any previous session data
        self.photo_count = 0
        self.collected_images = []
        self.refresh_items()
    
    def go_back(self):
        self.manager.current = 'delivery_notes'
    
    def show_loading(self, show=True):
        """显示或隐藏加载指示器"""
        if show:
            self.loading_layout.opacity = 1
            self.loading_spinner.active = True
        else:
            self.loading_layout.opacity = 0
            self.loading_spinner.active = False
    
    def scan_delivery_note(self):
        # Select image source
        content = MDBoxLayout(
            orientation='vertical',
            spacing=20,
            size_hint_y=None,
            height=200
        )
        
        camera_btn = MDRaisedButton(
            text="拍照",
            size_hint_y=None,
            height=50
        )
        camera_btn.bind(on_release=lambda x: self.take_photos())
        
        gallery_btn = MDRaisedButton(
            text="从相册选择",
            size_hint_y=None,
            height=50
        )
        gallery_btn.bind(on_release=lambda x: self.choose_from_gallery())
        
        content.add_widget(camera_btn)
        content.add_widget(gallery_btn)
        
        self.source_dialog = MDDialog(
            title="选择图像源",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="取消"
                ),
            ],
        )
        # Bind source dialog button
        self.source_dialog.buttons[0].bind(on_release=lambda x: self.source_dialog.dismiss())
        self.source_dialog.open()
    
    def take_photos(self):
        self.source_dialog.dismiss()
        self.photo_count = 0
        self.collected_images = []
        self.take_next_photo()
    
    def take_next_photo(self):
        self.photo_count += 1
        try:
            filename = f'temp_photo_{self.photo_count}.jpg'
            camera.take_picture(filename=filename, on_complete=self.on_photo_taken_multi)
        except Exception as e:
            print(f"相机失败: {e}")
    
    def on_photo_taken_multi(self, filename):
        if filename:
            self.collected_images.append(filename)
            
            # Ask if user wants to take more photos
            dialog = MDDialog(
                title="继续拍照？",
                text=f"第 {self.photo_count} 张照片已拍摄。是否继续拍照？",
                buttons=[
                    MDFlatButton(
                        text="完成"
                    ),
                    MDRaisedButton(
                        text="继续拍照"
                    ),
                ],
            )
            # Bind photo dialog buttons
            dialog.buttons[0].bind(on_release=lambda x: self.finish_photo_session(dialog))
            dialog.buttons[1].bind(on_release=lambda x: self.continue_photo_session(dialog))
            dialog.open()
    
    def continue_photo_session(self, dialog):
        dialog.dismiss()
        self.take_next_photo()
    
    def finish_photo_session(self, dialog):
        dialog.dismiss()
        if self.collected_images:
            self.process_images(self.collected_images)
    
    def choose_from_gallery(self):
        self.source_dialog.dismiss()
        self.collected_images = []
        self.select_next_image()
    
    def select_next_image(self):
        try:
            filechooser.open_file(on_selection=self.on_image_selected_multi)
        except Exception as e:
            print(f"文件选择器失败: {e}")
    
    def on_image_selected_multi(self, selection):
        if selection:
            self.collected_images.extend(selection)
            
            # Ask if user wants to select more images
            dialog = MDDialog(
                title="继续选择图片？",
                text=f"已选择 {len(self.collected_images)} 张图片。是否继续选择？",
                buttons=[
                    MDFlatButton(
                        text="完成"
                    ),
                    MDRaisedButton(
                        text="继续选择"
                    ),
                ],
            )
            # Bind selection dialog buttons
            dialog.buttons[0].bind(on_release=lambda x: self.finish_selection_session(dialog))
            dialog.buttons[1].bind(on_release=lambda x: self.continue_selection_session(dialog))
            dialog.open()
    
    def continue_selection_session(self, dialog):
        dialog.dismiss()
        self.select_next_image()
    
    def finish_selection_session(self, dialog):
        dialog.dismiss()
        if self.collected_images:
            self.process_images(self.collected_images)
    
    def process_images(self, image_paths):
        """处理收集的图像"""
        if not image_paths:
            return
        
        self.show_loading(True)
        
        def process_ocr():
            try:
                app = App.get_running_app()
                extracted_data = app.image_processor.extract_delivery_note_data(image_paths)
                
                # Schedule UI update on main thread
                Clock.schedule_once(lambda dt: self.show_column_mapping(extracted_data), 0)
                Clock.schedule_once(lambda dt: self.show_loading(False), 0)
                
            except Exception as e:
                print(f"OCR处理错误: {e}")
                Clock.schedule_once(lambda dt: self.show_loading(False), 0)
        
        threading.Thread(target=process_ocr).start()
    
    def show_column_mapping(self, extracted_data):
        """显示列映射对话框"""
        if not extracted_data:
            dialog = MDDialog(
                title="未找到数据",
                text="无法从图像中提取表格数据。",
                buttons=[
                    MDFlatButton(
                        text="确定"
                    ),
                ],
            )
            dialog.buttons[0].bind(on_release=lambda x: dialog.dismiss())
            dialog.open()
            return
        
        # Use first extracted table
        table_data = extracted_data[0]
        headers = table_data.get('headers', [])
        rows = table_data.get('rows', [])
        
        if not headers or not rows:
            dialog = MDDialog(
                title="未找到数据",
                text="无法从图像中提取有效的表格数据。",
                buttons=[
                    MDFlatButton(
                        text="确定"
                    ),
                ],
            )
            dialog.buttons[0].bind(on_release=lambda x: dialog.dismiss())
            dialog.open()
            return
        
        # Show column mapping screen
        app = App.get_running_app()
        mapping_screen = app.root.get_screen('column_mapping')
        mapping_screen.setup_mapping(headers, rows)
        self.manager.current = 'column_mapping'
    
    def refresh_items(self, highlight_item_id=None):
        self.items_list.clear_widgets()
        app = App.get_running_app()
        delivery_note_id = getattr(app, 'current_delivery_note_id', None)
        
        if delivery_note_id:
            try:
                items = self.db.get_items_by_delivery_note(delivery_note_id)
                
                for item in items:
                    # Create item card
                    card = MDCard(
                        padding=10,
                        size_hint_y=None,
                        height=100,
                        spacing=5,
                        elevation=1 if item[0] != highlight_item_id else 3,
                        md_bg_color=[0.9, 1, 0.9, 1] if item[0] == highlight_item_id else None
                    )
                    
                    content = MDBoxLayout(
                        orientation='horizontal',
                        spacing=10
                    )
                    
                    # Item info
                    info_layout = MDBoxLayout(orientation='vertical', size_hint_x=0.7)
                    info_layout.add_widget(MDLabel(
                        text=f"商品: {item[3]}", 
                        theme_text_color="Primary",
                        font_style="Subtitle2"
                    ))
                    info_layout.add_widget(MDLabel(
                        text=f"条码: {item[2] or '未知'}", 
                        theme_text_color="Secondary",
                        font_style="Caption"
                    ))
                    info_layout.add_widget(MDLabel(
                        text=f"数量: {item[5]} | 价格: ¥{item[4]:.2f}",
                        theme_text_color="Secondary",
                        font_style="Caption"
                    ))
                    
                    # Status and actions
                    actions_layout = MDBoxLayout(orientation='vertical', size_hint_x=0.3, spacing=5)
                    
                    status_color = [0, 0.8, 0, 1] if item[6] == 'correct' else ([0.8, 0, 0, 1] if item[6] == 'incorrect' else [0.5, 0.5, 0.5, 1])
                    status_text = "正确" if item[6] == 'correct' else ("错误" if item[6] == 'incorrect' else "未检查")
                    
                    status_btn = MDRaisedButton(
                        text=status_text,
                        size_hint_y=None,
                        height=30,
                        md_bg_color=status_color
                    )
                    status_btn.bind(on_release=lambda x, item_id=item[0]: self.toggle_item_status(item_id))
                    
                    scan_btn = MDIconButton(
                        icon="barcode-scan",
                        size_hint_y=None,
                        height=30
                    )
                    scan_btn.bind(on_release=lambda x, item_id=item[0]: self.scan_item_barcode(item_id))
                    
                    actions_layout.add_widget(status_btn)
                    actions_layout.add_widget(scan_btn)
                    
                    content.add_widget(info_layout)
                    content.add_widget(actions_layout)
                    card.add_widget(content)
                    self.items_list.add_widget(card)
                    
            except Exception as e:
                print(f"刷新商品列表时出错: {e}")
    
    def toggle_item_status(self, item_id):
        """切换商品状态"""
        current_status = self.db.get_item_status(item_id)
        
        if current_status == 'unchecked':
            new_status = 'correct'
        elif current_status == 'correct':
            new_status = 'incorrect'
        else:
            new_status = 'unchecked'
        
        self.db.update_item_status(item_id, new_status)
        self.refresh_items()
    
    def scan_item_barcode(self, item_id):
        """扫描商品条码"""
        try:
            app = App.get_running_app()
            app.current_item_id = item_id
            self.manager.current = 'barcode_scan'
        except Exception as e:
            print(f"启动条码扫描时出错: {e}")
    
    def export_to_excel(self):
        """导出到Excel"""
        try:
            app = App.get_running_app()
            delivery_note_id = getattr(app, 'current_delivery_note_id', None)
            
            if delivery_note_id:
                filename = self.db.export_delivery_note_to_excel(delivery_note_id)
                
                dialog = MDDialog(
                    title="导出成功",
                    text=f"送货单已导出到: {filename}",
                    buttons=[
                        MDFlatButton(
                            text="确定"
                        ),
                    ],
                )
                dialog.buttons[0].bind(on_release=lambda x: dialog.dismiss())
                dialog.open()
        except Exception as e:
            print(f"导出失败: {e}")

class ColumnMappingScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'column_mapping'
        self.headers = []
        self.rows = []
        
        # Main layout
        main_layout = MDBoxLayout(orientation='vertical')
        
        # Top toolbar
        toolbar = MDTopAppBar(
            title="列映射",
            left_action_items=[["arrow-left", lambda x: self.go_back()]],
            elevation=10,
        )
        main_layout.add_widget(toolbar)
        
        # Content
        self.content = MDScrollView()
        main_layout.add_widget(self.content)
        
        self.add_widget(main_layout)
    
    def on_enter(self):
        """进入屏幕时清除任何残留数据"""
        pass
    
    def go_back(self):
        self.manager.current = 'delivery_detail'
    
    def setup_mapping(self, headers, rows):
        """设置列映射界面"""
        # Clear previous data to avoid persistence
        self.headers = []
        self.rows = []
        
        self.headers = headers
        self.rows = rows
        
        layout = MDBoxLayout(
            orientation='vertical',
            spacing=20,
            padding=20,
            size_hint_y=None,
            height=len(headers) * 80 + 400  # Dynamic height
        )
        
        # Instructions
        layout.add_widget(MDLabel(
            text="将列映射到所需字段:",
            theme_text_color="Primary",
            size_hint_y=None,
            height=40
        ))
        
        # Show sample data
        sample_layout = MDBoxLayout(orientation='vertical', spacing=10, size_hint_y=None, height=100)
        sample_layout.add_widget(MDLabel(
            text="样本数据预览:",
            theme_text_color="Secondary",
            font_style="Caption"
        ))
        
        if rows:
            sample_text = " | ".join(str(cell)[:20] for cell in rows[0][:3])
            sample_layout.add_widget(MDLabel(
                text=sample_text,
                theme_text_color="Secondary",
                font_style="Caption"
            ))
        
        layout.add_widget(sample_layout)
        
        # Mapping controls
        self.mapping_controls = {}
        
        for i, header in enumerate(headers):
            control_layout = MDBoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=60)
            
            # Header label
            header_label = MDLabel(
                text=f"'{header}'",
                size_hint_x=0.4,
                theme_text_color="Primary"
            )
            
            # Mapping dropdown
            mapping_spinner = Spinner(
                text='选择字段',
                values=['条码', '商品名称', '单价', '数量', '忽略'],
                size_hint_x=0.6,
                height=40
            )
            
            # Auto-detect mapping based on header content
            header_lower = header.lower()
            if any(keyword in header_lower for keyword in ['código', 'code', 'barcode', '条码', 'referencia']):
                mapping_spinner.text = '条码'
            elif any(keyword in header_lower for keyword in ['nombre', 'name', 'product', '产品', '商品', 'producto']):
                mapping_spinner.text = '商品名称'
            elif any(keyword in header_lower for keyword in ['precio', 'price', 'cost', '价格']):
                mapping_spinner.text = '单价'
            elif any(keyword in header_lower for keyword in ['cantidad', 'quantity', 'qty', '数量']):
                mapping_spinner.text = '数量'
            
            self.mapping_controls[i] = mapping_spinner
            
            control_layout.add_widget(header_label)
            control_layout.add_widget(mapping_spinner)
            layout.add_widget(control_layout)
        
        # Import button
        import_btn = MDRaisedButton(
            text="导入数据",
            size_hint_y=None,
            height=50
        )
        import_btn.bind(on_release=self.import_mapped_data)
        layout.add_widget(import_btn)
        
        self.content.clear_widgets()
        self.content.add_widget(layout)
    
    def import_mapped_data(self, instance):
        """导入映射的数据"""
        try:
            app = App.get_running_app()
            delivery_note_id = getattr(app, 'current_delivery_note_id', None)
            
            if not delivery_note_id:
                return
            
            # Build mapping
            field_mapping = {}
            for col_index, spinner in self.mapping_controls.items():
                field_name = spinner.text
                if field_name != '忽略' and field_name != '选择字段':
                    if field_name == '条码':
                        field_mapping['barcode'] = col_index
                    elif field_name == '商品名称':
                        field_mapping['name'] = col_index
                    elif field_name == '单价':
                        field_mapping['unit_price'] = col_index
                    elif field_name == '数量':
                        field_mapping['quantity'] = col_index
            
            # Process rows
            imported_count = 0
            for row in self.rows:
                if len(row) > 0:
                    item_data = {
                        'barcode': row[field_mapping.get('barcode', 0)] if field_mapping.get('barcode', 0) < len(row) else '',
                        'name': row[field_mapping.get('name', 1)] if field_mapping.get('name', 1) < len(row) else '未知商品',
                        'unit_price': self._parse_price(row[field_mapping.get('unit_price', 2)] if field_mapping.get('unit_price', 2) < len(row) else 0),
                        'quantity': self._parse_quantity(row[field_mapping.get('quantity', 3)] if field_mapping.get('quantity', 3) < len(row) else 1)
                    }
                    
                    # Only add items with valid names
                    if item_data['name'] and item_data['name'] != '未知商品':
                        app.db.add_item(
                            delivery_note_id,
                            item_data['barcode'],
                            item_data['name'],
                            item_data['unit_price'],
                            item_data['quantity']
                        )
                        imported_count += 1
            
            # Update delivery note item count
            app.db.update_delivery_note_count(delivery_note_id)
            
            # Show success message
            dialog = MDDialog(
                title="导入成功",
                text=f"成功导入 {imported_count} 个商品。",
                buttons=[
                    MDFlatButton(
                        text="确定"
                    ),
                ],
            )
            dialog.buttons[0].bind(on_release=lambda x: self.finish_import(dialog))
            dialog.open()
            
        except Exception as e:
            print(f"导入数据时出错: {e}")
    
    def _parse_price(self, price):
        """解析价格"""
        if price is None:
            return 0.0
        
        try:
            # Remove currency symbols and spaces
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
    
    def finish_import(self, dialog):
        dialog.dismiss()
        self.manager.current = 'delivery_detail'

class BarcodeScanScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'barcode_scan'
        
        # Main layout
        main_layout = MDBoxLayout(orientation='vertical')
        
        # Top toolbar
        toolbar = MDTopAppBar(
            title="条码扫描",
            left_action_items=[["arrow-left", lambda x: self.go_back()]],
            elevation=10,
        )
        main_layout.add_widget(toolbar)
        
        # Content
        content = MDBoxLayout(
            orientation='vertical',
            padding=20,
            spacing=20
        )
        
        # Instructions
        instructions = MDLabel(
            text="请选择扫描方式:",
            theme_text_color="Primary",
            size_hint_y=None,
            height=50,
            halign="center"
        )
        content.add_widget(instructions)
        
        # Scan from camera button
        camera_btn = MDRaisedButton(
            text="使用相机扫描",
            size_hint_y=None,
            height=60
        )
        camera_btn.bind(on_release=self.scan_from_camera)
        content.add_widget(camera_btn)
        
        # Scan from image button
        image_btn = MDRaisedButton(
            text="从图片扫描",
            size_hint_y=None,
            height=60
        )
        image_btn.bind(on_release=self.scan_from_image)
        content.add_widget(image_btn)
        
        # Manual input
        manual_input = MDTextField(
            hint_text="或手动输入条码",
            helper_text="手动输入条码并按回车",
            helper_text_mode="on_focus"
        )
        manual_input.bind(on_text_validate=self.on_manual_input)
        content.add_widget(manual_input)
        
        main_layout.add_widget(content)
        self.add_widget(main_layout)
    
    def go_back(self):
        self.manager.current = 'delivery_detail'
    
    def scan_from_camera(self, instance):
        """从相机扫描条码"""
        try:
            app = App.get_running_app()
            barcode = app.barcode_scanner.scan_from_camera()
            if barcode:
                self.process_scanned_barcode(barcode)
        except Exception as e:
            print(f"相机扫描失败: {e}")
    
    def scan_from_image(self, instance):
        """从图片扫描条码"""
        try:
            filechooser.open_file(on_selection=self.on_image_selected)
        except Exception as e:
            print(f"文件选择失败: {e}")
    
    def on_image_selected(self, selection):
        if selection:
            try:
                app = App.get_running_app()
                barcode = app.barcode_scanner.scan_from_image(selection[0])
                if barcode:
                    self.process_scanned_barcode(barcode)
                else:
                    dialog = MDDialog(
                        title="扫描失败",
                        text="未能从图片中检测到条码。",
                        buttons=[
                            MDFlatButton(
                                text="确定"
                            ),
                        ],
                    )
                    dialog.buttons[0].bind(on_release=lambda x: dialog.dismiss())
                    dialog.open()
            except Exception as e:
                print(f"图片扫描失败: {e}")
    
    def on_manual_input(self, instance):
        """处理手动输入的条码"""
        barcode = instance.text.strip()
        if barcode:
            self.process_scanned_barcode(barcode)
    
    def process_scanned_barcode(self, barcode):
        """处理扫描到的条码"""
        try:
            app = App.get_running_app()
            item_id = getattr(app, 'current_item_id', None)
            
            if item_id:
                # Update item barcode
                app.db.update_item_barcode(item_id, barcode)
                
                # Show success message
                dialog = MDDialog(
                    title="扫描成功",
                    text=f"条码 {barcode} 已保存。",
                    buttons=[
                        MDFlatButton(
                            text="确定"
                        ),
                    ],
                )
                dialog.buttons[0].bind(on_release=lambda x: self.finish_scan(dialog, item_id))
                dialog.open()
        except Exception as e:
            print(f"处理条码时出错: {e}")
    
    def finish_scan(self, dialog, item_id):
        dialog.dismiss()
        # Go back to delivery detail and highlight the updated item
        detail_screen = self.manager.get_screen('delivery_detail')
        detail_screen.refresh_items(highlight_item_id=item_id)
        self.manager.current = 'delivery_detail'

class InventoryManagementApp(MDApp):
    def build(self):
        try:
            # Initialize database
            self.db = DatabaseManager()
            
            # Initialize image processor with API key check
            self.image_processor = None
            return self.check_api_key()
            
        except Exception as e:
            print(f"Error building app: {e}")
            # Return minimal screen on error
            from kivymd.uix.label import MDLabel
            return MDLabel(text=f"Error: {str(e)}")
    
    def check_api_key(self):
        """Check if API key exists, if not prompt user"""
        try:
            with open('config.txt', 'r') as f:
                api_key = f.read().strip()
                if api_key and api_key != 'your_claude_api_key_here':
                    self.image_processor = OCRProcessor(api_key)
                    return self.build_main_screens()
                else:
                    return self.show_api_key_dialog()
        except FileNotFoundError:
            return self.show_api_key_dialog()
        except Exception as e:
            print(f"Error reading API key: {e}")
            return self.show_api_key_dialog()
    
    def show_api_key_dialog(self):
        """Show dialog to input API key"""
        from kivymd.uix.textfield import MDTextField
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton, MDRaisedButton
        
        self.api_key_field = MDTextField(
            hint_text="输入 Claude API Key",
            helper_text="请输入您的 Claude API Key 以使用 OCR 功能",
            helper_text_mode="on_focus",
            password=True
        )
        
        self.api_dialog = MDDialog(
            title="设置 API Key",
            type="custom",
            content_cls=self.api_key_field,
            buttons=[
                MDFlatButton(
                    text="跳过"
                ),
                MDRaisedButton(
                    text="保存"
                ),
            ],
        )
        
        # Bind dialog buttons
        self.api_dialog.buttons[0].bind(on_release=lambda x: self.skip_api_key())
        self.api_dialog.buttons[1].bind(on_release=lambda x: self.save_api_key())
        
        # Build minimal screen first and show dialog after delay
        screen_manager = self.build_main_screens()
        
        # Show dialog after a short delay
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self.api_dialog.open(), 0.5)
        
        return screen_manager
    
    def skip_api_key(self):
        """Skip API key setup - OCR won't work"""
        self.api_dialog.dismiss()
        print("OCR功能已禁用 - 未设置 API Key")
    
    def save_api_key(self):
        """Save API key to config file"""
        api_key = self.api_key_field.text.strip()
        if api_key:
            try:
                with open('config.txt', 'w') as f:
                    f.write(api_key)
                self.image_processor = OCRProcessor(api_key)
                self.api_dialog.dismiss()
                
                # Show success
                success_dialog = MDDialog(
                    title="设置成功",
                    text="API Key 已保存，OCR 功能已启用。",
                    buttons=[
                        MDFlatButton(text="确定")
                    ],
                )
                success_dialog.buttons[0].bind(on_release=lambda x: success_dialog.dismiss())
                success_dialog.open()
                
            except Exception as e:
                print(f"Error saving API key: {e}")
        else:
            # Show error
            error_dialog = MDDialog(
                title="错误",
                text="请输入有效的 API Key",
                buttons=[
                    MDFlatButton(text="确定")
                ],
            )
            error_dialog.buttons[0].bind(on_release=lambda x: error_dialog.dismiss())
            error_dialog.open()
    
    def build_main_screens(self):
        """Build the main application screens"""
        try:
            # Initialize barcode scanner
            try:
                if BarcodeScanner:
                    self.barcode_scanner = BarcodeScanner()
                else:
                    self.barcode_scanner = None
            except Exception as e:
                print(f"Error initializing barcode scanner: {e}")
                self.barcode_scanner = None
            
            # Screen manager
            sm = ScreenManager()
            
            # Add screens
            sm.add_widget(MainScreen())
            sm.add_widget(DeliveryNotesScreen())
            sm.add_widget(DeliveryDetailScreen())
            sm.add_widget(ColumnMappingScreen())
            sm.add_widget(BarcodeScanScreen())
            
            return sm
            
        except Exception as e:
            print(f"Error building main screens: {e}")
            # Return minimal screen on error
            from kivymd.uix.label import MDLabel
            return MDLabel(text=f"Error: {str(e)}")

if __name__ == '__main__':
    InventoryManagementApp().run()