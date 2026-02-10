import pymysql

class SimpleDBManager:
    def __init__(self, config):
        self.config = config
        self.table_map = {"回款": "payment_records", "合同": "contract_records"}
        self.init_db()

    # 1. 链接数据库
    def get_conn(self):
        return pymysql.connect(**self.config, cursorclass=pymysql.cursors.DictCursor)

    # 2. 建立数据库与表
    def init_db(self):
        # 先连接到服务器创建数据库
        temp_cfg = self.config.copy()
        db_name = temp_cfg.pop("database")
        conn = pymysql.connect(**temp_cfg)
        conn.cursor().execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4")
        conn.close()
        
        # 连接数据库创建表
        conn = self.get_conn()
        with conn.cursor() as cur:
            # 回款表
            cur.execute("""CREATE TABLE IF NOT EXISTS payment_records (
                id INT AUTO_INCREMENT PRIMARY KEY, 负责人 VARCHAR(50), 公司名称 VARCHAR(100), 
                项目类型 VARCHAR(50), 项目名称 VARCHAR(100), 月初预计可能回款 DECIMAL(15,2), 
                月初预计确定回款 DECIMAL(15,2), 可能回款 DECIMAL(15,2), 确定回款 DECIMAL(15,2), 
                实际回款 DECIMAL(15,2), 回款节点 VARCHAR(50), 未回款金额 DECIMAL(15,2), 
                未完成原因 TEXT, 解决办法 TEXT, UNIQUE(负责人, 公司名称, 项目名称))""")
            # 合同表
            cur.execute("""CREATE TABLE IF NOT EXISTS contract_records (
                id INT AUTO_INCREMENT PRIMARY KEY, 负责人 VARCHAR(50), 公司名称 VARCHAR(100), 
                项目类型 VARCHAR(50), 项目名称 VARCHAR(100), 月初预计可能合同 DECIMAL(15,2), 
                月初预计确定合同 DECIMAL(15,2), 可能合同 DECIMAL(15,2), 确定合同 DECIMAL(15,2), 
                实际合同 DECIMAL(15,2), 完成情况 TEXT, UNIQUE(负责人, 公司名称, 项目名称))""")
        conn.commit()
        conn.close()

    # 3. 插入数据（支持 upsert：如果记录已存在则更新，不存在则插入）
    def insert(self, category, data):
        """
        插入或更新数据（upsert）
        :param category: 数据类别（"回款" 或 "合同"）
        :param data: 数据字典
        :return: 是否成功
        """
        table = self.table_map.get(category)
        if not table:
            print(f"⚠️ 未知的数据类别: {category}")
            return False
        
        keys = list(data.keys())
        placeholders = ", ".join(["%s"] * len(keys))
        update_clause = ", ".join([f"`{k}`=VALUES(`{k}`)" for k in keys])
        
        sql = f"""
            INSERT INTO {table} ({', '.join([f'`{k}`' for k in keys])})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE {update_clause}
        """
        
        return self._execute(sql, [data[k] for k in keys])

    # 4. 修改数据 (根据 负责人+公司名称+项目名称 定位)
    def update(self, category, data):
        table = self.table_map.get(category)
        fields = ", ".join([f"{k}=%s" for k in data.keys()])
        sql = f"UPDATE {table} SET {fields} WHERE 负责人=%s AND 公司名称=%s AND 项目名称=%s"
        params = list(data.values()) + [data['负责人'], data['公司名称'], data['项目名称']]
        return self._execute(sql, params)

    # 5. 删除数据
    def delete(self, category, person, company, project):
        table = self.table_map.get(category)
        sql = f"DELETE FROM {table} WHERE 负责人=%s AND 公司名称=%s AND 项目名称=%s"
        return self._execute(sql, [person, company, project])

    # 6. 查找功能
    def select(self, category, person=None):
        table = self.table_map.get(category)
        sql = f"SELECT * FROM {table}"
        params = []
        if person:
            sql += " WHERE 负责人=%s"
            params.append(person)
        conn = self.get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, params)
            result = cur.fetchall()
        conn.close()
        return result

    # 内部执行函数 (内部简化代码用)
    def _execute(self, sql, params):
        conn = self.get_conn()
        try:
            with conn.cursor() as cur:
                affected = cur.execute(sql, params)
            conn.commit()
            return affected > 0
        except Exception as e:
            print(f"操作失败: {e}")
            return False
        finally:
            conn.close()

# ================= 使用示例 =================
if __name__ == "__main__":
    db_config = {
        "host": "localhost", "user": "root", "password": "qwer1234", "database": "sell_report"
    }
    db = SimpleDBManager(db_config)
    
    # 插入示例
    test_data = {"负责人": "张三", "公司名称": "", "项目类型": "软件", "项目名称": "ERP", "实际回款": 5000}
    db.insert("回款", test_data)
    
    # 查询示例
    print(db.select("回款", "张三"))