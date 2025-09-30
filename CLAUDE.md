# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个SHP文件处理工具，用于从MySQL数据库查询并导出空间数据到SHP文件的图形化工具。该工具使用Python + Tkinter开发，支持多种几何类型和坐标系。主要特点包括灵活的字段选择、智能坐标解析和完整的GUI工作流。

## 运行和开发命令

### 启动应用
```bash
python main.py
```

### 安装依赖
```bash
pip install -r requirements.txt
```

### Windows用户注意事项
如果geopandas安装失败，建议使用conda：
```bash
conda install -c conda-forge geopandas
```

### 命令行参数
```bash
python main.py --version    # 显示版本信息
python main.py --help       # 显示帮助信息
```

## 核心架构

### 主要模块结构
- **config/**: 配置管理模块
  - `mysql_config.py`: MySQL数据库配置管理，支持配置文件加载和保存
- **core/**: 核心功能模块
  - `mysql_connector.py`: 数据库连接和查询执行
  - `coordinate_parser.py`: 坐标字符串解析和几何类型识别
  - `shapefile_exporter.py`: SHP文件导出功能，支持多种坐标系
- **gui/**: 图形界面模块（基于Tkinter）
  - `main_window.py`: 主窗口，整合所有功能面板
  - `database_config_frame.py`: 数据库配置面板
  - `query_frame.py`: SQL查询面板
  - `field_selection_frame.py`: 字段选择和分析面板
  - `export_frame.py`: 导出配置面板
- **utils/**: 工具函数模块
  - `geometry_utils.py`: 几何对象处理和分析工具

### 数据流程
1. **数据库连接**: 通过`MySQLConnector`建立数据库连接，使用原始cursor避免pandas兼容性问题
2. **SQL查询**: 执行用户自定义SQL查询获取数据，支持结果预览和示例查询
3. **字段选择**: 智能分析字段类型，用户可选择要导出的字段（排除不需要的字段）
4. **坐标解析**: `CoordinateParser`解析坐标字符串（支持JSON和正则表达式），具有详细的调试模式
5. **几何识别**: 自动识别点、线、面几何类型，支持手动覆盖
6. **SHP导出**: `ShapefileExporter`根据字段选择导出SHP文件，支持多种编码和坐标系

### 关键技术实现
- **MySQL连接优化**: 使用原生cursor而非pandas.read_sql_query以避免兼容性问题
- **字段选择器**: 在导出面板中提供复选框列表，支持全选/全不选/反选操作
- **坐标字段智能识别**: 自动检测包含坐标数据的字段并高亮显示
- **错误处理**: 完整的依赖检查和用户友好的错误提示

### 坐标数据格式
工具支持以下坐标格式（字符串格式）：
- 点数据: `[[116.404, 39.915]]`
- 线数据: `[[116.404, 39.915], [116.405, 39.916], [116.406, 39.917]]`
- 面数据（闭合）: `[[116.404, 39.915], [116.405, 39.916], [116.406, 39.917], [116.404, 39.915]]`

### 支持的坐标系
- WGS84 (EPSG:4326) - 默认
- GCJ02 (EPSG:4490) - 中国测绘坐标系
- Web Mercator (EPSG:3857)
- UTM Zone 49N (EPSG:32649)
- UTM Zone 50N (EPSG:32650)

## 配置文件

### MySQL配置文件 (mysql_config.json)
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

注意：默认配置已在代码中预设，但会被配置文件覆盖。

## 开发注意事项

### 依赖库要求
- Python 3.8+
- pandas>=1.5.0
- geopandas>=0.13.0
- shapely>=2.0.0
- pymysql>=1.0.0
- numpy>=1.21.0
- pyproj>=3.4.0
- Fiona>=1.8.0
- GDAL>=3.4.0

### 错误处理
- 程序具有完整的依赖检查功能，会在启动时验证必要库
- 数据库连接失败会提供详细错误信息
- 坐标解析失败会指出具体问题
- GUI异常会显示用户友好的错误对话框

### 扩展要点
- 添加新的几何类型支持需要修改`CoordinateParser`和`ShapefileExporter`
- 新增坐标系需要在`ShapefileExporter.COMMON_CRS`中定义
- GUI面板采用模块化设计，可独立开发和测试
- 字段选择功能可通过修改`export_frame.py`中的`initialize_field_selection`方法扩展

### 已知问题和解决方案
- **pandas兼容性问题**: MySQL连接器使用原生cursor而非pd.read_sql_query以避免数据解析错误
- **字段分析错误**: 修复了Series布尔判断导致的"truth value is ambiguous"错误
- **坐标解析失败**: 改进了空值检查和数据清理逻辑