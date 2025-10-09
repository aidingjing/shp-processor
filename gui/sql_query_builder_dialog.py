"""
SQL查询构建器对话框
提供可视化SQL查询构建功能
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
from typing import List, Dict, Optional, Tuple
import re


class SQLQueryBuilderDialog:
    """SQL查询构建器对话框"""

    def __init__(self, parent, config=None):
        """初始化SQL查询构建器对话框"""
        self.parent = parent
        self.config = config
        self.window = tk.Toplevel(parent)
        self.window.title("SQL查询构建器")
        self.window.geometry("1000x700")
        self.window.resizable(True, True)
        self.window.transient(parent)
        self.window.grab_set()

        # 查询组件
        self.tables = []
        self.columns = {}
        self.joins = []
        self.where_conditions = []
        self.group_by_columns = []
        self.having_conditions = []
        self.order_by_columns = []

        # 查询类型
        self.query_type = tk.StringVar(value="SELECT")

        self.create_widgets()
        self.center_window()

    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建标题
        title_label = tk.Label(main_frame, text="SQL查询构建器", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))

        # 创建工具栏
        self.create_toolbar(main_frame)

        # 创建主要内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 左侧：查询构建面板
        self.create_builder_panel(content_frame)

        # 右侧：SQL预览面板
        self.create_preview_panel(content_frame)

        # 创建按钮区域
        self.create_button_panel(main_frame)

        # 创建状态栏
        self.create_status_bar(main_frame)

    def create_toolbar(self, parent):
        """创建工具栏"""
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))

        # 查询类型选择
        ttk.Label(toolbar_frame, text="查询类型:").pack(side=tk.LEFT, padx=(0, 5))
        query_type_combo = ttk.Combobox(toolbar_frame, textvariable=self.query_type, 
                                       values=["SELECT", "INSERT", "UPDATE", "DELETE"], 
                                       width=15, state="readonly")
        query_type_combo.pack(side=tk.LEFT, padx=(0, 20))
        query_type_combo.bind("<<ComboboxSelected>>", self.on_query_type_changed)

        # 数据库连接按钮
        if self.config:
            connect_btn = ttk.Button(toolbar_frame, text="获取数据库结构", command=self.load_database_structure)
            connect_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 模板按钮
        template_btn = ttk.Button(toolbar_frame, text="加载模板", command=self.load_template)
        template_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 清空按钮
        clear_btn = ttk.Button(toolbar_frame, text="清空查询", command=self.clear_query)
        clear_btn.pack(side=tk.LEFT)

    def create_builder_panel(self, parent):
        """创建查询构建面板"""
        builder_frame = ttk.LabelFrame(parent, text="查询构建", padding="10")
        builder_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # 创建Notebook用于不同的查询部分
        self.builder_notebook = ttk.Notebook(builder_frame)
        self.builder_notebook.pack(fill=tk.BOTH, expand=True)

        # SELECT查询面板
        self.create_select_panel()
        
        # WHERE条件面板
        self.create_where_panel()
        
        # GROUP BY面板
        self.create_group_by_panel()
        
        # ORDER BY面板
        self.create_order_by_panel()

    def create_select_panel(self):
        """创建SELECT查询面板"""
        select_frame = ttk.Frame(self.builder_notebook)
        self.builder_notebook.add(select_frame, text="SELECT")

        # 表选择区域
        table_frame = ttk.LabelFrame(select_frame, text="表选择", padding="5")
        table_frame.pack(fill=tk.X, pady=(0, 10))

        # 表列表
        self.table_listbox = tk.Listbox(table_frame, height=6, selectmode=tk.MULTIPLE)
        table_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.table_listbox.yview)
        self.table_listbox.configure(yscrollcommand=table_scrollbar.set)

        self.table_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        table_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 双击添加表
        self.table_listbox.bind("<Double-Button-1>", self.add_table)

        # 表操作按钮
        table_btn_frame = ttk.Frame(table_frame)
        table_btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(table_btn_frame, text="添加表", command=self.add_table).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(table_btn_frame, text="移除表", command=self.remove_table).pack(side=tk.LEFT)

        # 列选择区域
        column_frame = ttk.LabelFrame(select_frame, text="列选择", padding="5")
        column_frame.pack(fill=tk.BOTH, expand=True)

        # 已选列列表
        selected_column_frame = ttk.Frame(column_frame)
        selected_column_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(selected_column_frame, text="已选择列:").pack(anchor=tk.W)

        # 列列表框架
        column_list_frame = ttk.Frame(selected_column_frame)
        column_list_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        self.column_listbox = tk.Listbox(column_list_frame, height=8)
        column_scrollbar = ttk.Scrollbar(column_list_frame, orient=tk.VERTICAL, command=self.column_listbox.yview)
        self.column_listbox.configure(yscrollcommand=column_scrollbar.set)

        self.column_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        column_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 列操作按钮
        column_btn_frame = ttk.Frame(selected_column_frame)
        column_btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(column_btn_frame, text="添加列", command=self.add_column).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(column_btn_frame, text="移除列", command=self.remove_column).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(column_btn_frame, text="全选", command=self.select_all_columns).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(column_btn_frame, text="移除全部", command=self.clear_columns).pack(side=tk.LEFT)

        # 别名输入
        alias_frame = ttk.Frame(selected_column_frame)
        alias_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(alias_frame, text="列别名:").pack(side=tk.LEFT)
        self.column_alias_entry = ttk.Entry(alias_frame, width=20)
        self.column_alias_entry.pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(alias_frame, text="设置别名", command=self.set_column_alias).pack(side=tk.LEFT, padx=(5, 0))

    def create_where_panel(self):
        """创建WHERE条件面板"""
        where_frame = ttk.Frame(self.builder_notebook)
        self.builder_notebook.add(where_frame, text="WHERE")

        # 条件列表
        condition_list_frame = ttk.LabelFrame(where_frame, text="条件列表", padding="5")
        condition_list_frame.pack(fill=tk.BOTH, expand=True)

        # 条件树形视图
        columns = ('字段', '操作符', '值', '连接符')
        self.where_tree = ttk.Treeview(condition_list_frame, columns=columns, show='tree headings', height=10)
        
        for col in columns:
            self.where_tree.heading(col, text=col)
            self.where_tree.column(col, width=120)

        where_scrollbar = ttk.Scrollbar(condition_list_frame, orient=tk.VERTICAL, command=self.where_tree.yview)
        self.where_tree.configure(yscrollcommand=where_scrollbar.set)

        self.where_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        where_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 条件编辑区域
        edit_frame = ttk.LabelFrame(where_frame, text="条件编辑", padding="5")
        edit_frame.pack(fill=tk.X, pady=(10, 0))

        # 字段选择
        field_frame = ttk.Frame(edit_frame)
        field_frame.pack(fill=tk.X, pady=2)
        ttk.Label(field_frame, text="字段:").pack(side=tk.LEFT, padx=(0, 5))
        self.where_field_combo = ttk.Combobox(field_frame, width=20)
        self.where_field_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 操作符选择
        operator_frame = ttk.Frame(edit_frame)
        operator_frame.pack(fill=tk.X, pady=2)
        ttk.Label(operator_frame, text="操作符:").pack(side=tk.LEFT, padx=(0, 5))
        self.where_operator_combo = ttk.Combobox(operator_frame, 
                                               values=["=", "!=", ">", "<", ">=", "<=", "LIKE", "IN", "IS NULL", "IS NOT NULL"], 
                                               width=20)
        self.where_operator_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 值输入
        value_frame = ttk.Frame(edit_frame)
        value_frame.pack(fill=tk.X, pady=2)
        ttk.Label(value_frame, text="值:").pack(side=tk.LEFT, padx=(0, 5))
        self.where_value_entry = ttk.Entry(value_frame, width=20)
        self.where_value_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 连接符选择
        connector_frame = ttk.Frame(edit_frame)
        connector_frame.pack(fill=tk.X, pady=2)
        ttk.Label(connector_frame, text="连接符:").pack(side=tk.LEFT, padx=(0, 5))
        self.where_connector_combo = ttk.Combobox(connector_frame, values=["AND", "OR"], width=20)
        self.where_connector_combo.set("AND")
        self.where_connector_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 条件操作按钮
        condition_btn_frame = ttk.Frame(edit_frame)
        condition_btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(condition_btn_frame, text="添加条件", command=self.add_where_condition).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(condition_btn_frame, text="更新条件", command=self.update_where_condition).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(condition_btn_frame, text="删除条件", command=self.remove_where_condition).pack(side=tk.LEFT)

        # 绑定选择事件
        self.where_tree.bind("<<TreeviewSelect>>", self.on_where_select)

    def create_group_by_panel(self):
        """创建GROUP BY面板"""
        group_frame = ttk.Frame(self.builder_notebook)
        self.builder_notebook.add(group_frame, text="GROUP BY")

        # 分组列选择
        group_column_frame = ttk.LabelFrame(group_frame, text="分组列", padding="5")
        group_column_frame.pack(fill=tk.X, pady=(0, 10))

        # 分组列列表
        self.group_listbox = tk.Listbox(group_column_frame, height=6)
        group_scrollbar = ttk.Scrollbar(group_column_frame, orient=tk.VERTICAL, command=self.group_listbox.yview)
        self.group_listbox.configure(yscrollcommand=group_scrollbar.set)

        self.group_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        group_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 分组操作按钮
        group_btn_frame = ttk.Frame(group_column_frame)
        group_btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(group_btn_frame, text="添加分组", command=self.add_group_by).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(group_btn_frame, text="移除分组", command=self.remove_group_by).pack(side=tk.LEFT)

        # HAVING条件
        having_frame = ttk.LabelFrame(group_frame, text="HAVING条件", padding="5")
        having_frame.pack(fill=tk.BOTH, expand=True)

        # HAVING条件列表
        columns = ('聚合函数', '操作符', '值')
        self.having_tree = ttk.Treeview(having_frame, columns=columns, show='tree headings', height=8)
        
        for col in columns:
            self.having_tree.heading(col, text=col)
            self.having_tree.column(col, width=120)

        having_scrollbar = ttk.Scrollbar(having_frame, orient=tk.VERTICAL, command=self.having_tree.yview)
        self.having_tree.configure(yscrollcommand=having_scrollbar.set)

        self.having_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        having_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # HAVING条件编辑
        having_edit_frame = ttk.Frame(having_frame)
        having_edit_frame.pack(fill=tk.X, pady=(10, 0))

        # 聚合函数选择
        agg_frame = ttk.Frame(having_edit_frame)
        agg_frame.pack(fill=tk.X, pady=2)
        ttk.Label(agg_frame, text="聚合函数:").pack(side=tk.LEFT, padx=(0, 5))
        self.having_agg_combo = ttk.Combobox(agg_frame, values=["COUNT", "SUM", "AVG", "MAX", "MIN"], width=15)
        self.having_agg_combo.pack(side=tk.LEFT)

        # 字段选择
        having_field_frame = ttk.Frame(having_edit_frame)
        having_field_frame.pack(fill=tk.X, pady=2)
        ttk.Label(having_field_frame, text="字段:").pack(side=tk.LEFT, padx=(0, 5))
        self.having_field_combo = ttk.Combobox(having_field_frame, width=15)
        self.having_field_combo.pack(side=tk.LEFT)

        # 操作符和值
        having_op_frame = ttk.Frame(having_edit_frame)
        having_op_frame.pack(fill=tk.X, pady=2)
        ttk.Label(having_op_frame, text="操作符:").pack(side=tk.LEFT, padx=(0, 5))
        self.having_operator_combo = ttk.Combobox(having_op_frame, values=["=", "!=", ">", "<", ">=", "<="], width=10)
        self.having_operator_combo.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(having_op_frame, text="值:").pack(side=tk.LEFT, padx=(0, 5))
        self.having_value_entry = ttk.Entry(having_op_frame, width=10)
        self.having_value_entry.pack(side=tk.LEFT)

        # HAVING操作按钮
        having_btn_frame = ttk.Frame(having_edit_frame)
        having_btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(having_btn_frame, text="添加HAVING", command=self.add_having_condition).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(having_btn_frame, text="删除HAVING", command=self.remove_having_condition).pack(side=tk.LEFT)

    def create_order_by_panel(self):
        """创建ORDER BY面板"""
        order_frame = ttk.Frame(self.builder_notebook)
        self.builder_notebook.add(order_frame, text="ORDER BY")

        # 排序列表
        order_list_frame = ttk.LabelFrame(order_frame, text="排序列表", padding="5")
        order_list_frame.pack(fill=tk.BOTH, expand=True)

        # 排序树形视图
        columns = ('字段', '排序方式', '优先级')
        self.order_tree = ttk.Treeview(order_list_frame, columns=columns, show='tree headings', height=10)
        
        for col in columns:
            self.order_tree.heading(col, text=col)
            self.order_tree.column(col, width=120)

        order_scrollbar = ttk.Scrollbar(order_list_frame, orient=tk.VERTICAL, command=self.order_tree.yview)
        self.order_tree.configure(yscrollcommand=order_scrollbar.set)

        self.order_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        order_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 排序编辑区域
        order_edit_frame = ttk.LabelFrame(order_frame, text="排序编辑", padding="5")
        order_edit_frame.pack(fill=tk.X, pady=(10, 0))

        # 字段选择
        order_field_frame = ttk.Frame(order_edit_frame)
        order_field_frame.pack(fill=tk.X, pady=2)
        ttk.Label(order_field_frame, text="字段:").pack(side=tk.LEFT, padx=(0, 5))
        self.order_field_combo = ttk.Combobox(order_field_frame, width=20)
        self.order_field_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 排序方式
        order_dir_frame = ttk.Frame(order_edit_frame)
        order_dir_frame.pack(fill=tk.X, pady=2)
        ttk.Label(order_dir_frame, text="排序方式:").pack(side=tk.LEFT, padx=(0, 5))
        self.order_direction_combo = ttk.Combobox(order_dir_frame, values=["ASC", "DESC"], width=20)
        self.order_direction_combo.set("ASC")
        self.order_direction_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 排序操作按钮
        order_btn_frame = ttk.Frame(order_edit_frame)
        order_btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(order_btn_frame, text="添加排序", command=self.add_order_by).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(order_btn_frame, text="上移", command=self.move_order_up).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(order_btn_frame, text="下移", command=self.move_order_down).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(order_btn_frame, text="删除排序", command=self.remove_order_by).pack(side=tk.LEFT)

    def create_preview_panel(self, parent):
        """创建SQL预览面板"""
        preview_frame = ttk.LabelFrame(parent, text="SQL预览", padding="10")
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # SQL预览文本框
        self.sql_text = tk.Text(preview_frame, wrap=tk.NONE, font=("Courier", 10))
        sql_scrollbar_y = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.sql_text.yview)
        sql_scrollbar_x = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.sql_text.xview)
        
        self.sql_text.configure(yscrollcommand=sql_scrollbar_y.set, xscrollcommand=sql_scrollbar_x.set)
        
        self.sql_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sql_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        sql_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # 刷新按钮
        refresh_btn = ttk.Button(preview_frame, text="刷新SQL", command=self.update_sql_preview)
        refresh_btn.pack(pady=(10, 0))

    def create_button_panel(self, parent):
        """创建按钮面板"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X)

        # 验证按钮
        validate_btn = ttk.Button(button_frame, text="验证SQL", command=self.validate_sql)
        validate_btn.pack(side=tk.LEFT)

        # 执行按钮
        execute_btn = ttk.Button(button_frame, text="执行查询", command=self.execute_query)
        execute_btn.pack(side=tk.LEFT, padx=(10, 0))

        # 保存按钮
        save_btn = ttk.Button(button_frame, text="保存SQL", command=self.save_sql)
        save_btn.pack(side=tk.LEFT, padx=(10, 0))

        # 复制按钮
        copy_btn = ttk.Button(button_frame, text="复制SQL", command=self.copy_sql)
        copy_btn.pack(side=tk.LEFT, padx=(10, 0))

    def create_status_bar(self, parent):
        """创建状态栏"""
        self.status_label = tk.Label(parent, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, pady=(10, 0))

    def load_database_structure(self):
        """加载数据库结构"""
        if not self.config:
            messagebox.showwarning("提示", "未配置数据库连接")
            return

        try:
            self.status_label.config(text="正在获取数据库结构...")
            self.window.update()

            # 这里应该调用实际的数据库查询获取表结构
            # 模拟一些表和数据
            self.load_sample_database()

            self.status_label.config(text="数据库结构加载完成")

        except Exception as e:
            messagebox.showerror("错误", f"加载数据库结构失败：\n{e}")
            self.status_label.config(text="加载失败")

    def load_sample_database(self):
        """加载示例数据库结构"""
        # 示例表结构
        sample_tables = [
            "users",
            "orders", 
            "products",
            "categories",
            "order_items"
        ]

        # 示例列结构
        sample_columns = {
            "users": ["id", "name", "email", "created_at"],
            "orders": ["id", "user_id", "total_amount", "order_date", "status"],
            "products": ["id", "name", "price", "category_id", "stock"],
            "categories": ["id", "name", "description"],
            "order_items": ["id", "order_id", "product_id", "quantity", "price"]
        }

        # 清空现有数据
        self.table_listbox.delete(0, tk.END)
        self.tables = sample_tables
        self.columns = sample_columns

        # 添加表到列表
        for table in sample_tables:
            self.table_listbox.insert(tk.END, table)

        # 更新字段下拉框
        self.update_field_combos()

    def update_field_combos(self):
        """更新字段下拉框"""
        all_fields = []
        for table, columns in self.columns.items():
            for col in columns:
                all_fields.append(f"{table}.{col}")

        # 更新WHERE字段下拉框
        self.where_field_combo['values'] = all_fields

        # 更新ORDER BY字段下拉框
        self.order_field_combo['values'] = all_fields

        # 更新HAVING字段下拉框
        self.having_field_combo['values'] = all_fields

        # 更新GROUP BY可用字段
        self.update_group_by_fields()

    def update_group_by_fields(self):
        """更新GROUP BY可用字段"""
        # 获取已选择的列
        selected_columns = []
        for i in range(self.column_listbox.size()):
            item = self.column_listbox.get(i)
            if ' AS ' in item:
                # 如果有别名，使用别名
                selected_columns.append(item.split(' AS ')[1])
            else:
                selected_columns.append(item)

        self.having_field_combo['values'] = selected_columns

    def add_table(self):
        """添加表"""
        selection = self.table_listbox.curselection()
        if selection:
            table = self.table_listbox.get(selection[0])
            if table not in self.tables:
                self.tables.append(table)
                self.update_field_combos()
                self.update_sql_preview()

    def remove_table(self):
        """移除表"""
        selection = self.table_listbox.curselection()
        if selection:
            table = self.table_listbox.get(selection[0])
            if table in self.tables:
                self.tables.remove(table)
                self.update_field_combos()
                self.update_sql_preview()

    def add_column(self):
        """添加列"""
        # 这里应该显示列选择对话框
        # 简化实现，添加示例列
        if self.tables:
            table = self.tables[0]
            if table in self.columns:
                for col in self.columns[table][:3]:  # 添加前3列作为示例
                    column_text = f"{table}.{col}"
                    if column_text not in [self.column_listbox.get(i) for i in range(self.column_listbox.size())]:
                        self.column_listbox.insert(tk.END, column_text)
        self.update_sql_preview()

    def remove_column(self):
        """移除列"""
        selection = self.column_listbox.curselection()
        if selection:
            self.column_listbox.delete(selection[0])
            self.update_sql_preview()

    def select_all_columns(self):
        """全选列"""
        if self.tables:
            table = self.tables[0]
            if table in self.columns:
                for col in self.columns[table]:
                    column_text = f"{table}.{col}"
                    if column_text not in [self.column_listbox.get(i) for i in range(self.column_listbox.size())]:
                        self.column_listbox.insert(tk.END, column_text)
        self.update_sql_preview()

    def clear_columns(self):
        """清空列"""
        self.column_listbox.delete(0, tk.END)
        self.update_sql_preview()

    def set_column_alias(self):
        """设置列别名"""
        selection = self.column_listbox.curselection()
        if selection:
            alias = self.column_alias_entry.get().strip()
            if alias:
                current_text = self.column_listbox.get(selection[0])
                new_text = f"{current_text} AS {alias}"
                self.column_listbox.delete(selection[0])
                self.column_listbox.insert(selection[0], new_text)
                self.column_alias_entry.delete(0, tk.END)
                self.update_sql_preview()

    def add_where_condition(self):
        """添加WHERE条件"""
        field = self.where_field_combo.get()
        operator = self.where_operator_combo.get()
        value = self.where_value_entry.get()
        connector = self.where_connector_combo.get()

        if field and operator:
            condition = {
                'field': field,
                'operator': operator,
                'value': value,
                'connector': connector
            }
            self.where_conditions.append(condition)
            
            # 添加到树形视图
            self.where_tree.insert('', 'end', values=(field, operator, value, connector))
            
            # 清空输入
            self.where_value_entry.delete(0, tk.END)
            
            self.update_sql_preview()

    def remove_where_condition(self):
        """删除WHERE条件"""
        selection = self.where_tree.selection()
        if selection:
            item = self.where_tree.item(selection[0])
            values = item['values']
            
            # 查找并删除条件
            for i, condition in enumerate(self.where_conditions):
                if (condition['field'] == values[0] and 
                    condition['operator'] == values[1] and 
                    condition['value'] == values[2]):
                    del self.where_conditions[i]
                    break
            
            self.where_tree.delete(selection[0])
            self.update_sql_preview()

    def on_where_select(self, event):
        """WHERE条件选择事件"""
        selection = self.where_tree.selection()
        if selection:
            item = self.where_tree.item(selection[0])
            values = item['values']
            
            # 填充编辑框
            self.where_field_combo.set(values[0])
            self.where_operator_combo.set(values[1])
            self.where_value_entry.delete(0, tk.END)
            self.where_value_entry.insert(0, values[2])
            self.where_connector_combo.set(values[3])

    def update_where_condition(self):
        """更新WHERE条件"""
        selection = self.where_tree.selection()
        if selection:
            field = self.where_field_combo.get()
            operator = self.where_operator_combo.get()
            value = self.where_value_entry.get()
            connector = self.where_connector_combo.get()

            if field and operator:
                # 更新树形视图
                self.where_tree.item(selection[0], values=(field, operator, value, connector))
                
                # 更新条件列表
                item = self.where_tree.item(selection[0])
                old_values = item['values']
                
                for i, condition in enumerate(self.where_conditions):
                    if (condition['field'] == old_values[0] and 
                        condition['operator'] == old_values[1] and 
                        condition['value'] == old_values[2]):
                        self.where_conditions[i] = {
                            'field': field,
                            'operator': operator,
                            'value': value,
                            'connector': connector
                        }
                        break
                
                self.update_sql_preview()

    def add_group_by(self):
        """添加GROUP BY"""
        if self.order_field_combo.get():
            column = self.order_field_combo.get()
            if column not in self.group_by_columns:
                self.group_by_columns.append(column)
                self.group_listbox.insert(tk.END, column)
                self.update_sql_preview()

    def remove_group_by(self):
        """移除GROUP BY"""
        selection = self.group_listbox.curselection()
        if selection:
            column = self.group_listbox.get(selection[0])
            if column in self.group_by_columns:
                self.group_by_columns.remove(column)
                self.group_listbox.delete(selection[0])
                self.update_sql_preview()

    def add_having_condition(self):
        """添加HAVING条件"""
        agg_func = self.having_agg_combo.get()
        field = self.having_field_combo.get()
        operator = self.having_operator_combo.get()
        value = self.having_value_entry.get()

        if agg_func and field and operator and value:
            condition = {
                'aggregate': agg_func,
                'field': field,
                'operator': operator,
                'value': value
            }
            self.having_conditions.append(condition)
            
            # 添加到树形视图
            self.having_tree.insert('', 'end', values=(f"{agg_func}({field})", operator, value))
            
            # 清空输入
            self.having_value_entry.delete(0, tk.END)
            
            self.update_sql_preview()

    def remove_having_condition(self):
        """删除HAVING条件"""
        selection = self.having_tree.selection()
        if selection:
            self.having_tree.delete(selection[0])
            # 重新构建条件列表
            self.having_conditions.clear()
            for item in self.having_tree.get_children():
                values = self.having_tree.item(item)['values']
                # 解析聚合函数和字段
                match = re.match(r'(\w+)\((\w+\.\w+)\)', values[0])
                if match:
                    self.having_conditions.append({
                        'aggregate': match.group(1),
                        'field': match.group(2),
                        'operator': values[1],
                        'value': values[2]
                    })
            self.update_sql_preview()

    def add_order_by(self):
        """添加ORDER BY"""
        field = self.order_field_combo.get()
        direction = self.order_direction_combo.get()

        if field:
            order_item = {
                'field': field,
                'direction': direction,
                'priority': len(self.order_by_columns) + 1
            }
            self.order_by_columns.append(order_item)
            
            # 添加到树形视图
            self.order_tree.insert('', 'end', values=(field, direction, len(self.order_by_columns)))
            self.update_sql_preview()

    def remove_order_by(self):
        """移除ORDER BY"""
        selection = self.order_tree.selection()
        if selection:
            self.order_tree.delete(selection[0])
            # 重新构建排序列表
            self.order_by_columns.clear()
            for item in self.order_tree.get_children():
                values = self.order_tree.item(item)['values']
                self.order_by_columns.append({
                    'field': values[0],
                    'direction': values[1],
                    'priority': values[2]
                })
            self.update_sql_preview()

    def move_order_up(self):
        """上移排序"""
        selection = self.order_tree.selection()
        if selection:
            item = selection[0]
            prev_item = self.order_tree.prev(item)
            if prev_item:
                # 交换位置
                self.order_tree.move(item, '', prev_item)
                self.update_order_priorities()
                self.update_sql_preview()

    def move_order_down(self):
        """下移排序"""
        selection = self.order_tree.selection()
        if selection:
            item = selection[0]
            next_item = self.order_tree.next(item)
            if next_item:
                # 交换位置
                self.order_tree.move(item, '', self.order_tree.next(next_item))
                self.update_order_priorities()
                self.update_sql_preview()

    def update_order_priorities(self):
        """更新排序优先级"""
        self.order_by_columns.clear()
        for i, item in enumerate(self.order_tree.get_children()):
            values = self.order_tree.item(item)['values']
            self.order_by_columns.append({
                'field': values[0],
                'direction': values[1],
                'priority': i + 1
            })
            # 更新显示的优先级
            self.order_tree.item(item, values=(values[0], values[1], i + 1))

    def update_sql_preview(self):
        """更新SQL预览"""
        sql = self.build_sql()
        self.sql_text.delete("1.0", tk.END)
        self.sql_text.insert("1.0", sql)

    def build_sql(self):
        """构建SQL语句"""
        query_type = self.query_type.get()
        
        if query_type == "SELECT":
            return self.build_select_sql()
        elif query_type == "INSERT":
            return self.build_insert_sql()
        elif query_type == "UPDATE":
            return self.build_update_sql()
        elif query_type == "DELETE":
            return self.build_delete_sql()
        else:
            return "-- 不支持的查询类型"

    def build_select_sql(self):
        """构建SELECT SQL"""
        sql_parts = []
        
        # SELECT子句
        if self.column_listbox.size() > 0:
            columns = []
            for i in range(self.column_listbox.size()):
                columns.append(self.column_listbox.get(i))
            sql_parts.append(f"SELECT {', '.join(columns)}")
        else:
            sql_parts.append("SELECT *")
        
        # FROM子句
        if self.tables:
            sql_parts.append(f"FROM {', '.join(self.tables)}")
        
        # WHERE子句
        if self.where_conditions:
            where_clauses = []
            for condition in self.where_conditions:
                field = condition['field']
                operator = condition['operator']
                value = condition['value']
                connector = condition['connector']
                
                if operator.upper() in ["IS NULL", "IS NOT NULL"]:
                    clause = f"{field} {operator}"
                elif operator.upper() == "IN":
                    clause = f"{field} {operator} ({value})"
                elif operator.upper() == "LIKE":
                    clause = f"{field} {operator} '{value}'"
                else:
                    clause = f"{field} {operator} '{value}'"
                
                where_clauses.append(f"{connector} {clause}" if where_clauses else clause)
            
            sql_parts.append(f"WHERE {' '.join(where_clauses)}")
        
        # GROUP BY子句
        if self.group_by_columns:
            sql_parts.append(f"GROUP BY {', '.join(self.group_by_columns)}")
        
        # HAVING子句
        if self.having_conditions:
            having_clauses = []
            for condition in self.having_conditions:
                agg = condition['aggregate']
                field = condition['field']
                operator = condition['operator']
                value = condition['value']
                having_clauses.append(f"{agg}({field}) {operator} '{value}'")
            sql_parts.append(f"HAVING {' AND '.join(having_clauses)}")
        
        # ORDER BY子句
        if self.order_by_columns:
            # 按优先级排序
            sorted_orders = sorted(self.order_by_columns, key=lambda x: x['priority'])
            order_clauses = []
            for order in sorted_orders:
                order_clauses.append(f"{order['field']} {order['direction']}")
            sql_parts.append(f"ORDER BY {', '.join(order_clauses)}")
        
        return "\n".join(sql_parts)

    def build_insert_sql(self):
        """构建INSERT SQL"""
        return "-- INSERT SQL 构建功能待实现"

    def build_update_sql(self):
        """构建UPDATE SQL"""
        return "-- UPDATE SQL 构建功能待实现"

    def build_delete_sql(self):
        """构建DELETE SQL"""
        return "-- DELETE SQL 构建功能待实现"

    def on_query_type_changed(self, event=None):
        """查询类型改变事件"""
        query_type = self.query_type.get()
        # 根据查询类型启用/禁用相应的面板
        if query_type != "SELECT":
            # 禁用非SELECT相关的面板
            for i in range(1, self.builder_notebook.index("end")):
                self.builder_notebook.tab(i, state="disabled")
        else:
            # 启用所有面板
            for i in range(self.builder_notebook.index("end")):
                self.builder_notebook.tab(i, state="normal")
        
        self.update_sql_preview()

    def validate_sql(self):
        """验证SQL语法"""
        sql = self.sql_text.get("1.0", tk.END).strip()
        if not sql or sql.startswith("--"):
            messagebox.showwarning("提示", "请先构建有效的SQL语句")
            return
        
        # 简单的SQL语法检查
        try:
            # 这里可以添加更复杂的SQL语法验证
            if sql.upper().startswith("SELECT"):
                if "FROM" not in sql.upper():
                    messagebox.showerror("语法错误", "SELECT语句缺少FROM子句")
                    return
            
            messagebox.showinfo("验证结果", "SQL语法检查通过")
            self.status_label.config(text="SQL验证通过")
            
        except Exception as e:
            messagebox.showerror("验证错误", f"SQL验证失败：\n{e}")
            self.status_label.config(text="SQL验证失败")

    def execute_query(self):
        """执行查询"""
        sql = self.sql_text.get("1.0", tk.END).strip()
        if not sql or sql.startswith("--"):
            messagebox.showwarning("提示", "请先构建有效的SQL语句")
            return
        
        # 这里应该调用实际的查询执行方法
        messagebox.showinfo("执行查询", f"将要执行的SQL：\n\n{sql}")
        self.status_label.config(text="查询执行功能待实现")

    def save_sql(self):
        """保存SQL到文件"""
        from tkinter import filedialog
        
        sql = self.sql_text.get("1.0", tk.END).strip()
        if not sql or sql.startswith("--"):
            messagebox.showwarning("提示", "没有可保存的SQL语句")
            return
        
        filename = filedialog.asksaveasfilename(
            title="保存SQL文件",
            defaultextension=".sql",
            filetypes=[("SQL文件", "*.sql"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(sql)
                messagebox.showinfo("保存成功", f"SQL文件已保存到：\n{filename}")
                self.status_label.config(text=f"SQL已保存到: {filename}")
            except Exception as e:
                messagebox.showerror("保存错误", f"保存文件失败：\n{e}")

    def copy_sql(self):
        """复制SQL到剪贴板"""
        sql = self.sql_text.get("1.0", tk.END).strip()
        if not sql or sql.startswith("--"):
            messagebox.showwarning("提示", "没有可复制的SQL语句")
            return
        
        try:
            self.window.clipboard_clear()
            self.window.clipboard_append(sql)
            messagebox.showinfo("复制成功", "SQL已复制到剪贴板")
            self.status_label.config(text="SQL已复制到剪贴板")
        except Exception as e:
            messagebox.showerror("复制错误", f"复制失败：\n{e}")

    def load_template(self):
        """加载查询模板"""
        templates = {
            "基础查询": "SELECT * FROM table_name WHERE condition = 'value'",
            "聚合查询": "SELECT column1, COUNT(*) as count FROM table_name GROUP BY column1",
            "连接查询": "SELECT a.*, b.column2 FROM table_a a JOIN table_b b ON a.id = b.a_id",
            "子查询": "SELECT * FROM table_name WHERE id IN (SELECT id FROM other_table WHERE condition = 'value')"
        }
        
        # 创建模板选择对话框
        template_window = tk.Toplevel(self.window)
        template_window.title("选择查询模板")
        template_window.geometry("400x300")
        template_window.transient(self.window)
        template_window.grab_set()
        
        # 模板列表
        template_listbox = tk.Listbox(template_window, height=10)
        template_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for name in templates.keys():
            template_listbox.insert(tk.END, name)
        
        def use_template():
            selection = template_listbox.curselection()
            if selection:
                template_name = template_listbox.get(selection[0])
                template_sql = templates[template_name]
                self.sql_text.delete("1.0", tk.END)
                self.sql_text.insert("1.0", template_sql)
                template_window.destroy()
        
        # 按钮
        button_frame = ttk.Frame(template_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="使用模板", command=use_template).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="取消", command=template_window.destroy).pack(side=tk.LEFT)

    def clear_query(self):
        """清空查询"""
        # 清空所有数据
        self.tables.clear()
        self.columns.clear()
        self.where_conditions.clear()
        self.group_by_columns.clear()
        self.having_conditions.clear()
        self.order_by_columns.clear()
        
        # 清空界面
        self.table_listbox.delete(0, tk.END)
        self.column_listbox.delete(0, tk.END)
        self.group_listbox.delete(0, tk.END)
        
        # 清空树形视图
        for item in self.where_tree.get_children():
            self.where_tree.delete(item)
        for item in self.having_tree.get_children():
            self.having_tree.delete(item)
        for item in self.order_tree.get_children():
            self.order_tree.delete(item)
        
        # 清空SQL预览
        self.sql_text.delete("1.0", tk.END)
        
        self.status_label.config(text="查询已清空")

    def center_window(self):
        """居中显示窗口"""
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
