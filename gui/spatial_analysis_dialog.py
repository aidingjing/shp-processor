#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
空间统计分析对话框
提供空间统计分析的用户界面

作者: Claude Code
创建时间: 2024-10-09
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import pandas as pd
from typing import Optional, Dict, Any
import logging

from core.spatial_analyzer import SpatialAnalyzer
from utils.geometry_utils import GeometryUtils


class SpatialAnalysisDialog:
    """空间统计分析对话框"""

    def __init__(self, parent):
        """
        初始化对话框

        Args:
            parent: 父窗口
        """
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("空间统计分析工具")
        self.window.geometry("1000x700")
        self.window.resizable(True, True)

        # 分析器
        self.analyzer = SpatialAnalyzer()
        self.logger = logging.getLogger(__name__)

        # 分析结果
        self.analysis_results: Optional[Dict[str, Any]] = None

        # 创建界面
        self.create_widgets()
        self.create_menu()

        # 绑定窗口关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建步骤面板
        self.create_step_panel(main_frame)

        # 创建内容面板
        self.create_content_panel(main_frame)

        # 创建状态栏
        self.create_status_bar()

    def create_step_panel(self, parent):
        """创建步骤面板"""
        step_frame = ttk.LabelFrame(parent, text="分析步骤", padding=10)
        step_frame.grid(row=0, column=0, sticky="ns", padx=(0, 10))

        # 步骤列表
        self.steps = [
            {"name": "1. 选择面图层", "status": "pending", "description": "选择包含统计区域的面图层"},
            {"name": "2. 选择目标图层", "status": "pending", "description": "选择要统计的目标图层（点/线/面）"},
            {"name": "3. 配置参数", "status": "pending", "description": "设置分析参数和字段映射"},
            {"name": "4. 执行分析", "status": "pending", "description": "运行空间统计分析"},
            {"name": "5. 查看结果", "status": "pending", "description": "查看和导出分析结果"}
        ]

        self.step_labels = []
        self.step_indicators = []

        for i, step in enumerate(self.steps):
            # 步骤框架
            step_container = ttk.Frame(step_frame)
            step_container.pack(fill=tk.X, pady=5)

            # 状态指示器
            indicator_frame = ttk.Frame(step_container)
            indicator_frame.pack(side=tk.LEFT, padx=(0, 10))

            indicator = tk.Canvas(indicator_frame, width=20, height=20, highlightthickness=0, bg="white")
            indicator.pack()
            self.draw_step_indicator(indicator, "pending")

            # 步骤名称和描述
            text_frame = ttk.Frame(step_container)
            text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

            name_label = ttk.Label(text_frame, text=step["name"], font=("Arial", 10, "bold"))
            name_label.pack(anchor="w")

            desc_label = ttk.Label(text_frame, text=step["description"], font=("Arial", 8), foreground="gray")
            desc_label.pack(anchor="w")

            # 绑定点击事件
            for widget in [indicator, name_label]:
                widget.bind("<Button-1>", lambda e, idx=i: self.switch_to_step(idx))
                widget.config(cursor="hand2")

            self.step_indicators.append(indicator)
            self.step_labels.append((name_label, desc_label))

    def draw_step_indicator(self, canvas, status):
        """绘制步骤指示器"""
        canvas.delete("all")
        x, y = 10, 10

        if status == "pending":
            color = "#CCCCCC"  # 灰色
        elif status == "current":
            color = "#2196F3"  # 蓝色
        elif status == "completed":
            color = "#4CAF50"  # 绿色
        else:
            color = "#F44336"  # 红色

        canvas.create_oval(x-8, y-8, x+8, y+8, fill=color, outline="")

        if status == "completed":
            # 绘制对勾
            canvas.create_line(x-4, y, x-1, y+3, fill="white", width=2)
            canvas.create_line(x-1, y+3, x+4, y-3, fill="white", width=2)

    def create_content_panel(self, parent):
        """创建内容面板"""
        # 使用Notebook管理不同步骤的内容
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=0, column=1, sticky="nsew")

        # 配置权重
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)

        # 创建各个步骤的面板
        self.create_polygons_selection_frame()
        self.create_target_selection_frame()
        self.create_parameters_frame()
        self.create_analysis_frame()
        self.create_results_frame()

        # 绑定标签页切换事件
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # 初始状态：只启用第一个标签页
        self.update_tab_states()

    def create_polygons_selection_frame(self):
        """创建面图层选择面板"""
        self.polygons_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.polygons_frame, text="面图层选择")

        # 文件选择区域
        file_frame = ttk.LabelFrame(self.polygons_frame, text="面图层文件", padding=10)
        file_frame.pack(fill=tk.X, padx=10, pady=10)

        # 文件路径输入
        path_frame = ttk.Frame(file_frame)
        path_frame.pack(fill=tk.X, pady=5)

        ttk.Label(path_frame, text="SHP文件路径:").pack(side=tk.LEFT)
        self.polygons_path_var = tk.StringVar()
        path_entry = ttk.Entry(path_frame, textvariable=self.polygons_path_var, width=50)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5))

        browse_btn = ttk.Button(path_frame, text="浏览", command=self.browse_polygons_file)
        browse_btn.pack(side=tk.RIGHT)

        # 字段选择区域
        fields_frame = ttk.LabelFrame(self.polygons_frame, text="字段映射", padding=10)
        fields_frame.pack(fill=tk.X, padx=10, pady=10)

        field_row = ttk.Frame(fields_frame)
        field_row.pack(fill=tk.X, pady=5)

        ttk.Label(field_row, text="唯一标识字段:").pack(side=tk.LEFT)
        self.polygons_id_field_var = tk.StringVar()
        self.polygons_id_field_combo = ttk.Combobox(field_row, textvariable=self.polygons_id_field_var, width=20)
        self.polygons_id_field_combo.pack(side=tk.LEFT, padx=(10, 0))

        ttk.Label(field_row, text="(可选，留空则使用自动编号)").pack(side=tk.LEFT, padx=(10, 0))

        # 文件信息显示区域
        info_frame = ttk.LabelFrame(self.polygons_frame, text="文件信息", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.polygons_info_text = tk.Text(info_frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
        self.polygons_info_text.pack(fill=tk.BOTH, expand=True)

        # 加载按钮
        load_frame = ttk.Frame(self.polygons_frame)
        load_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(load_frame, text="加载面图层", command=self.load_polygons_layer).pack(side=tk.RIGHT)

    def create_target_selection_frame(self):
        """创建目标图层选择面板"""
        self.target_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.target_frame, text="目标图层选择")

        # 文件选择区域
        file_frame = ttk.LabelFrame(self.target_frame, text="目标图层文件", padding=10)
        file_frame.pack(fill=tk.X, padx=10, pady=10)

        # 文件路径输入
        path_frame = ttk.Frame(file_frame)
        path_frame.pack(fill=tk.X, pady=5)

        ttk.Label(path_frame, text="SHP文件路径:").pack(side=tk.LEFT)
        self.target_path_var = tk.StringVar()
        path_entry = ttk.Entry(path_frame, textvariable=self.target_path_var, width=50)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5))

        browse_btn = ttk.Button(path_frame, text="浏览", command=self.browse_target_file)
        browse_btn.pack(side=tk.RIGHT)

        # 字段选择区域
        fields_frame = ttk.LabelFrame(self.target_frame, text="字段映射", padding=10)
        fields_frame.pack(fill=tk.X, padx=10, pady=10)

        field_row = ttk.Frame(fields_frame)
        field_row.pack(fill=tk.X, pady=5)

        ttk.Label(field_row, text="唯一标识字段:").pack(side=tk.LEFT)
        self.target_id_field_var = tk.StringVar()
        self.target_id_field_combo = ttk.Combobox(field_row, textvariable=self.target_id_field_var, width=20)
        self.target_id_field_combo.pack(side=tk.LEFT, padx=(10, 0))

        ttk.Label(field_row, text="(可选，留空则使用自动编号)").pack(side=tk.LEFT, padx=(10, 0))

        # 文件信息显示区域
        info_frame = ttk.LabelFrame(self.target_frame, text="文件信息", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.target_info_text = tk.Text(info_frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
        self.target_info_text.pack(fill=tk.BOTH, expand=True)

        # 加载按钮
        load_frame = ttk.Frame(self.target_frame)
        load_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(load_frame, text="加载目标图层", command=self.load_target_layer).pack(side=tk.RIGHT)

    def create_parameters_frame(self):
        """创建参数配置面板"""
        self.params_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.params_frame, text="参数配置")

        # 分析参数区域
        analysis_frame = ttk.LabelFrame(self.params_frame, text="分析参数", padding=10)
        analysis_frame.pack(fill=tk.X, padx=10, pady=10)

        # 坐标系选择
        crs_frame = ttk.Frame(analysis_frame)
        crs_frame.pack(fill=tk.X, pady=5)

        ttk.Label(crs_frame, text="坐标系:").pack(side=tk.LEFT)
        self.crs_var = tk.StringVar(value="auto")
        crs_combo = ttk.Combobox(crs_frame, textvariable=self.crs_var, width=30)
        crs_combo['values'] = ["auto", "EPSG:4326", "EPSG:4490", "EPSG:3857", "EPSG:32649", "EPSG:32650"]
        crs_combo.pack(side=tk.LEFT, padx=(10, 0))

        ttk.Label(crs_frame, text="(auto: 自动选择)").pack(side=tk.LEFT, padx=(10, 0))

        # 容差设置
        tolerance_frame = ttk.Frame(analysis_frame)
        tolerance_frame.pack(fill=tk.X, pady=5)

        ttk.Label(tolerance_frame, text="容差:").pack(side=tk.LEFT)
        self.tolerance_var = tk.StringVar(value="0.0")
        tolerance_entry = ttk.Entry(tolerance_frame, textvariable=self.tolerance_var, width=15)
        tolerance_entry.pack(side=tk.LEFT, padx=(10, 0))

        ttk.Label(tolerance_frame, text="度").pack(side=tk.LEFT)

        # 预览信息区域
        preview_frame = ttk.LabelFrame(self.params_frame, text="分析预览", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.preview_text = tk.Text(preview_frame, height=15, wrap=tk.WORD, state=tk.DISABLED)
        self.preview_text.pack(fill=tk.BOTH, expand=True)

        # 预览按钮
        preview_btn_frame = ttk.Frame(self.params_frame)
        preview_btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(preview_btn_frame, text="生成预览", command=self.generate_preview).pack(side=tk.RIGHT)

    def create_analysis_frame(self):
        """创建分析执行面板"""
        self.analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analysis_frame, text="执行分析")

        # 分析控制区域
        control_frame = ttk.LabelFrame(self.analysis_frame, text="分析控制", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        # 分析选项
        options_frame = ttk.Frame(control_frame)
        options_frame.pack(fill=tk.X, pady=5)

        self.analyze_points_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="分析点要素", variable=self.analyze_points_var).pack(side=tk.LEFT)

        self.analyze_lines_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="分析线要素", variable=self.analyze_lines_var).pack(side=tk.LEFT, padx=(20, 0))

        self.analyze_polygons_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="分析面要素", variable=self.analyze_polygons_var).pack(side=tk.LEFT, padx=(20, 0))

        # 执行按钮
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=10)

        self.analyze_btn = ttk.Button(button_frame, text="开始分析", command=self.start_analysis)
        self.analyze_btn.pack(side=tk.RIGHT)

        self.stop_btn = ttk.Button(button_frame, text="停止分析", command=self.stop_analysis, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.RIGHT, padx=(0, 10))

        # 进度显示区域
        progress_frame = ttk.LabelFrame(self.analysis_frame, text="分析进度", padding=10)
        progress_frame.pack(fill=tk.X, padx=10, pady=10)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)

        self.status_label = ttk.Label(progress_frame, text="准备就绪")
        self.status_label.pack()

        # 日志显示区域
        log_frame = ttk.LabelFrame(self.analysis_frame, text="分析日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 日志滚动条
        log_scrollbar = ttk.Scrollbar(self.log_text, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scrollbar.set)

    def create_results_frame(self):
        """创建结果显示面板"""
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="分析结果")

        # 结果概览区域
        overview_frame = ttk.LabelFrame(self.results_frame, text="结果概览", padding=10)
        overview_frame.pack(fill=tk.X, padx=10, pady=10)

        self.overview_text = tk.Text(overview_frame, height=8, wrap=tk.WORD, state=tk.DISABLED)
        self.overview_text.pack(fill=tk.X)

        # 结果表格区域
        table_frame = ttk.LabelFrame(self.results_frame, text="详细统计", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建表格
        columns = ("polygon_id", "point_count", "line_count", "polygon_count", "total_count")
        self.results_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        # 设置列标题
        self.results_tree.heading("polygon_id", text="面ID")
        self.results_tree.heading("point_count", text="点数量")
        self.results_tree.heading("line_count", text="线数量")
        self.results_tree.heading("polygon_count", text="面数量")
        self.results_tree.heading("total_count", text="总计")

        # 设置列宽
        self.results_tree.column("polygon_id", width=100)
        self.results_tree.column("point_count", width=80)
        self.results_tree.column("line_count", width=80)
        self.results_tree.column("polygon_count", width=80)
        self.results_tree.column("total_count", width=80)

        # 添加滚动条
        tree_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.config(yscrollcommand=tree_scrollbar.set)

        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 导出按钮区域
        export_frame = ttk.LabelFrame(self.results_frame, text="导出结果", padding=10)
        export_frame.pack(fill=tk.X, padx=10, pady=10)

        button_frame = ttk.Frame(export_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="导出为SHP文件", command=self.export_shapefile).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="导出为Excel文件", command=self.export_excel).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(button_frame, text="生成统计图表", command=self.generate_chart).pack(side=tk.LEFT, padx=(10, 0))

    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="打开面图层", command=self.browse_polygons_file)
        file_menu.add_command(label="打开目标图层", command=self.browse_target_file)
        file_menu.add_separator()
        file_menu.add_command(label="保存配置", command=self.save_config)
        file_menu.add_command(label="加载配置", command=self.load_config)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_closing)

        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="数据验证", command=self.validate_data)
        tools_menu.add_command(label="坐标系转换", command=self.convert_crs)
        tools_menu.add_command(label="清除结果", command=self.clear_results)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)

    def create_status_bar(self):
        """创建状态栏"""
        status_frame = ttk.Frame(self.window)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # 状态标签
        self.status_label_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(status_frame, textvariable=self.status_label_var, relief=tk.SUNKEN)
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 版本信息
        version_label = ttk.Label(status_frame, text="空间统计分析 v1.0.0", relief=tk.SUNKEN)
        version_label.pack(side=tk.RIGHT)

    def browse_polygons_file(self):
        """浏览面图层文件"""
        filename = filedialog.askopenfilename(
            title="选择面图层SHP文件",
            filetypes=[("SHP文件", "*.shp"), ("所有文件", "*.*")]
        )
        if filename:
            self.polygons_path_var.set(filename)

    def browse_target_file(self):
        """浏览目标图层文件"""
        filename = filedialog.askopenfilename(
            title="选择目标图层SHP文件",
            filetypes=[("SHP文件", "*.shp"), ("所有文件", "*.*")]
        )
        if filename:
            self.target_path_var.set(filename)

    def load_polygons_layer(self):
        """加载面图层"""
        file_path = self.polygons_path_var.get().strip()
        if not file_path:
            messagebox.showerror("错误", "请先选择面图层文件")
            return

        if not os.path.exists(file_path):
            messagebox.showerror("错误", "文件不存在")
            return

        try:
            # 临时读取文件获取字段信息
            import geopandas as gpd
            temp_gdf = gpd.read_file(file_path)

            # 更新字段选择下拉框
            fields = list(temp_gdf.columns)
            self.polygons_id_field_combo['values'] = fields

            # 加载到分析器
            id_field = self.polygons_id_field_var.get().strip()
            if not id_field:
                id_field = None

            result = self.analyzer.load_polygons_layer(file_path, id_field)

            if result['success']:
                self.update_text_widget(self.polygons_info_text, self.format_polygons_info(result))
                self.update_step_status(0, "completed")
                self.update_tab_states()
                self.status_label_var.set(f"面图层加载成功: {result['polygon_count']} 个面要素")
            else:
                messagebox.showerror("加载失败", result['error'])

        except Exception as e:
            messagebox.showerror("加载失败", f"加载面图层时发生错误：{str(e)}")

    def load_target_layer(self):
        """加载目标图层"""
        file_path = self.target_path_var.get().strip()
        if not file_path:
            messagebox.showerror("错误", "请先选择目标图层文件")
            return

        if not os.path.exists(file_path):
            messagebox.showerror("错误", "文件不存在")
            return

        try:
            # 临时读取文件获取字段信息
            import geopandas as gpd
            temp_gdf = gpd.read_file(file_path)

            # 更新字段选择下拉框
            fields = list(temp_gdf.columns)
            self.target_id_field_combo['values'] = fields

            # 加载到分析器
            id_field = self.target_id_field_var.get().strip()
            if not id_field:
                id_field = None

            result = self.analyzer.load_target_layer(file_path, id_field)

            if result['success']:
                self.update_text_widget(self.target_info_text, self.format_target_info(result))
                self.update_step_status(1, "completed")
                self.update_tab_states()
                self.status_label_var.set(f"目标图层加载成功: {result['feature_count']} 个要素")
            else:
                messagebox.showerror("加载失败", result['error'])

        except Exception as e:
            messagebox.showerror("加载失败", f"加载目标图层时发生错误：{str(e)}")

    def generate_preview(self):
        """生成分析预览"""
        try:
            # 验证输入数据
            if not self.analyzer.polygons_gdf or not self.analyzer.target_gdf:
                messagebox.showerror("错误", "请先加载面图层和目标图层")
                return

            # 验证数据
            validation = GeometryUtils.validate_spatial_analysis_inputs(
                self.analyzer.polygons_gdf, self.analyzer.target_gdf
            )

            preview_text = "=== 分析预览 ===\n\n"

            if validation['errors']:
                preview_text += "❌ 错误:\n"
                for error in validation['errors']:
                    preview_text += f"  • {error}\n"
                preview_text += "\n"

            if validation['warnings']:
                preview_text += "⚠️ 警告:\n"
                for warning in validation['warnings']:
                    preview_text += f"  • {warning}\n"
                preview_text += "\n"

            # 添加统计信息
            info = validation['info']
            preview_text += "📊 数据统计:\n"
            preview_text += f"  • 面图层数量: {info['polygons_count']}\n"
            preview_text += f"  • 目标图层数量: {info['target_count']}\n"
            preview_text += f"  • 面图层坐标系: {info['polygons_crs']}\n"
            preview_text += f"  • 目标图层坐标系: {info['target_crs']}\n\n"

            preview_text += "🔍 目标图层几何类型:\n"
            for geom_type, count in info['target_geom_types'].items():
                preview_text += f"  • {geom_type}: {count}\n"

            preview_text += "\n=== 分析配置 ===\n"
            preview_text += f"  • 坐标系: {self.crs_var.get()}\n"
            preview_text += f"  • 容差: {self.tolerance_var.get()} 度\n"
            preview_text += f"  • 分析点要素: {'是' if self.analyze_points_var.get() else '否'}\n"
            preview_text += f"  • 分析线要素: {'是' if self.analyze_lines_var.get() else '否'}\n"
            preview_text += f"  • 分析面要素: {'是' if self.analyze_polygons_var.get() else '否'}\n"

            self.update_text_widget(self.preview_text, preview_text)

        except Exception as e:
            messagebox.showerror("预览失败", f"生成预览时发生错误：{str(e)}")

    def start_analysis(self):
        """开始分析"""
        try:
            # 验证输入
            if not self.analyzer.polygons_gdf or not self.analyzer.target_gdf:
                messagebox.showerror("错误", "请先加载面图层和目标图层")
                return

            # 更新界面状态
            self.analyze_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.progress_var.set(0)
            self.status_label_var.set("正在分析...")

            # 在后台线程中执行分析
            self.analysis_thread = threading.Thread(target=self.perform_analysis)
            self.analysis_thread.daemon = True
            self.analysis_thread.start()

        except Exception as e:
            messagebox.showerror("分析失败", f"启动分析时发生错误：{str(e)}")

    def perform_analysis(self):
        """执行分析（在后台线程中）"""
        try:
            # 更新进度
            self.update_progress(10, "初始化分析器...")

            # 执行空间分析
            self.update_progress(30, "执行空间关系分析...")
            self.analysis_results = self.analyzer.perform_spatial_analysis()

            if not self.analysis_results['success']:
                raise Exception(self.analysis_results['error'])

            # 更新进度
            self.update_progress(80, "生成结果统计...")

            # 处理结果
            self.process_results()

            # 更新进度
            self.update_progress(100, "分析完成")

            # 更新界面
            self.window.after(0, self.analysis_completed)

        except Exception as e:
            self.window.after(0, lambda: self.analysis_failed(str(e)))

    def process_results(self):
        """处理分析结果"""
        if not self.analysis_results or not self.analysis_results['success']:
            return

        # 合并不同类型的统计结果
        results_data = self.analysis_results['results']

        # 获取所有面的ID
        polygon_ids = set()
        for analysis_type, result in results_data.items():
            if 'statistics' in result:
                polygon_ids.update(result['statistics']['polygon_id'])

        # 创建综合统计表
        combined_stats = {}
        for polygon_id in polygon_ids:
            combined_stats[polygon_id] = {
                'polygon_id': polygon_id,
                'point_count': 0,
                'line_count': 0,
                'polygon_count': 0,
                'total_count': 0
            }

        # 填充统计数据
        if 'points' in results_data:
            points_stats = results_data['points']['statistics']
            for _, row in points_stats.iterrows():
                polygon_id = row['polygon_id']
                if polygon_id in combined_stats:
                    combined_stats[polygon_id]['point_count'] = row['point_count']

        if 'lines' in results_data:
            lines_stats = results_data['lines']['statistics']
            for _, row in lines_stats.iterrows():
                polygon_id = row['polygon_id']
                if polygon_id in combined_stats:
                    combined_stats[polygon_id]['line_count'] = row['line_count']

        if 'polygons' in results_data:
            polygons_stats = results_data['polygons']['statistics']
            for _, row in polygons_stats.iterrows():
                polygon_id = row['polygon_id']
                if polygon_id in combined_stats:
                    combined_stats[polygon_id]['polygon_count'] = row['target_polygon_count']

        # 计算总计
        for polygon_id in combined_stats:
            stats = combined_stats[polygon_id]
            stats['total_count'] = stats['point_count'] + stats['line_count'] + stats['polygon_count']

        # 存储处理后的结果
        self.processed_results = list(combined_stats.values())

    def analysis_completed(self):
        """分析完成"""
        try:
            # 更新界面状态
            self.analyze_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_label_var.set("分析完成")

            # 更新步骤状态
            self.update_step_status(3, "completed")
            self.update_step_status(4, "current")
            self.update_tab_states()

            # 显示结果
            self.display_results()

            # 切换到结果标签页
            self.notebook.select(4)

            messagebox.showinfo("分析完成", "空间统计分析已完成！")

        except Exception as e:
            messagebox.showerror("显示结果失败", f"显示分析结果时发生错误：{str(e)}")

    def analysis_failed(self, error_message):
        """分析失败"""
        self.analyze_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label_var.set("分析失败")
        messagebox.showerror("分析失败", f"分析过程中发生错误：{error_message}")

    def stop_analysis(self):
        """停止分析"""
        try:
            # 这里可以添加停止分析的逻辑
            self.stop_btn.config(state=tk.DISABLED)
            self.analyze_btn.config(state=tk.NORMAL)
            self.status_label_var.set("分析已停止")
            self.update_log("用户停止了分析")
        except Exception as e:
            messagebox.showerror("停止失败", f"停止分析时发生错误：{str(e)}")

    def display_results(self):
        """显示分析结果"""
        try:
            # 显示概览信息
            overview_text = self.format_results_overview()
            self.update_text_widget(self.overview_text, overview_text)

            # 显示详细统计表格
            self.display_results_table()

        except Exception as e:
            messagebox.showerror("显示结果失败", f"显示结果时发生错误：{str(e)}")

    def display_results_table(self):
        """显示结果表格"""
        try:
            # 清空表格
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)

            # 添加数据
            if hasattr(self, 'processed_results'):
                for row in self.processed_results:
                    self.results_tree.insert("", tk.END, values=(
                        row['polygon_id'],
                        row['point_count'],
                        row['line_count'],
                        row['polygon_count'],
                        row['total_count']
                    ))

        except Exception as e:
            messagebox.showerror("显示表格失败", f"显示结果表格时发生错误：{str(e)}")

    def export_shapefile(self):
        """导出为SHP文件"""
        try:
            if not self.analysis_results or not self.analysis_results['success']:
                messagebox.showerror("错误", "没有可导出的分析结果")
                return

            filename = filedialog.asksaveasfilename(
                title="保存SHP文件",
                defaultextension=".shp",
                filetypes=[("SHP文件", "*.shp"), ("所有文件", "*.*")]
            )

            if filename:
                result = self.analyzer.export_results_to_shapefile(self.analysis_results, filename)
                if result['success']:
                    messagebox.showinfo("导出成功", f"结果已成功导出到：{filename}")
                else:
                    messagebox.showerror("导出失败", result['error'])

        except Exception as e:
            messagebox.showerror("导出失败", f"导出SHP文件时发生错误：{str(e)}")

    def export_excel(self):
        """导出为Excel文件"""
        try:
            if not self.analysis_results or not self.analysis_results['success']:
                messagebox.showerror("错误", "没有可导出的分析结果")
                return

            filename = filedialog.asksaveasfilename(
                title="保存Excel文件",
                defaultextension=".xlsx",
                filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
            )

            if filename:
                result = self.analyzer.export_results_to_excel(self.analysis_results, filename)
                if result['success']:
                    messagebox.showinfo("导出成功", f"结果已成功导出到：{filename}")
                else:
                    messagebox.showerror("导出失败", result['error'])

        except Exception as e:
            messagebox.showerror("导出失败", f"导出Excel文件时发生错误：{str(e)}")

    def generate_chart(self):
        """生成统计图表"""
        messagebox.showinfo("功能开发中", "统计图表功能正在开发中...")

    def validate_data(self):
        """验证数据"""
        try:
            if not self.analyzer.polygons_gdf or not self.analyzer.target_gdf:
                messagebox.showerror("错误", "请先加载面图层和目标图层")
                return

            validation = GeometryUtils.validate_spatial_analysis_inputs(
                self.analyzer.polygons_gdf, self.analyzer.target_gdf
            )

            # 显示验证结果
            result_text = "=== 数据验证结果 ===\n\n"

            if validation['valid']:
                result_text += "✅ 数据验证通过\n\n"
            else:
                result_text += "❌ 数据验证失败\n\n"

            if validation['errors']:
                result_text += "错误:\n"
                for error in validation['errors']:
                    result_text += f"  • {error}\n"
                result_text += "\n"

            if validation['warnings']:
                result_text += "警告:\n"
                for warning in validation['warnings']:
                    result_text += f"  • {warning}\n"
                result_text += "\n"

            info = validation['info']
            result_text += "数据信息:\n"
            result_text += f"  • 面图层数量: {info['polygons_count']}\n"
            result_text += f"  • 目标图层数量: {info['target_count']}\n"
            result_text += f"  • 面图层坐标系: {info['polygons_crs']}\n"
            result_text += f"  • 目标图层坐标系: {info['target_crs']}\n"

            messagebox.showinfo("数据验证", result_text)

        except Exception as e:
            messagebox.showerror("验证失败", f"数据验证时发生错误：{str(e)}")

    def convert_crs(self):
        """坐标系转换"""
        messagebox.showinfo("功能开发中", "坐标系转换功能正在开发中...")

    def clear_results(self):
        """清除结果"""
        try:
            # 清空结果
            self.analysis_results = None
            if hasattr(self, 'processed_results'):
                self.processed_results = []

            # 清空界面
            self.overview_text.config(state=tk.NORMAL)
            self.overview_text.delete("1.0", tk.END)
            self.overview_text.config(state=tk.DISABLED)

            for item in self.results_tree.get_children():
                self.results_tree.delete(item)

            # 重置步骤状态
            for i in range(2, 5):
                self.update_step_status(i, "pending")

            self.update_tab_states()

            messagebox.showinfo("清除完成", "分析结果已清除")

        except Exception as e:
            messagebox.showerror("清除失败", f"清除结果时发生错误：{str(e)}")

    def save_config(self):
        """保存配置"""
        messagebox.showinfo("功能开发中", "配置保存功能正在开发中...")

    def load_config(self):
        """加载配置"""
        messagebox.showinfo("功能开发中", "配置加载功能正在开发中...")

    def show_help(self):
        """显示帮助信息"""
        help_text = """
空间统计分析工具使用说明：

1. 选择面图层
   - 点击"浏览"选择包含统计区域的面图层SHP文件
   - 可选择唯一标识字段（留空则自动编号）
   - 点击"加载面图层"导入数据

2. 选择目标图层
   - 选择要统计的目标图层SHP文件（点/线/面）
   - 可选择唯一标识字段
   - 点击"加载目标图层"导入数据

3. 配置参数
   - 设置坐标系（推荐使用"auto"自动选择）
   - 设置容差（如需要）
   - 选择要分析的几何类型
   - 点击"生成预览"查看分析概览

4. 执行分析
   - 选择要分析的几何类型（点/线/面）
   - 点击"开始分析"执行空间统计
   - 查看分析进度和日志

5. 查看结果
   - 查看分析结果概览
   - 查看详细统计表格
   - 导出结果为SHP或Excel文件

注意事项：
• 确保面图层和目标图层的坐标系一致
• 面图层必须包含Polygon或MultiPolygon几何类型
• 每个目标要素只会归属于一个面（最大归属原则）
• 导出的SHP文件包含统计字段

技术支持：
如有问题请联系开发团队或提交issue
        """
        help_window = tk.Toplevel(self.window)
        help_window.title("使用说明")
        help_window.geometry("600x500")
        help_window.resizable(False, False)

        text_widget = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert("1.0", help_text)
        text_widget.config(state=tk.DISABLED)

        close_button = ttk.Button(help_window, text="关闭", command=help_window.destroy)
        close_button.pack(pady=10)

    def show_about(self):
        """显示关于信息"""
        about_text = """
空间统计分析工具 v1.0.0

一个用于分析空间分布关系的GIS工具。

主要功能：
• 面图层与目标图层的空间关系统计
• 支持点、线、面多种几何类型
• 智能避免重复统计
• 详细的统计结果和导出功能

技术特点：
• 基于Shapely和GeoPandas的空间分析
• 支持多种坐标系
• 提供直观的用户界面
• 完整的错误处理机制

开发语言：Python
界面框架：Tkinter
GIS库：GeoPandas, Shapely

版权所有 © 2024
        """
        messagebox.showinfo("关于", about_text)

    def switch_to_step(self, step_index):
        """切换到指定步骤"""
        if 0 <= step_index < len(self.steps):
            self.notebook.select(step_index)

    def update_step_status(self, step_index, status):
        """更新步骤状态"""
        if 0 <= step_index < len(self.steps):
            self.steps[step_index]["status"] = status
            self.draw_step_indicator(self.step_indicators[step_index], status)

            # 更新标签颜色
            name_label, desc_label = self.step_labels[step_index]
            if status == "completed":
                name_label.config(foreground="#4CAF50")
            elif status == "current":
                name_label.config(foreground="#2196F3")
            elif status == "error":
                name_label.config(foreground="#F44336")
            else:
                name_label.config(foreground="gray")

    def update_tab_states(self):
        """更新标签页状态"""
        for i, step in enumerate(self.steps):
            if i == 0:
                self.notebook.tab(i, state="normal")
            elif step["status"] == "completed":
                self.notebook.tab(i, state="normal")
            elif i > 0 and self.steps[i-1]["status"] == "completed":
                self.notebook.tab(i, state="normal")
            else:
                self.notebook.tab(i, state="disabled")

    def on_tab_changed(self, event):
        """标签页切换事件"""
        current_tab = self.notebook.index(self.notebook.select())

        # 更新当前步骤指示器
        for i, step in enumerate(self.steps):
            if i == current_tab:
                if step["status"] == "pending":
                    self.update_step_status(i, "current")
                elif step["status"] != "completed":
                    self.update_step_status(i, "current")
            elif step["status"] == "current":
                self.update_step_status(i, "pending")

    def update_progress(self, value, message):
        """更新进度条"""
        self.window.after(0, lambda: self.progress_var.set(value))
        self.window.after(0, lambda: self.status_label.config(text=message))
        self.update_log(message)

    def update_log(self, message):
        """更新日志"""
        self.window.after(0, lambda: self._append_log(message))

    def _append_log(self, message):
        """添加日志消息"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def update_text_widget(self, widget, text):
        """更新文本组件"""
        widget.config(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)
        widget.config(state=tk.DISABLED)

    def format_polygons_info(self, result):
        """格式化面图层信息"""
        info = f"面图层加载成功\n\n"
        info += f"📊 统计信息:\n"
        info += f"  • 面要素数量: {result['polygon_count']}\n"
        info += f"  • 边界范围: [{result['bounds'][0]:.4f}, {result['bounds'][1]:.4f}, {result['bounds'][2]:.4f}, {result['bounds'][3]:.4f}]\n\n"
        info += f"📋 字段列表:\n"
        for i, field in enumerate(result['columns']):
            info += f"  {i+1:2d}. {field}\n"
        return info

    def format_target_info(self, result):
        """格式化目标图层信息"""
        info = f"目标图层加载成功\n\n"
        info += f"📊 统计信息:\n"
        info += f"  • 要素总数: {result['feature_count']}\n"
        info += f"  • 边界范围: [{result['bounds'][0]:.4f}, {result['bounds'][1]:.4f}, {result['bounds'][2]:.4f}, {result['bounds'][3]:.4f}]\n\n"
        info += f"🔍 几何类型分布:\n"
        for geom_type, count in result['geometry_types'].items():
            info += f"  • {geom_type}: {count}\n\n"
        info += f"📋 字段列表:\n"
        for i, field in enumerate(result['columns']):
            info += f"  {i+1:2d}. {field}\n"
        return info

    def format_results_overview(self):
        """格式化结果概览"""
        if not self.analysis_results or not self.analysis_results['success']:
            return "没有分析结果"

        results = self.analysis_results['results']
        summary = self.analysis_results['summary']

        overview = "=== 分析结果概览 ===\n\n"

        # 分析类型统计
        overview += f"📈 分析类型: {', '.join(summary['analysis_types'])}\n\n"

        # 各种要素统计
        if 'points' in results:
            points_result = results['points']
            overview += f"📍 点要素统计:\n"
            overview += f"  • 总点数: {points_result['total_points']}\n"
            overview += f"  • 已分配: {points_result['assigned_points']}\n"
            overview += f"  • 未分配: {points_result['unassigned_points']}\n"
            overview += f"  • 包含点的面数: {points_result['summary']['polygons_with_points']}\n\n"

        if 'lines' in results:
            lines_result = results['lines']
            overview += f"〰️ 线要素统计:\n"
            overview += f"  • 总线数: {lines_result['total_lines']}\n"
            overview += f"  • 已分配: {lines_result['assigned_lines']}\n"
            overview += f"  • 未分配: {lines_result['unassigned_lines']}\n"
            overview += f"  • 包含线的面数: {lines_result['summary']['polygons_with_lines']}\n\n"

        if 'polygons' in results:
            polygons_result = results['polygons']
            overview += f"▭ 面要素统计:\n"
            overview += f"  • 总面数: {polygons_result['total_target_polygons']}\n"
            overview += f"  • 已分配: {polygons_result['assigned_polygons']}\n"
            overview += f"  • 未分配: {polygons_result['unassigned_polygons']}\n"
            overview += f"  • 包含目标面的面数: {polygons_result['summary']['polygons_with_targets']}\n\n"

        # 总体统计
        if hasattr(self, 'processed_results'):
            total_assigned = sum(r['total_count'] for r in self.processed_results)
            max_count = max(r['total_count'] for r in self.processed_results) if self.processed_results else 0
            avg_count = total_assigned / len(self.processed_results) if self.processed_results else 0

            overview += f"📊 总体统计:\n"
            overview += f"  • 统计面数: {len(self.processed_results)}\n"
            overview += f"  • 分配要素总数: {total_assigned}\n"
            overview += f"  • 每个面平均要素数: {avg_count:.1f}\n"
            overview += f"  • 每个面最大要素数: {max_count}\n"

        return overview

    def on_closing(self):
        """窗口关闭事件"""
        if messagebox.askokcancel("退出", "确定要退出空间统计分析工具吗？"):
            self.window.destroy()