# 库存管理系统 (Inventory Management System)

一个基于Python开发的Android库存管理应用，支持送货单扫描、条形码识别和数据管理。

## 功能特点

### 📱 核心功能
- **送货单扫描**: 使用相机或从相册选择图片扫描送货单
- **智能识别**: 通过Claude AI自动提取商品信息（条形码、名称、价格、数量）
- **条形码扫描**: 支持相机实时扫描和手动输入条形码
- **数据管理**: SQLite数据库存储，支持导出Excel
- **状态验证**: 三色状态系统（白色=未检查，绿色=正确，黄色=错误）

### 🎨 界面特点
- 全中文界面
- Material Design风格
- 简洁美观的用户体验
- 适配Android设备

## 技术栈

- **框架**: Kivy + KivyMD
- **数据库**: SQLite
- **图像处理**: Pillow
- **条形码识别**: Android原生API / pyzbar
- **OCR**: Claude AI API
- **数据导出**: CSV格式

## 安装配置

### 1. 环境准备
```bash
# 安装依赖
pip install -r requirements.txt

# 安装buildozer (用于Android打包)
pip install buildozer
```

### 2. Claude API配置
1. 获取Claude API Key
2. 在应用设置中输入API Key
3. 或创建`config.txt`文件，将API Key写入其中

### 3. 运行应用
```bash
# 桌面测试
python main.py

# Android打包
buildozer android debug
```

## 使用方法

### 1. 创建送货单
- 点击"送货单管理"
- 创建新的送货单
- 为送货单命名

### 2. 扫描送货单
- 进入送货单详情
- 点击相机图标
- 选择拍照或从相册选择
- 等待AI自动识别商品信息

### 3. 条形码查询
- 点击"扫描条形码"
- 选择送货单
- 扫描或输入条形码
- 查看商品详情

### 4. 状态管理
- 点击商品卡片
- 标记商品状态：
  - 绿色：信息正确
  - 黄色：信息有误
  - 白色：未检查

### 5. 数据导出
- 在送货单详情页面
- 点击下载图标
- 导出CSV文件

## 项目结构

```
ScanAPP/
├── main.py              # 主应用文件
├── database.py          # 数据库管理
├── ocr_processor.py     # OCR处理模块
├── barcode_scanner.py   # 条形码扫描
├── requirements.txt     # Python依赖
├── buildozer.spec      # Android打包配置
└── README.md           # 说明文档
```

## 注意事项

1. **API限制**: Claude API有使用限制，请合理使用
2. **相机权限**: Android需要授权相机和存储权限
3. **网络连接**: OCR功能需要网络连接
4. **图片质量**: 清晰的图片能提高识别准确率

## 常见问题

### Q: OCR识别不准确怎么办？
A: 
- 确保图片清晰
- 光线充足
- 避免模糊和倾斜
- 可以尝试多次识别

### Q: 无法扫描条形码？
A: 
- 检查相机权限
- 确保条形码清晰可见
- 尝试手动输入条形码

### Q: 无法导出CSV？
A: 
- 检查存储权限
- 确保有足够存储空间
- 重启应用后重试

## 开发说明

本应用使用Kivy框架开发，支持跨平台运行。主要模块说明：

- `MainScreen`: 主界面导航
- `DeliveryNotesScreen`: 送货单列表管理
- `DeliveryDetailScreen`: 送货单详情和扫描
- `BarcodeScanScreen`: 条形码扫描查询
- `SettingsScreen`: 应用设置

数据库采用SQLite，包含两个主要表：
- `delivery_notes`: 送货单信息
- `items`: 商品信息

## 许可证

本项目仅供学习和个人使用。