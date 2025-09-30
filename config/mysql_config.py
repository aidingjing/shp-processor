"""
MySQL数据库配置管理模块
提供数据库连接配置的读取、验证和保存功能
"""

import json
import os
from typing import Dict, Optional, Any


class MySQLConfig:
    """MySQL数据库配置类"""

    DEFAULT_CONFIG = {
        "host": "59.110.116.46",
        "port": 3306,
        "user": "ljw",
        "password": "123456",
        "database": "GEO",
        "charset": "utf8mb4"
    }

    def __init__(self, config_file: str = "mysql_config.json"):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config = self.DEFAULT_CONFIG.copy()
        self.load_config()

    def load_config(self) -> None:
        """从文件加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    # 合并配置，保留默认值
                    self.config.update(file_config)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            self.config = self.DEFAULT_CONFIG.copy()

    def save_config(self) -> bool:
        """
        保存配置到文件

        Returns:
            bool: 保存是否成功
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False

    def get_config(self) -> Dict[str, Any]:
        """
        获取完整配置

        Returns:
            Dict: 配置字典
        """
        return self.config.copy()

    def update_config(self, **kwargs) -> None:
        """
        更新配置参数

        Args:
            **kwargs: 配置参数
        """
        self.config.update(kwargs)

    def set_config(self, host: str, port: int, user: str, password: str, database: str) -> None:
        """
        设置数据库连接参数

        Args:
            host: 主机地址
            port: 端口号
            user: 用户名
            password: 密码
            database: 数据库名
        """
        self.config.update({
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database
        })

    def validate_config(self) -> tuple[bool, str]:
        """
        验证配置是否完整

        Returns:
            tuple: (是否有效, 错误信息)
        """
        required_fields = ["host", "user", "database"]

        for field in required_fields:
            if not self.config.get(field):
                return False, f"缺少必要配置项: {field}"

        if self.config.get("port") and not isinstance(self.config["port"], int):
            try:
                self.config["port"] = int(self.config["port"])
            except ValueError:
                return False, "端口号必须是数字"

        return True, "配置有效"

    def get_connection_string(self) -> str:
        """
        生成连接字符串（隐藏密码）

        Returns:
            str: 连接字符串
        """
        config = self.config
        password_mask = "*" * len(config.get("password", "")) if config.get("password") else ""

        return f"mysql://{config['user']}:{password_mask}@{config['host']}:{config['port']}/{config['database']}"

    def test_connection(self) -> tuple[bool, str]:
        """
        测试数据库连接

        Returns:
            tuple: (连接是否成功, 结果信息)
        """
        try:
            import pymysql
            from pymysql import MySQLError

            config = self.get_config()
            connection = pymysql.connect(
                host=config['host'],
                port=config['port'],
                user=config['user'],
                password=config['password'],
                database=config['database'],
                charset=config['charset'],
                connect_timeout=10
            )

            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()

            connection.close()
            return True, "数据库连接成功"

        except MySQLError as e:
            return False, f"MySQL连接错误: {e}"
        except Exception as e:
            return False, f"连接测试失败: {e}"


if __name__ == "__main__":
    # 测试代码
    config = MySQLConfig()

    # 设置测试配置
    config.set_config(
        host="localhost",
        port=3306,
        user="root",
        password="password",
        database="test"
    )

    # 验证配置
    is_valid, msg = config.validate_config()
    print(f"配置验证: {is_valid}, {msg}")

    # 显示连接字符串
    print(f"连接字符串: {config.get_connection_string()}")

    # 测试连接
    success, result = config.test_connection()
    print(f"连接测试: {success}, {result}")