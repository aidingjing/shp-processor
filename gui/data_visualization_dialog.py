"""
数据可视化工具对话框
提供数据图表生成和展示功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
from typing import List, Dict, Optional, Tuple
import json
import os

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class DataVisualizationDialog:
    """数据可视化工具对话框"""

    def __init__(self, parent, dataframe=None):
        """初始化数据可视化工具对话框"""
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("数据可视化工具")
        self.window.geometry("1200x800")
        self.window.resizable(True, True)
        self.window.transient(parent)
        self.window.grab_set()

        # 数据存储
        self.dataframe = dataframe
        self.current_figure = None
        self.current_canvas = None

        # 图表配置
        self.chart_types = {
            "柱状图": "bar",
            "折线图": "line", 
            "散点图": "scatter",
            "饼图": "pie",
            "箱线图": "box",
            "直方图": "histogram",
            "热力图": "heatmap",
            "面积图": "area"
        }

        # 创建界面
        self.create_widgets()
        self.center_window()

        # 如果有数据，自动加载
        if self.dataframe is not None:
            self.load_data()

    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建标题
        title_label = tk.Label(main_frame, text="数据可视化工具", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))

        # 创建工具栏
        self.create_toolbar(main_frame)

        # 创建主要内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 左侧：配置面板
        self.create_config_panel(content_frame)

        # 右侧：图表显示面板
        self.create_chart_panel(content_frame)

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

        # 导出按钮
        export_btn = ttk.Button(toolbar_frame, text="导出图表", command=self.export_chart)
        export_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 刷新按钮
        refresh_btn = ttk.Button(toolbar_frame, text="刷新图表", command=self.refresh_chart)
        refresh_btn.pack(side=tk.LEFT)

    def create_config_panel(self, parent):
        """创建配置面板"""
        config_frame = ttk.LabelFrame(parent, text="图表配置", padding="10")
        config_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # 图表类型选择
        chart_type_frame = ttk.LabelFrame(config_frame, text="图表类型", padding="5")
        chart_type_frame.pack(fill=tk.X, pady=(0, 10))

        self.chart_type_var = tk.StringVar(value="柱状图")
        for chart_type in self.chart_types.keys():
            ttk.Radiobutton(chart_type_frame, text=chart_type, 
                          variable=self.chart_type_var, value=chart_type,
                          command=self.on_chart_type_changed).pack(anchor=tk.W)

        # 数据配置
        data_frame = ttk.LabelFrame(config_frame, text="数据配置", padding="5")
        data_frame.pack(fill=tk.X, pady=(0, 10))

        # X轴字段
        ttk.Label(data_frame, text="X轴字段:").pack(anchor=tk.W)
        self.x_field_combo = ttk.Combobox(data_frame, width=20, state="readonly")
        self.x_field_combo.pack(fill=tk.X, pady=(2, 5))
        self.x_field_combo.bind("<<ComboboxSelected>>", self.on_field_changed)

        # Y轴字段
        ttk.Label(data_frame, text="Y轴字段:").pack(anchor=tk.W)
        self.y_field_combo = ttk.Combobox(data_frame, width=20, state="readonly")
        self.y_field_combo.pack(fill=tk.X, pady=(2, 5))
        self.y_field_combo.bind("<<ComboboxSelected>>", self.on_field_changed)

        # 分组字段（可选）
        ttk.Label(data_frame, text="分组字段:").pack(anchor=tk.W)
        self.group_field_combo = ttk.Combobox(data_frame, width=20, state="readonly")
        self.group_field_combo.pack(fill=tk.X, pady=(2, 5))
        self.group_field_combo['values'] = ["无"]
        self.group_field_combo.set("无")
        self.group_field_combo.bind("<<ComboboxSelected>>", self.on_field_changed)

        # 样式配置
        style_frame = ttk.LabelFrame(config_frame, text="样式配置", padding="5")
        style_frame.pack(fill=tk.X, pady=(0, 10))

        # 图表标题
        ttk.Label(style_frame, text="图表标题:").pack(anchor=tk.W)
        self.title_entry = ttk.Entry(style_frame, width=20)
        self.title_entry.pack(fill=tk.X, pady=(2, 5))
        self.title_entry.insert(0, "数据可视化图表")

        # X轴标签
        ttk.Label(style_frame, text="X轴标签:").pack(anchor=tk.W)
        self.xlabel_entry = ttk.Entry(style_frame, width=20)
        self.xlabel_entry.pack(fill=tk.X, pady=(2, 5))

        # Y轴标签
        ttk.Label(style_frame, text="Y轴标签:").pack(anchor=tk.W)
        self.ylabel_entry = ttk.Entry(style_frame, width=20)
        self.ylabel_entry.pack(fill=tk.X, pady=(2, 5))

        # 图例显示
        self.show_legend_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(style_frame, text="显示图例", 
                       variable=self.show_legend_var).pack(anchor=tk.W, pady=5)

        # 网格显示
        self.show_grid_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(style_frame, text="显示网格", 
                       variable=self.show_grid_var).pack(anchor=tk.W, pady=2)

        # 高级选项
        advanced_frame = ttk.LabelFrame(config_frame, text="高级选项", padding="5")
        advanced_frame.pack(fill=tk.X, pady=(0, 10))

        # 图表大小
        size_frame = ttk.Frame(advanced_frame)
        size_frame.pack(fill=tk.X, pady=2)
        ttk.Label(size_frame, text="图表大小:").pack(side=tk.LEFT)
        self.size_var = tk.StringVar(value="8x6")
        size_combo = ttk.Combobox(size_frame, textvariable=self.size_var, 
                                  values=["6x4", "8x6", "10x8", "12x9"], 
                                  width=8, state="readonly")
        size_combo.pack(side=tk.LEFT, padx=(5, 0))

        # 颜色主题
        ttk.Label(advanced_frame, text="颜色主题:").pack(anchor=tk.W, pady=(5, 2))
        self.theme_var = tk.StringVar(value="默认")
        theme_combo = ttk.Combobox(advanced_frame, textvariable=self.theme_var,
                                   values=["默认", "蓝色", "绿色", "红色", "彩虹"], 
                                   width=18, state="readonly")
        theme_combo.pack(fill=tk.X, pady=(0, 5))

        # 生成按钮
        generate_btn = ttk.Button(config_frame, text="生成图表", command=self.generate_chart)
        generate_btn.pack(fill=tk.X, pady=(20, 0))

        # 预设模板
        template_btn = ttk.Button(config_frame, text="快速模板", command=self.show_templates)
        template_btn.pack(fill=tk.X, pady=(5, 0))

    def create_chart_panel(self, parent):
        """创建图表显示面板"""
        chart_frame = ttk.LabelFrame(parent, text="图表显示", padding="10")
        chart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 创建matplotlib图形区域
        self.figure_frame = ttk.Frame(chart_frame)
        self.figure_frame.pack(fill=tk.BOTH, expand=True)

        # 初始化空的图形
        self.create_empty_chart()

    def create_empty_chart(self):
        """创建空图表"""
        if self.current_figure:
            plt.close(self.current_figure)
        
        self.current_figure = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.current_figure.add_subplot(111)
        
        # 显示提示信息
        self.ax.text(0.5, 0.5, '请加载数据并配置图表参数', 
                    ha='center', va='center', fontsize=14, 
                    transform=self.ax.transAxes)
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.axis('off')
        
        # 创建画布
        if self.current_canvas:
            self.current_canvas.get_tk_widget().destroy()
        
        self.current_canvas = FigureCanvasTkAgg(self.current_figure, self.figure_frame)
        self.current_canvas.draw()
        self.current_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 添加工具栏
        toolbar_frame = ttk.Frame(self.figure_frame)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.current_canvas, toolbar_frame)
        toolbar.update()

    def create_status_bar(self, parent):
        """创建状态栏"""
        self.status_label = tk.Label(parent, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, pady=(10, 0))

    def load_data(self):
        """加载数据"""
        if self.dataframe is not None:
            self.update_field_combos()
            self.data_label.config(text=f"已加载 {len(self.dataframe)} 行数据")
            self.status_label.config(text=f"数据加载成功，共 {len(self.dataframe)} 行 {len(self.dataframe.columns)} 列")
        else:
            self.data_label.config(text="未加载数据")
            self.status_label.config(text="请加载数据文件")

    def load_data_from_file(self):
        """从文件加载数据"""
        file_types = [
            ("CSV文件", "*.csv"),
            ("Excel文件", "*.xlsx *.xls"),
            ("JSON文件", "*.json"),
            ("所有文件", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="选择数据文件",
            filetypes=file_types
        )
        
        if filename:
            try:
                self.status_label.config(text="正在加载数据...")
                self.window.update()
                
                # 根据文件扩展名选择读取方式
                if filename.endswith('.csv'):
                    self.dataframe = pd.read_csv(filename, encoding='utf-8')
                elif filename.endswith(('.xlsx', '.xls')):
                    self.dataframe = pd.read_excel(filename)
                elif filename.endswith('.json'):
                    self.dataframe = pd.read_json(filename, encoding='utf-8')
                else:
                    messagebox.showerror("错误", "不支持的文件格式")
                    return
                
                self.load_data()
                
                # 自动设置一些默认值
                self.set_default_values()
                
            except Exception as e:
                messagebox.showerror("加载错误", f"加载数据失败：\n{e}")
                self.status_label.config(text="数据加载失败")

    def set_default_values(self):
        """设置默认值"""
        if self.dataframe is not None:
            # 获取数值列和分类列
            numeric_columns = self.dataframe.select_dtypes(include=[np.number]).columns.tolist()
            categorical_columns = self.dataframe.select_dtypes(include=['object']).columns.tolist()
            
            # 设置默认字段
            if categorical_columns:
                self.x_field_combo.set(categorical_columns[0])
                if len(categorical_columns) > 1:
                    self.group_field_combo['values'] = ["无"] + categorical_columns
                    self.group_field_combo.set("无")
            
            if numeric_columns:
                self.y_field_combo['values'] = numeric_columns
                if numeric_columns:
                    self.y_field_combo.set(numeric_columns[0])
            
            if categorical_columns:
                self.x_field_combo['values'] = categorical_columns
                if categorical_columns:
                    self.x_field_combo.set(categorical_columns[0])

    def update_field_combos(self):
        """更新字段下拉框"""
        if self.dataframe is not None:
            columns = self.dataframe.columns.tolist()
            
            # 更新X轴字段
            self.x_field_combo['values'] = columns
            
            # 更新Y轴字段（仅数值列）
            numeric_columns = self.dataframe.select_dtypes(include=[np.number]).columns.tolist()
            self.y_field_combo['values'] = numeric_columns
            
            # 更新分组字段
            categorical_columns = self.dataframe.select_dtypes(include=['object']).columns.tolist()
            self.group_field_combo['values'] = ["无"] + categorical_columns

    def on_chart_type_changed(self):
        """图表类型改变事件"""
        # 根据图表类型调整可用选项
        chart_type = self.chart_type_var.get()
        
        if chart_type == "饼图":
            # 饼图不需要Y轴
            self.y_field_combo.set("")
            self.y_field_combo.config(state="disabled")
        else:
            self.y_field_combo.config(state="readonly")
            
        if chart_type in ["直方图", "箱线图"]:
            # 直方图和箱线图只需要一个数值字段
            self.x_field_combo.config(state="disabled")
            self.y_field_combo.config(state="readonly")
        else:
            self.x_field_combo.config(state="readonly")

    def on_field_changed(self, event=None):
        """字段改变事件"""
        # 可以在这里添加字段改变的逻辑
        pass

    def get_color_palette(self):
        """获取颜色调色板"""
        theme = self.theme_var.get()
        
        if theme == "默认":
            return plt.rcParams['axes.prop_cycle'].by_key()['color']
        elif theme == "蓝色":
            return plt.cm.Blues(np.linspace(0.3, 0.9, 10))
        elif theme == "绿色":
            return plt.cm.Greens(np.linspace(0.3, 0.9, 10))
        elif theme == "红色":
            return plt.cm.Reds(np.linspace(0.3, 0.9, 10))
        elif theme == "彩虹":
            return plt.cm.rainbow(np.linspace(0, 1, 10))
        else:
            return plt.rcParams['axes.prop_cycle'].by_key()['color']

    def generate_chart(self):
        """生成图表"""
        if self.dataframe is None:
            messagebox.showwarning("提示", "请先加载数据")
            return
        
        x_field = self.x_field_combo.get()
        y_field = self.y_field_combo.get()
        chart_type = self.chart_type_var.get()
        
        # 验证字段选择
        if chart_type not in ["直方图", "箱线图"] and not x_field:
            messagebox.showwarning("提示", "请选择X轴字段")
            return
            
        if chart_type not in ["饼图", "直方图", "箱线图"] and not y_field:
            messagebox.showwarning("提示", "请选择Y轴字段")
            return
        
        if chart_type in ["直方图", "箱线图"] and not y_field:
            messagebox.showwarning("提示", f"{chart_type}需要选择数值字段")
            return
        
        try:
            self.status_label.config(text="正在生成图表...")
            self.window.update()
            
            # 清除当前图形
            if self.current_figure:
                plt.close(self.current_figure)
            
            # 获取图表大小
            size_str = self.size_var.get()
            width, height = map(float, size_str.split('x'))
            self.current_figure = Figure(figsize=(width, height), dpi=100)
            self.ax = self.current_figure.add_subplot(111)
            
            # 获取颜色
            colors = self.get_color_palette()
            
            # 根据图表类型生成图表
            if chart_type == "柱状图":
                self.create_bar_chart(x_field, y_field, colors)
            elif chart_type == "折线图":
                self.create_line_chart(x_field, y_field, colors)
            elif chart_type == "散点图":
                self.create_scatter_chart(x_field, y_field, colors)
            elif chart_type == "饼图":
                self.create_pie_chart(x_field, colors)
            elif chart_type == "箱线图":
                self.create_box_chart(y_field, colors)
            elif chart_type == "直方图":
                self.create_histogram(y_field, colors)
            elif chart_type == "热力图":
                self.create_heatmap(colors)
            elif chart_type == "面积图":
                self.create_area_chart(x_field, y_field, colors)
            
            # 设置图表样式
            self.set_chart_style()
            
            # 创建新的画布
            if self.current_canvas:
                self.current_canvas.get_tk_widget().destroy()
            
            self.current_canvas = FigureCanvasTkAgg(self.current_figure, self.figure_frame)
            self.current_canvas.draw()
            self.current_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # 添加工具栏
            toolbar_frame = ttk.Frame(self.figure_frame)
            toolbar_frame.pack(fill=tk.X)
            toolbar = NavigationToolbar2Tk(self.current_canvas, toolbar_frame)
            toolbar.update()
            
            self.status_label.config(text="图表生成完成")
            
        except Exception as e:
            messagebox.showerror("生成错误", f"生成图表失败：\n{e}")
            self.status_label.config(text="图表生成失败")

    def create_bar_chart(self, x_field, y_field, colors):
        """创建柱状图"""
        group_field = self.group_field_combo.get()
        
        if group_field != "无":
            # 分组柱状图
            pivot_data = self.dataframe.pivot_table(values=y_field, index=x_field, 
                                                  columns=group_field, aggfunc='mean')
            pivot_data.plot(kind='bar', ax=self.ax, color=colors)
        else:
            # 简单柱状图
            if pd.api.types.is_numeric_dtype(self.dataframe[x_field]):
                # 如果X轴是数值，先分组
                grouped_data = self.dataframe.groupby(x_field)[y_field].mean()
            else:
                grouped_data = self.dataframe.groupby(x_field)[y_field].mean()
            
            grouped_data.plot(kind='bar', ax=self.ax, color=colors[0])

    def create_line_chart(self, x_field, y_field, colors):
        """创建折线图"""
        group_field = self.group_field_combo.get()
        
        if group_field != "无":
            # 分组折线图
            for i, (name, group) in enumerate(self.dataframe.groupby(group_field)):
                group.plot(x=x_field, y=y_field, ax=self.ax, label=name, 
                          color=colors[i % len(colors)], marker='o')
        else:
            # 简单折线图
            self.ax.plot(self.dataframe[x_field], self.dataframe[y_field], 
                        color=colors[0], marker='o', linewidth=2)

    def create_scatter_chart(self, x_field, y_field, colors):
        """创建散点图"""
        group_field = self.group_field_combo.get()
        
        if group_field != "无":
            # 分组散点图
            for i, (name, group) in enumerate(self.dataframe.groupby(group_field)):
                self.ax.scatter(group[x_field], group[y_field], 
                              label=name, color=colors[i % len(colors)], alpha=0.7)
        else:
            # 简单散点图
            self.ax.scatter(self.dataframe[x_field], self.dataframe[y_field], 
                          color=colors[0], alpha=0.7)

    def create_pie_chart(self, x_field, colors):
        """创建饼图"""
        # 统计数据
        value_counts = self.dataframe[x_field].value_counts()
        
        # 限制显示数量（超过10个时只显示前10个）
        if len(value_counts) > 10:
            value_counts = value_counts.head(10)
            title_suffix = " (前10个)"
        else:
            title_suffix = ""
        
        # 创建饼图
        wedges, texts, autotexts = self.ax.pie(value_counts.values, 
                                               labels=value_counts.index,
                                               colors=colors[:len(value_counts)],
                                               autopct='%1.1f%%', startangle=90)
        
        # 设置标题后缀
        self.title_suffix = title_suffix

    def create_box_chart(self, y_field, colors):
        """创建箱线图"""
        group_field = self.group_field_combo.get()
        
        if group_field != "无":
            # 分组箱线图
            groups = self.dataframe.groupby(group_field)[y_field].apply(list)
            self.ax.boxplot(groups.values, labels=groups.index)
            plt.xticks(rotation=45)
        else:
            # 简单箱线图
            self.ax.boxplot(self.dataframe[y_field].dropna())
            self.ax.set_xticklabels([y_field])

    def create_histogram(self, y_field, colors):
        """创建直方图"""
        data = self.dataframe[y_field].dropna()
        
        # 自动确定分箱数量
        bins = min(30, int(np.sqrt(len(data))))
        
        self.ax.hist(data, bins=bins, color=colors[0], alpha=0.7, edgecolor='black')

    def create_heatmap(self, colors):
        """创建热力图"""
        # 选择数值列
        numeric_data = self.dataframe.select_dtypes(include=[np.number])
        
        if numeric_data.empty:
            messagebox.showwarning("提示", "数据中没有数值列，无法生成热力图")
            return
        
        # 计算相关性矩阵
        corr_matrix = numeric_data.corr()
        
        # 创建热力图
        im = self.ax.imshow(corr_matrix, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
        
        # 设置刻度标签
        self.ax.set_xticks(range(len(corr_matrix.columns)))
        self.ax.set_yticks(range(len(corr_matrix.columns)))
        self.ax.set_xticklabels(corr_matrix.columns, rotation=45, ha='right')
        self.ax.set_yticklabels(corr_matrix.columns)
        
        # 添加数值标签
        for i in range(len(corr_matrix.columns)):
            for j in range(len(corr_matrix.columns)):
                text = self.ax.text(j, i, f'{corr_matrix.iloc[i, j]:.2f}',
                                   ha="center", va="center", color="black", fontsize=8)
        
        # 添加颜色条
        cbar = self.current_figure.colorbar(im, ax=self.ax)
        cbar.set_label('相关系数')

    def create_area_chart(self, x_field, y_field, colors):
        """创建面积图"""
        group_field = self.group_field_combo.get()
        
        if group_field != "无":
            # 分组面积图
            pivot_data = self.dataframe.pivot_table(values=y_field, index=x_field, 
                                                  columns=group_field, aggfunc='sum')
            pivot_data.plot(kind='area', ax=self.ax, color=colors, alpha=0.7)
        else:
            # 简单面积图
            if pd.api.types.is_numeric_dtype(self.dataframe[x_field]):
                # 如果X轴是数值，先排序
                sorted_data = self.dataframe.sort_values(x_field)
            else:
                sorted_data = self.dataframe
            
            self.ax.fill_between(sorted_data[x_field], sorted_data[y_field], 
                               color=colors[0], alpha=0.7)

    def set_chart_style(self):
        """设置图表样式"""
        # 设置标题
        title = self.title_entry.get()
        if hasattr(self, 'title_suffix'):
            title += self.title_suffix
        self.ax.set_title(title, fontsize=14, fontweight='bold')
        
        # 设置轴标签
        xlabel = self.xlabel_entry.get() or self.x_field_combo.get()
        ylabel = self.ylabel_entry.get() or self.y_field_combo.get()
        
        if xlabel:
            self.ax.set_xlabel(xlabel, fontsize=12)
        if ylabel:
            self.ax.set_ylabel(ylabel, fontsize=12)
        
        # 显示图例
        if self.show_legend_var.get() and self.ax.get_legend_handles_labels()[0]:
            self.ax.legend()
        
        # 显示网格
        if self.show_grid_var.get():
            self.ax.grid(True, alpha=0.3)
        
        # 调整布局
        self.current_figure.tight_layout()

    def refresh_chart(self):
        """刷新图表"""
        if self.dataframe is not None:
            self.generate_chart()
        else:
            messagebox.showwarning("提示", "请先加载数据")

    def export_chart(self):
        """导出图表"""
        if self.current_figure is None:
            messagebox.showwarning("提示", "没有可导出的图表")
            return
        
        file_types = [
            ("PNG图片", "*.png"),
            ("PDF文件", "*.pdf"),
            ("SVG文件", "*.svg"),
            ("所有文件", "*.*")
        ]
        
        filename = filedialog.asksaveasfilename(
            title="保存图表",
            defaultextension=".png",
            filetypes=file_types
        )
        
        if filename:
            try:
                self.current_figure.savefig(filename, dpi=300, bbox_inches='tight')
                messagebox.showinfo("导出成功", f"图表已保存到：\n{filename}")
                self.status_label.config(text=f"图表已导出到: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("导出错误", f"导出图表失败：\n{e}")

    def show_templates(self):
        """显示快速模板"""
        template_window = tk.Toplevel(self.window)
        template_window.title("快速模板")
        template_window.geometry("400x500")
        template_window.transient(self.window)
        template_window.grab_set()
        
        # 模板列表
        templates = [
            {
                "name": "基础柱状图",
                "description": "显示分类数据的数值对比",
                "setup": lambda: self.apply_template("柱状图", None, None, False)
            },
            {
                "name": "时间序列折线图",
                "description": "显示数据随时间的变化趋势",
                "setup": lambda: self.apply_template("折线图", None, None, False)
            },
            {
                "name": "相关性散点图",
                "description": "显示两个变量之间的关系",
                "setup": lambda: self.apply_template("散点图", None, None, False)
            },
            {
                "name": "数据分布直方图",
                "description": "显示数值数据的分布情况",
                "setup": lambda: self.apply_template("直方图", None, None, False)
            },
            {
                "name": "占比饼图",
                "description": "显示各部分的占比情况",
                "setup": lambda: self.apply_template("饼图", None, None, False)
            },
            {
                "name": "相关性热力图",
                "description": "显示数值变量之间的相关性",
                "setup": lambda: self.apply_template("热力图", None, None, False)
            }
        ]
        
        # 创建模板列表
        template_frame = ttk.Frame(template_window)
        template_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for i, template in enumerate(templates):
            # 模板框架
            item_frame = ttk.LabelFrame(template_frame, text=template["name"], padding="10")
            item_frame.pack(fill=tk.X, pady=(0, 10))
            
            # 描述
            desc_label = tk.Label(item_frame, text=template["description"], wraplength=350)
            desc_label.pack(anchor=tk.W)
            
            # 应用按钮
            apply_btn = ttk.Button(item_frame, text="应用模板", 
                                 command=template["setup"])
            apply_btn.pack(anchor=tk.E, pady=(5, 0))
        
        # 关闭按钮
        close_btn = ttk.Button(template_window, text="关闭", command=template_window.destroy)
        close_btn.pack(pady=10)

    def apply_template(self, chart_type, x_field, y_field, use_legend):
        """应用模板"""
        # 设置图表类型
        self.chart_type_var.set(chart_type)
        
        # 自动选择字段
        if self.dataframe is not None:
            numeric_columns = self.dataframe.select_dtypes(include=[np.number]).columns.tolist()
            categorical_columns = self.dataframe.select_dtypes(include=['object']).columns.tolist()
            
            if chart_type == "柱状图":
                if categorical_columns and numeric_columns:
                    self.x_field_combo.set(categorical_columns[0])
                    self.y_field_combo.set(numeric_columns[0])
            elif chart_type == "折线图":
                if len(categorical_columns) >= 2 and numeric_columns:
                    self.x_field_combo.set(categorical_columns[0])
                    self.y_field_combo.set(numeric_columns[0])
            elif chart_type == "散点图":
                if len(numeric_columns) >= 2:
                    self.x_field_combo.set(numeric_columns[0])
                    self.y_field_combo.set(numeric_columns[1])
            elif chart_type == "直方图" or chart_type == "箱线图":
                if numeric_columns:
                    self.y_field_combo.set(numeric_columns[0])
            elif chart_type == "饼图":
                if categorical_columns:
                    self.x_field_combo.set(categorical_columns[0])
        
        # 设置其他选项
        self.show_legend_var.set(use_legend)
        
        # 更新图表类型
        self.on_chart_type_changed()
        
        # 关闭模板窗口
        for widget in self.window.winfo_children():
            if isinstance(widget, tk.Toplevel) and widget.title() == "快速模板":
                widget.destroy()
                break
        
        # 自动生成图表
        self.generate_chart()

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
