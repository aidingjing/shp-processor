"""
导出配置GUI面板
提供SHP文件导出配置和执行的图形界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import pandas as pd
from typing import Optional, Dict, Any, Callable

from core.shapefile_exporter import ShapefileExporter


class ExportFrame(tk.Frame):
    """导出配置面板"""

    def __init__(self, parent, on_export_completed: Optional[Callable] = None):
        """
        初始化导出配置面板

        Args:
            parent: 父窗口
            on_export_completed: 导出完成回调函数
        """
        super().__init__(parent)

        self.on_export_completed = on_export_completed
        self.exporter = ShapefileExporter()
        self.current_dataframe: Optional[pd.DataFrame] = None
        self.selected_field: Optional[str] = None
        self.geometry_type: str = "auto"

        self.create_widgets()

    def create_widgets(self):
        """创建界面组件"""
        # 标题
        title_label = tk.Label(self, text="SHP文件导出配置", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(10, 20))

        # 导出预览区域
        preview_frame = tk.LabelFrame(self, text="导出预览", padx=10, pady=10)
        preview_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

        # 显示字段和几何类型信息
        self.field_info_label = tk.Label(preview_frame, text="未选择字段", fg="gray")
        self.field_info_label.grid(row=0, column=0, sticky="w", pady=5)

        self.geometry_info_label = tk.Label(preview_frame, text="未确定几何类型", fg="gray")
        self.geometry_info_label.grid(row=1, column=0, sticky="w", pady=5)

        self.records_info_label = tk.Label(preview_frame, text="没有可导出的数据", fg="gray")
        self.records_info_label.grid(row=2, column=0, sticky="w", pady=5)

        # 导出配置区域
        config_frame = tk.LabelFrame(self, text="导出配置", padx=10, pady=10)
        config_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

        # 输出文件路径
        tk.Label(config_frame, text="输出文件:").grid(row=0, column=0, sticky="w", pady=5)
        self.output_path_var = tk.StringVar()
        self.output_path_entry = tk.Entry(config_frame, textvariable=self.output_path_var, width=60)
        self.output_path_entry.grid(row=0, column=1, sticky="ew", padx=(10, 5))

        browse_button = tk.Button(config_frame, text="浏览...", command=self.browse_output_path)
        browse_button.grid(row=0, column=2, padx=5)

        # 坐标系选择
        tk.Label(config_frame, text="坐标系:").grid(row=1, column=0, sticky="w", pady=5)
        self.crs_var = tk.StringVar(value="WGS84")
        self.crs_combobox = ttk.Combobox(config_frame, textvariable=self.crs_var, width=25, state="readonly")
        self.crs_combobox.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=5)

        # 填充坐标系选项
        crs_options = list(self.exporter.get_supported_crs().keys())
        self.crs_combobox['values'] = crs_options

        # 文件编码选择
        tk.Label(config_frame, text="文件编码:").grid(row=2, column=0, sticky="w", pady=5)
        self.encoding_var = tk.StringVar(value="utf-8")
        encoding_options = ["utf-8", "gbk", "gb2312", "utf-8-sig"]
        self.encoding_combobox = ttk.Combobox(config_frame, textvariable=self.encoding_var, width=25, state="readonly")
        self.encoding_combobox['values'] = encoding_options
        self.encoding_combobox.grid(row=1, column=2, sticky="w", padx=(20, 0), pady=5)

        # 导出字段选择区域
        field_selection_frame = tk.LabelFrame(self, text="导出字段选择", padx=10, pady=10)
        field_selection_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

        # 字段选择标题
        tk.Label(field_selection_frame, text="选择要导出的字段:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )

        # 字段选择框架
        field_list_frame = tk.Frame(field_selection_frame)
        field_list_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)

        # 创建滚动文本框用于字段选择
        self.field_list_canvas = tk.Canvas(field_list_frame, height=150)
        field_scrollbar = ttk.Scrollbar(field_list_frame, orient="vertical", command=self.field_list_canvas.yview)
        self.field_list_frame_inner = tk.Frame(self.field_list_canvas)

        self.field_list_frame_inner.bind(
            "<Configure>",
            lambda e: self.field_list_canvas.configure(scrollregion=self.field_list_canvas.bbox("all"))
        )

        self.field_list_canvas.create_window((0, 0), window=self.field_list_frame_inner, anchor="nw")
        self.field_list_canvas.configure(yscrollcommand=field_scrollbar.set)

        self.field_list_canvas.pack(side="left", fill="both", expand=True)
        field_scrollbar.pack(side="right", fill="y")

        # 字段选择控制按钮
        field_button_frame = tk.Frame(field_selection_frame)
        field_button_frame.grid(row=2, column=0, columnspan=3, pady=5)

        select_all_button = tk.Button(
            field_button_frame,
            text="全选",
            command=self.select_all_fields,
            width=10
        )
        select_all_button.pack(side="left", padx=5)

        deselect_all_button = tk.Button(
            field_button_frame,
            text="全不选",
            command=self.deselect_all_fields,
            width=10
        )
        deselect_all_button.pack(side="left", padx=5)

        invert_selection_button = tk.Button(
            field_button_frame,
            text="反选",
            command=self.invert_field_selection,
            width=10
        )
        invert_selection_button.pack(side="left", padx=5)

        # 存储字段选择状态
        self.field_vars = {}  # 字段名 -> BooleanVar
        self.field_checkboxes = {}  # 字段名 -> Checkbutton

        # 高级选项（可折叠）
        self.advanced_frame = tk.LabelFrame(self, text="高级选项", padx=10, pady=10)
        self.advanced_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

        # 是否包含无效记录
        self.include_invalid_var = tk.BooleanVar(value=False)
        self.include_invalid_check = tk.Checkbutton(
            self.advanced_frame,
            text="包含无效的坐标记录",
            variable=self.include_invalid_var,
            command=self.update_preview
        )
        self.include_invalid_check.grid(row=0, column=0, sticky="w", pady=5)

        # 几何类型覆盖
        tk.Label(self.advanced_frame, text="强制几何类型:").grid(row=1, column=0, sticky="w", pady=5)
        self.force_geometry_var = tk.StringVar(value="auto")
        force_geometry_options = ["自动检测", "Point", "LineString", "Polygon"]
        force_geometry_values = ["auto", "Point", "LineString", "Polygon"]
        self.force_geometry_combobox = ttk.Combobox(
            self.advanced_frame,
            textvariable=self.force_geometry_var,
            width=20,
            state="readonly"
        )
        self.force_geometry_combobox['values'] = force_geometry_options
        self.force_geometry_combobox.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=5)

        # 按钮区域
        button_frame = tk.Frame(self)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)

        # 预览导出按钮
        preview_button = tk.Button(
            button_frame,
            text="预览导出",
            command=self.preview_export,
            bg="#2196F3",
            fg="white",
            padx=15
        )
        preview_button.grid(row=0, column=0, padx=10)

        # 执行导出按钮
        self.export_button = tk.Button(
            button_frame,
            text="执行导出",
            command=self.execute_export,
            bg="#4CAF50",
            fg="white",
            padx=20,
            font=("Arial", 11, "bold"),
            state=tk.DISABLED
        )
        self.export_button.grid(row=0, column=1, padx=10)

        # 打开输出目录按钮
        self.open_folder_button = tk.Button(
            button_frame,
            text="打开文件夹",
            command=self.open_output_folder,
            bg="#FF9800",
            fg="white",
            padx=15,
            state=tk.DISABLED
        )
        self.open_folder_button.grid(row=0, column=2, padx=10)

        # 进度条
        self.progress_frame = tk.Frame(self)
        self.progress_frame.grid(row=5, column=0, columnspan=3, sticky="ew", padx=10, pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=400
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.progress_label = tk.Label(self.progress_frame, text="准备就绪", fg="gray")
        self.progress_label.pack(side=tk.LEFT, padx=(10, 0))

        # 状态栏
        self.status_label = tk.Label(self, text="请先完成前面的配置步骤", fg="gray", anchor="w")
        self.status_label.grid(row=6, column=0, columnspan=3, sticky="ew", padx=10, pady=5)

        # 配置权重
        config_frame.columnconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

    def set_export_data(self, df: pd.DataFrame, field_name: str, geometry_type: str):
        """
        设置要导出的数据

        Args:
            df: 数据DataFrame
            field_name: 坐标字段名
            geometry_type: 几何类型
        """
        self.current_dataframe = df
        self.selected_field = field_name
        self.geometry_type = geometry_type

        # 初始化字段选择列表
        self.initialize_field_selection()

        # 更新信息显示
        self.update_field_info()
        self.update_preview()

        # 设置默认输出文件名
        if not self.output_path_var.get():
            default_name = f"export_{field_name}.shp"
            self.output_path_var.set(default_name)

        # 启用导出按钮
        self.export_button.config(state=tk.NORMAL)

        self.status_label.config(text="导出配置已完成，可以开始导出", fg="green")

    def update_field_info(self):
        """更新字段信息显示"""
        if self.selected_field:
            self.field_info_label.config(text=f"坐标字段: {self.selected_field}", fg="blue")

            geometry_display = {
                "auto": "自动检测",
                "Point": "Point (点)",
                "LineString": "LineString (线)",
                "Polygon": "Polygon (面)"
            }
            self.geometry_info_label.config(
                text=f"几何类型: {geometry_display.get(self.geometry_type, self.geometry_type)}",
                fg="blue"
            )

            if self.current_dataframe is not None:
                total_records = len(self.current_dataframe)
                selected_fields = self.get_selected_fields()
                fields_info = f"总记录数: {total_records} | 将导出 {len(selected_fields)} 个字段"
                self.records_info_label.config(text=fields_info, fg="blue")
        else:
            self.field_info_label.config(text="未选择字段", fg="gray")
            self.geometry_info_label.config(text="未确定几何类型", fg="gray")
            self.records_info_label.config(text="没有可导出的数据", fg="gray")

    def browse_output_path(self):
        """浏览选择输出文件路径"""
        filename = filedialog.asksaveasfilename(
            title="选择SHP文件保存位置",
            defaultextension=".shp",
            filetypes=[("Shapefile文件", "*.shp"), ("所有文件", "*.*")],
            initialdir=os.getcwd(),
            initialfile=self.output_path_var.get() or "export.shp"
        )

        if filename:
            self.output_path_var.set(filename)

    def preview_export(self):
        """预览导出结果"""
        if not self.validate_inputs():
            return

        try:
            self.status_label.config(text="正在生成预览...", fg="orange")
            self.update()

            # 获取预览信息
            preview = self.exporter.preview_export(
                self.current_dataframe,
                self.selected_field,
                self.force_geometry_var.get()
            )

            if 'error' in preview:
                messagebox.showerror("预览错误", f"生成预览时发生错误：\n\n{preview['error']}")
                return

            # 显示预览对话框
            self.show_preview_dialog(preview)

            self.status_label.config(text="预览生成完成", fg="green")

        except Exception as e:
            self.status_label.config(text="预览生成失败", fg="red")
            messagebox.showerror("预览错误", f"生成预览时发生错误：\n\n{e}")

    def show_preview_dialog(self, preview: Dict[str, Any]):
        """显示预览对话框"""
        dialog = tk.Toplevel(self)
        dialog.title("导出预览")
        dialog.geometry("500x400")
        dialog.resizable(False, False)

        # 预览内容
        preview_frame = tk.Frame(dialog)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 基本信息
        info_frame = tk.LabelFrame(preview_frame, text="基本信息", padx=10, pady=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        info_items = [
            ("总记录数:", preview.get('total_records', 0)),
            ("有效记录数:", preview.get('valid_records', 0)),
            ("无效记录数:", preview.get('invalid_records', 0)),
            ("成功率:", f"{preview.get('success_rate', 0):.1%}")
        ]

        for i, (label, value) in enumerate(info_items):
            tk.Label(info_frame, text=label, font=("Arial", 10, "bold")).grid(
                row=i, column=0, sticky="w", pady=2
            )
            tk.Label(info_frame, text=str(value), fg="blue").grid(
                row=i, column=1, sticky="w", padx=(20, 0), pady=2
            )

        # 几何类型分布
        geometry_frame = tk.LabelFrame(preview_frame, text="几何类型分布", padx=10, pady=10)
        geometry_frame.pack(fill=tk.X, pady=(0, 10))

        geometry_types = preview.get('geometry_types', {})
        for i, (geom_type, count) in enumerate(geometry_types.items()):
            tk.Label(geometry_frame, text=f"{geom_type}:", font=("Arial", 10, "bold")).grid(
                row=i, column=0, sticky="w", pady=2
            )
            tk.Label(geometry_frame, text=str(count), fg="blue").grid(
                row=i, column=1, sticky="w", padx=(20, 0), pady=2
            )

        # 字段列表
        fields_frame = tk.LabelFrame(preview_frame, text="导出字段", padx=10, pady=10)
        fields_frame.pack(fill=tk.BOTH, expand=True)

        fields_text = tk.Text(fields_frame, height=8, wrap=tk.WORD)
        fields_text.pack(fill=tk.BOTH, expand=True)

        columns = preview.get('columns', [])
        fields_text.insert("1.0", f"坐标字段: {preview.get('coordinate_column', 'N/A')}\n\n")
        fields_text.insert(tk.END, "属性字段:\n")
        for col in columns:
            fields_text.insert(tk.END, f"  • {col}\n")

        fields_text.config(state=tk.DISABLED)

        # 关闭按钮
        close_button = tk.Button(dialog, text="关闭", command=dialog.destroy, bg="#2196F3", fg="white", padx=20)
        close_button.pack(pady=10)

    def validate_inputs(self) -> bool:
        """验证输入参数"""
        if self.current_dataframe is None or self.current_dataframe.empty:
            messagebox.showwarning("数据为空", "没有可导出的数据")
            return False

        if not self.selected_field:
            messagebox.showwarning("字段未选择", "请先选择坐标字段")
            return False

        # 验证字段选择
        selected_fields = self.get_selected_fields()
        if not selected_fields:
            messagebox.showwarning("字段选择", "请至少选择一个字段用于导出")
            return False

        output_path = self.output_path_var.get().strip()
        if not output_path:
            messagebox.showwarning("路径未设置", "请设置输出文件路径")
            return False

        # 验证输出路径
        is_valid, error_msg = self.exporter.validate_output_path(output_path)
        if not is_valid:
            messagebox.showerror("路径错误", error_msg)
            return False

        return True

    def execute_export(self):
        """执行导出"""
        if not self.validate_inputs():
            return

        # 获取选中的字段
        export_dataframe = self.get_export_dataframe()
        if export_dataframe.empty:
            return

        output_path = self.output_path_var.get().strip()
        geometry_type = self.force_geometry_var.get()
        crs = self.crs_var.get()
        encoding = self.encoding_var.get()

        # 确认导出
        success_rate = self.exporter.preview_export(
            export_dataframe, self.selected_field, geometry_type
        ).get('success_rate', 0)

        if success_rate < 0.8:
            if not messagebox.askyesno(
                "确认导出",
                f"坐标解析成功率较低 ({success_rate:.1%})，\n确定要继续导出吗？"
            ):
                return

        # 检查文件是否已存在
        if os.path.exists(output_path):
            if not messagebox.askyesno(
                "文件已存在",
                f"文件 '{output_path}' 已存在，\n确定要覆盖吗？"
            ):
                return

        # 开始导出
        self.export_button.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.progress_label.config(text="正在导出...", fg="blue")
        self.update()

        try:
            success = self.exporter.export_to_shapefile(
                export_dataframe,
                self.selected_field,
                output_path,
                geometry_type,
                crs,
                encoding
            )

            if success:
                self.progress_var.set(100)
                self.progress_label.config(text="导出完成", fg="green")
                self.status_label.config(text=f"导出成功: {output_path}", fg="green")
                self.open_folder_button.config(state=tk.NORMAL)

                messagebox.showinfo("导出成功", f"SHP文件已成功导出到：\n\n{output_path}")

                if self.on_export_completed:
                    self.on_export_completed(output_path)

            else:
                self.progress_label.config(text="导出失败", fg="red")
                self.status_label.config(text="导出失败", fg="red")
                messagebox.showerror("导出失败", "导出SHP文件时发生错误，请检查日志信息")

        except Exception as e:
            self.progress_label.config(text="导出失败", fg="red")
            self.status_label.config(text="导出失败", fg="red")
            messagebox.showerror("导出错误", f"导出过程中发生错误：\n\n{e}")

        finally:
            self.export_button.config(state=tk.NORMAL)

    def open_output_folder(self):
        """打开输出文件所在的文件夹"""
        output_path = self.output_path_var.get().strip()
        if output_path and os.path.exists(output_path):
            folder_path = os.path.dirname(os.path.abspath(output_path))
            os.startfile(folder_path)  # Windows系统
        else:
            messagebox.showwarning("文件不存在", "输出文件不存在或路径未设置")

    def update_preview(self):
        """更新预览信息"""
        if self.current_dataframe is not None and self.selected_field:
            # 更新字段选择统计信息
            selected_fields = self.get_selected_fields()
            total_fields = len(self.field_vars)

            if selected_fields:
                self.status_label.config(
                    text=f"已选择 {len(selected_fields)}/{total_fields} 个字段用于导出",
                    fg="green"
                )
            else:
                self.status_label.config(
                    text="请选择至少一个字段用于导出",
                    fg="orange"
                )

    def initialize_field_selection(self):
        """初始化字段选择列表"""
        # 清空现有字段
        for widget in self.field_list_frame_inner.winfo_children():
            widget.destroy()

        self.field_vars.clear()
        self.field_checkboxes.clear()

        if self.current_dataframe is None or self.current_dataframe.empty:
            return

        # 创建字段选择复选框
        columns = list(self.current_dataframe.columns)
        for i, column in enumerate(columns):
            # 默认选择所有字段，除了坐标字段（因为它会被转换为几何图形）
            default_selected = column != self.selected_field

            var = tk.BooleanVar(value=default_selected)
            self.field_vars[column] = var

            checkbox = tk.Checkbutton(
                self.field_list_frame_inner,
                text=f"{column} ({self.current_dataframe[column].dtype})",
                variable=var,
                command=self.update_preview,
                anchor="w"
            )

            # 标记坐标字段
            if column == self.selected_field:
                checkbox.config(fg="blue")

            checkbox.grid(row=i, column=0, sticky="w", padx=5, pady=2)
            self.field_checkboxes[column] = checkbox

    def get_selected_fields(self):
        """获取选中的字段列表"""
        selected_fields = []
        for field_name, var in self.field_vars.items():
            if var.get():
                selected_fields.append(field_name)
        return selected_fields

    def select_all_fields(self):
        """全选所有字段"""
        for var in self.field_vars.values():
            var.set(True)
        self.update_preview()

    def deselect_all_fields(self):
        """全不选所有字段"""
        for var in self.field_vars.values():
            var.set(False)
        self.update_preview()

    def invert_field_selection(self):
        """反选字段"""
        for var in self.field_vars.values():
            var.set(not var.get())
        self.update_preview()

    def get_export_dataframe(self):
        """
        根据字段选择创建用于导出的DataFrame

        Returns:
            pd.DataFrame: 包含选中字段的DataFrame
        """
        if self.current_dataframe is None:
            return pd.DataFrame()

        selected_fields = self.get_selected_fields()

        if not selected_fields:
            messagebox.showwarning("字段选择", "请至少选择一个字段用于导出")
            return pd.DataFrame()

        # 确保包含坐标字段
        if self.selected_field not in selected_fields:
            selected_fields.append(self.selected_field)

        # 创建导出用的DataFrame
        export_df = self.current_dataframe[selected_fields].copy()

        return export_df


if __name__ == "__main__":
    # 测试代码
    root = tk.Tk()
    root.title("导出配置测试")
    root.geometry("600x500")

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

    def on_export_completed(output_path):
        messagebox.showinfo("导出完成回调", f"导出已完成: {output_path}")

    # 创建导出配置面板
    export_frame = ExportFrame(root, on_export_completed)
    export_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # 设置测试数据
    export_frame.set_export_data(test_data, 'coordinates', 'auto')

    root.mainloop()