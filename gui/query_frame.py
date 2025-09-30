"""
SQL查询GUI面板
提供SQL查询输入、执行和结果预览的图形界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import pandas as pd
from typing import Optional, Callable

from core.mysql_connector import MySQLConnector
from config.mysql_config import MySQLConfig


class QueryFrame(tk.Frame):
    """SQL查询面板"""

    def __init__(self, parent, config: MySQLConfig, on_query_executed: Optional[Callable] = None):
        """
        初始化查询面板

        Args:
            parent: 父窗口
            config: MySQL配置对象
            on_query_executed: 查询执行完成回调函数
        """
        super().__init__(parent)

        self.config = config
        self.connector = MySQLConnector(config)
        self.on_query_executed = on_query_executed
        self.current_dataframe: Optional[pd.DataFrame] = None

        self.create_widgets()

    def create_widgets(self):
        """创建界面组件"""
        # 标题
        title_label = tk.Label(self, text="SQL查询", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(10, 20))

        # 查询编辑区域
        query_frame = tk.LabelFrame(self, text="SQL查询语句", padx=5, pady=5)
        query_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

        self.query_text = scrolledtext.ScrolledText(
            query_frame,
            width=80,
            height=15,
            font=("Consolas", 11),
            wrap=tk.NONE
        )
        self.query_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 按钮区域
        button_frame = tk.Frame(self)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)

        # 执行查询按钮
        self.execute_button = tk.Button(
            button_frame,
            text="执行查询",
            command=self.execute_query,
            bg="#4CAF50",
            fg="white",
            padx=20,
            font=("Arial", 10, "bold")
        )
        self.execute_button.grid(row=0, column=0, padx=5)

        # 验证语法按钮
        validate_button = tk.Button(
            button_frame,
            text="验证语法",
            command=self.validate_syntax,
            bg="#2196F3",
            fg="white",
            padx=15
        )
        validate_button.grid(row=0, column=1, padx=5)

        # 清空按钮
        clear_button = tk.Button(
            button_frame,
            text="清空",
            command=self.clear_query,
            bg="#FF9800",
            fg="white",
            padx=15
        )
        clear_button.grid(row=0, column=2, padx=5)

        # 示例查询按钮
        example_button = tk.Button(
            button_frame,
            text="示例查询",
            command=self.load_example_query,
            bg="#9C27B0",
            fg="white",
            padx=15
        )
        example_button.grid(row=0, column=3, padx=5)

        # 结果区域
        result_frame = tk.LabelFrame(self, text="查询结果", padx=5, pady=5)
        result_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

        # 创建Treeview来显示结果
        self.result_tree = ttk.Treeview(result_frame)
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 滚动条
        v_scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_tree.configure(yscrollcommand=v_scrollbar.set)

        h_scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.result_tree.xview)
        h_scrollbar.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 5))
        self.result_tree.configure(xscrollcommand=h_scrollbar.set)

        # 状态栏
        status_frame = tk.Frame(self)
        status_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

        self.status_label = tk.Label(status_frame, text="准备就绪", fg="green", anchor="w")
        self.status_label.pack(side=tk.LEFT)

        self.record_count_label = tk.Label(status_frame, text="", anchor="e")
        self.record_count_label.pack(side=tk.RIGHT)

        # 配置权重
        self.rowconfigure(1, weight=1)
        self.rowconfigure(3, weight=2)
        self.columnconfigure(0, weight=1)

        # 添加右键菜单
        self.create_context_menu()

    def create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="复制", command=self.copy_selected)
        self.context_menu.add_command(label="复制所有", command=self.copy_all)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="导出为CSV", command=self.export_to_csv)

        self.result_tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        """显示右键菜单"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def copy_selected(self):
        """复制选中的内容"""
        try:
            selected_items = self.result_tree.selection()
            if selected_items:
                # 获取选中行的数据
                data = []
                for item in selected_items:
                    values = self.result_tree.item(item, 'values')
                    data.append('\t'.join(map(str, values)))

                # 复制到剪贴板
                import pyperclip
                pyperclip.copy('\n'.join(data))
                messagebox.showinfo("复制成功", f"已复制 {len(data)} 行数据到剪贴板")
        except ImportError:
            messagebox.showwarning("功能不可用", "需要安装 pyperclip 库来使用复制功能")
        except Exception as e:
            messagebox.showerror("复制失败", f"复制数据时发生错误：\n{e}")

    def copy_all(self):
        """复制所有数据"""
        try:
            # 获取表头
            columns = self.result_tree['columns']
            header = '\t'.join(columns)

            # 获取所有数据
            data = []
            for item in self.result_tree.get_children():
                values = self.result_tree.item(item, 'values')
                data.append('\t'.join(map(str, values)))

            # 复制到剪贴板
            import pyperclip
            pyperclip.copy(header + '\n' + '\n'.join(data))
            messagebox.showinfo("复制成功", f"已复制表头和 {len(data)} 行数据到剪贴板")
        except ImportError:
            messagebox.showwarning("功能不可用", "需要安装 pyperclip 库来使用复制功能")
        except Exception as e:
            messagebox.showerror("复制失败", f"复制数据时发生错误：\n{e}")

    def export_to_csv(self):
        """导出为CSV文件"""
        if self.current_dataframe is None or self.current_dataframe.empty:
            messagebox.showwarning("导出失败", "没有可导出的数据")
            return

        try:
            from tkinter import filedialog
            import os

            filename = filedialog.asksaveasfilename(
                title="保存CSV文件",
                defaultextension=".csv",
                filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
                initialdir=os.getcwd()
            )

            if filename:
                self.current_dataframe.to_csv(filename, index=False, encoding='utf-8-sig')
                messagebox.showinfo("导出成功", f"数据已导出到：\n{filename}")
        except Exception as e:
            messagebox.showerror("导出失败", f"导出CSV文件时发生错误：\n{e}")

    def execute_query(self):
        """执行SQL查询"""
        query = self.query_text.get("1.0", tk.END).strip()

        if not query:
            messagebox.showwarning("查询为空", "请输入SQL查询语句")
            return

        
        # 更新状态
        self.status_label.config(text="正在执行查询...", fg="orange")
        self.execute_button.config(state=tk.DISABLED)
        self.update()

        try:
            # 执行查询
            self.current_dataframe = self.connector.execute_query(query)

            
            if self.current_dataframe.empty:
                self.status_label.config(text="查询结果为空", fg="orange")
                self.record_count_label.config(text="0 行")
                self.clear_results()
            else:
                self.display_results(self.current_dataframe)
                self.status_label.config(text="查询执行成功", fg="green")
                self.record_count_label.config(text=f"{len(self.current_dataframe)} 行")

                # 调用回调函数
                if self.on_query_executed:
                    self.on_query_executed(self.current_dataframe)

        except Exception as e:
            self.status_label.config(text="查询执行失败", fg="red")
            self.record_count_label.config(text="")
            messagebox.showerror("查询错误", f"执行查询时发生错误：\n\n{e}")
            self.clear_results()

        finally:
            self.execute_button.config(state=tk.NORMAL)

    def validate_syntax(self):
        """验证SQL语法"""
        query = self.query_text.get("1.0", tk.END).strip()

        if not query:
            messagebox.showwarning("查询为空", "请输入SQL查询语句")
            return

        try:
            is_valid, message = self.connector.validate_query(query)

            if is_valid:
                messagebox.showinfo("语法验证", "SQL语法正确")
                self.status_label.config(text="语法验证通过", fg="green")
            else:
                messagebox.showerror("语法错误", f"SQL语法错误：\n\n{message}")
                self.status_label.config(text="语法验证失败", fg="red")

        except Exception as e:
            messagebox.showerror("验证错误", f"验证SQL语法时发生错误：\n\n{e}")
            self.status_label.config(text="语法验证失败", fg="red")

    def clear_query(self):
        """清空查询语句"""
        self.query_text.delete("1.0", tk.END)
        self.status_label.config(text="查询已清空", fg="gray")

    def clear_results(self):
        """清空结果表格"""
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

    def display_results(self, df: pd.DataFrame, max_rows: int = 1000):
        """
        在表格中显示查询结果

        Args:
            df: 要显示的DataFrame
            max_rows: 最大显示行数
        """
        # 清空现有结果
        self.clear_results()

        # 设置列
        columns = list(df.columns)
        self.result_tree['columns'] = columns
        self.result_tree['show'] = 'headings'

        # 设置列标题
        for col in columns:
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=100, minwidth=50)

        # 插入数据
        display_df = df.head(max_rows) if len(df) > max_rows else df

        for _, row in display_df.iterrows():
            values = [str(value) if pd.notna(value) else "NULL" for value in row]
            self.result_tree.insert('', tk.END, values=values)

        # 如果数据被截断，显示提示
        if len(df) > max_rows:
            self.result_tree.insert('', tk.END, values=[f"... (共 {len(df)} 行，只显示前 {max_rows} 行)"] + [''] * (len(columns) - 1))

    def load_example_query(self):
        """加载示例查询"""
        example_queries = {
            "查看所有表": "SHOW TABLES",
            "查看表结构": "DESCRIBE your_table_name",
            "基本查询": "SELECT * FROM your_table_name LIMIT 10",
            "条件查询": "SELECT * FROM your_table_name WHERE condition_column = 'value' LIMIT 10",
            "查找坐标字段": """SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = DATABASE()
    AND (column_name LIKE '%coord%'
         OR column_name LIKE '%geo%'
         OR column_name LIKE '%point%'
         OR column_name LIKE '%location%')
ORDER BY table_name, column_name""",
            "查看示例数据": """SELECT
    id,
    name,
    coordinates
FROM your_table_name
WHERE coordinates IS NOT NULL
    AND coordinates != ''
LIMIT 5""",
            "测试你的坐标": """SELECT
    id,
    name,
    '[[111.987608,34.192642],[111.986551,34.193325],[111.985826,34.194013],[111.984814,34.194998],[111.983828,34.195668],[111.982845,34.196038],[111.982693,34.195756],[111.983549,34.195319],[111.984446,34.194554],[111.985276,34.193613],[111.985877,34.192947],[111.986298,34.192318],[111.987608,34.192642]]' as test_coordinates
FROM dual"""
        }

        # 创建选择对话框
        dialog = tk.Toplevel(self)
        dialog.title("选择示例查询")
        dialog.geometry("400x300")
        dialog.resizable(False, False)

        tk.Label(dialog, text="选择一个示例查询：", font=("Arial", 12)).pack(pady=10)

        listbox = tk.Listbox(dialog, height=len(example_queries))
        listbox.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        for name in example_queries.keys():
            listbox.insert(tk.END, name)

        def load_selected():
            selection = listbox.curselection()
            if selection:
                selected_name = list(selection)[0]
                query_name = list(example_queries.keys())[selected_name]
                query_text = example_queries[query_name]

                self.query_text.delete("1.0", tk.END)
                self.query_text.insert("1.0", query_text)
                self.status_label.config(text=f"已加载示例查询: {query_name}", fg="blue")

            dialog.destroy()

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="加载", command=load_selected, bg="#4CAF50", fg="white", padx=20).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="取消", command=dialog.destroy, bg="#F44336", fg="white", padx=20).pack(side=tk.LEFT, padx=5)

    def get_current_dataframe(self) -> Optional[pd.DataFrame]:
        """获取当前查询结果DataFrame"""
        return self.current_dataframe

    def set_query(self, query: str):
        """设置查询语句"""
        self.query_text.delete("1.0", tk.END)
        self.query_text.insert("1.0", query)

    def update_config(self, config: MySQLConfig):
        """更新数据库配置"""
        self.config = config
        self.connector = MySQLConnector(config)
        self.status_label.config(text="数据库配置已更新", fg="blue")


if __name__ == "__main__":
    # 测试代码
    root = tk.Tk()
    root.title("SQL查询测试")
    root.geometry("900x700")

    # 创建配置对象（测试用）
    config = MySQLConfig()

    # 创建查询面板
    query_frame = QueryFrame(root, config)
    query_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    root.mainloop()