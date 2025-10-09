"""
坐标转换工具对话框
提供不同坐标系之间的坐标转换功能
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
from typing import Dict, List, Tuple, Optional
import math


class CoordinateConverterDialog:
    """坐标转换工具对话框"""

    def __init__(self, parent):
        """初始化坐标转换工具对话框"""
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("坐标转换工具")
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        self.window.transient(parent)
        self.window.grab_set()

        # 坐标转换参数（简化版本，实际应用中应使用专业的坐标转换库）
        self.coord_systems = {
            "WGS84 (经纬度)": {
                "epsg": "4326",
                "description": "世界大地坐标系，GPS使用的坐标系"
            },
            "CGCS2000 (经纬度)": {
                "epsg": "4490", 
                "description": "中国大地坐标系2000"
            },
            "Web墨卡托": {
                "epsg": "3857",
                "description": "Web地图常用的投影坐标系"
            },
            "UTM Zone 50N": {
                "epsg": "32650",
                "description": "通用横轴墨卡托投影，中国东部地区"
            },
            "北京54": {
                "epsg": "4214",
                "description": "北京54坐标系"
            },
            "西安80": {
                "epsg": "4610",
                "description": "西安80坐标系"
            }
        }

        self.conversion_history = []

        self.create_widgets()
        self.center_window()

    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建标题
        title_label = tk.Label(main_frame, text="坐标转换工具", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))

        # 创建转换配置区域
        config_frame = ttk.LabelFrame(main_frame, text="转换配置", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 10))

        # 源坐标系选择
        source_frame = ttk.Frame(config_frame)
        source_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(source_frame, text="源坐标系:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 10))
        self.source_system = ttk.Combobox(source_frame, values=list(self.coord_systems.keys()), 
                                         width=30, state="readonly")
        self.source_system.set("WGS84 (经纬度)")
        self.source_system.pack(side=tk.LEFT, padx=(0, 20))
        self.source_system.bind("<<ComboboxSelected>>", self.on_system_changed)

        # 目标坐标系选择
        target_frame = ttk.Frame(config_frame)
        target_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(target_frame, text="目标坐标系:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 10))
        self.target_system = ttk.Combobox(target_frame, values=list(self.coord_systems.keys()), 
                                         width=30, state="readonly")
        self.target_system.set("Web墨卡托")
        self.target_system.pack(side=tk.LEFT, padx=(0, 20))
        self.target_system.bind("<<ComboboxSelected>>", self.on_system_changed)

        # 批量转换选项
        self.batch_mode = tk.BooleanVar(value=False)
        batch_check = ttk.Checkbutton(config_frame, text="批量转换模式", 
                                     variable=self.batch_mode, command=self.on_mode_changed)
        batch_check.pack(anchor=tk.W, pady=5)

        # 创建输入输出区域
        io_frame = ttk.Frame(main_frame)
        io_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 左侧：输入区域
        input_frame = ttk.LabelFrame(io_frame, text="输入坐标", padding="10")
        input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # 输入格式说明
        format_label = tk.Label(input_frame, text="格式: 经度,纬度 或 [经度,纬度]", 
                               fg="gray", font=("Arial", 9))
        format_label.pack(anchor=tk.W, pady=(0, 5))

        # 单点输入控件
        self.single_input_frame = ttk.Frame(input_frame)
        self.single_input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.single_input_frame, text="经度:").pack(side=tk.LEFT)
        self.lon_entry = ttk.Entry(self.single_input_frame, width=15)
        self.lon_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(self.single_input_frame, text="纬度:").pack(side=tk.LEFT)
        self.lat_entry = ttk.Entry(self.single_input_frame, width=15)
        self.lat_entry.pack(side=tk.LEFT, padx=(5, 10))

        # 批量输入控件
        self.batch_input_frame = ttk.Frame(input_frame)
        
        ttk.Label(self.batch_input_frame, text="批量输入 (每行一个坐标):").pack(anchor=tk.W, pady=(0, 5))
        
        # 创建文本框和滚动条的容器
        text_container = ttk.Frame(self.batch_input_frame)
        text_container.pack(fill=tk.BOTH, expand=True)
        
        self.batch_text = tk.Text(text_container, height=10, wrap=tk.NONE)
        batch_scrollbar_y = ttk.Scrollbar(text_container, orient=tk.VERTICAL, 
                                         command=self.batch_text.yview)
        batch_scrollbar_x = ttk.Scrollbar(text_container, orient=tk.HORIZONTAL, 
                                         command=self.batch_text.xview)
        
        self.batch_text.configure(yscrollcommand=batch_scrollbar_y.set, 
                                 xscrollcommand=batch_scrollbar_x.set)
        
        # 使用pack布局管理器
        self.batch_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        batch_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        batch_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # 右侧：输出区域
        output_frame = ttk.LabelFrame(io_frame, text="转换结果", padding="10")
        output_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # 输出文本框
        self.output_text = tk.Text(output_frame, height=15, wrap=tk.NONE, state=tk.DISABLED)
        output_scrollbar_y = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, 
                                         command=self.output_text.yview)
        output_scrollbar_x = ttk.Scrollbar(output_frame, orient=tk.HORIZONTAL, 
                                         command=self.output_text.xview)
        
        self.output_text.configure(yscrollcommand=output_scrollbar_y.set, 
                                 xscrollcommand=output_scrollbar_x.set)
        
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        output_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        output_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        # 转换按钮
        convert_btn = ttk.Button(button_frame, text="执行转换", command=self.execute_conversion)
        convert_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 清空按钮
        clear_btn = ttk.Button(button_frame, text="清空", command=self.clear_all)
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 导入按钮
        import_btn = ttk.Button(button_frame, text="导入坐标", command=self.import_coordinates)
        import_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 导出按钮
        export_btn = ttk.Button(button_frame, text="导出结果", command=self.export_results)
        export_btn.pack(side=tk.LEFT)

        # 历史记录按钮
        history_btn = ttk.Button(button_frame, text="历史记录", command=self.show_history)
        history_btn.pack(side=tk.RIGHT)

        # 状态栏
        self.status_label = tk.Label(main_frame, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, pady=(10, 0))

        # 初始化显示模式
        self.on_mode_changed()

    def on_mode_changed(self):
        """模式切换事件"""
        if self.batch_mode.get():
            self.single_input_frame.pack_forget()
            self.batch_input_frame.pack(fill=tk.BOTH, expand=True)
        else:
            self.batch_input_frame.pack_forget()
            self.single_input_frame.pack(fill=tk.X, pady=5)

    def on_system_changed(self, event=None):
        """坐标系改变事件"""
        source = self.source_system.get()
        target = self.target_system.get()
        
        if source and target:
            source_info = self.coord_systems.get(source, {})
            target_info = self.coord_systems.get(target, {})
            
            info_text = f"源: {source_info.get('description', '')} | 目标: {target_info.get('description', '')}"
            self.status_label.config(text=info_text)

    def parse_coordinates(self) -> List[Tuple[float, float]]:
        """解析输入的坐标"""
        coordinates = []
        
        if self.batch_mode.get():
            # 批量模式
            text = self.batch_text.get("1.0", tk.END).strip()
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            for line in lines:
                try:
                    # 尝试不同格式
                    if line.startswith('[') and line.endswith(']'):
                        # [经度,纬度] 格式
                        coords_str = line[1:-1]
                        lon, lat = map(float, [x.strip() for x in coords_str.split(',')])
                    else:
                        # 经度,纬度 格式
                        lon, lat = map(float, [x.strip() for x in line.split(',')])
                    
                    coordinates.append((lon, lat))
                except ValueError:
                    continue  # 跳过无效行
        else:
            # 单点模式
            try:
                lon = float(self.lon_entry.get().strip())
                lat = float(self.lat_entry.get().strip())
                coordinates.append((lon, lat))
            except ValueError:
                pass
        
        return coordinates

    def convert_coordinates(self, coordinates: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """坐标转换（简化版本）"""
        source = self.source_system.get()
        target = self.target_system.get()
        
        if source == target:
            return coordinates
        
        converted = []
        
        for lon, lat in coordinates:
            try:
                # 这里是简化的坐标转换逻辑
                # 实际应用中应该使用pyproj等专业库
                
                if source == "WGS84 (经纬度)" and target == "Web墨卡托":
                    # WGS84转Web墨卡托
                    x = lon * 20037508.34 / 180
                    y = math.log(math.tan((90 + lat) * math.pi / 360)) * 20037508.34 / math.pi
                    converted.append((x, y))
                    
                elif source == "Web墨卡托" and target == "WGS84 (经纬度)":
                    # Web墨卡托转WGS84
                    x = lon * 20037508.34 / 180
                    y = math.log(math.tan((90 + lat) * math.pi / 360)) * 20037508.34 / math.pi
                    converted_lon = x * 180 / 20037508.34
                    converted_lat = math.atan(math.exp(y * math.pi / 20037508.34)) * 360 / math.pi - 90
                    converted.append((converted_lon, converted_lat))
                    
                else:
                    # 其他转换暂时返回原值（实际应用中需要实现具体转换）
                    converted.append((lon, lat))
                    
            except Exception as e:
                # 转换失败时返回原值
                converted.append((lon, lat))
        
        return converted

    def execute_conversion(self):
        """执行坐标转换"""
        coordinates = self.parse_coordinates()
        
        if not coordinates:
            messagebox.showwarning("输入错误", "请输入有效的坐标数据")
            return
        
        self.status_label.config(text="正在转换...")
        self.window.update()
        
        try:
            converted = self.convert_coordinates(coordinates)
            
            # 显示结果
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete("1.0", tk.END)
            
            source = self.source_system.get()
            target = self.target_system.get()
            
            self.output_text.insert(tk.END, f"坐标转换结果\n")
            self.output_text.insert(tk.END, f"源坐标系: {source}\n")
            self.output_text.insert(tk.END, f"目标坐标系: {target}\n")
            self.output_text.insert(tk.END, f"转换数量: {len(coordinates)} 个点\n")
            self.output_text.insert(tk.END, "=" * 50 + "\n\n")
            
            for i, ((src_lon, src_lat), (dst_lon, dst_lat)) in enumerate(zip(coordinates, converted), 1):
                self.output_text.insert(tk.END, f"点 {i}:\n")
                self.output_text.insert(tk.END, f"  输入: [{src_lon:.6f}, {src_lat:.6f}]\n")
                self.output_text.insert(tk.END, f"  输出: [{dst_lon:.6f}, {dst_lat:.6f}]\n\n")
            
            self.output_text.config(state=tk.DISABLED)
            
            # 保存到历史记录
            self.conversion_history.append({
                'source_system': source,
                'target_system': target,
                'input_count': len(coordinates),
                'coordinates': coordinates,
                'converted': converted
            })
            
            self.status_label.config(text=f"转换完成，共转换 {len(coordinates)} 个坐标点")
            
        except Exception as e:
            messagebox.showerror("转换错误", f"坐标转换失败：\n{e}")
            self.status_label.config(text="转换失败")

    def clear_all(self):
        """清空所有输入输出"""
        self.lon_entry.delete(0, tk.END)
        self.lat_entry.delete(0, tk.END)
        self.batch_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.status_label.config(text="已清空")

    def import_coordinates(self):
        """导入坐标文件"""
        from tkinter import filedialog
        
        filename = filedialog.askopenfilename(
            title="选择坐标文件",
            filetypes=[
                ("文本文件", "*.txt"),
                ("CSV文件", "*.csv"),
                ("所有文件", "*.*")
            ]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.batch_text.delete("1.0", tk.END)
                self.batch_text.insert("1.0", content)
                self.batch_mode.set(True)
                self.on_mode_changed()
                
                self.status_label.config(text=f"已导入文件: {filename}")
                
            except Exception as e:
                messagebox.showerror("导入错误", f"导入文件失败：\n{e}")

    def export_results(self):
        """导出转换结果"""
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            title="保存转换结果",
            defaultextension=".txt",
            filetypes=[
                ("文本文件", "*.txt"),
                ("CSV文件", "*.csv"),
                ("所有文件", "*.*")
            ]
        )
        
        if filename:
            try:
                content = self.output_text.get("1.0", tk.END)
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.status_label.config(text=f"结果已保存到: {filename}")
                
            except Exception as e:
                messagebox.showerror("导出错误", f"导出文件失败：\n{e}")

    def show_history(self):
        """显示历史记录"""
        if not self.conversion_history:
            messagebox.showinfo("历史记录", "暂无转换历史记录")
            return
        
        history_window = tk.Toplevel(self.window)
        history_window.title("转换历史记录")
        history_window.geometry("600x400")
        
        # 创建历史记录列表
        frame = ttk.Frame(history_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 列表框
        listbox = tk.Listbox(frame, height=15)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        
        for i, record in enumerate(self.conversion_history, 1):
            text = f"{i}. {record['source_system']} → {record['target_system']} ({record['input_count']}个点)"
            listbox.insert(tk.END, text)
        
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 详情按钮
        def show_detail():
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                record = self.conversion_history[index]
                
                detail_text = f"转换详情:\n\n"
                detail_text += f"源坐标系: {record['source_system']}\n"
                detail_text += f"目标坐标系: {record['target_system']}\n"
                detail_text += f"转换点数: {record['input_count']}\n\n"
                detail_text += "转换结果:\n"
                
                for i, (src, dst) in enumerate(zip(record['coordinates'], record['converted']), 1):
                    detail_text += f"{i}. [{src[0]:.6f}, {src[1]:.6f}] → [{dst[0]:.6f}, {dst[1]:.6f}]\n"
                
                messagebox.showinfo("转换详情", detail_text)
        
        detail_btn = ttk.Button(history_window, text="查看详情", command=show_detail)
        detail_btn.pack(pady=10)

    def center_window(self):
        """居中显示窗口"""
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
