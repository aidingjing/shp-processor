"""
数据库配置GUI面板
提供MySQL数据库连接配置的图形界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from typing import Optional, Callable

from config.mysql_config import MySQLConfig


class DatabaseConfigFrame(tk.Frame):
    """数据库配置面板"""

    def __init__(self, parent, config: MySQLConfig, on_config_changed: Optional[Callable] = None):
        """
        初始化数据库配置面板

        Args:
            parent: 父窗口
            config: MySQL配置对象
            on_config_changed: 配置变更回调函数
        """
        super().__init__(parent)

        self.config = config
        self.on_config_changed = on_config_changed

        self.create_widgets()
        self.load_current_config()

    def create_widgets(self):
        """创建界面组件"""
        # 标题
        title_label = tk.Label(self, text="MySQL数据库配置", font=("Arial", 12, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(8, 15))

        # 配置字段
        self.fields = {}

        # 主机地址
        tk.Label(self, text="主机地址:").grid(row=1, column=0, sticky="e", padx=(15, 5), pady=4)
        self.fields['host'] = tk.Entry(self, width=25)
        self.fields['host'].grid(row=1, column=1, padx=(0, 15), pady=4, sticky="ew")

        # 端口号
        tk.Label(self, text="端口号:").grid(row=2, column=0, sticky="e", padx=(15, 5), pady=4)
        self.fields['port'] = tk.Entry(self, width=25)
        self.fields['port'].grid(row=2, column=1, padx=(0, 15), pady=4, sticky="ew")
        self.fields['port'].insert(0, "3306")

        # 用户名
        tk.Label(self, text="用户名:").grid(row=3, column=0, sticky="e", padx=(15, 5), pady=4)
        self.fields['user'] = tk.Entry(self, width=25)
        self.fields['user'].grid(row=3, column=1, padx=(0, 15), pady=4, sticky="ew")

        # 密码
        tk.Label(self, text="密码:").grid(row=4, column=0, sticky="e", padx=(15, 5), pady=4)
        self.fields['password'] = tk.Entry(self, width=25, show="*")
        self.fields['password'].grid(row=4, column=1, padx=(0, 15), pady=4, sticky="ew")

        # 数据库名
        tk.Label(self, text="数据库名:").grid(row=5, column=0, sticky="e", padx=(15, 5), pady=4)
        self.fields['database'] = tk.Entry(self, width=25)
        self.fields['database'].grid(row=5, column=1, padx=(0, 15), pady=4, sticky="ew")

        # 字符集
        tk.Label(self, text="字符集:").grid(row=6, column=0, sticky="e", padx=(15, 5), pady=4)
        self.fields['charset'] = ttk.Combobox(self, width=22, values=["utf8mb4", "utf8", "latin1"])
        self.fields['charset'].grid(row=6, column=1, padx=(0, 15), pady=4, sticky="ew")
        self.fields['charset'].set("utf8mb4")

        # 按钮区域
        button_frame = tk.Frame(self)
        button_frame.grid(row=7, column=0, columnspan=3, pady=15)

        # 测试连接按钮
        self.test_button = tk.Button(button_frame, text="测试连接", command=self.test_connection,
                                   bg="#4CAF50", fg="white", padx=15, font=("Arial", 9))
        self.test_button.grid(row=0, column=0, padx=3)

        # 保存配置按钮
        save_button = tk.Button(button_frame, text="保存配置", command=self.save_config,
                              bg="#2196F3", fg="white", padx=15, font=("Arial", 9))
        save_button.grid(row=0, column=1, padx=3)

        # 加载配置按钮
        load_button = tk.Button(button_frame, text="加载配置", command=self.load_config,
                              bg="#FF9800", fg="white", padx=15, font=("Arial", 9))
        load_button.grid(row=0, column=2, padx=3)

        # 重置按钮
        reset_button = tk.Button(button_frame, text="重置", command=self.reset_config,
                               bg="#F44336", fg="white", padx=15, font=("Arial", 9))
        reset_button.grid(row=0, column=3, padx=3)

        # 状态显示区域
        status_frame = tk.Frame(self)
        status_frame.grid(row=8, column=0, columnspan=3, pady=8, sticky="ew")

        tk.Label(status_frame, text="状态:", font=("Arial", 9)).grid(row=0, column=0, sticky="w", padx=(15, 5))
        self.status_label = tk.Label(status_frame, text="未配置", fg="gray", font=("Arial", 9))
        self.status_label.grid(row=0, column=1, sticky="w")

        # 连接信息显示
        info_frame = tk.Frame(self)
        info_frame.grid(row=9, column=0, columnspan=3, pady=5, sticky="ew")

        tk.Label(info_frame, text="连接信息:", font=("Arial", 9)).grid(row=0, column=0, sticky="w", padx=(15, 5))
        self.info_label = tk.Label(info_frame, text="mysql://", fg="blue", font=("Arial", 8))
        self.info_label.grid(row=0, column=1, sticky="w")

        # 配置列权重
        self.columnconfigure(1, weight=1)

        # 绑定输入事件
        for field in self.fields.values():
            if isinstance(field, tk.Entry):
                field.bind("<KeyRelease>", self.on_field_changed)
            elif isinstance(field, ttk.Combobox):
                field.bind("<<ComboboxSelected>>", self.on_field_changed)

    def load_current_config(self):
        """加载当前配置"""
        config_dict = self.config.get_config()

        for key, value in config_dict.items():
            if key in self.fields:
                self.fields[key].delete(0, tk.END)
                self.fields[key].insert(0, str(value))

        self.update_status()

    def on_field_changed(self, event=None):
        """字段变更事件处理"""
        self.update_connection_info()

    def update_connection_info(self):
        """更新连接信息显示"""
        try:
            config_dict = self.get_current_config()
            if config_dict['user'] and config_dict['host']:
                password_mask = "*" * len(config_dict['password']) if config_dict['password'] else ""
                connection_string = f"mysql://{config_dict['user']}:{password_mask}@{config_dict['host']}:{config_dict['port']}/{config_dict['database']}"
                self.info_label.config(text=connection_string)
            else:
                self.info_label.config(text="mysql://")
        except Exception:
            self.info_label.config(text="mysql://")

    def get_current_config(self) -> dict:
        """获取当前配置"""
        return {
            'host': self.fields['host'].get().strip(),
            'port': int(self.fields['port'].get().strip()) if self.fields['port'].get().strip() else 3306,
            'user': self.fields['user'].get().strip(),
            'password': self.fields['password'].get(),
            'database': self.fields['database'].get().strip(),
            'charset': self.fields['charset'].get()
        }

    def test_connection(self):
        """测试数据库连接"""
        try:
            config_dict = self.get_current_config()

            # 验证配置
            self.config.update_config(**config_dict)
            is_valid, error_msg = self.config.validate_config()

            if not is_valid:
                messagebox.showerror("配置错误", error_msg)
                return

            # 更新状态
            self.status_label.config(text="正在测试连接...", fg="orange")
            self.test_button.config(state=tk.DISABLED)
            self.update()

            # 执行连接测试
            success, result = self.config.test_connection()

            if success:
                self.status_label.config(text="连接成功", fg="green")
                messagebox.showinfo("连接测试", f"数据库连接成功！\n\n{result}")
            else:
                self.status_label.config(text="连接失败", fg="red")
                messagebox.showerror("连接测试", f"数据库连接失败！\n\n{result}")

        except Exception as e:
            self.status_label.config(text="测试失败", fg="red")
            messagebox.showerror("连接测试", f"测试过程中发生错误：\n\n{e}")
        finally:
            self.test_button.config(state=tk.NORMAL)

    def save_config(self):
        """保存配置"""
        try:
            config_dict = self.get_current_config()
            self.config.update_config(**config_dict)

            if self.config.save_config():
                self.status_label.config(text="配置已保存", fg="green")
                messagebox.showinfo("保存配置", "配置已成功保存到文件！")

                if self.on_config_changed:
                    self.on_config_changed()
            else:
                self.status_label.config(text="保存失败", fg="red")
                messagebox.showerror("保存配置", "保存配置到文件失败！")

        except Exception as e:
            self.status_label.config(text="保存失败", fg="red")
            messagebox.showerror("保存配置", f"保存配置时发生错误：\n\n{e}")

    def load_config(self):
        """加载配置文件"""
        try:
            filename = filedialog.askopenfilename(
                title="选择配置文件",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
                initialdir=os.getcwd()
            )

            if filename:
                # 临时更改配置文件路径并加载
                original_file = self.config.config_file
                self.config.config_file = filename
                self.config.load_config()
                self.config.config_file = original_file

                # 更新界面
                self.load_current_config()
                self.status_label.config(text="配置已加载", fg="green")
                messagebox.showinfo("加载配置", "配置已成功加载！")

                if self.on_config_changed:
                    self.on_config_changed()

        except Exception as e:
            self.status_label.config(text="加载失败", fg="red")
            messagebox.showerror("加载配置", f"加载配置时发生错误：\n\n{e}")

    def reset_config(self):
        """重置配置"""
        if messagebox.askyesno("重置配置", "确定要重置所有配置吗？"):
            # 清空所有字段
            for field_name, field in self.fields.items():
                if field_name == 'port':
                    field.delete(0, tk.END)
                    field.insert(0, "3306")
                elif field_name == 'charset':
                    field.set("utf8mb4")
                else:
                    field.delete(0, tk.END)

            self.status_label.config(text="配置已重置", fg="gray")
            self.update_connection_info()

    def update_status(self):
        """更新状态显示"""
        try:
            config_dict = self.get_current_config()
            is_valid, _ = self.config.validate_config()

            if is_valid:
                self.status_label.config(text="配置有效", fg="green")
            else:
                self.status_label.config(text="配置不完整", fg="orange")

            self.update_connection_info()

        except Exception:
            self.status_label.config(text="配置错误", fg="red")

    def get_config(self) -> MySQLConfig:
        """获取配置对象"""
        config_dict = self.get_current_config()
        self.config.update_config(**config_dict)
        return self.config


if __name__ == "__main__":
    # 测试代码
    root = tk.Tk()
    root.title("数据库配置测试")
    root.geometry("500x400")

    # 创建配置对象
    config = MySQLConfig()

    # 创建配置面板
    config_frame = DatabaseConfigFrame(root, config)
    config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    root.mainloop()
