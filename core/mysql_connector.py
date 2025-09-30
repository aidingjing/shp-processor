"""
MySQL数据库连接器模块
提供数据库连接、查询执行和数据获取功能
"""

import pandas as pd
import pymysql
from pymysql import MySQLError
from typing import Optional, List, Dict, Any, Union
from contextlib import contextmanager

from config.mysql_config import MySQLConfig


class MySQLConnector:
    """MySQL数据库连接器"""

    def __init__(self, config: MySQLConfig):
        """
        初始化连接器

        Args:
            config: MySQL配置对象
        """
        self.config = config
        self.connection: Optional[pymysql.Connection] = None

    @contextmanager
    def get_connection(self):
        """
        获取数据库连接的上下文管理器

        Yields:
            pymysql.Connection: 数据库连接对象
        """
        connection = None
        try:
            config_dict = self.config.get_config()
            connection = pymysql.connect(
                host=config_dict['host'],
                port=config_dict['port'],
                user=config_dict['user'],
                password=config_dict['password'],
                database=config_dict['database'],
                charset=config_dict['charset'],
                cursorclass=pymysql.cursors.DictCursor
            )
            yield connection
        except Exception as e:
            raise Exception(f"数据库连接失败: {e}")
        finally:
            if connection:
                connection.close()

    def test_connection(self) -> tuple[bool, str]:
        """
        测试数据库连接

        Returns:
            tuple: (连接是否成功, 结果信息)
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
            return True, "数据库连接成功"
        except Exception as e:
            return False, f"连接测试失败: {e}"

    def execute_query(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """
        执行SQL查询并返回DataFrame

        Args:
            query: SQL查询语句
            params: 查询参数

        Returns:
            pd.DataFrame: 查询结果

        Raises:
            Exception: 查询执行失败时抛出异常
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)

                    # 获取列名
                    if cursor.description:
                        columns = [desc[0] for desc in cursor.description]
                    else:
                        return pd.DataFrame()

                    # 获取所有数据
                    rows = cursor.fetchall()

                    # 如果没有数据，返回空DataFrame
                    if not rows:
                        return pd.DataFrame(columns=columns)

                    # 转换为DataFrame
                    if rows and isinstance(rows[0], dict):
                        # 如果返回的是字典列表
                        df = pd.DataFrame(rows)
                    else:
                        # 如果返回的是元组列表，手动构建DataFrame
                        df = pd.DataFrame(rows, columns=columns)

                    return df
        except Exception as e:
            raise Exception(f"执行查询失败: {e}")

    def execute_query_raw(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        执行SQL查询并返回原始字典列表

        Args:
            query: SQL查询语句
            params: 查询参数

        Returns:
            List[Dict]: 查询结果列表

        Raises:
            Exception: 查询执行失败时抛出异常
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    result = cursor.fetchall()
                    return result
        except Exception as e:
            raise Exception(f"执行查询失败: {e}")

    def get_table_info(self) -> Dict[str, List[Dict[str, str]]]:
        """
        获取数据库中所有表的信息

        Returns:
            Dict: 表信息字典 {表名: [字段信息列表]}
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # 获取所有表名
                    cursor.execute("SHOW TABLES")
                    tables = cursor.fetchall()

                    table_info = {}
                    for table_dict in tables:
                        table_name = list(table_dict.values())[0]

                        # 获取表结构信息
                        cursor.execute(f"DESCRIBE {table_name}")
                        columns = cursor.fetchall()

                        table_info[table_name] = columns

                    return table_info
        except Exception as e:
            raise Exception(f"获取表信息失败: {e}")

    def get_table_columns(self, table_name: str) -> List[Dict[str, str]]:
        """
        获取指定表的字段信息

        Args:
            table_name: 表名

        Returns:
            List[Dict]: 字段信息列表
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"DESCRIBE {table_name}")
                    return cursor.fetchall()
        except Exception as e:
            raise Exception(f"获取表结构失败: {e}")

    def get_query_columns(self, query: str) -> List[str]:
        """
        获取查询语句的字段列表（通过分析查询或执行LIMIT 0）

        Args:
            query: SQL查询语句

        Returns:
            List[str]: 字段名称列表
        """
        try:
            # 尝试通过LIMIT 0获取字段信息
            with self.get_connection() as conn:
                df = pd.read_sql_query(f"SELECT * FROM ({query}) AS subquery LIMIT 0", conn)
                return df.columns.tolist()
        except Exception:
            # 如果失败，尝试执行查询获取前几行来推断字段
            try:
                df = self.execute_query(query + " LIMIT 1")
                return df.columns.tolist()
            except Exception as e:
                raise Exception(f"无法获取查询字段信息: {e}")

    def validate_query(self, query: str) -> tuple[bool, str]:
        """
        验证SQL查询语句的语法

        Args:
            query: SQL查询语句

        Returns:
            tuple: (是否有效, 错误信息)
        """
        try:
            # 尝试执行查询但不返回结果
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("EXPLAIN " + query)
            return True, "查询语法正确"
        except Exception as e:
            return False, f"查询语法错误: {e}"

    def get_database_info(self) -> Dict[str, Any]:
        """
        获取数据库基本信息

        Returns:
            Dict: 数据库信息
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # 获取数据库名称
                    cursor.execute("SELECT DATABASE()")
                    database_name = cursor.fetchone()['DATABASE()']

                    # 获取数据库版本
                    cursor.execute("SELECT VERSION()")
                    version = cursor.fetchone()['VERSION()']

                    # 获取表数量
                    cursor.execute("SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = %s", (database_name,))
                    table_count = cursor.fetchone()['table_count']

                    return {
                        'database_name': database_name,
                        'version': version,
                        'table_count': table_count
                    }
        except Exception as e:
            raise Exception(f"获取数据库信息失败: {e}")


if __name__ == "__main__":
    # 测试代码
    from config.mysql_config import MySQLConfig

    # 创建配置
    config = MySQLConfig()
    config.set_config(
        host="localhost",
        port=3306,
        user="root",
        password="password",
        database="test"
    )

    # 创建连接器
    connector = MySQLConnector(config)

    # 测试连接
    success, msg = connector.test_connection()
    print(f"连接测试: {success}, {msg}")

    if success:
        try:
            # 获取数据库信息
            db_info = connector.get_database_info()
            print(f"数据库信息: {db_info}")

            # 执行查询测试
            test_query = "SELECT 1 as test_col, 'test' as test_str"
            df = connector.execute_query(test_query)
            print(f"查询结果: {df}")

            # 获取查询字段
            columns = connector.get_query_columns(test_query)
            print(f"查询字段: {columns}")

        except Exception as e:
            print(f"测试失败: {e}")