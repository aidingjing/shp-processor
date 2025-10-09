"""
主窗口GUI模块
整合所有功能面板，提供完整的用户界面
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from typing import Optional

from config.mysql_config import MySQLConfig
from gui.database_config_frame import DatabaseConfigFrame
from gui.query_frame import QueryFrame
from gui.field_selection_frame import FieldSelectionFrame
from gui.export_frame import ExportFrame
from gui.shapefile_merger_dialog import ShapefileMergerDialog


class MainWindow:
    """主窗口类"""

    def __init__(self):
        """初始化主窗口"""
        self.root = tk.Tk()
        self.root.title("SHP文件处理工具 - MySQL数据导出")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)

        # 设置窗口图标（如果有的话）
        try:
            # self.root.iconbitmap("icon.ico")  # 如果有图标文件
            pass
        except:
            pass

        # 配置对象
        self.config = MySQLConfig()

        # 当前数据
        self.current_dataframe: Optional[pd.DataFrame] = None
        self.selected_field: Optional[str] = None
        self.geometry_type: str = "auto"

        # 创建界面
        self.create_widgets()
        self.create_menu()
        self.create_status_bar()

        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        """创建主界面组件"""
        # 创建主框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建左侧步骤导航面板
        self.create_step_panel(main_frame)

        # 创建右侧内容面板（使用Notebook）
        self.create_content_panel(main_frame)

    def create_step_panel(self, parent):
        """创建步骤导航面板"""
        step_frame = tk.LabelFrame(parent, text="操作步骤", padx=10, pady=10)
        step_frame.grid(row=0, column=0, sticky="ns", padx=(0, 10))

        # 步骤列表
        self.steps = [
            {"name": "1. 数据库配置", "status": "pending", "panel": "config"},
            {"name": "2. SQL查询", "status": "pending", "panel": "query"},
            {"name": "3. 字段选择", "status": "pending", "panel": "field"},
            {"name": "4. 导出配置", "status": "pending", "panel": "export"}
        ]

        self.step_labels = []
        self.step_indicators = []

        for i, step in enumerate(self.steps):
            # 步骤指示器
            indicator_frame = tk.Frame(step_frame)
            indicator_frame.pack(fill=tk.X, pady=5)

            # 状态指示圆圈
            indicator = tk.Canvas(indicator_frame, width=20, height=20, highlightthickness=0)
            indicator.pack(side=tk.LEFT, padx=(0, 10))
            self.draw_step_indicator(indicator, "pending")

            # 步骤名称
            label = tk.Label(indicator_frame, text=step["name"], font=("Arial", 10), anchor="w")
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # 绑定点击事件
            for widget in [indicator, label]:
                widget.bind("<Button-1>", lambda e, idx=i: self.switch_to_step(idx))
                widget.config(cursor="hand2")

            self.step_indicators.append(indicator)
            self.step_labels.append(label)

        # 添加间距
        tk.Frame(step_frame, height=20).pack()

        # 当前步骤信息
        info_frame = tk.LabelFrame(step_frame, text="当前状态", padx=10, pady=10)
        info_frame.pack(fill=tk.X, pady=10)

        self.status_text = tk.Text(info_frame, height=8, width=25, wrap=tk.WORD, state=tk.DISABLED)
        self.status_text.pack()

        # 操作提示
        tip_frame = tk.LabelFrame(step_frame, text="操作提示", padx=10, pady=10)
        tip_frame.pack(fill=tk.X, pady=10)

        self.tip_label = tk.Label(tip_frame, text="请先配置数据库连接", wraplength=200, justify=tk.LEFT)
        self.tip_label.pack()

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
        # 使用Notebook来管理不同的面板
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=0, column=1, sticky="nsew")

        # 创建各个功能面板
        self.config_frame = DatabaseConfigFrame(self.notebook, self.config, self.on_config_changed)
        self.query_frame = QueryFrame(self.notebook, self.config, self.on_query_executed)
        self.field_frame = FieldSelectionFrame(self.notebook, self.on_field_selected)
        self.export_frame = ExportFrame(self.notebook, self.on_export_completed)

        # 添加到Notebook
        self.notebook.add(self.config_frame, text="数据库配置")
        self.notebook.add(self.query_frame, text="SQL查询")
        self.notebook.add(self.field_frame, text="字段选择")
        self.notebook.add(self.export_frame, text="导出配置")

        # 配置权重
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)

        # 初始状态：只启用第一个标签页
        self.update_tab_states()

        # 绑定标签页切换事件
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="新建项目", command=self.new_project)
        file_menu.add_command(label="打开配置", command=self.open_config)
        file_menu.add_command(label="保存配置", command=self.save_config)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_closing)

        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="SHP文件合并工具", command=self.show_shp_merger)
        tools_menu.add_separator()
        tools_menu.add_command(label="坐标转换工具", command=self.show_coordinate_converter)
        tools_menu.add_command(label="SHP文件查看器", command=self.show_shp_viewer)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)

    def create_status_bar(self):
        """创建状态栏"""
        status_frame = tk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # 连接状态
        self.connection_status = tk.Label(status_frame, text="未连接", fg="red", padx=10)
        self.connection_status.pack(side=tk.LEFT)

        # 分隔符
        ttk.Separator(status_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # 数据状态
        self.data_status = tk.Label(status_frame, text="无数据", fg="gray", padx=10)
        self.data_status.pack(side=tk.LEFT)

        # 分隔符
        ttk.Separator(status_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # 版本信息
        version_label = tk.Label(status_frame, text="v1.0.0", fg="gray", padx=10)
        version_label.pack(side=tk.RIGHT)

    def update_step_status(self, step_index: int, status: str):
        """更新步骤状态"""
        if 0 <= step_index < len(self.steps):
            self.steps[step_index]["status"] = status
            self.draw_step_indicator(self.step_indicators[step_index], status)

            # 更新标签颜色
            if status == "completed":
                self.step_labels[step_index].config(fg="#4CAF50")
            elif status == "current":
                self.step_labels[step_index].config(fg="#2196F3", font=("Arial", 10, "bold"))
            elif status == "error":
                self.step_labels[step_index].config(fg="#F44336")
            else:
                self.step_labels[step_index].config(fg="gray", font=("Arial", 10))

    def switch_to_step(self, step_index: int):
        """切换到指定步骤"""
        if 0 <= step_index < len(self.steps):
            self.notebook.select(step_index)

    def update_tab_states(self):
        """更新标签页状态"""
        # 检查每个步骤是否可以访问
        for i, step in enumerate(self.steps):
            if i == 0:
                # 第一步总是可以访问
                self.notebook.tab(i, state="normal")
            elif step["status"] == "completed":
                # 已完成的步骤可以访问
                self.notebook.tab(i, state="normal")
            elif i > 0 and self.steps[i-1]["status"] == "completed":
                # 前一步已完成的可以访问
                self.notebook.tab(i, state="normal")
            else:
                # 其他情况禁用
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

        # 更新提示信息
        tips = [
            "配置MySQL数据库连接参数，点击'测试连接'验证配置",
            "编写SQL查询语句，获取包含空间坐标的数据",
            "选择包含空间坐标的字段，系统会自动分析数据格式",
            "配置导出参数，选择坐标系和输出路径，开始导出SHP文件"
        ]

        if current_tab < len(tips):
            self.tip_label.config(text=tips[current_tab])

    def on_config_changed(self):
        """数据库配置变更事件"""
        try:
            # 测试连接
            success, message = self.config.test_connection()

            if success:
                self.update_step_status(0, "completed")
                self.connection_status.config(text="已连接", fg="green")
                self.update_status_text("数据库配置成功，可以执行SQL查询")
                self.update_tip("数据库连接成功，请编写SQL查询语句获取数据")
            else:
                self.update_step_status(0, "error")
                self.connection_status.config(text="连接失败", fg="red")
                self.update_status_text(f"数据库配置失败: {message}")
                self.update_tip(f"数据库连接失败: {message}")

        except Exception as e:
            self.update_step_status(0, "error")
            self.connection_status.config(text="错误", fg="red")
            self.update_status_text(f"配置错误: {e}")

        self.update_tab_states()

    def on_query_executed(self, df: pd.DataFrame):
        """SQL查询执行完成事件"""
        self.current_dataframe = df

        if df is not None and not df.empty:
            self.update_step_status(1, "completed")
            self.data_status.config(text=f"{len(df)} 行数据", fg="green")
            self.update_status_text(f"查询成功，获取 {len(df)} 行数据")
            self.update_tip("查询成功！请在字段选择面板中选择坐标字段")

            # 自动切换到字段选择面板
            self.notebook.select(2)

            # 设置字段选择面板的数据
            self.field_frame.set_dataframe(df)
        else:
            self.update_step_status(1, "error")
            self.data_status.config(text="无数据", fg="red")
            self.update_status_text("查询结果为空或失败")

        self.update_tab_states()

    def on_field_selected(self, field_name: str, geometry_type: str, analysis: dict):
        """字段选择完成事件"""
        self.selected_field = field_name
        self.geometry_type = geometry_type

        if field_name and analysis.get('success_rate', 0) > 0:
            self.update_step_status(2, "completed")
            self.update_status_text(f"已选择字段: {field_name}, 几何类型: {geometry_type}")
            self.update_tip("字段选择完成！请在导出配置面板中设置导出参数")

            # 设置导出面板数据
            self.export_frame.set_export_data(self.current_dataframe, field_name, geometry_type)

            # 自动切换到导出面板
            self.notebook.select(3)
        else:
            self.update_step_status(2, "error")
            self.update_status_text("字段选择失败")

        self.update_tab_states()

    def on_export_completed(self, output_path: str):
        """导出完成事件"""
        self.update_step_status(3, "completed")
        self.update_status_text(f"导出成功: {output_path}")
        self.update_tip("导出完成！您可以开始新的导出任务")

    def update_status_text(self, message: str):
        """更新状态文本"""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete("1.0", tk.END)
        self.status_text.insert("1.0", message)
        self.status_text.config(state=tk.DISABLED)

    def update_tip(self, tip: str):
        """更新提示信息"""
        self.tip_label.config(text=tip)

    # 菜单功能方法
    def new_project(self):
        """新建项目"""
        if messagebox.askyesno("新建项目", "确定要新建项目吗？当前配置将不会保存。"):
            # 重置所有状态
            for i in range(len(self.steps)):
                self.update_step_status(i, "pending")

            self.current_dataframe = None
            self.selected_field = None
            self.geometry_type = "auto"

            # 重置连接器
            self.query_frame.update_config(self.config)

            # 切换到第一步
            self.notebook.select(0)
            self.update_tab_states()

            self.connection_status.config(text="未连接", fg="red")
            self.data_status.config(text="无数据", fg="gray")
            self.update_status_text("已重置为新建项目状态")

    def open_config(self):
        """打开配置"""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )

        if filename:
            try:
                self.config.config_file = filename
                self.config.load_config()

                # 更新界面
                self.config_frame.load_current_config()
                self.query_frame.update_config(self.config)

                messagebox.showinfo("成功", "配置文件加载成功")
            except Exception as e:
                messagebox.showerror("错误", f"加载配置文件失败：\n{e}")

    def save_config(self):
        """保存配置"""
        try:
            if self.config.save_config():
                messagebox.showinfo("成功", "配置文件保存成功")
            else:
                messagebox.showerror("错误", "保存配置文件失败")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置文件失败：\n{e}")

    def show_coordinate_converter(self):
        """显示坐标转换工具"""
        messagebox.showinfo("功能开发中", "坐标转换工具正在开发中...")

    def show_shp_viewer(self):
        """显示SHP文件查看器"""
        messagebox.showinfo("功能开发中", "SHP文件查看器正在开发中...")

    def show_shp_merger(self):
        """显示SHP文件合并工具"""
        try:
            merger_dialog = ShapefileMergerDialog(self.root)
            self.root.wait_window(merger_dialog.window)
        except Exception as e:
            messagebox.showerror("错误", f"打开SHP文件合并工具失败：\n{e}")

    def show_help(self):
        """显示帮助信息"""
        help_text = """
