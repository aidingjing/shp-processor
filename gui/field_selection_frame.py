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
        title_label = tk.Label(self, text="空间坐标字段选择", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(10, 20))

        # 字段选择区域
        field_frame = tk.LabelFrame(self, text="选择坐标字段", padx=10, pady=10)
        field_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

        tk.Label(field_frame, text="坐标字段:").grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.field_combobox = ttk.Combobox(field_frame, width=40, state="readonly")
        self.field_combobox.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        self.field_combobox.bind("<<ComboboxSelected>>", self.on_field_selection_changed)

        # 分析按钮
        analyze_button = tk.Button(field_frame, text="分析字段", command=self.analyze_selected_field,
                                 bg="#2196F3", fg="white", padx=15)
        analyze_button.grid(row=0, column=2)

        # 预览区域
        preview_frame = tk.LabelFrame(self, text="字段预览", padx=10, pady=10)
        preview_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="nsew")

        # 字段值预览
        tk.Label(preview_frame, text="字段值示例:").grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.preview_text = tk.Text(preview_frame, width=80, height=8, wrap=tk.WORD)
        self.preview_text.grid(row=1, column=0, sticky="ew")

        preview_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_text.yview)
        preview_scrollbar.grid(row=1, column=1, sticky="ns")
        self.preview_text.configure(yscrollcommand=preview_scrollbar.set)

        # 分析结果区域
        analysis_frame = tk.LabelFrame(self, text="字段分析结果", padx=10, pady=10)
        analysis_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

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

            tk.Label(analysis_frame, text=label_text, font=("Arial", 10, "bold")).grid(
                row=row, column=col, sticky="w", padx=(0, 5), pady=2
            )
            self.analysis_labels[key] = tk.Label(analysis_frame, text="--", fg="blue")
            self.analysis_labels[key].grid(row=row, column=col + 1, sticky="w", padx=(0, 20), pady=2)

        # 几何类型选择区域
        geometry_frame = tk.LabelFrame(self, text="几何类型设置", padx=10, pady=10)
        geometry_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

        tk.Label(geometry_frame, text="指定几何类型:").grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.geometry_var = tk.StringVar(value="auto")
        geometry_types = ["自动检测", "Point (点)", "LineString (线)", "Polygon (面)"]
        geometry_values = ["auto", "Point", "LineString", "Polygon"]

        for i, (text, value) in enumerate(zip(geometry_types, geometry_values)):
            tk.Radiobutton(
                geometry_frame,
                text=text,
                variable=self.geometry_var,
                value=value,
                command=self.on_geometry_type_changed
            ).grid(row=0, column=i + 1, sticky="w", padx=5)

        # 按钮区域
        button_frame = tk.Frame(self)
        button_frame.grid(row=5, column=0, columnspan=3, pady=20)

        # 确认选择按钮
        self.confirm_button = tk.Button(
            button_frame,
            text="确认选择",
            command=self.confirm_selection,
            bg="#4CAF50",
            fg="white",
            padx=20,
            font=("Arial", 11, "bold"),
            state=tk.DISABLED
        )
        self.confirm_button.grid(row=0, column=0, padx=10)

        # 重新分析按钮
        reanalyze_button = tk.Button(
            button_frame,
            text="重新分析",
            command=self.reanalyze_field,
            bg="#FF9800",
            fg="white",
            padx=15
        )
        reanalyze_button.grid(row=0, column=1, padx=10)

        # 状态栏
        self.status_label = tk.Label(self, text="请先执行SQL查询获取数据", fg="gray", anchor="w")
        self.status_label.grid(row=6, column=0, columnspan=3, sticky="ew", padx=10, pady=5)

        # 配置权重
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        field_frame.columnconfigure(1, weight=1)
        preview_frame.columnconfigure(0, weight=1)

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

            if columns:
                self.field_combobox.current(0)
                self.status_label.config(text=f"已加载 {len(columns)} 个字段，请选择坐标字段", fg="blue")
                self.analyze_selected_field()
            else:
                self.status_label.config(text="数据中没有字段", fg="red")
        else:
            self.clear_fields()
            self.status_label.config(text="没有可用的数据", fg="red")

    def clear_fields(self):
        """清空字段选择"""
        self.field_combobox['values'] = []
        self.field_combobox.set("")
        self.clear_preview()
        self.clear_analysis()
        self.selected_field = None
        self.field_analysis = {}
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

    def get_selection(self) -> Dict[str, Any]:
        """获取当前选择结果"""
        return {
            'field_name': self.selected_field,
            'geometry_type': self.geometry_var.get(),
            'analysis': self.field_analysis
        }


if __name__ == "__main__":
    # 测试代码
    root = tk.Tk()
    root.title("字段选择测试")
    root.geometry("700x600")

    # 创建测试数据
    test_data = pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['点1', '线1', '面1', '无效1', '点2'],
        'coordinates': [
            "[[116.404, 39.915]]",
            "[[116.404, 39.915], [116.405, 39.916]]",
            "[[116.404, 39.915], [116.405, 39.916], [116.406, 39.917], [116.404, 39.915]]",
            "invalid coordinate",
            "[[121.474, 31.230]]"
        ],
        'description': ['测试点1', '测试线1', '测试面1', '无效数据', '测试点2']
    })

    def on_field_selected(field_name, geometry_type, analysis):
        messagebox.showinfo(
            "字段选择完成",
            f"字段: {field_name}\n几何类型: {geometry_type}\n成功率: {analysis.get('success_rate', 0):.1%}"
        )

    # 创建字段选择面板
    field_frame = FieldSelectionFrame(root, on_field_selected)
    field_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # 设置测试数据
    field_frame.set_dataframe(test_data)

    root.mainloop()