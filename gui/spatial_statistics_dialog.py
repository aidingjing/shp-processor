"""
空间统计分析工具对话框
提供空间数据的统计分析功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, Polygon, LineString, MultiPoint, MultiPolygon
from shapely.ops import unary_union
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from typing import List, Dict, Optional, Tuple, Union
import json
import os
from scipy import stats
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class SpatialStatisticsDialog:
    """空间统计分析工具对话框"""

    def __init__(self, parent, gdf=None):
        """初始化空间统计分析工具对话框"""
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("空间统计分析工具")
        self.window.geometry("1400x900")
        self.window.resizable(True, True)
        self.window.transient(parent)
        self.window.grab_set()

        # 数据存储
        self.gdf = gdf
        self.current_figure = None
        self.current_canvas = None
        self.analysis_results = {}

        # 分析类型
        self.analysis_types = {
            "基础统计": "basic",
            "空间分布": "distribution",
            "空间聚类": "clustering",
            "空间相关性": "correlation",
            "距离分析": "distance",
            "密度分析": "density"
        }

        # 创建界面
        self.create_widgets()
        self.center_window()

        # 如果有数据，自动加载
        if self.gdf is not None:
            self.load_data()

    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建标题
        title_label = tk.Label(main_frame, text="空间统计分析工具", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))

        # 创建工具栏
        self.create_toolbar(main_frame)

        # 创建主要内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 左侧：配置面板
        self.create_config_panel(content_frame)

        # 右侧：结果显示面板
        self.create_results_panel(content_frame)

        # 创建状态栏
        self.create_status_bar(main_frame)

    def create_toolbar(self, parent):
        """创建工具栏"""
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))

        # 数据加载按钮
        load_btn = ttk.Button(toolbar_frame, text="加载数据", command=self.load_data_from_file)
        load_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 当前数据标签
        self.data_label = tk.Label(toolbar_frame, text="未加载数据", fg="gray")
        self.data_label.pack(side=tk.LEFT, padx=(0, 20))

        # 分隔符
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # 导出结果按钮
        export_btn = ttk.Button(toolbar_frame, text="导出结果", command=self.export_results)
        export_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 清除结果按钮
        clear_btn = ttk.Button(toolbar_frame, text="清除结果", command=self.clear_results)
        clear_btn.pack(side=tk.LEFT)

    def create_config_panel(self, parent):
        """创建配置面板"""
        config_frame = ttk.LabelFrame(parent, text="分析配置", padding="10")
        config_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # 分析类型选择
        analysis_type_frame = ttk.LabelFrame(config_frame, text="分析类型", padding="5")
        analysis_type_frame.pack(fill=tk.X, pady=(0, 10))

        self.analysis_type_var = tk.StringVar(value="基础统计")
        for analysis_type in self.analysis_types.keys():
            ttk.Radiobutton(analysis_type_frame, text=analysis_type, 
                          variable=self.analysis_type_var, value=analysis_type,
                          command=self.on_analysis_type_changed).pack(anchor=tk.W)

        # 数据配置
        data_frame = ttk.LabelFrame(config_frame, text="数据配置", padding="5")
        data_frame.pack(fill=tk.X, pady=(0, 10))

        # 几何类型显示
        ttk.Label(data_frame, text="几何类型:").pack(anchor=tk.W)
        self.geometry_type_label = tk.Label(data_frame, text="未知", fg="blue")
        self.geometry_type_label.pack(anchor=tk.W, pady=(2, 5))

        # 字段选择
        ttk.Label(data_frame, text="分析字段:").pack(anchor=tk.W)
        self.field_combo = ttk.Combobox(data_frame, width=20, state="readonly")
        self.field_combo.pack(fill=tk.X, pady=(2, 5))

        # 分组字段（可选）
        ttk.Label(data_frame, text="分组字段:").pack(anchor=tk.W)
        self.group_field_combo = ttk.Combobox(data_frame, width=20, state="readonly")
        self.group_field_combo.pack(fill=tk.X, pady=(2, 5))
        self.group_field_combo['values'] = ["无"]
        self.group_field_combo.set("无")

        # 分析参数
        params_frame = ttk.LabelFrame(config_frame, text="分析参数", padding="5")
        params_frame.pack(fill=tk.X, pady=(0, 10))

        # 聚类数量（用于聚类分析）
        ttk.Label(params_frame, text="聚类数量:").pack(anchor=tk.W)
        self.cluster_count_var = tk.IntVar(value=3)
        cluster_spinbox = ttk.Spinbox(params_frame, from_=2, to=10, 
                                     textvariable=self.cluster_count_var, width=18)
        cluster_spinbox.pack(fill=tk.X, pady=(2, 5))

        # 距离阈值（用于距离分析）
        ttk.Label(params_frame, text="距离阈值:").pack(anchor=tk.W)
        self.distance_threshold_var = tk.DoubleVar(value=1000.0)
        distance_entry = ttk.Entry(params_frame, textvariable=self.distance_threshold_var)
        distance_entry.pack(fill=tk.X, pady=(2, 5))

        # 网格大小（用于密度分析）
        ttk.Label(params_frame, text="网格大小:").pack(anchor=tk.W)
        self.grid_size_var = tk.IntVar(value=100)
        grid_spinbox = ttk.Spinbox(params_frame, from_=50, to=500, 
                                  textvariable=self.grid_size_var, width=18)
        grid_spinbox.pack(fill=tk.X, pady=(2, 5))

        # 可视化选项
        viz_frame = ttk.LabelFrame(config_frame, text="可视化选项", padding="5")
        viz_frame.pack(fill=tk.X, pady=(0, 10))

        self.show_map_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(viz_frame, text="显示地图", 
                       variable=self.show_map_var).pack(anchor=tk.W, pady=2)

        self.show_chart_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(viz_frame, text="显示图表", 
                       variable=self.show_chart_var).pack(anchor=tk.W, pady=2)

        self.show_table_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(viz_frame, text="显示表格", 
                       variable=self.show_table_var).pack(anchor=tk.W, pady=2)

        # 分析按钮
        analyze_btn = ttk.Button(config_frame, text="开始分析", command=self.run_analysis)
        analyze_btn.pack(fill=tk.X, pady=(20, 0))

        # 预设分析
        preset_btn = ttk.Button(config_frame, text="预设分析", command=self.show_presets)
        preset_btn.pack(fill=tk.X, pady=(5, 0))

    def create_results_panel(self, parent):
        """创建结果显示面板"""
        results_frame = ttk.LabelFrame(parent, text="分析结果", padding="10")
        results_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 创建笔记本用于多标签页显示结果
        self.notebook = ttk.Notebook(results_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 地图标签页
        self.map_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.map_frame, text="地图")
        self.create_map_panel()

        # 图表标签页
        self.chart_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.chart_frame, text="图表")
        self.create_chart_panel()

        # 统计表格标签页
        self.table_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.table_frame, text="统计表格")
        self.create_table_panel()

        # 文本报告标签页
        self.report_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.report_frame, text="分析报告")
        self.create_report_panel()

    def create_map_panel(self):
        """创建地图面板"""
        # 创建matplotlib图形区域
        self.map_figure_frame = ttk.Frame(self.map_frame)
        self.map_figure_frame.pack(fill=tk.BOTH, expand=True)

        # 初始化空的地图
        self.create_empty_map()

    def create_empty_map(self):
        """创建空地图"""
        # 清除所有现有组件
        for widget in self.map_figure_frame.winfo_children():
            widget.destroy()
        
        if self.current_figure:
            plt.close(self.current_figure)
        
        self.current_figure = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.current_figure.add_subplot(111)
        
        # 显示提示信息
        self.ax.text(0.5, 0.5, '请加载数据并运行分析', 
                    ha='center', va='center', fontsize=14, 
                    transform=self.ax.transAxes)
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.axis('off')
        
        # 创建画布
        self.current_canvas = FigureCanvasTkAgg(self.current_figure, self.map_figure_frame)
        self.current_canvas.draw()
        self.current_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 添加工具栏
        toolbar_frame = ttk.Frame(self.map_figure_frame)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.current_canvas, toolbar_frame)
        toolbar.update()

    def create_chart_panel(self):
        """创建图表面板"""
        # 创建图表框架
        self.chart_figure_frame = ttk.Frame(self.chart_frame)
        self.chart_figure_frame.pack(fill=tk.BOTH, expand=True)

        # 初始化提示标签
        self.chart_placeholder = tk.Label(self.chart_figure_frame, 
                                         text="运行分析后将显示图表", 
                                         font=("Arial", 12))
        self.chart_placeholder.pack(expand=True)

    def create_table_panel(self):
        """创建统计表格面板"""
        # 创建表格框架
        table_container = ttk.Frame(self.table_frame)
        table_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 创建滚动条
        scrollbar = ttk.Scrollbar(table_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建表格
        self.results_tree = ttk.Treeview(table_container, yscrollcommand=scrollbar.set)
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.results_tree.yview)

        # 初始化提示标签
        self.table_placeholder = tk.Label(self.table_frame, 
                                         text="运行分析后将显示统计表格", 
                                         font=("Arial", 12))
        self.table_placeholder.pack(expand=True)

    def create_report_panel(self):
        """创建分析报告面板"""
        # 创建文本框架
        text_container = ttk.Frame(self.report_frame)
        text_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 创建滚动条
        scrollbar = ttk.Scrollbar(text_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建文本框
        self.report_text = tk.Text(text_container, wrap=tk.WORD, 
                                  yscrollcommand=scrollbar.set)
        self.report_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.report_text.yview)

        # 初始化提示文本
        self.report_text.insert(tk.END, "运行分析后将显示详细的分析报告...")
        self.report_text.config(state=tk.DISABLED)

    def create_status_bar(self, parent):
        """创建状态栏"""
        self.status_label = tk.Label(parent, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, pady=(10, 0))

    def load_data(self):
        """加载数据"""
        if self.gdf is not None:
            self.update_field_combos()
            self.geometry_type_label.config(text=self.get_geometry_type())
            self.data_label.config(text=f"已加载 {len(self.gdf)} 个要素")
            self.status_label.config(text=f"数据加载成功，共 {len(self.gdf)} 个要素")
        else:
            self.data_label.config(text="未加载数据")
            self.status_label.config(text="请加载空间数据文件")

    def load_data_from_file(self):
        """从文件加载数据"""
        file_types = [
            ("Shapefile文件", "*.shp"),
            ("GeoJSON文件", "*.geojson"),
            ("所有文件", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="选择空间数据文件",
            filetypes=file_types
        )
        
        if filename:
            try:
                self.status_label.config(text="正在加载数据...")
                self.window.update()
                
                # 读取空间数据
                self.gdf = gpd.read_file(filename)
                
                # 确保坐标系为WGS84
                if self.gdf.crs is None:
                    self.gdf.crs = "EPSG:4326"
                elif self.gdf.crs != "EPSG:4326":
                    self.gdf = self.gdf.to_crs("EPSG:4326")
                
                self.load_data()
                
            except Exception as e:
                messagebox.showerror("加载错误", f"加载数据失败：\n{e}")
                self.status_label.config(text="数据加载失败")

    def get_geometry_type(self):
        """获取几何类型"""
        if self.gdf is not None:
            geom_types = self.gdf.geometry.geom_type.unique()
            if len(geom_types) == 1:
                return geom_types[0]
            else:
                return f"混合 ({', '.join(geom_types[:3])})"
        return "未知"

    def update_field_combos(self):
        """更新字段下拉框"""
        if self.gdf is not None:
            # 获取数值字段
            numeric_fields = self.gdf.select_dtypes(include=[np.number]).columns.tolist()
            # 排除几何字段
            numeric_fields = [field for field in numeric_fields if field != 'geometry']
            
            # 更新分析字段
            self.field_combo['values'] = numeric_fields
            if numeric_fields:
                self.field_combo.set(numeric_fields[0])
            
            # 更新分组字段（包括字符串字段）
            all_fields = [field for field in self.gdf.columns if field != 'geometry']
            self.group_field_combo['values'] = ["无"] + all_fields

    def on_analysis_type_changed(self):
        """分析类型改变事件"""
        analysis_type = self.analysis_type_var.get()
        
        # 根据分析类型启用/禁用相关参数
        if analysis_type == "空间聚类":
            # 聚类分析需要聚类数量
            pass
        elif analysis_type == "距离分析":
            # 距离分析需要距离阈值
            pass
        elif analysis_type == "密度分析":
            # 密度分析需要网格大小
            pass

    def run_analysis(self):
        """运行分析"""
        if self.gdf is None:
            messagebox.showwarning("提示", "请先加载数据")
            return
        
        analysis_type = self.analysis_type_var.get()
        field = self.field_combo.get()
        
        try:
            self.status_label.config(text="正在运行分析...")
            self.window.update()
            
            # 清除之前的结果
            self.clear_results()
            
            # 根据分析类型运行相应的分析
            if analysis_type == "基础统计":
                self.run_basic_statistics(field)
            elif analysis_type == "空间分布":
                self.run_spatial_distribution(field)
            elif analysis_type == "空间聚类":
                self.run_spatial_clustering(field)
            elif analysis_type == "空间相关性":
                self.run_spatial_correlation(field)
            elif analysis_type == "距离分析":
                self.run_distance_analysis()
            elif analysis_type == "密度分析":
                self.run_density_analysis()
            
            self.status_label.config(text="分析完成")
            
        except Exception as e:
            messagebox.showerror("分析错误", f"分析失败：\n{e}")
            self.status_label.config(text="分析失败")

    def run_basic_statistics(self, field):
        """运行基础统计分析"""
        if not field:
            messagebox.showwarning("提示", "请选择分析字段")
            return
        
        # 计算基础统计
        data = self.gdf[field].dropna()
        
        stats_results = {
            'count': len(data),
            'mean': data.mean(),
            'std': data.std(),
            'min': data.min(),
            'max': data.max(),
            'median': data.median(),
            'q25': data.quantile(0.25),
            'q75': data.quantile(0.75),
            'skewness': stats.skew(data),
            'kurtosis': stats.kurtosis(data)
        }
        
        self.analysis_results['basic_stats'] = stats_results
        
        # 显示结果
        if self.show_table_var.get():
            self.display_basic_stats_table(stats_results)
        
        if self.show_chart_var.get():
            self.create_histogram_chart(field, data)
        
        if self.show_map_var.get():
            self.create_choropleth_map(field)
        
        # 生成报告
        self.generate_basic_stats_report(field, stats_results)

    def run_spatial_distribution(self, field):
        """运行空间分布分析"""
        if not field:
            messagebox.showwarning("提示", "请选择分析字段")
            return
        
        # 计算空间分布统计
        data = self.gdf[field].dropna()
        
        # 计算重心
        centroids = self.gdf.geometry.centroid
        mean_center = Point(centroids.x.mean(), centroids.y.mean())
        
        # 计算标准距离
        distances = centroids.distance(mean_center)
        std_distance = np.sqrt((distances**2).sum() / len(distances))
        
        # 计算空间自相关（Moran's I的简化版本）
        weights = self.create_spatial_weights()
        moran_i = self.calculate_morans_i(data, weights)
        
        distribution_results = {
            'mean_center': (mean_center.x, mean_center.y),
            'std_distance': std_distance,
            'morans_i': moran_i,
            'spatial_variance': distances.var()
        }
        
        self.analysis_results['spatial_distribution'] = distribution_results
        
        # 显示结果
        if self.show_map_var.get():
            self.create_distribution_map(distribution_results)
        
        if self.show_chart_var.get():
            self.create_distribution_scatter_plot(field, distances)
        
        # 生成报告
        self.generate_distribution_report(field, distribution_results)

    def run_spatial_clustering(self, field):
        """运行空间聚类分析"""
        if not field:
            messagebox.showwarning("提示", "请选择分析字段")
            return
        
        # 准备数据
        data = self.gdf[field].dropna()
        valid_indices = data.index
        valid_gdf = self.gdf.loc[valid_indices].copy()
        
        # 获取坐标
        coords = np.array([[geom.x, geom.y] for geom in valid_gdf.geometry.centroid])
        
        # 标准化数据
        scaler = StandardScaler()
        features = scaler.fit_transform(data.values.reshape(-1, 1))
        
        # K-means聚类
        n_clusters = self.cluster_count_var.get()
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(features)
        
        # 添加聚类结果到数据
        valid_gdf['cluster'] = cluster_labels
        
        clustering_results = {
            'cluster_labels': cluster_labels,
            'cluster_centers': kmeans.cluster_centers_,
            'inertia': kmeans.inertia_,
            'n_clusters': n_clusters,
            'clustered_gdf': valid_gdf
        }
        
        self.analysis_results['spatial_clustering'] = clustering_results
        
        # 显示结果
        if self.show_map_var.get():
            self.create_clustering_map(clustering_results)
        
        if self.show_chart_var.get():
            self.create_clustering_chart(field, clustering_results)
        
        if self.show_table_var.get():
            self.display_clustering_table(clustering_results)
        
        # 生成报告
        self.generate_clustering_report(field, clustering_results)

    def run_spatial_correlation(self, field):
        """运行空间相关性分析"""
        if not field:
            messagebox.showwarning("提示", "请选择分析字段")
            return
        
        # 计算空间权重
        weights = self.create_spatial_weights()
        
        # 计算Moran's I
        data = self.gdf[field].dropna()
        moran_i = self.calculate_morans_i(data, weights)
        
        # 计算Geary's C
        geary_c = self.calculate_geary_c(data, weights)
        
        correlation_results = {
            'morans_i': moran_i,
            'geary_c': geary_c,
            'field': field
        }
        
        self.analysis_results['spatial_correlation'] = correlation_results
        
        # 显示结果
        if self.show_map_var.get():
            self.create_correlation_map(field, data)
        
        if self.show_chart_var.get():
            self.create_moran_scatterplot(field, data, weights, moran_i)
        
        # 生成报告
        self.generate_correlation_report(field, correlation_results)

    def run_distance_analysis(self):
        """运行距离分析"""
        # 计算所有要素之间的距离矩阵
        centroids = self.gdf.geometry.centroid
        coords = np.array([[geom.x, geom.y] for geom in centroids])
        
        # 计算距离矩阵
        distance_matrix = squareform(pdist(coords))
        
        # 计算距离统计
        threshold = self.distance_threshold_var.get()
        
        # 找出距离小于阈值的要素对
        close_pairs = np.where((distance_matrix > 0) & (distance_matrix < threshold))
        
        distance_results = {
            'mean_distance': np.mean(distance_matrix[distance_matrix > 0]),
            'std_distance': np.std(distance_matrix[distance_matrix > 0]),
            'min_distance': np.min(distance_matrix[distance_matrix > 0]),
            'max_distance': np.max(distance_matrix),
            'close_pairs_count': len(close_pairs[0]),
            'threshold': threshold,
            'distance_matrix': distance_matrix
        }
        
        self.analysis_results['distance_analysis'] = distance_results
        
        # 显示结果
        if self.show_map_var.get():
            self.create_distance_map(distance_results)
        
        if self.show_chart_var.get():
            self.create_distance_histogram(distance_results)
        
        if self.show_table_var.get():
            self.display_distance_table(distance_results)
        
        # 生成报告
        self.generate_distance_report(distance_results)

    def run_density_analysis(self):
        """运行密度分析"""
        # 创建网格
        grid_size = self.grid_size_var.get()
        
        # 获取数据范围
        bounds = self.gdf.total_bounds
        x_min, y_min, x_max, y_max = bounds
        
        # 创建网格
        x_cells = int((x_max - x_min) / grid_size) + 1
        y_cells = int((y_max - y_min) / grid_size) + 1
        
        # 计算每个网格的密度
        density_grid = np.zeros((y_cells, x_cells))
        
        for geom in self.gdf.geometry:
            if geom.geom_type == 'Point':
                x_idx = int((geom.x - x_min) / grid_size)
                y_idx = int((geom.y - y_min) / grid_size)
                if 0 <= x_idx < x_cells and 0 <= y_idx < y_cells:
                    density_grid[y_idx, x_idx] += 1
        
        density_results = {
            'density_grid': density_grid,
            'grid_size': grid_size,
            'bounds': bounds,
            'total_points': len(self.gdf),
            'max_density': np.max(density_grid),
            'mean_density': np.mean(density_grid)
        }
        
        self.analysis_results['density_analysis'] = density_results
        
        # 显示结果
        if self.show_map_var.get():
            self.create_density_map(density_results)
        
        if self.show_chart_var.get():
            self.create_density_chart(density_results)
        
        # 生成报告
        self.generate_density_report(density_results)

    def create_spatial_weights(self):
        """创建空间权重矩阵"""
        # 简化的反距离权重
        centroids = self.gdf.geometry.centroid
        coords = np.array([[geom.x, geom.y] for geom in centroids])
        
        n = len(coords)
        weights = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    distance = np.linalg.norm(coords[i] - coords[j])
                    if distance > 0:
                        weights[i, j] = 1.0 / distance
        
        # 行标准化
        row_sums = weights.sum(axis=1)
        weights = weights / row_sums[:, np.newaxis]
        
        return weights

    def calculate_morans_i(self, data, weights):
        """计算Moran's I"""
        n = len(data)
        data_array = data.values
        
        # 计算全局均值
        mean_y = np.mean(data_array)
        
        # 计算Moran's I
        numerator = 0
        denominator = 0
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    numerator += weights[i, j] * (data_array[i] - mean_y) * (data_array[j] - mean_y)
            
            denominator += (data_array[i] - mean_y) ** 2
        
        if denominator > 0:
            morans_i = (n / np.sum(weights)) * (numerator / denominator)
        else:
            morans_i = 0
        
        return morans_i

    def calculate_geary_c(self, data, weights):
        """计算Geary's C"""
        n = len(data)
        data_array = data.values
        
        numerator = 0
        denominator = 0
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    numerator += weights[i, j] * (data_array[i] - data_array[j]) ** 2
            
            denominator += (data_array[i] - np.mean(data_array)) ** 2
        
        if denominator > 0:
            geary_c = (n - 1) / (2 * np.sum(weights)) * (numerator / denominator)
        else:
            geary_c = 0
        
        return geary_c

    def display_basic_stats_table(self, stats):
        """显示基础统计表格"""
        # 清除占位符
        if hasattr(self, 'table_placeholder'):
            self.table_placeholder.destroy()
        
        # 清除现有表格
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # 设置列
        self.results_tree['columns'] = ('statistic', 'value')
        self.results_tree.column('#0', width=0, stretch=tk.NO)
        self.results_tree.column('statistic', anchor=tk.W, width=200)
        self.results_tree.column('value', anchor=tk.W, width=150)
        
        self.results_tree.heading('#0', text='', anchor=tk.W)
        self.results_tree.heading('statistic', text='统计量', anchor=tk.W)
        self.results_tree.heading('value', text='值', anchor=tk.W)
        
        # 添加数据
        stat_names = {
            'count': '样本数量',
            'mean': '平均值',
            'std': '标准差',
            'min': '最小值',
            'max': '最大值',
            'median': '中位数',
            'q25': '第一四分位数',
            'q75': '第三四分位数',
            'skewness': '偏度',
            'kurtosis': '峰度'
        }
        
        for key, value in stats.items():
            if key in stat_names:
                self.results_tree.insert('', tk.END, values=(stat_names[key], f"{value:.4f}"))

    def create_histogram_chart(self, field, data):
        """创建直方图"""
        if hasattr(self, 'chart_placeholder'):
            self.chart_placeholder.destroy()
        
        # 清除现有图表
        for widget in self.chart_figure_frame.winfo_children():
            widget.destroy()
        
        # 创建新图形
        fig = Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        # 创建直方图
        ax.hist(data, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        ax.set_title(f'{field} 分布直方图', fontsize=14, fontweight='bold')
        ax.set_xlabel(field, fontsize=12)
        ax.set_ylabel('频数', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # 添加统计线
        mean_val = data.mean()
        median_val = data.median()
        ax.axvline(mean_val, color='red', linestyle='--', label=f'平均值: {mean_val:.2f}')
        ax.axvline(median_val, color='green', linestyle='--', label=f'中位数: {median_val:.2f}')
        ax.legend()
        
        # 创建画布
        canvas = FigureCanvasTkAgg(fig, self.chart_figure_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def create_choropleth_map(self, field):
        """创建分级统计图"""
        # 清除所有现有组件
        for widget in self.map_figure_frame.winfo_children():
            widget.destroy()
        
        if self.current_figure:
            plt.close(self.current_figure)
        
        self.current_figure = Figure(figsize=(8, 6), dpi=100)
        ax = self.current_figure.add_subplot(111)
        
        # 绘制分级统计图
        self.gdf.plot(column=field, ax=ax, legend=True, cmap='viridis',
                     legend_kwds={'label': field, 'orientation': 'horizontal'})
        
        ax.set_title(f'{field} 空间分布', fontsize=14, fontweight='bold')
        ax.set_xlabel('经度', fontsize=12)
        ax.set_ylabel('纬度', fontsize=12)
        
        # 创建画布
        self.current_canvas = FigureCanvasTkAgg(self.current_figure, self.map_figure_frame)
        self.current_canvas.draw()
        self.current_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 添加工具栏
        toolbar_frame = ttk.Frame(self.map_figure_frame)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.current_canvas, toolbar_frame)
        toolbar.update()

    def generate_basic_stats_report(self, field, stats):
        """生成基础统计分析报告"""
        self.report_text.config(state=tk.NORMAL)
        self.report_text.delete(1.0, tk.END)
        
        report = f"""
基础统计分析报告
================

分析字段: {field}
样本数量: {stats['count']}

描述性统计:
-----------
平均值: {stats['mean']:.4f}
标准差: {stats['std']:.4f}
最小值: {stats['min']:.4f}
最大值: {stats['max']:.4f}
中位数: {stats['median']:.4f}
第一四分位数: {stats['q25']:.4f}
第三四分位数: {stats['q75']:.4f}

分布特征:
---------
偏度: {stats['skewness']:.4f}
峰度: {stats['kurtosis']:.4f}

解释:
-----
偏度 > 0: 右偏分布（长尾在右）
偏度 < 0: 左偏分布（长尾在左）
偏度 = 0: 对称分布

峰度 > 0: 尖峰分布（比正态分布更尖）
峰度 < 0: 平峰分布（比正态分布更平）
峰度 = 0: 正态分布的峰度
"""
        
        self.report_text.insert(tk.END, report)
        self.report_text.config(state=tk.DISABLED)

    def clear_results(self):
        """清除结果"""
        self.analysis_results = {}
        
        # 清除地图
        self.create_empty_map()
        
        # 清除图表
        for widget in self.chart_figure_frame.winfo_children():
            widget.destroy()
        self.chart_placeholder = tk.Label(self.chart_figure_frame, 
                                         text="运行分析后将显示图表", 
                                         font=("Arial", 12))
        self.chart_placeholder.pack(expand=True)
        
        # 清除表格
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # 清除报告
        self.report_text.config(state=tk.NORMAL)
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, "运行分析后将显示详细的分析报告...")
        self.report_text.config(state=tk.DISABLED)

    def export_results(self):
        """导出结果"""
        if not self.analysis_results:
            messagebox.showwarning("提示", "没有可导出的结果")
            return
        
        file_types = [
            ("JSON文件", "*.json"),
            ("CSV文件", "*.csv"),
            ("所有文件", "*.*")
        ]
        
        filename = filedialog.asksaveasfilename(
            title="保存分析结果",
            defaultextension=".json",
            filetypes=file_types
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    # 导出为JSON
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(self.analysis_results, f, indent=2, ensure_ascii=False, default=str)
                elif filename.endswith('.csv'):
                    # 导出为CSV（只导出数值结果）
                    df = pd.DataFrame(self.analysis_results)
                    df.to_csv(filename, index=False, encoding='utf-8')
                
                messagebox.showinfo("导出成功", f"结果已保存到：\n{filename}")
                self.status_label.config(text=f"结果已导出到: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("导出错误", f"导出结果失败：\n{e}")

    def show_presets(self):
        """显示预设分析"""
        preset_window = tk.Toplevel(self.window)
        preset_window.title("预设分析")
        preset_window.geometry("400x400")
        preset_window.transient(self.window)
        preset_window.grab_set()
        
        # 预设分析列表
        presets = [
            {
                "name": "完整数据概览",
                "description": "运行所有基础分析，获得数据概览",
                "setup": lambda: self.run_preset_analysis("overview")
            },
            {
                "name": "空间模式分析",
                "description": "分析空间分布模式和聚类特征",
                "setup": lambda: self.run_preset_analysis("spatial_pattern")
            },
            {
                "name": "相关性分析",
                "description": "分析空间相关性和依赖性",
                "setup": lambda: self.run_preset_analysis("correlation")
            },
            {
                "name": "密度分析",
                "description": "分析空间密度分布",
                "setup": lambda: self.run_preset_analysis("density")
            }
        ]
        
        # 创建预设列表
        preset_frame = ttk.Frame(preset_window)
        preset_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for preset in presets:
            # 预设框架
            item_frame = ttk.LabelFrame(preset_frame, text=preset["name"], padding="10")
            item_frame.pack(fill=tk.X, pady=(0, 10))
            
            # 描述
            desc_label = tk.Label(item_frame, text=preset["description"], wraplength=350)
            desc_label.pack(anchor=tk.W)
            
            # 运行按钮
            run_btn = ttk.Button(item_frame, text="运行分析", command=preset["setup"])
            run_btn.pack(anchor=tk.E, pady=(5, 0))
        
        # 关闭按钮
        close_btn = ttk.Button(preset_window, text="关闭", command=preset_window.destroy)
        close_btn.pack(pady=10)

    def run_preset_analysis(self, preset_type):
        """运行预设分析"""
        if self.gdf is None:
            messagebox.showwarning("提示", "请先加载数据")
            return
        
        try:
            if preset_type == "overview":
                # 运行基础统计
                field = self.field_combo.get()
                if field:
                    self.run_basic_statistics(field)
                
            elif preset_type == "spatial_pattern":
                # 运行空间分布和聚类分析
                field = self.field_combo.get()
                if field:
                    self.run_spatial_distribution(field)
                    self.run_spatial_clustering(field)
                
            elif preset_type == "correlation":
                # 运行空间相关性分析
                field = self.field_combo.get()
                if field:
                    self.run_spatial_correlation(field)
                
            elif preset_type == "density":
                # 运行密度分析
                self.run_density_analysis()
            
            # 关闭预设窗口
            for widget in self.window.winfo_children():
                if isinstance(widget, tk.Toplevel) and widget.title() == "预设分析":
                    widget.destroy()
                    break
                    
        except Exception as e:
            messagebox.showerror("分析错误", f"预设分析失败：\n{e}")

    def center_window(self):
        """将窗口居中显示"""
        self.window.update_idletasks()
        
        width = self.window.winfo_reqwidth()
        height = self.window.winfo_reqheight()
        
        # 获取屏幕尺寸
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # 计算居中位置
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # 设置窗口位置
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    # 其他分析方法的实现（为了节省空间，这里只展示了部分方法）
    def create_distribution_map(self, results):
        """创建分布地图"""
        # 实现分布地图创建
        pass

    def create_distribution_scatter_plot(self, field, distances):
        """创建分布散点图"""
        # 实现分布散点图创建
        pass

    def generate_distribution_report(self, field, results):
        """生成分布分析报告"""
        # 实现分布报告生成
        pass

    def create_clustering_map(self, results):
        """创建聚类地图"""
        # 实现聚类地图创建
        pass

    def create_clustering_chart(self, field, results):
        """创建聚类图表"""
        # 实现聚类图表创建
        pass

    def display_clustering_table(self, results):
        """显示聚类表格"""
        # 实现聚类表格显示
        pass

    def generate_clustering_report(self, field, results):
        """生成聚类分析报告"""
        # 实现聚类报告生成
        pass

    def create_correlation_map(self, field, data):
        """创建相关性地图"""
        # 实现相关性地图创建
        pass

    def create_moran_scatterplot(self, field, data, weights, moran_i):
        """创建Moran散点图"""
        # 实现Moran散点图创建
        pass

    def generate_correlation_report(self, field, results):
        """生成相关性分析报告"""
        # 实现相关性报告生成
        pass

    def create_distance_map(self, results):
        """创建距离地图"""
        # 实现距离地图创建
        pass

    def create_distance_histogram(self, results):
        """创建距离直方图"""
        # 实现距离直方图创建
        pass

    def display_distance_table(self, results):
        """显示距离表格"""
        # 实现距离表格显示
        pass

    def generate_distance_report(self, results):
        """生成距离分析报告"""
        # 实现距离报告生成
        pass

    def create_density_map(self, results):
        """创建密度地图"""
        # 实现密度地图创建
        pass

    def create_density_chart(self, results):
        """创建密度图表"""
        # 实现密度图表创建
        pass

    def generate_density_report(self, results):
        """生成密度分析报告"""
        # 实现密度报告生成
        pass
