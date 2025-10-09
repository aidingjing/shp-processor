"""
几何数据修复工具对话框
提供几何数据质量检测和修复功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon
from shapely.validation import make_valid
from shapely.ops import unary_union, linemerge, polygonize_full
import json
from typing import List, Dict, Tuple, Optional
import tempfile
import os


class GeometryRepairDialog:
    """几何数据修复工具对话框"""

    def __init__(self, parent):
        """初始化几何数据修复工具对话框"""
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("几何数据修复工具")
        self.window.geometry("900x700")
        self.window.resizable(True, True)
        self.window.transient(parent)
        self.window.grab_set()

        # 数据存储
        self.original_gdf: Optional[gpd.GeoDataFrame] = None
        self.repaired_gdf: Optional[gpd.GeoDataFrame] = None
        self.repair_log: List[Dict] = []
        self.current_file_path: Optional[str] = None

        # 修复选项
        self.repair_options = {
            'invalid_geometries': tk.BooleanVar(value=True),
            'duplicate_points': tk.BooleanVar(value=True),
            'self_intersections': tk.BooleanVar(value=True),
            'zero_area_polygons': tk.BooleanVar(value=True),
            'zero_length_lines': tk.BooleanVar(value=True),
            'simplify_geometries': tk.BooleanVar(value=False),
            'tolerance': tk.DoubleVar(value=0.0001)
        }

        self.create_widgets()
        self.center_window()

    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建标题
        title_label = tk.Label(main_frame, text="几何数据修复工具", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))

        # 创建工具栏
        self.create_toolbar(main_frame)

        # 创建主要内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 左侧：修复选项
        self.create_options_panel(content_frame)

        # 右侧：结果显示
        self.create_results_panel(content_frame)

        # 创建按钮区域
        self.create_button_panel(main_frame)

        # 创建状态栏
        self.create_status_bar(main_frame)

    def create_toolbar(self, parent):
        """创建工具栏"""
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))

        # 打开文件按钮
        open_btn = ttk.Button(toolbar_frame, text="打开SHP文件", command=self.load_shapefile)
        open_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 当前文件标签
        self.file_label = tk.Label(toolbar_frame, text="未选择文件", fg="gray")
        self.file_label.pack(side=tk.LEFT, padx=(0, 20))

        # 分隔符
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # 导出按钮
        self.export_btn = ttk.Button(toolbar_frame, text="导出修复结果", command=self.export_results, state=tk.DISABLED)
        self.export_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 清空按钮
        clear_btn = ttk.Button(toolbar_frame, text="清空", command=self.clear_all)
        clear_btn.pack(side=tk.LEFT)

    def create_options_panel(self, parent):
        """创建修复选项面板"""
        options_frame = ttk.LabelFrame(parent, text="修复选项", padding="10")
        options_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # 修复选项
        ttk.Checkbutton(options_frame, text="修复无效几何体", 
                       variable=self.repair_options['invalid_geometries']).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="移除重复点", 
                       variable=self.repair_options['duplicate_points']).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="修复自相交", 
                       variable=self.repair_options['self_intersections']).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="移除零面积多边形", 
                       variable=self.repair_options['zero_area_polygons']).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="移除零长度线", 
                       variable=self.repair_options['zero_length_lines']).pack(anchor=tk.W, pady=2)

        # 分隔符
        ttk.Separator(options_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # 简化选项
        ttk.Checkbutton(options_frame, text="简化几何体", 
                       variable=self.repair_options['simplify_geometries']).pack(anchor=tk.W, pady=2)

        # 容差设置
        tolerance_frame = ttk.Frame(options_frame)
        tolerance_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(tolerance_frame, text="容差:").pack(side=tk.LEFT)
        tolerance_entry = ttk.Entry(tolerance_frame, textvariable=self.repair_options['tolerance'], width=10)
        tolerance_entry.pack(side=tk.LEFT, padx=(5, 0))

        # 分析按钮
        analyze_btn = ttk.Button(options_frame, text="分析数据", command=self.analyze_data)
        analyze_btn.pack(fill=tk.X, pady=(20, 10))

        # 修复按钮
        self.repair_btn = ttk.Button(options_frame, text="开始修复", command=self.start_repair, state=tk.DISABLED)
        self.repair_btn.pack(fill=tk.X)

    def create_results_panel(self, parent):
        """创建结果显示面板"""
        results_frame = ttk.LabelFrame(parent, text="修复结果", padding="10")
        results_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 创建Notebook用于多个结果页
        self.results_notebook = ttk.Notebook(results_frame)
        self.results_notebook.pack(fill=tk.BOTH, expand=True)

        # 问题汇总页
        self.create_summary_tab()
        
        # 详细日志页
        self.create_log_tab()
        
        # 统计信息页
        self.create_stats_tab()

    def create_summary_tab(self):
        """创建问题汇总页"""
        summary_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(summary_frame, text="问题汇总")

        # 创建树形视图
        columns = ('类型', '数量', '描述')
        self.summary_tree = ttk.Treeview(summary_frame, columns=columns, show='tree headings', height=15)
        
        # 设置列标题
        self.summary_tree.heading('#0', text='问题类别')
        self.summary_tree.heading('类型', text='类型')
        self.summary_tree.heading('数量', text='数量')
        self.summary_tree.heading('描述', text='描述')

        # 设置列宽
        self.summary_tree.column('#0', width=150)
        self.summary_tree.column('类型', width=100)
        self.summary_tree.column('数量', width=80)
        self.summary_tree.column('描述', width=300)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(summary_frame, orient=tk.VERTICAL, command=self.summary_tree.yview)
        self.summary_tree.configure(yscrollcommand=scrollbar.set)

        self.summary_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_log_tab(self):
        """创建详细日志页"""
        log_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(log_frame, text="详细日志")

        # 创建文本框
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, state=tk.DISABLED)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_stats_tab(self):
        """创建统计信息页"""
        stats_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(stats_frame, text="统计信息")

        # 创建统计信息显示
        self.stats_text = tk.Text(stats_frame, wrap=tk.WORD, state=tk.DISABLED, font=("Courier", 10))
        stats_scrollbar = ttk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=stats_scrollbar.set)

        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_button_panel(self, parent):
        """创建按钮面板"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X)

        # 刷新按钮
        refresh_btn = ttk.Button(button_frame, text="刷新分析", command=self.analyze_data)
        refresh_btn.pack(side=tk.LEFT)

        # 导出报告按钮
        report_btn = ttk.Button(button_frame, text="导出报告", command=self.export_report)
        report_btn.pack(side=tk.LEFT, padx=(10, 0))

    def create_status_bar(self, parent):
        """创建状态栏"""
        self.status_label = tk.Label(parent, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, pady=(10, 0))

    def load_shapefile(self):
        """加载SHP文件"""
        filename = filedialog.askopenfilename(
            title="选择SHP文件",
            filetypes=[("SHP文件", "*.shp"), ("所有文件", "*.*")]
        )

        if filename:
            try:
                self.status_label.config(text="正在加载文件...")
                self.window.update()

                # 加载GeoDataFrame
                self.original_gdf = gpd.read_file(filename)
                self.current_file_path = filename

                # 更新文件标签
                self.file_label.config(text=f"已加载: {os.path.basename(filename)}")
                
                # 启用按钮
                self.repair_btn.config(state=tk.NORMAL)
                
                # 自动分析数据
                self.analyze_data()

                self.status_label.config(text=f"文件加载成功，共 {len(self.original_gdf)} 条记录")

            except Exception as e:
                messagebox.showerror("加载错误", f"加载SHP文件失败：\n{e}")
                self.status_label.config(text="加载失败")

    def analyze_data(self):
        """分析几何数据问题"""
        if self.original_gdf is None:
            messagebox.showwarning("提示", "请先加载SHP文件")
            return

        self.status_label.config(text="正在分析数据...")
        self.window.update()

        # 清空之前的结果
        self.repair_log = []
        self.clear_results()

        # 分析各种问题
        issues = {}
        total_issues = 0

        for idx, row in self.original_gdf.iterrows():
            geom = row.geometry
            row_issues = []

            # 检查无效几何体
            if not geom.is_valid:
                row_issues.append({
                    'type': 'invalid_geometry',
                    'description': f'无效几何体: {geom.is_valid_reason}',
                    'severity': 'high'
                })
                issues['invalid_geometry'] = issues.get('invalid_geometry', 0) + 1

            # 检查空几何体
            if geom.is_empty:
                row_issues.append({
                    'type': 'empty_geometry',
                    'description': '空几何体',
                    'severity': 'medium'
                })
                issues['empty_geometry'] = issues.get('empty_geometry', 0) + 1

            # 检查重复点（仅对点和多点）
            if geom.geom_type in ['Point', 'MultiPoint']:
                if self.has_duplicate_points(geom):
                    row_issues.append({
                        'type': 'duplicate_points',
                        'description': '包含重复点',
                        'severity': 'low'
                    })
                    issues['duplicate_points'] = issues.get('duplicate_points', 0) + 1

            # 检查自相交
            if hasattr(geom, 'is_simple') and not geom.is_simple:
                row_issues.append({
                    'type': 'self_intersection',
                    'description': '几何体自相交',
                    'severity': 'medium'
                })
                issues['self_intersection'] = issues.get('self_intersection', 0) + 1

            # 检查零面积多边形
            if geom.geom_type in ['Polygon', 'MultiPolygon'] and geom.area < 1e-10:
                row_issues.append({
                    'type': 'zero_area',
                    'description': f'零面积多边形 (面积: {geom.area})',
                    'severity': 'low'
                })
                issues['zero_area'] = issues.get('zero_area', 0) + 1

            # 检查零长度线
            if geom.geom_type in ['LineString', 'MultiLineString'] and geom.length < 1e-10:
                row_issues.append({
                    'type': 'zero_length',
                    'description': f'零长度线 (长度: {geom.length})',
                    'severity': 'low'
                })
                issues['zero_length'] = issues.get('zero_length', 0) + 1

            # 记录问题
            if row_issues:
                self.repair_log.append({
                    'index': idx,
                    'geometry': geom,
                    'issues': row_issues
                })
                total_issues += len(row_issues)

        # 显示分析结果
        self.display_analysis_results(issues, total_issues)
        self.display_statistics()

        if total_issues > 0:
            self.status_label.config(text=f"分析完成，发现 {total_issues} 个问题")
        else:
            self.status_label.config(text="分析完成，未发现问题")

    def has_duplicate_points(self, geom) -> bool:
        """检查是否包含重复点"""
        if geom.geom_type == 'Point':
            return False
        elif geom.geom_type == 'MultiPoint':
            coords = list(geom.geoms)
            return len(coords) != len(set(coords))
        return False

    def display_analysis_results(self, issues: Dict, total_issues: int):
        """显示分析结果"""
        # 清空树形视图
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)

        # 问题类型映射
        issue_types = {
            'invalid_geometry': ('几何体', '无效几何体', 'red'),
            'empty_geometry': ('几何体', '空几何体', 'orange'),
            'duplicate_points': ('点数据', '重复点', 'blue'),
            'self_intersection': ('拓扑', '自相交', 'orange'),
            'zero_area': ('多边形', '零面积', 'gray'),
            'zero_length': ('线数据', '零长度', 'gray')
        }

        # 添加问题到树形视图
        for issue_type, count in issues.items():
            if issue_type in issue_types:
                category, desc, color = issue_types[issue_type]
                self.summary_tree.insert('', 'end', text=desc, values=(category, count, f'发现{count}个{desc}'))

        # 添加日志
        self.add_log(f"数据分析完成，共发现 {total_issues} 个问题")
        for issue_type, count in issues.items():
            if issue_type in issue_types:
                _, desc, _ = issue_types[issue_type]
                self.add_log(f"  - {desc}: {count} 个")

    def display_statistics(self):
        """显示统计信息"""
        if self.original_gdf is None:
            return

        stats = []
        stats.append("=" * 50)
        stats.append("数据统计信息")
        stats.append("=" * 50)
        stats.append(f"总记录数: {len(self.original_gdf)}")
        stats.append(f"几何类型: {self.original_gdf.geom_type.value_counts().to_dict()}")
        stats.append(f"坐标系统: {self.original_gdf.crs}")
        stats.append(f"总边界: {self.original_gdf.total_bounds}")
        stats.append("")

        # 问题统计
        if self.repair_log:
            stats.append("问题统计:")
            issue_counts = {}
            for log_entry in self.repair_log:
                for issue in log_entry['issues']:
                    issue_type = issue['type']
                    issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1

            for issue_type, count in issue_counts.items():
                stats.append(f"  {issue_type}: {count}")

        # 显示统计信息
        stats_text = "\n".join(str(stat) for stat in stats)
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete("1.0", tk.END)
        self.stats_text.insert("1.0", stats_text)
        self.stats_text.config(state=tk.DISABLED)

    def start_repair(self):
        """开始修复几何数据"""
        if self.original_gdf is None:
            messagebox.showwarning("提示", "请先加载SHP文件")
            return

        self.status_label.config(text="正在修复数据...")
        self.window.update()

        try:
            # 复制原始数据
            self.repaired_gdf = self.original_gdf.copy()
            repair_count = 0

            # 逐条修复
            for idx, row in self.repaired_gdf.iterrows():
                original_geom = row.geometry
                repaired_geom = original_geom

                # 修复无效几何体
                if self.repair_options['invalid_geometries'].get() and not original_geom.is_valid:
                    repaired_geom = make_valid(original_geom)
                    if repaired_geom.is_valid and repaired_geom != original_geom:
                        self.add_log(f"修复无效几何体 (索引 {idx}): {original_geom.is_valid_reason}")
                        repair_count += 1

                # 修复自相交
                if self.repair_options['self_intersections'].get() and hasattr(repaired_geom, 'is_simple'):
                    if not repaired_geom.is_simple:
                        if repaired_geom.geom_type in ['LineString', 'MultiLineString']:
                            # 对线进行合并处理
                            if repaired_geom.geom_type == 'MultiLineString':
                                merged = linemerge(repaired_geom)
                                if merged.is_valid:
                                    repaired_geom = merged
                                    self.add_log(f"修复自相交线 (索引 {idx})")
                                    repair_count += 1

                # 移除零面积多边形
                if (self.repair_options['zero_area_polygons'].get() and 
                    repaired_geom.geom_type in ['Polygon', 'MultiPolygon'] and 
                    repaired_geom.area < 1e-10):
                    repaired_geom = None
                    self.add_log(f"移除零面积多边形 (索引 {idx})")
                    repair_count += 1

                # 移除零长度线
                if (self.repair_options['zero_length_lines'].get() and 
                    repaired_geom.geom_type in ['LineString', 'MultiLineString'] and 
                    repaired_geom.length < 1e-10):
                    repaired_geom = None
                    self.add_log(f"移除零长度线 (索引 {idx})")
                    repair_count += 1

                # 简化几何体
                if (self.repair_options['simplify_geometries'].get() and 
                    repaired_geom is not None):
                    tolerance = self.repair_options['tolerance'].get()
                    simplified = repaired_geom.simplify(tolerance, preserve_topology=True)
                    if simplified != repaired_geom:
                        repaired_geom = simplified
                        self.add_log(f"简化几何体 (索引 {idx})")
                        repair_count += 1

                # 更新几何体
                self.repaired_gdf.at[idx, 'geometry'] = repaired_geom

            # 移除空几何体记录
            self.repaired_gdf = self.repaired_gdf[~self.repaired_gdf.geometry.is_empty]

            # 启用导出按钮
            self.export_btn.config(state=tk.NORMAL)

            self.status_label.config(text=f"修复完成，共修复 {repair_count} 个问题")
            messagebox.showinfo("修复完成", f"几何数据修复完成！\n共修复 {repair_count} 个问题\n\n修复后记录数: {len(self.repaired_gdf)}")

        except Exception as e:
            messagebox.showerror("修复错误", f"修复过程中发生错误：\n{e}")
            self.status_label.config(text="修复失败")

    def export_results(self):
        """导出修复结果"""
        if self.repaired_gdf is None:
            messagebox.showwarning("提示", "没有可导出的修复结果")
            return

        filename = filedialog.asksaveasfilename(
            title="保存修复结果",
            defaultextension=".shp",
            filetypes=[("SHP文件", "*.shp"), ("所有文件", "*.*")]
        )

        if filename:
            try:
                self.repaired_gdf.to_file(filename)
                self.status_label.config(text=f"修复结果已导出到: {filename}")
                messagebox.showinfo("导出成功", f"修复结果已成功导出到:\n{filename}")
            except Exception as e:
                messagebox.showerror("导出错误", f"导出文件失败：\n{e}")

    def export_report(self):
        """导出修复报告"""
        if not self.repair_log:
            messagebox.showwarning("提示", "没有可导出的报告数据")
            return

        filename = filedialog.asksaveasfilename(
            title="保存修复报告",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("几何数据修复报告\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"文件: {self.current_file_path}\n")
                    f.write(f"分析时间: {pd.Timestamp.now()}\n")
                    f.write(f"总记录数: {len(self.original_gdf) if self.original_gdf is not None else 0}\n")
                    f.write(f"发现问题数: {len(self.repair_log)}\n\n")

                    f.write("详细问题列表:\n")
                    f.write("-" * 50 + "\n")

                    for log_entry in self.repair_log:
                        idx = log_entry['index']
                        f.write(f"\n记录索引: {idx}\n")
                        for issue in log_entry['issues']:
                            f.write(f"  - {issue['description']}\n")

                messagebox.showinfo("导出成功", f"修复报告已成功导出到:\n{filename}")
            except Exception as e:
                messagebox.showerror("导出错误", f"导出报告失败：\n{e}")

    def add_log(self, message: str):
        """添加日志信息"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def clear_results(self):
        """清空结果显示"""
        # 清空树形视图
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)

        # 清空日志
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)

        # 清空统计信息
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete("1.0", tk.END)
        self.stats_text.config(state=tk.DISABLED)

    def clear_all(self):
        """清空所有数据"""
        self.original_gdf = None
        self.repaired_gdf = None
        self.repair_log = []
        self.current_file_path = None

        self.file_label.config(text="未选择文件")
        self.repair_btn.config(state=tk.DISABLED)
        self.export_btn.config(state=tk.DISABLED)

        self.clear_results()
        self.status_label.config(text="已清空所有数据")

    def center_window(self):
        """居中显示窗口"""
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
