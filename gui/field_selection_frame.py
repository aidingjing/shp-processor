"""
字段选择GUI面板
提供空间坐标字段选择和预览的图形界面
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from typing import Optional, List, Dict, Any, Callable

from core.coordinate_parser import CoordinateParser


class FieldSelectionFrame(tk.Frame):
    """字段选择面板"""

    def __init__(self, parent, on_field_selected: Optional[Callable] = None):
        """
        初始化字段选择面板

        Args:
            parent: 父窗口
            on_field_selected: 字段选择完成回调函数
        """
        super().__init__(parent)

        self.on_field_selected = on_field_selected
        self.coordinate_parser = CoordinateParser()
        self.current_dataframe: Optional[pd.DataFrame] = None
        self.selected_field: Optional[str] = None
        self.field_analysis: Dict[str, Any] = {}

        self.create_widgets()

    def create_widgets(self):
        """创建界面组件"""
        # 标题
        title_label = tk.Label(self, text="空间坐标字段选择", font=("Arial", 12, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(8, 12))

        # 字段选择区域
        field_frame = tk.LabelFrame(self, text="选择坐标字段", padx=8, pady=8)
        field_frame.grid(row=1, column=0, columnspan=3, padx=8, pady=4, sticky="ew")

        # 坐标类型选择
        tk.Label(field_frame, text="坐标类型:", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.coord_type_var = tk.StringVar(value="single")
        coord_types = [
            ("单一坐标字段", "single"),
            ("分离经纬度字段", "separate")
        ]

        for i, (text, value) in enumerate(coord_types):
            tk.Radiobutton(
                field_frame,
                text=text,
                variable=self.coord_type_var,
                value=value,
                command=self.on_coord_type_changed,
                font=("Arial", 9)
            ).grid(row=0, column=i+1, sticky="w", padx=4)

        # 单一字段选择区域
        self.single_frame = tk.Frame(field_frame)
        self.single_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(8, 0))

        tk.Label(self.single_frame, text="坐标字段:").grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.field_combobox = ttk.Combobox(self.single_frame, width=35, state="readonly")
        self.field_combobox.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        self.field_combobox.bind("<<ComboboxSelected>>", self.on_field_selection_changed)

        # 分析按钮
        analyze_button = tk.Button(self.single_frame, text="分析字段", command=self.analyze_selected_field,
                                 bg="#2196F3", fg="white", padx=12, font=("Arial", 9))
        analyze_button.grid(row=0, column=2)

        # 分离字段选择区域
        self.separate_frame = tk.Frame(field_frame)

        # 经度字段选择
        tk.Label(self.separate_frame, text="经度字段:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.lng_combobox = ttk.Combobox(self.separate_frame, width=25, state="readonly")
        self.lng_combobox.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        self.lng_combobox.bind("<<ComboboxSelected>>", self.on_separate_field_changed)

        # 纬度字段选择
        tk.Label(self.separate_frame, text="纬度字段:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(4, 0))
        self.lat_combobox = ttk.Combobox(self.separate_frame, width=25, state="readonly")
        self.lat_combobox.grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=(4, 0))
        self.lat_combobox.bind("<<ComboboxSelected>>", self.on_separate_field_changed)

        # 自动检测按钮
        auto_detect_button = tk.Button(self.separate_frame, text="自动检测", command=self.auto_detect_coordinate_fields,
                                      bg="#4CAF50", fg="white", padx=10, font=("Arial", 9))
        auto_detect_button.grid(row=0, column=2, rowspan=2, padx=(8, 0))

        # 分析分离字段按钮
        analyze_separate_button = tk.Button(self.separate_frame, text="分析字段", command=self.analyze_separate_fields,
                                          bg="#2196F3", fg="white", padx=10, font=("Arial", 9))
        analyze_separate_button.grid(row=0, column=3, rowspan=2, padx=(4, 0))

        self.separate_frame.columnconfigure(1, weight=1)

        # 预览区域
        preview_frame = tk.LabelFrame(self, text="字段预览", padx=8, pady=8)
        preview_frame.grid(row=2, column=0, columnspan=3, padx=8, pady=4, sticky="nsew")

        # 字段值预览
        tk.Label(preview_frame, text="字段值示例:", font=("Arial", 9)).grid(row=0, column=0, sticky="w", pady=(0, 4))

        self.preview_text = tk.Text(preview_frame, width=70, height=6, wrap=tk.WORD, font=("Arial", 9))
        self.preview_text.grid(row=1, column=0, sticky="ew")

        preview_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_text.yview)
        preview_scrollbar.grid(row=1, column=1, sticky="ns")
        self.preview_text.configure(yscrollcommand=preview_scrollbar.set)

        # 分析结果区域
        analysis_frame = tk.LabelFrame(self, text="字段分析结果", padx=8, pady=8)
        analysis_frame.grid(row=3, column=0, columnspan=3, padx=8, pady=4, sticky="ew")

        # 创建分析结果显示的标签
        self.analysis_labels = {}

        analysis_items = [
            ("总记录数:", "total_records"),
            ("有效记录数:", "valid_records"),
            ("无效记录数:", "invalid_records"),
            ("成功率:", "success_rate"),
            ("主要几何类型:", "main_geometry_type"),
            ("几何类型分布:", "geometry_types"),
            ("平均坐标点数:", "avg_coordinates")
        ]

        for i, (label_text, key) in enumerate(analysis_items):
            row = i // 2
            col = (i % 2) * 2

            tk.Label(analysis_frame, text=label_text, font=("Arial", 9, "bold")).grid(
                row=row, column=col, sticky="w", padx=(0, 5), pady=2
            )
            self.analysis_labels[key] = tk.Label(analysis_frame, text="--", fg="blue", font=("Arial", 9))
            self.analysis_labels[key].grid(row=row, column=col + 1, sticky="w", padx=(0, 15), pady=2)

        # 几何类型选择区域
        geometry_frame = tk.LabelFrame(self, text="几何类型设置", padx=8, pady=8)
        geometry_frame.grid(row=4, column=0, columnspan=3, padx=8, pady=4, sticky="ew")

        tk.Label(geometry_frame, text="指定几何类型:", font=("Arial", 9)).grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.geometry_var = tk.StringVar(value="auto")
        geometry_types = ["自动检测", "Point (点)", "LineString (线)", "Polygon (面)"]
        geometry_values = ["auto", "Point", "LineString", "Polygon"]

        for i, (text, value) in enumerate(zip(geometry_types, geometry_values)):
            tk.Radiobutton(
                geometry_frame,
                text=text,
                variable=self.geometry_var,
                value=value,
                command=self.on_geometry_type_changed,
                font=("Arial", 9)
            ).grid(row=0, column=i + 1, sticky="w", padx=4)

        # 按钮区域
        button_frame = tk.Frame(self)
        button_frame.grid(row=5, column=0, columnspan=3, pady=15)

        # 确认选择按钮
        self.confirm_button = tk.Button(
            button_frame,
            text="确认选择",
            command=self.confirm_selection,
            bg="#4CAF50",
            fg="white",
            padx=15,
            font=("Arial", 10, "bold"),
            state=tk.DISABLED
        )
        self.confirm_button.grid(row=0, column=0, padx=8)

        # 重新分析按钮
        reanalyze_button = tk.Button(
            button_frame,
            text="重新分析",
            command=self.reanalyze_field,
            bg="#FF9800",
            fg="white",
            padx=12,
            font=("Arial", 9)
        )
        reanalyze_button.grid(row=0, column=1, padx=8)

        # 状态栏
        self.status_label = tk.Label(self, text="请先执行SQL查询获取数据", fg="gray", anchor="w", font=("Arial", 9))
        self.status_label.grid(row=6, column=0, columnspan=3, sticky="ew", padx=8, pady=4)

        # 配置权重
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        field_frame.columnconfigure(1, weight=1)
        field_frame.columnconfigure(2, weight=1)
        field_frame.columnconfigure(3, weight=1)
        preview_frame.columnconfigure(0, weight=1)
        self.single_frame.columnconfigure(1, weight=1)

    def set_dataframe(self, df: pd.DataFrame):
        """
        设置要分析的DataFrame

        Args:
            df: 查询结果DataFrame
        """
        self.current_dataframe = df

        if df is not None and not df.empty:
            # 获取所有字段名
            columns = list(df.columns)
            self.field_combobox['values'] = columns
            self.lng_combobox['values'] = columns
            self.lat_combobox['values'] = columns

            if columns:
                self.field_combobox.current(0)
                self.lng_combobox.current(0)
                self.lat_combobox.current(0 if len(columns) > 1 else 0)
                self.status_label.config(text=f"已加载 {len(columns)} 个字段，请选择坐标字段", fg="blue")

                # 根据当前坐标类型进行分析
                if self.coord_type_var.get() == "single":
                    self.analyze_selected_field()
                else:
                    self.auto_detect_coordinate_fields()
            else:
                self.status_label.config(text="数据中没有字段", fg="red")
        else:
            self.clear_fields()
            self.status_label.config(text="没有可用的数据", fg="red")

    def clear_fields(self):
        """清空字段选择"""
        self.field_combobox['values'] = []
        self.field_combobox.set("")
        self.lng_combobox['values'] = []
        self.lng_combobox.set("")
        self.lat_combobox['values'] = []
        self.lat_combobox.set("")
        self.clear_preview()
        self.clear_analysis()
        self.selected_field = None
        self.selected_lng_field = None
        self.selected_lat_field = None
        self.field_analysis = {}
        self.separate_analysis = {}
        self.confirm_button.config(state=tk.DISABLED)

    def on_field_selection_changed(self, event=None):
        """字段选择变更事件"""
        selected = self.field_combobox.get()
        if selected:
            self.status_label.config(text=f"已选择字段: {selected}，点击'分析字段'查看详细信息", fg="blue")
        else:
            self.status_label.config(text="请选择一个坐标字段", fg="orange")

    def analyze_selected_field(self):
        """分析选中的字段"""
        if self.current_dataframe is None or self.current_dataframe.empty:
            messagebox.showwarning("数据为空", "请先执行SQL查询获取数据")
            return

        selected_field = self.field_combobox.get()
        if not selected_field:
            messagebox.showwarning("未选择字段", "请先选择要分析的坐标字段")
            return

        try:
            self.status_label.config(text="正在分析字段...", fg="orange")
            self.update()

            # 显示字段值预览
            self.show_field_preview(selected_field)

            # 分析字段模式
            analysis = self.coordinate_parser.analyze_column_patterns(
                self.current_dataframe, selected_field, sample_size=100
            )

            self.field_analysis = analysis
            self.display_analysis_results(analysis)

            # 更新几何类型选择
            detected_type = analysis.get('main_geometry_type', 'Unknown')
            self.update_geometry_type_selection(detected_type)

            self.selected_field = selected_field
            self.confirm_button.config(state=tk.NORMAL)

            if analysis.get('success_rate', 0) > 0.8:
                self.status_label.config(text=f"字段分析完成: {selected_field} (成功率: {analysis.get('success_rate', 0):.1%})", fg="green")
            else:
                self.status_label.config(text=f"字段分析完成，但成功率较低: {selected_field} (成功率: {analysis.get('success_rate', 0):.1%})", fg="orange")

        except Exception as e:
            self.status_label.config(text=f"字段分析失败: {str(e)}", fg="red")
            messagebox.showerror("分析错误", f"分析字段时发生错误：\n\n{e}")

    def show_field_preview(self, field_name: str):
        """显示字段值预览"""
        if self.current_dataframe is None:
            return

        self.preview_text.delete("1.0", tk.END)

        # 获取字段的前10个非空值
        non_null_values = self.current_dataframe[field_name].dropna().head(10)

        preview_text = f"字段 '{field_name}' 的前10个值:\n\n"
        preview_text += "=" * 50 + "\n"

        for i, value in enumerate(non_null_values, 1):
            value_str = str(value)
            if len(value_str) > 100:
                value_str = value_str[:100] + "..."
            preview_text += f"{i}. {value_str}\n"

        preview_text += "=" * 50 + "\n"
        preview_text += f"数据类型: {self.current_dataframe[field_name].dtype}\n"
        preview_text += f"非空记录数: {len(non_null_values)}/{len(self.current_dataframe)}"

        self.preview_text.insert("1.0", preview_text)

    def display_analysis_results(self, analysis: Dict[str, Any]):
        """显示分析结果"""
        # 基本统计信息
        total_samples = analysis.get('total_samples', 0)
        error_count = analysis.get('error_count', 0)
        valid_records = total_samples - error_count

        self.analysis_labels['total_records'].config(text=str(total_samples))
        self.analysis_labels['valid_records'].config(text=str(valid_records))
        self.analysis_labels['invalid_records'].config(text=str(error_count))

        # 成功率
        success_rate = analysis.get('success_rate', 0)
        self.analysis_labels['success_rate'].config(text=f"{success_rate:.1%}")

        # 主要几何类型
        main_type = analysis.get('main_geometry_type', 'Unknown')
        self.analysis_labels['main_geometry_type'].config(text=main_type)

        # 几何类型分布
        geometry_types = analysis.get('geometry_types', {})
        if geometry_types:
            type_str = ", ".join([f"{k}: {v}" for k, v in geometry_types.items() if v > 0])
            self.analysis_labels['geometry_types'].config(text=type_str if type_str else "无")
        else:
            self.analysis_labels['geometry_types'].config(text="无")

        # 平均坐标点数
        coord_stats = analysis.get('coordinate_stats', {})
        avg_coords = coord_stats.get('average', 0)
        self.analysis_labels['avg_coordinates'].config(text=f"{avg_coords:.1f}")

    def update_geometry_type_selection(self, detected_type: str):
        """根据检测到的几何类型更新选择"""
        if detected_type == "Unknown":
            self.geometry_var.set("auto")
        elif detected_type in ["Point", "LineString", "Polygon"]:
            self.geometry_var.set(detected_type)
        else:
            self.geometry_var.set("auto")

    def on_geometry_type_changed(self):
        """几何类型变更事件"""
        if self.selected_field:
            self.status_label.config(
                text=f"字段: {self.selected_field}, 几何类型: {self.geometry_var.get()}",
                fg="blue"
            )

    def reanalyze_field(self):
        """重新分析当前字段"""
        if self.field_combobox.get():
            self.analyze_selected_field()
        else:
            messagebox.showwarning("未选择字段", "请先选择要分析的坐标字段")

    def confirm_selection(self):
        """确认字段选择"""
        if not self.selected_field:
            messagebox.showwarning("未选择字段", "请先选择并分析坐标字段")
            return

        geometry_type = self.geometry_var.get()

        # 检查成功率
        success_rate = self.field_analysis.get('success_rate', 0)
        if success_rate < 0.5:
            if not messagebox.askyesno(
                "确认选择",
                f"字段 '{self.selected_field}' 的解析成功率较低 ({success_rate:.1%})，\n确定要继续使用此字段吗？"
            ):
                return

        # 调用回调函数
        if self.on_field_selected:
            self.on_field_selected(
                field_name=self.selected_field,
                geometry_type=geometry_type,
                analysis=self.field_analysis
            )

        self.status_label.config(
            text=f"已确认选择字段: {self.selected_field}, 几何类型: {geometry_type}",
            fg="green"
        )

    def clear_preview(self):
        """清空预览区域"""
        self.preview_text.delete("1.0", tk.END)

    def clear_analysis(self):
        """清空分析结果"""
        for label in self.analysis_labels.values():
            label.config(text="--")

    def on_coord_type_changed(self):
        """坐标类型变更事件"""
        coord_type = self.coord_type_var.get()

        if coord_type == "single":
            self.single_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(8, 0))
            self.separate_frame.grid_remove()
            if self.field_combobox.get():
                self.analyze_selected_field()
        else:
            self.single_frame.grid_remove()
            self.separate_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(8, 0))
            self.auto_detect_coordinate_fields()

        self.clear_preview()
        self.clear_analysis()
        self.confirm_button.config(state=tk.DISABLED)

    def on_separate_field_changed(self, event=None):
        """分离字段选择变更事件"""
        lng_field = self.lng_combobox.get()
        lat_field = self.lat_combobox.get()

        if lng_field and lat_field:
            self.status_label.config(
                text=f"已选择经度字段: {lng_field}, 纬度字段: {lat_field}，点击'分析字段'查看详细信息",
                fg="blue"
            )
        else:
            self.status_label.config(text="请选择经度和纬度字段", fg="orange")

    def auto_detect_coordinate_fields(self):
        """自动检测经纬度字段"""
        if self.current_dataframe is None or self.current_dataframe.empty:
            messagebox.showwarning("数据为空", "请先执行SQL查询获取数据")
            return

        try:
            self.status_label.config(text="正在检测经纬度字段...", fg="orange")
            self.update()

            # 使用坐标解析器检测字段
            detection_result = self.coordinate_parser.detect_coordinate_columns(
                self.current_dataframe, debug=False
            )

            # 获取最佳配对建议
            if detection_result['pair_suggestions']:
                best_pair = max(detection_result['pair_suggestions'], key=lambda x: x['confidence'])
                lng_field = best_pair['lng_column']
                lat_field = best_pair['lat_column']

                # 设置选择框
                if lng_field in self.lng_combobox['values']:
                    self.lng_combobox.set(lng_field)
                if lat_field in self.lat_combobox['values']:
                    self.lat_combobox.set(lat_field)

                self.status_label.config(
                    text=f"自动检测到经度字段: {lng_field}, 纬度字段: {lat_field} (置信度: {best_pair['confidence']:.1%})",
                    fg="green"
                )

                # 自动分析检测到的字段
                self.analyze_separate_fields()
            else:
                self.status_label.config(text="未检测到合适的经纬度字段，请手动选择", fg="orange")

        except Exception as e:
            self.status_label.config(text=f"字段检测失败: {str(e)}", fg="red")
            messagebox.showerror("检测错误", f"检测经纬度字段时发生错误：\n\n{e}")

    def analyze_separate_fields(self):
        """分析分离的经纬度字段"""
        if self.current_dataframe is None or self.current_dataframe.empty:
            messagebox.showwarning("数据为空", "请先执行SQL查询获取数据")
            return

        lng_field = self.lng_combobox.get()
        lat_field = self.lat_combobox.get()

        if not lng_field or not lat_field:
            messagebox.showwarning("未选择字段", "请先选择经度和纬度字段")
            return

        if lng_field == lat_field:
            messagebox.showwarning("字段重复", "经度字段和纬度字段不能相同")
            return

        try:
            self.status_label.config(text="正在分析分离字段...", fg="orange")
            self.update()

            # 显示字段值预览
            self.show_separate_field_preview(lng_field, lat_field)

            # 分析分离字段数据质量
            analysis = self.coordinate_parser.analyze_separate_coordinates(
                self.current_dataframe, lng_field, lat_field, sample_size=100
            )

            self.separate_analysis = analysis
            self.display_separate_analysis_results(analysis)

            self.selected_lng_field = lng_field
            self.selected_lat_field = lat_field
            self.confirm_button.config(state=tk.NORMAL)

            confidence = analysis.get('confidence', 0)
            if confidence > 0.8:
                self.status_label.config(
                    text=f"分离字段分析完成: {lng_field} + {lat_field} (置信度: {confidence:.1%})",
                    fg="green"
                )
            else:
                self.status_label.config(
                    text=f"分离字段分析完成，但置信度较低: {lng_field} + {lat_field} (置信度: {confidence:.1%})",
                    fg="orange"
                )

        except Exception as e:
            self.status_label.config(text=f"分离字段分析失败: {str(e)}", fg="red")
            messagebox.showerror("分析错误", f"分析分离字段时发生错误：\n\n{e}")

    def show_separate_field_preview(self, lng_field: str, lat_field: str):
        """显示分离字段值预览"""
        if self.current_dataframe is None:
            return

        self.preview_text.delete("1.0", tk.END)

        # 获取字段的前10个非空值
        lng_values = self.current_dataframe[lng_field].dropna().head(10)
        lat_values = self.current_dataframe[lat_field].dropna().head(10)

        preview_text = f"分离字段预览 (前10个值):\n\n"
        preview_text += "=" * 60 + "\n"
        preview_text += f"经度字段 '{lng_field}':\n"

        for i, value in enumerate(lng_values, 1):
            preview_text += f"  {i}. {value}\n"

        preview_text += f"\n纬度字段 '{lat_field}':\n"

        for i, value in enumerate(lat_values, 1):
            preview_text += f"  {i}. {value}\n"

        preview_text += "=" * 60 + "\n"
        preview_text += f"经度字段数据类型: {self.current_dataframe[lng_field].dtype}\n"
        preview_text += f"纬度字段数据类型: {self.current_dataframe[lat_field].dtype}\n"
        preview_text += f"有效经度记录数: {len(lng_values)}/{len(self.current_dataframe)}\n"
        preview_text += f"有效纬度记录数: {len(lat_values)}/{len(self.current_dataframe)}"

        self.preview_text.insert("1.0", preview_text)

    def display_separate_analysis_results(self, analysis: Dict[str, Any]):
        """显示分离字段分析结果"""
        # 基本统计信息
        total_records = analysis.get('total_records', 0)
        valid_coordinates = analysis.get('valid_coordinates', 0)
        completeness = analysis.get('completeness', 0)
        confidence = analysis.get('confidence', 0)

        self.analysis_labels['total_records'].config(text=str(total_records))
        self.analysis_labels['valid_records'].config(text=str(valid_coordinates))
        self.analysis_labels['invalid_records'].config(text=str(total_records - valid_coordinates))
        self.analysis_labels['success_rate'].config(text=f"{confidence:.1%}")

        # 主要几何类型 (分离字段通常是点)
        suggested_geometry = analysis.get('suggested_geometry', 'Point')
        self.analysis_labels['main_geometry_type'].config(text=suggested_geometry)

        # 几何类型分布 (对于分离字段，只有点)
        self.analysis_labels['geometry_types'].config(text="Point: 100%")

        # 平均坐标点数 (分离字段总是1)
        self.analysis_labels['avg_coordinates'].config(text="1.0")

        # 显示经纬度统计信息
        lng_stats = analysis.get('lng_stats', {})
        lat_stats = analysis.get('lat_stats', {})

        additional_info = f"\n经度范围: [{lng_stats.get('min', 0):.6f}, {lng_stats.get('max', 0):.6f}]\n"
        additional_info += f"纬度范围: [{lat_stats.get('min', 0):.6f}, {lat_stats.get('max', 0):.6f}]\n"
        additional_info += f"超出范围坐标: 经度{lng_stats.get('out_of_range_count', 0)}个, 纬度{lat_stats.get('out_of_range_count', 0)}个"

        # 在预览文本框末尾添加统计信息
        current_text = self.preview_text.get("1.0", tk.END)
        self.preview_text.insert(tk.END, f"\n\n=== 数据质量分析 ===\n{additional_info}")

    def get_selection(self) -> Dict[str, Any]:
        """获取当前选择结果"""
        coord_type = self.coord_type_var.get()

        if coord_type == "single":
            return {
                'coord_type': 'single',
                'field_name': self.selected_field,
                'geometry_type': self.geometry_var.get(),
                'analysis': self.field_analysis
            }
        else:
            return {
                'coord_type': 'separate',
                'lng_field': self.selected_lng_field,
                'lat_field': self.selected_lat_field,
                'geometry_type': self.geometry_var.get(),
                'analysis': self.separate_analysis
            }


if __name__ == "__main__":
    # 测试代码
    root = tk.Tk()
    root.title("字段选择测试")
    root.geometry("700x600")

    # 创建测试数据
    test_data = pd.DataFrame({
        'id': [1, 2, 3, 4, 5, 6, 7],
        'name': ['点1', '线1', '面1', '无效1', '点2', '地点3', '地点4'],
        'coordinates': [
            "[[116.404, 39.915]]",
            "[[116.404, 39.915], [116.405, 39.916]]",
            "[[116.404, 39.915], [116.405, 39.916], [116.406, 39.917], [116.404, 39.915]]",
            "invalid coordinate",
            "[[121.474, 31.230]]",
            None,
            None
        ],
        'longitude': [116.404, 116.405, 116.406, 116.407, 121.474, 121.475, 121.476],
        'latitude': [39.915, 39.916, 39.917, 39.918, 31.230, 31.231, 31.232],
        'lng': [116.408, 116.409, 116.410, None, 121.477, 121.478, 121.479],
        'lat': [39.919, 39.920, 39.921, 39.922, 31.233, 31.234, 31.235],
        'description': ['测试点1', '测试线1', '测试面1', '无效数据', '测试点2', '测试点3', '测试点4']
    })

    def on_field_selected(selection):
        coord_type = selection.get('coord_type', 'single')
        geometry_type = selection.get('geometry_type', 'auto')

        if coord_type == 'single':
            field_name = selection.get('field_name', '')
            analysis = selection.get('analysis', {})
            success_rate = analysis.get('success_rate', 0)
            message = f"坐标类型: 单一字段\n字段: {field_name}\n几何类型: {geometry_type}\n成功率: {success_rate:.1%}"
        else:
            lng_field = selection.get('lng_field', '')
            lat_field = selection.get('lat_field', '')
            analysis = selection.get('analysis', {})
            confidence = analysis.get('confidence', 0)
            message = f"坐标类型: 分离字段\n经度字段: {lng_field}\n纬度字段: {lat_field}\n几何类型: {geometry_type}\n置信度: {confidence:.1%}"

        messagebox.showinfo("字段选择完成", message)

    # 创建字段选择面板
    field_frame = FieldSelectionFrame(root, on_field_selected)
    field_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # 设置测试数据
    field_frame.set_dataframe(test_data)

    root.mainloop()