SHP文件处理工具使用说明：

1. 数据库配置
   - 配置MySQL数据库连接参数
   - 测试连接确保配置正确

2. SQL查询
   - 编写SQL查询语句获取数据
   - 确保查询结果包含空间坐标字段

3. 字段选择
   - 选择包含空间坐标的字段
   - 系统会自动分析坐标格式
   - 确认几何类型（点/线/面）

4. 导出配置
   - 设置输出文件路径
   - 选择合适的坐标系
   - 执行导出操作

注意事项：
- 坐标字段格式应为：[[经度,纬度],...]
- 支持多种几何类型自动识别
- 导出的SHP文件可用QGIS等软件打开

更多详细信息请参考用户手册。
        """

        help_window = tk.Toplevel(self.root)
        help_window.title("使用说明")
        help_window.geometry("600x500")
        help_window.resizable(False, False)

        text_widget = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert("1.0", help_text)
        text_widget.config(state=tk.DISABLED)

        close_button = tk.Button(help_window, text="关闭", command=help_window.destroy, padx=20)
        close_button.pack(pady=10)

    def show_about(self):
        """显示关于信息"""
        about_text = """
SHP文件处理工具 v1.0.0

一个用于从MySQL数据库导出空间数据到SHP文件的工具。

主要功能：
• MySQL数据库连接和查询
• 空间坐标数据解析
• 多种几何类型支持（点/线/面）
• SHP文件导出
• 图形化操作界面

开发语言：Python
界面框架：Tkinter
GIS库：GeoPandas, Shapely

版权所有 © 2024
        """

        messagebox.showinfo("关于", about_text)

    def on_closing(self):
        """窗口关闭事件"""
        if messagebox.askokcancel("退出", "确定要退出程序吗？"):
            self.root.destroy()

    def run(self):
        """运行主窗口"""
        # 初始状态
        self.update_status_text("欢迎使用SHP文件处理工具！\n请先配置数据库连接参数。")
        self.update_tip("请开始配置数据库连接")

        # 启动主循环
        self.root.mainloop()


if __name__ == "__main__":
    # 创建并运行主窗口
    app = MainWindow()
    app.run()