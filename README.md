# SHP文件处理工具

一个用于从MySQL数据库查询并导出空间数据到SHP文件的图形化工具。

## 主要功能

- 📊 **MySQL数据库连接** - 支持自定义数据库配置
- 🔍 **SQL查询执行** - 灵活的数据查询功能
- 🧭 **智能坐标解析** - 自动识别坐标字段格式
- 🗺️ **多几何类型支持** - 点、线、面自动识别
- 📁 **SHP文件导出** - 支持多种坐标系
- 🖥️ **图形化界面** - 友好的用户操作体验

## 安装要求

### Python版本
- Python 3.8 或更高版本

### 依赖包安装
```bash
pip install -r requirements.txt
```

### Windows用户注意事项
如果geopandas安装失败，建议使用conda：
```bash
conda install -c conda-forge geopandas
```

## 快速开始

### 1. 启动程序
```bash
python main.py
```

### 2. 数据库配置
- 在"数据库配置"面板中填写MySQL连接信息
- 点击"测试连接"验证配置
- 保存配置以备后用

### 3. 执行SQL查询
- 在"SQL查询"面板中编写查询语句
- 确保查询结果包含空间坐标字段
- 坐标字段格式应为：`[[经度,纬度],...]`

### 4. 选择坐标字段
- 在"字段选择"面板中选择包含空间坐标的字段
- 系统会自动分析数据格式和几何类型
- 确认选择结果

### 5. 导出SHP文件
- 在"导出配置"面板中设置输出路径
- 选择合适的坐标系（默认WGS84）
- 点击"执行导出"完成操作

## 坐标字段格式

工具支持以下坐标格式：

### 点数据
```json
[[116.404, 39.915]]
```

### 线数据
```json
[[116.404, 39.915], [116.405, 39.916], [116.406, 39.917]]
```

### 面数据（闭合）
```json
[[116.404, 39.915], [116.405, 39.916],
 [116.406, 39.917], [116.404, 39.915]]
```

## 支持的坐标系

- WGS84 (EPSG:4326) - 默认
- GCJ02 (EPSG:4490) - 中国测绘坐标系
- Web Mercator (EPSG:3857)
- UTM Zone 49N (EPSG:32649)
- UTM Zone 50N (EPSG:32650)

## 示例SQL查询

```sql
-- 查询包含坐标的点数据
SELECT id, name, coordinates
FROM poi_points
WHERE city = '北京'
LIMIT 1000;

-- 查询线数据
SELECT road_id, road_name, coordinates
FROM road_network
WHERE length > 100;

-- 查询面数据
SELECT area_id, area_name, coordinates, area_type
FROM administrative_areas
WHERE level = 'district';
```

## 配置文件

程序支持配置文件保存和加载：

### mysql_config.json
```json
{
    "host": "localhost",
    "port": 3306,
    "user": "your_username",
    "password": "your_password",
    "database": "your_database",
    "charset": "utf8mb4"
}
```

## 项目结构

```
shp-processor/
├── config/                  # 配置模块
│   ├── __init__.py
│   └── mysql_config.py
├── core/                    # 核心功能
│   ├── __init__.py
│   ├── mysql_connector.py
│   ├── coordinate_parser.py
│   └── shapefile_exporter.py
├── gui/                     # 图形界面
│   ├── __init__.py
│   ├── main_window.py
│   ├── database_config_frame.py
│   ├── query_frame.py
│   ├── field_selection_frame.py
│   └── export_frame.py
├── utils/                   # 工具函数
│   ├── __init__.py
│   └── geometry_utils.py
├── main.py                  # 主程序入口
├── requirements.txt         # 依赖包列表
├── config_example.json      # 配置文件示例
└── README.md               # 说明文档
```

## 常见问题

### 1. 连接数据库失败
- 检查数据库服务是否启动
- 验证连接参数是否正确
- 确认网络连接是否正常

### 2. 坐标解析失败
- 确保坐标字段格式正确
- 检查是否包含非法字符
- 验证经纬度范围是否合理

### 3. 导出SHP文件失败
- 检查输出路径是否有写入权限
- 确保磁盘空间充足
- 验证坐标数据是否有效

### 4. 几何类型识别错误
- 可以手动指定几何类型
- 检查坐标数据格式
- 查看字段分析结果

## 技术支持

如遇到问题，请检查：

1. **Python环境** - 确保Python版本兼容
2. **依赖包** - 检查所有依赖是否正确安装
3. **数据库连接** - 验证连接参数和网络
4. **数据格式** - 确认坐标字段格式正确

## 更新日志

### v1.0.0 (2024-09-30)
- 初始版本发布
- 支持MySQL数据库连接
- 实现坐标解析和SHP导出
- 提供图形化用户界面

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 贡献

欢迎提交问题报告和功能建议到项目仓库。