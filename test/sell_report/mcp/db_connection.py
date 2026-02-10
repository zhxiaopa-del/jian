"""
统一的数据库连接管理模块
一次性初始化，避免重复连接
"""
import pymysql
from contextlib import contextmanager
from typing import Dict, Any, Optional


class DBConnectionManager:
    """数据库连接管理器 - 单例模式"""
    _instance = None
    _config = None
    
    def __new__(cls, config: Optional[Dict[str, Any]] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not self._initialized:
            if config is None:
                # 延迟导入避免循环依赖
                from config import DB_CONFIG
                config = DB_CONFIG
            self._config = config
            self._initialized = True
    
    @contextmanager
    def get_connection(self, use_dict_cursor: bool = False):
        """
        获取数据库连接的上下文管理器
        自动处理连接的创建和关闭
        
        Args:
            use_dict_cursor: 是否使用字典游标（默认False，返回元组；True返回字典）
        """
        if use_dict_cursor:
            conn = pymysql.connect(**self._config, cursorclass=pymysql.cursors.DictCursor)
        else:
            conn = pymysql.connect(**self._config)
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, sql: str, params: tuple = None, use_dict_cursor: bool = True):
        """
        执行查询SQL，返回结果列表
        
        Args:
            sql: SQL语句
            params: 参数元组
            use_dict_cursor: 是否返回字典格式（默认True）
        
        Returns:
            查询结果列表
        """
        with self.get_connection(use_dict_cursor=use_dict_cursor) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                return cur.fetchall()
    
    def execute_update(self, sql: str, params: tuple = None):
        """
        执行更新SQL（INSERT/UPDATE/DELETE）
        
        Args:
            sql: SQL语句
            params: 参数元组
        
        Returns:
            受影响的行数
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                affected = cur.execute(sql, params or ())
                conn.commit()
                return affected


# ================= 全局数据库连接管理器实例 =================
db_manager = DBConnectionManager()

# ================= 便捷函数 =================
def get_db_connection(use_dict_cursor: bool = False):
    """
    获取数据库连接的上下文管理器（向后兼容）
    
    Args:
        use_dict_cursor: 是否使用字典游标
    
    Returns:
        上下文管理器
    """
    return db_manager.get_connection(use_dict_cursor=use_dict_cursor)
