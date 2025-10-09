#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SHP文件合并对话框
提供图形界面用于合并两个或多个SHP文件

作者: Claude Code
创建时间: 2024-10-09
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import logging
from typing import List, Dict, Optional
from core.shapefile_merger import ShapefileMerger


class ShapefileMergerDialog:
    """SHP文件合并对话框"""

    def __init__(self, parent):
        """
        初始化合并对话框

        Args:
            parent: 父窗口
        """
        self.parent = parent
        self.merger = ShapefileMerger()
        self.selected_files = []
        self.preview_info = None

        # 创建对话框窗口
        self.window = tk.Toplevel(parent)
        self.window.title("SHP文件合并工具")
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        self.window.transient(parent)
        self.window.grab_set()

        # 设置窗口在父窗口中央
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.window.winfo_screenheight() // 2) - (600 // 2)
        self.window.geometry(f"800x600+{x}+{y}")

        self.create_widgets()
        self.update_ui_state()

    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 标题
        title_label = ttk.Label(main_frame, text="SHP文件合并工具",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="文件选择", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))

        # 文件列表框架
        list_frame = ttk.Frame(file_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 文件列表
        self.file_listbox = tk.Listbox(list_frame, height=6)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL,
                                 command=self.file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=scrollbar.set)

        # 文件操作按钮
        file_button_frame = ttk.Frame(file_frame)
        file_button_frame.pack(fill=tk.X)

        self.add_file_btn = ttk.Button(file_button_frame, text="添加SHP文件",
                                      command=self.add_file)
        self.add_file_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.remove_file_btn = ttk.Button(file_button_frame, text="移除选中",
                                         command=self.remove_file)
        self.remove_file_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.clear_files_btn = ttk.Button(file_button_frame, text="清空列表",
                                         command=self.clear_files)
        self.clear_files_btn.pack(side=tk.LEFT)

        # 文件计数标签
        self.file_count_label = ttk.Label(file_button_frame, text="已选择 0 个文件")
        self.file_count_label.pack(side=tk.RIGHT)

        # 合并选项区域
        options_frame = ttk.LabelFrame(main_frame, text="合并选项", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 10))

        # 目标坐标系选择
        crs_frame = ttk.Frame(options_frame)
        crs_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(crs_frame, text="目标坐标系:").pack(side=tk.LEFT, padx=(0, 10))

        self.crs_var = tk.StringVar(value="auto")
        self.crs_combo = ttk.Combobox(crs_frame, textvariable=self.crs_var,
                                      values=["auto", "EPSG:4326", "EPSG:4490",
                                             "EPSG:3857", "EPSG:32649", "EPSG:32650"],
                                      width=20, state="readonly")
        self.crs_combo.pack(side=tk.LEFT, padx=(0, 10))

        self.crs_help_btn = ttk.Button(crs_frame, text="?",
                                      command=self.show_crs_help, width=3)
        self.crs_help_btn.pack(side=tk.LEFT)

        # 合并策略选择
        strategy_frame = ttk.Frame(options_frame)
        strategy_frame.pack(fill=tk.X)

        ttk.Label(strategy_frame, text="合并策略:").pack(side=tk.LEFT, padx=(0, 10))

        self.strategy_var = tk.StringVar(value="union")
        self.union_radio = ttk.Radiobutton(strategy_frame, text="联合（去重）",
                                          variable=self.strategy_var, value="union")
        self.union_radio.pack(side=tk.LEFT, padx=(0, 20))

        self.append_radio = ttk.Radiobutton(strategy_frame, text="追加（保留重复）",
                                           variable=self.strategy_var, value="append")
        self.append_radio.pack(side=tk.LEFT)

        # 预览区域
        preview_frame = ttk.LabelFrame(main_frame, text="预览信息", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=10,
                                                      wrap=tk.WORD, state=tk.DISABLED)
        self.preview_text.pack(fill=tk.BOTH, expand=True)

        # 操作按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        self.preview_btn = ttk.Button(button_frame, text="预览合并信息",
                                     command=self.preview_merge)
        self.preview_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.merge_btn = ttk.Button(button_frame, text="开始合并",
                                   command=self.start_merge,
                                   style="Accent.TButton")
        self.merge_btn.pack(side=tk.LEFT, padx=(0, 5))

        # 进度条
        self.progress = ttk.Progressbar(button_frame, mode='indeterminate')
        self.progress.pack(side=tk.LEFT, padx=(0, 10))

        # 状态标签
        self.status_label = ttk.Label(button_frame, text="就绪")
        self.status_label.pack(side=tk.LEFT, padx=(0, 10))

        # 关闭按钮
        self.close_btn = ttk.Button(button_frame, text="关闭",
                                    command=self.close_dialog)
        self.close_btn.pack(side=tk.RIGHT)

    def update_ui_state(self):
        """更新界面状态"""
        has_files = len(self.selected_files) > 0
        has_multiple_files = len(self.selected_files) >= 2

        # 更新按钮状态
        self.remove_file_btn.config(state=tk.NORMAL if has_files else tk.DISABLED)
        self.clear_files_btn.config(state=tk.NORMAL if has_files else tk.DISABLED)
        self.preview_btn.config(state=tk.NORMAL if has_multiple_files else tk.DISABLED)
        self.merge_btn.config(state=tk.NORMAL if has_multiple_files else tk.DISABLED)

        # 更新计数标签
        self.file_count_label.config(text=f"已选择 {len(self.selected_files)} 个文件")

    def add_file(self):
        """添加SHP文件"""
        files = filedialog.askopenfilenames(
            title="选择SHP文件",
            filetypes=[("SHP文件", "*.shp"), ("所有文件", "*.*")]
        )

        if files:
            for file_path in files:
                if file_path not in self.selected_files:
                    self.selected_files.append(file_path)
                    self.file_listbox.insert(tk.END, os.path.basename(file_path))

            self.update_ui_state()
            self.set_status(f"已添加 {len(files)} 个文件")

    def remove_file(self):
        """移除选中的文件"""
        selection = self.file_listbox.curselection()
        if selection:
            # 从后往前删除，避免索引变化
            for index in reversed(selection):
                del self.selected_files[index]
                self.file_listbox.delete(index)

            self.update_ui_state()
            self.set_status("已移除选中文件")

    def clear_files(self):
        """清空文件列表"""
        if self.selected_files and messagebox.askyesno("确认", "确定要清空文件列表吗？"):
            self.selected_files.clear()
            self.file_listbox.delete(0, tk.END)
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.config(state=tk.DISABLED)
            self.update_ui_state()
            self.set_status("已清空文件列表")

    def preview_merge(self):
        """预览合并信息"""
        if len(self.selected_files) < 2:
            messagebox.showwarning("警告", "请至少选择两个SHP文件进行预览")
            return

        self.set_status("正在分析文件...")
        self.window.update()

        try:
            # 获取预览信息
            summary = self.merger.get_merge_summary(self.selected_files)

            # 显示预览信息
            self.display_preview_info(summary)

        except Exception as e:
            messagebox.showerror("错误", f"预览失败：{str(e)}")
            self.set_status("预览失败")

    def display_preview_info(self, summary: Dict):
        """显示预览信息"""
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)

        if not summary.get('compatible', False) and 'error' in summary:
            self.preview_text.insert(tk.END, f"❌ 预览失败\n\n")
            self.preview_text.insert(tk.END, f"错误信息：{summary['error']}\n")
        else:
            # 基本信息
            self.preview_text.insert(tk.END, f"📊 合并预览信息\n\n")
            self.preview_text.insert(tk.END, f"📁 输入文件数量：{summary['files_count']}\n")
            self.preview_text.insert(tk.END, f"✅ 有效文件数量：{summary['valid_files']}\n")
            self.preview_text.insert(tk.END, f"📈 总要素数量：{summary['total_features']}\n\n")

            # 兼容性信息
            compatibility = summary.get('compatibility', {})
            if compatibility.get('compatible', False):
                self.preview_text.insert(tk.END, f"✅ 文件兼容性：良好\n")
                self.preview_text.insert(tk.END, f"🔧 合并类型：{compatibility.get('merge_type', '未知')}\n")

                crs = compatibility.get('common_crs')
                if crs:
                    self.preview_text.insert(tk.END, f"🌐 坐标系：{crs}\n")
                else:
                    self.preview_text.insert(tk.END, f"🌐 坐标系：自动检测\n")

                geometry_types = compatibility.get('all_geometry_types', [])
                self.preview_text.insert(tk.END, f"📐 几何类型：{', '.join(geometry_types)}\n")
            else:
                self.preview_text.insert(tk.END, f"❌ 文件兼容性：不兼容\n")
                issues = compatibility.get('issues', [])
                if issues:
                    self.preview_text.insert(tk.END, f"⚠️ 问题：{'; '.join(issues)}\n")

            # 文件详细信息
            self.preview_text.insert(tk.END, f"\n📋 文件详细信息：\n")
            files_info = summary.get('files_info', [])
            for i, info in enumerate(files_info, 1):
                if info.get('success', False):
                    file_info = info.get('file_info', {})
                    filename = os.path.basename(info.get('path', ''))
                    self.preview_text.insert(tk.END, f"\n{i}. {filename}\n")
                    self.preview_text.insert(tk.END, f"   要素数量：{file_info.get('feature_count', 0)}\n")
                    self.preview_text.insert(tk.END, f"   几何类型：{', '.join(file_info.get('geometry_types', []))}\n")
                    self.preview_text.insert(tk.END, f"   坐标系：{file_info.get('crs', '未知')}\n")
                else:
                    self.preview_text.insert(tk.END, f"\n{i}. ❌ {info.get('path', '未知文件')}\n")
                    self.preview_text.insert(tk.END, f"   错误：{info.get('error', '未知错误')}\n")

        self.preview_text.config(state=tk.DISABLED)
        self.set_status("预览完成")

    def start_merge(self):
        """开始合并"""
        if len(self.selected_files) < 2:
            messagebox.showwarning("警告", "请至少选择两个SHP文件进行合并")
            return

        # 选择输出文件
        output_file = filedialog.asksaveasfilename(
            title="保存合并后的SHP文件",
            defaultextension=".shp",
            filetypes=[("SHP文件", "*.shp"), ("所有文件", "*.*")]
        )

        if not output_file:
            return

        # 确认合并
        if not messagebox.askyesno("确认",
                                  f"确定要合并 {len(self.selected_files)} 个文件到\n{output_file}\n吗？"):
            return

        self.set_status("正在合并文件...")
        self.progress.start()
        self.window.update()

        try:
            # 获取目标坐标系
            target_crs = None
            if self.crs_var.get() != "auto":
                target_crs = self.crs_var.get()

            # 执行合并
            result = self.merger.merge_shapefiles(
                self.selected_files,
                output_file,
                target_crs=target_crs,
                merge_strategy=self.strategy_var.get()
            )

            if result['success']:
                messagebox.showinfo("成功",
                                  f"SHP文件合并成功！\n\n"
                                  f"输出文件：{result['output_path']}\n"
                                  f"合并要素数量：{result['merge_info']['total_features']}\n"
                                  f"几何类型：{result['merge_info']['geometry_type']}\n"
                                  f"坐标系：{result['merge_info']['crs']}")
                self.set_status("合并成功")
            else:
                messagebox.showerror("失败", f"合并失败：{result['error']}")
                self.set_status("合并失败")

        except Exception as e:
            messagebox.showerror("错误", f"合并过程中发生错误：{str(e)}")
            self.set_status("合并出错")

        finally:
            self.progress.stop()

    def show_crs_help(self):
        """显示坐标系帮助信息"""
        help_text = """
坐标系说明：

• auto - 自动选择（推荐）
    如果文件有相同坐标系则使用，否则使用WGS84

• EPSG:4326 - WGS84
    世界大地坐标系，GPS使用的坐标系

• EPSG:4490 - GCJ02
    中国测绘坐标系，国家测绘局制定的坐标系

• EPSG:3857 - Web Mercator
    网络地图投影坐标系，Google Maps、OpenStreetMap使用

• EPSG:32649 - UTM Zone 49N
    通用横轴墨卡托投影，覆盖中国东部地区

• EPSG:32650 - UTM Zone 50N
    通用横轴墨卡托投影，覆盖中国西部地区

建议：如果所有输入文件使用相同坐标系，请选择"auto"。
        """

        help_window = tk.Toplevel(self.window)
        help_window.title("坐标系帮助")
        help_window.geometry("500x400")
        help_window.resizable(False, False)
        help_window.transient(self.window)

        text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert("1.0", help_text)
        text_widget.config(state=tk.DISABLED)

        close_button = ttk.Button(help_window, text="关闭", command=help_window.destroy)
        close_button.pack(pady=10)

    def set_status(self, message: str):
        """设置状态信息"""
        self.status_label.config(text=message)

    def close_dialog(self):
        """关闭对话框"""
        if messagebox.askyesno("确认", "确定要关闭SHP文件合并工具吗？"):
            self.window.destroy()


if __name__ == "__main__":
    # 测试代码
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    dialog = ShapefileMergerDialog(root)
    root.mainloop()