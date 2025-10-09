"""
SHP文件查看器对话框
提供SHP文件的查看、分析和基本操作功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from typing import Optional, Dict, Any, List
import os


class ShpViewerDialog:
    """SHP文件查看器对话框"""

    def __init__(self, parent):
        """初始化SHP文件查看器对话框"""
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("SHP文件查看器")
        self.window.geometry("1200x800")
        self.window.resizable(True, True)
        self.window.transient(parent)
        self.window.grab_set()

        # 数据存储
        self.gdf: Optional[gpd.GeoDataFrame] = None
        self.file_path: Optional[str] = None
        self.current_layer_index = 0

        # 颜色映射
        self.geometry_colors = {
            'Point': '#FF6B6B',
            'LineString': '#4ECDC4', 
            'Polygon': '#45B7D1',
            'MultiPoint': '#FF6B6B',
            'MultiLineString': '#4ECDC4',
            'MultiPolygon': '#45B7D1'
        }

        self.create_widgets()
        self.center_window()

    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建工具栏
        self.create_toolbar(main_frame)

        # 创建内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # 左侧：信息面板
        self.create_info_panel(content_frame)

        # 右侧：地图和表格面板
        self.create_map_table_panel(content_frame)

        # 创建状态栏
        self.create_status_bar(main_frame)

        # 初始化状态
        self.update_ui_state()

    def create_toolbar(self, parent):
        """创建工具栏"""
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))

        # 文件操作按钮
        ttk.Button(toolbar_frame, text="打开SHP文件", command=self.open_shapefile).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="关闭文件", command=self.close_file).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # 视图操作按钮
        ttk.Button(toolbar_frame, text="刷新", command=self.refresh_view).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="缩放适应", command=self.zoom_to_fit).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="导出图片", command=self.export_map).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # 数据操作按钮
        ttk.Button(toolbar_frame, text="属性统计", command=self.show_statistics).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="导出属性", command=self.export_attributes).pack(side=tk.LEFT, padx=(0, 5))

    def create_info_panel(self, parent):
        """创建信息面板"""
        info_frame = ttk.LabelFrame(parent, text="文件信息", padding="10")
        info_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # 文件基本信息
        self.info_text = tk.Text(info_frame, width=30, height=15, wrap=tk.WORD, state=tk.DISABLED)
        info_scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scrollbar.set)

        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 图层选择（如果有多个图层）
        layer_frame = ttk.LabelFrame(info_frame, text="图层", padding="5")
        layer_frame.pack(fill=tk.X, pady=(10, 0))

        self.layer_var = tk.StringVar()
        self.layer_combobox = ttk.Combobox(layer_frame, textvariable=self.layer_var, 
                                         state="readonly", width=25)
        self.layer_combobox.pack(fill=tk.X)
        self.layer_combobox.bind("<<ComboboxSelected>>", self.on_layer_changed)

    def create_map_table_panel(self, parent):
        """创建地图和表格面板"""
        # 创建Notebook用于切换地图和表格视图
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 地图视图
        self.create_map_view()

        # 表格视图
        self.create_table_view()

    def create_map_view(self):
        """创建地图视图"""
        map_frame = ttk.Frame(self.notebook)
        self.notebook.add(map_frame, text="地图视图")

        # 创建matplotlib图形
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)

        # 创建canvas
        self.canvas = FigureCanvasTkAgg(self.fig, map_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 绑定鼠标事件
        self.canvas.mpl_connect('button_press_event', self.on_map_click)
        self.canvas.mpl_connect('scroll_event', self.on_map_scroll)

    def create_table_view(self):
        """创建表格视图"""
        table_frame = ttk.Frame(self.notebook)
        self.notebook.add(table_frame, text="属性表")

        # 创建Treeview
        columns = ('field', 'value', 'type')
        self.table_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)

        # 设置列标题
        self.table_tree.heading('field', text='字段名')
        self.table_tree.heading('value', text='值')
        self.table_tree.heading('type', text='类型')

        # 设置列宽
        self.table_tree.column('field', width=150)
        self.table_tree.column('value', width=200)
        self.table_tree.column('type', width=100)

        # 创建滚动条
        table_scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.table_tree.yview)
        table_scrollbar_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.table_tree.xview)

        self.table_tree.configure(yscrollcommand=table_scrollbar_y.set, xscrollcommand=table_scrollbar_x.set)

        # 布局
        self.table_tree.grid(row=0, column=0, sticky='nsew')
        table_scrollbar_y.grid(row=0, column=1, sticky='ns')
        table_scrollbar_x.grid(row=1, column=0, sticky='ew')

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # 绑定选择事件
        self.table_tree.bind('<<TreeviewSelect>>', self.on_table_select)

    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        self.status_label = tk.Label(status_frame, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 坐标显示
        self.coord_label = tk.Label(status_frame, text="坐标: --", relief=tk.SUNKEN, anchor=tk.W, width=20)
        self.coord_label.pack(side=tk.RIGHT, padx=(10, 0))

    def open_shapefile(self):
        """打开SHP文件"""
        filename = filedialog.askopenfilename(
            title="选择SHP文件",
            filetypes=[
                ("Shapefile文件", "*.shp"),
                ("所有文件", "*.*")
            ]
        )

        if filename:
            try:
                self.load_shapefile(filename)
            except Exception as e:
                messagebox.showerror("加载错误", f"无法加载SHP文件：\n{e}")

    def load_shapefile(self, file_path: str):
        """加载SHP文件"""
        try:
            # 读取SHP文件
            self.gdf = gpd.read_file(file_path)
            self.file_path = file_path

            # 更新信息面板
            self.update_info_panel()

            # 更新表格视图
            self.update_table_view()

            # 更新地图视图
            self.update_map_view()

            # 更新UI状态
            self.update_ui_state()

            self.status_label.config(text=f"已加载: {os.path.basename(file_path)}")

        except Exception as e:
            raise Exception(f"加载SHP文件失败: {e}")

    def update_info_panel(self):
        """更新信息面板"""
        if self.gdf is None:
            return

        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)

        # 文件信息
        info = f"文件路径: {self.file_path}\n\n"
        info += f"要素数量: {len(self.gdf)}\n"
        info += f"几何类型: {self.gdf.geometry.type.iloc[0] if len(self.gdf) > 0 else 'Unknown'}\n"
        info += f"坐标系: {self.gdf.crs}\n\n"

        # 字段信息
        info += "字段信息:\n"
        for col in self.gdf.columns:
            if col != 'geometry':
                dtype = str(self.gdf[col].dtype)
                info += f"  • {col}: {dtype}\n"

        # 边界信息
        if len(self.gdf) > 0:
            bounds = self.gdf.total_bounds
            info += f"\n边界范围:\n"
            info += f"  minX: {bounds[0]:.6f}\n"
            info += f"  minY: {bounds[1]:.6f}\n"
            info += f"  maxX: {bounds[2]:.6f}\n"
            info += f"  maxY: {bounds[3]:.6f}\n"

        self.info_text.insert("1.0", info)
        self.info_text.config(state=tk.DISABLED)

    def update_table_view(self):
        """更新表格视图"""
        # 清空现有数据
        for item in self.table_tree.get_children():
            self.table_tree.delete(item)

        if self.gdf is None or len(self.gdf) == 0:
            return

        # 显示前几行数据作为示例
        sample_size = min(100, len(self.gdf))
        sample_df = self.gdf.head(sample_size)

        for idx, row in sample_df.iterrows():
            for col in self.gdf.columns:
                if col != 'geometry':
                    value = str(row[col]) if pd.notna(row[col]) else ""
                    dtype = str(self.gdf[col].dtype)
                    
                    self.table_tree.insert('', 'end', values=(col, value, dtype))

    def update_map_view(self):
        """更新地图视图"""
        self.ax.clear()

        if self.gdf is None or len(self.gdf) == 0:
            self.ax.text(0.5, 0.5, '无数据', horizontalalignment='center', 
                        verticalalignment='center', transform=self.ax.transAxes, fontsize=16)
            self.canvas.draw()
            return

        try:
            # 获取几何类型
            geom_type = self.gdf.geometry.type.iloc[0] if len(self.gdf) > 0 else 'Unknown'
            
            # 设置颜色
            color = self.geometry_colors.get(geom_type, '#3388ff')

            # 绘制几何图形
            self.gdf.plot(ax=self.ax, color=color, edgecolor='black', linewidth=0.5, alpha=0.7)

            # 设置标题和标签
            self.ax.set_title(f"SHP文件地图视图 - {geom_type}", fontsize=14, fontweight='bold')
            self.ax.set_xlabel("经度")
            self.ax.set_ylabel("纬度")

            # 添加网格
            self.ax.grid(True, alpha=0.3)

            # 调整布局
            self.fig.tight_layout()

            self.canvas.draw()

        except Exception as e:
            self.ax.text(0.5, 0.5, f'绘制错误: {str(e)}', horizontalalignment='center', 
                        verticalalignment='center', transform=self.ax.transAxes, fontsize=12)
            self.canvas.draw()

    def on_layer_changed(self, event=None):
        """图层切换事件"""
        # 这里可以实现多图层支持
        pass

    def on_table_select(self, event):
        """表格选择事件"""
        selection = self.table_tree.selection()
        if selection:
            item = self.table_tree.item(selection[0])
            values = item['values']
            if values:
                field_name = values[0]
                self.status_label.config(text=f"已选择字段: {field_name}")

    def on_map_click(self, event):
        """地图点击事件"""
        if event.inaxes != self.ax:
            return

        # 获取点击坐标
        x, y = event.xdata, event.ydata
        self.coord_label.config(text=f"坐标: {x:.6f}, {y:.6f}")

        # 查找附近的要素
        if self.gdf is not None and len(self.gdf) > 0:
            # 创建点击点的几何对象
            click_point = Point(x, y)
            
            # 查找距离点击点最近的要素
            distances = self.gdf.geometry.distance(click_point)
            if not distances.empty:
                min_idx = distances.idxmin()
                min_distance = distances[min_idx]
                
                if min_distance < 0.01:  # 阈值距离
                    # 高亮显示选中的要素
                    self.highlight_feature(min_idx)

    def on_map_scroll(self, event):
        """地图滚轮缩放事件"""
        # 这里可以实现缩放功能
        pass

    def highlight_feature(self, index):
        """高亮显示指定索引的要素"""
        try:
            self.update_map_view()
            
            # 高亮显示选中的要素
            if index < len(self.gdf):
                feature = self.gdf.iloc[index:index+1]
                feature.plot(ax=self.ax, color='red', edgecolor='yellow', linewidth=2, alpha=0.8)
                self.canvas.draw()
                
                # 显示要素信息
                self.status_label.config(text=f"已选择要素 {index}")
                
        except Exception as e:
            print(f"高亮显示失败: {e}")

    def refresh_view(self):
        """刷新视图"""
        if self.gdf is not None:
            self.update_info_panel()
            self.update_table_view()
            self.update_map_view()
            self.status_label.config(text="视图已刷新")

    def zoom_to_fit(self):
        """缩放到适应范围"""
        if self.gdf is None or len(self.gdf) == 0:
            return

        try:
            # 获取数据边界
            bounds = self.gdf.total_bounds
            
            # 设置轴范围
            self.ax.set_xlim(bounds[0], bounds[2])
            self.ax.set_ylim(bounds[1], bounds[3])
            
            self.canvas.draw()
            self.status_label.config(text="已缩放到适应范围")
            
        except Exception as e:
            messagebox.showerror("缩放错误", f"缩放失败：\n{e}")

    def export_map(self):
        """导出地图为图片"""
        if self.gdf is None:
            messagebox.showwarning("导出错误", "没有可导出的地图数据")
            return

        filename = filedialog.asksaveasfilename(
            title="保存地图图片",
            defaultextension=".png",
            filetypes=[
                ("PNG文件", "*.png"),
                ("JPG文件", "*.jpg"),
                ("PDF文件", "*.pdf"),
                ("所有文件", "*.*")
            ]
        )

        if filename:
            try:
                self.fig.savefig(filename, dpi=300, bbox_inches='tight')
                self.status_label.config(text=f"地图已保存: {filename}")
                messagebox.showinfo("导出成功", f"地图已保存到：\n{filename}")
            except Exception as e:
                messagebox.showerror("导出错误", f"导出地图失败：\n{e}")

    def show_statistics(self):
        """显示属性统计"""
        if self.gdf is None:
            messagebox.showwarning("统计错误", "没有可统计的数据")
            return

        stats_window = tk.Toplevel(self.window)
        stats_window.title("属性统计")
        stats_window.geometry("600x400")

        # 创建统计文本框
        stats_text = tk.Text(stats_window, wrap=tk.WORD, padx=10, pady=10)
        stats_scrollbar = ttk.Scrollbar(stats_window, orient=tk.VERTICAL, command=stats_text.yview)
        stats_text.configure(yscrollcommand=stats_scrollbar.set)

        stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 生成统计信息
        stats = "数据统计信息\n"
        stats += "=" * 50 + "\n\n"

        # 基本统计
        stats += f"总要素数量: {len(self.gdf)}\n"
        stats += f"几何类型: {self.gdf.geometry.type.iloc[0] if len(self.gdf) > 0 else 'Unknown'}\n"
        stats += f"坐标系: {self.gdf.crs}\n\n"

        # 字段统计
        stats += "字段统计:\n"
        stats += "-" * 30 + "\n"

        for col in self.gdf.columns:
            if col != 'geometry':
                stats += f"\n{col}:\n"
                
                if self.gdf[col].dtype in ['int64', 'float64']:
                    # 数值型字段
                    stats += f"  数据类型: {self.gdf[col].dtype}\n"
                    stats += f"  非空值数量: {self.gdf[col].count()}\n"
                    stats += f"  空值数量: {self.gdf[col].isnull().sum()}\n"
                    
                    if self.gdf[col].dtype in ['int64', 'float64']:
                        stats += f"  最小值: {self.gdf[col].min():.6f}\n"
                        stats += f"  最大值: {self.gdf[col].max():.6f}\n"
                        stats += f"  平均值: {self.gdf[col].mean():.6f}\n"
                        stats += f"  标准差: {self.gdf[col].std():.6f}\n"
                        
                else:
                    # 字符串型字段
                    stats += f"  数据类型: {self.gdf[col].dtype}\n"
                    stats += f"  非空值数量: {self.gdf[col].count()}\n"
                    stats += f"  空值数量: {self.gdf[col].isnull().sum()}\n"
                    stats += f"  唯一值数量: {self.gdf[col].nunique()}\n"

        stats_text.insert("1.0", stats)
        stats_text.config(state=tk.DISABLED)

    def export_attributes(self):
        """导出属性表"""
        if self.gdf is None:
            messagebox.showwarning("导出错误", "没有可导出的属性数据")
            return

        filename = filedialog.asksaveasfilename(
            title="保存属性表",
            defaultextension=".csv",
            filetypes=[
                ("CSV文件", "*.csv"),
                ("Excel文件", "*.xlsx"),
                ("GeoJSON文件", "*.geojson"),
                ("所有文件", "*.*")
            ]
        )

        if filename:
            try:
                if filename.endswith('.csv'):
                    # 导出为CSV（不包含几何列）
                    df = self.gdf.drop('geometry', axis=1)
                    df.to_csv(filename, index=False, encoding='utf-8-sig')
                elif filename.endswith('.xlsx'):
                    # 导出为Excel
                    df = self.gdf.drop('geometry', axis=1)
                    df.to_excel(filename, index=False)
                elif filename.endswith('.geojson'):
                    # 导出为GeoJSON
                    self.gdf.to_file(filename, driver='GeoJSON')
                else:
                    # 默认导出为CSV
                    df = self.gdf.drop('geometry', axis=1)
                    df.to_csv(filename, index=False, encoding='utf-8-sig')

                self.status_label.config(text=f"属性表已保存: {filename}")
                messagebox.showinfo("导出成功", f"属性表已保存到：\n{filename}")
                
            except Exception as e:
                messagebox.showerror("导出错误", f"导出属性表失败：\n{e}")

    def close_file(self):
        """关闭当前文件"""
        self.gdf = None
        self.file_path = None

        # 清空视图
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        self.info_text.config(state=tk.DISABLED)

        for item in self.table_tree.get_children():
            self.table_tree.delete(item)

        self.ax.clear()
        self.ax.text(0.5, 0.5, '请打开SHP文件', horizontalalignment='center', 
                    verticalalignment='center', transform=self.ax.transAxes, fontsize=16)
        self.canvas.draw()

        self.update_ui_state()
        self.status_label.config(text="文件已关闭")

    def update_ui_state(self):
        """更新UI状态"""
        has_data = self.gdf is not None
        
        # 这里可以根据数据状态启用/禁用按钮
        pass

    def center_window(self):
        """居中显示窗口"""
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
