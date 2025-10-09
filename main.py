#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SHP文件处理工具 - 主程序入口
从MySQL数据库查询并导出空间数据到SHP文件的图形化工具

作者: Claude Code
版本: 1.0.0
创建时间: 2024-09-30

主要功能:
1. MySQL数据库连接配置
2. 自定义SQL查询执行
3. 空间坐标字段选择和分析
4. SHP文件导出配置和执行
"""

import sys
import os
import traceback
import tkinter as tk
from tkinter import messagebox

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from gui.main_window import MainWindow
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保所有依赖包已正确安装:")
    print("pip install -r requirements.txt")
    sys.exit(1)


def check_dependencies():
    """检查必要的依赖包"""
    required_packages = [
        ('pandas', 'pandas'),
        ('geopandas', 'geopandas'),
        ('shapely', 'shapely'),
        ('pymysql', 'pymysql'),
        ('numpy', 'numpy'),
        ('pyproj', 'pyproj'),
        ('rtree', 'rtree'),
        ('openpyxl', 'openpyxl')
    ]

    missing_packages = []

    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)

    if missing_packages:
        error_msg = f"缺少以下依赖包:\n{', '.join(missing_packages)}\n\n"
        error_msg += "请运行以下命令安装依赖:\n"
        error_msg += "pip install -r requirements.txt"

        print(error_msg)

        # 如果GUI可用，显示错误对话框
        try:
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
            messagebox.showerror("依赖检查失败", error_msg)
            root.destroy()
        except:
            pass

        return False

    return True


def main():
    """主函数"""
    try:
        print("=" * 60)
        print("SHP文件处理工具 v1.0.0")
        print("从MySQL数据库导出空间数据到SHP文件")
        print("=" * 60)

        # 检查依赖
        print("正在检查依赖包...")
        if not check_dependencies():
            print("依赖检查失败，程序退出")
            return

        print("依赖检查通过，正在启动程序...")

        # 创建并运行主窗口
        app = MainWindow()
        app.run()

    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        error_msg = f"程序运行时发生错误:\n{str(e)}\n\n"
        error_msg += f"详细错误信息:\n{traceback.format_exc()}"

        print(error_msg)

        # 显示错误对话框
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("程序错误", error_msg)
            root.destroy()
        except:
            pass

        sys.exit(1)


def show_version():
    """显示版本信息"""
    version_info = """
SHP文件处理工具 v1.0.0

主要功能:
- MySQL数据库连接和查询
- 空间坐标数据解析
- 多种几何类型支持（点/线/面）
- SHP文件导出
- SHP文件合并工具
- 图形化操作界面

依赖库:
- pandas - 数据处理
- geopandas - 空间数据处理
- shapely - 几何对象操作
- pymysql - MySQL数据库连接
- tkinter - 图形界面

使用方法:
python main.py

更多详情请参考README.md文件
"""
    print(version_info)


def show_help():
    """显示帮助信息"""
    help_info = """
使用方法:
    python main.py          # 启动图形界面程序

命令行参数:
    --version, -v         # 显示版本信息
    --help, -h           # 显示帮助信息

配置文件:
    mysql_config.json     # MySQL数据库配置文件
    config_example.json   # 配置文件示例

常见问题:
1. 如果遇到依赖包缺失，请运行: pip install -r requirements.txt
2. 如果geopandas安装失败，建议使用conda: conda install -c conda-forge geopandas
3. 如果rtree安装失败，建议使用conda: conda install -c conda-forge rtree

技术支持:
如有问题请联系开发团队或提交issue到项目仓库
"""
    print(help_info)


if __name__ == "__main__":
    # 处理命令行参数
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['--version', '-v']:
            show_version()
            sys.exit(0)
        elif arg in ['--help', '-h']:
            show_help()
            sys.exit(0)
        else:
            print(f"未知参数: {arg}")
            print("使用 --help 查看帮助信息")
            sys.exit(1)

    # 运行主程序
    main()