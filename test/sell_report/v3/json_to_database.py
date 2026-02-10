from msilib import type_nullable
import pymysql

"""
中英文字段对照表

【表名映射】：
| 中文 | 英文 |
| --- | --- |
| 回款 | payment |
| 合同 | contract |

【通用字段】：
| 中文 | 英文 |
| --- | --- |
| 负责人 | responsible_person |
| 公司名称 | company_name |
| 项目类型 | project_type |
| 项目名称 | project_name |

【回款类字段】：
| 中文 | 英文 |
| --- | --- |
| 回款 | payment |
| 月初预计可能回款 | estimated_possible_payment_at_start |
| 月初预计确定回款 | estimated_confirmed_payment_at_start |
| 可能回款 | possible_payment |
| 确定回款 | confirmed_payment |
| 实际回款 | actual_payment |
| 回款节点确定 | payment_node_confirmed |
| 回款节点 | payment_node |
| 未回款金额 | unpaid_amount |
| 未完成原因 | incomplete_reason |
| 解决办法 | solution |

【合同类字段（参考 CSV 表头）】：
| 中文 | 英文 |
| --- | --- |
| 合同 | contract |
| 月初预计可能合同 | estimated_possible_at_start |
| 月初预计确定合同 | estimated_confirmed_at_start |
| 可能合同 | possible_contract |
| 确定合同 | confirmed_contract |
| 实际合同 | actual_contract |
| 完成情况 | completion_status |
| 合同节点 | contract_node |
| 未完成合同金额 | incomplete_contract_amount |
| 未完成合同原因 | incomplete_contract_reason |
| 解决办法 | solution |
"""

class SimpleDBManager:
    def __init__(self, config):
        self.config = config
        # 表名映射（使用英文键）
        self.table_map = {
            "payment": "payment_records",
            "contract": "contract_records",
            "回款": "payment_records",
            "合同": "contract_records"
        }
        # 中英文字段名映射表
        self.field_mapping = {
    
            "负责人": "responsible_person",
            "公司名称": "company_name",
            "项目类型": "project_type",
            "项目名称": "project_name",
            "月初预计可能回款": "estimated_possible_payment_at_start",
            "月初预计确定回款": "estimated_confirmed_payment_at_start",
            "可能回款": "possible_payment",
            "确定回款": "confirmed_payment",
            "实际回款": "actual_payment",
            "回款节点确定": "payment_node_confirmed",
            "回款节点": "payment_node",
            "未回款金额": "unpaid_amount",
            "未完成原因": "incomplete_reason",
            "解决办法": "solution",
            "月初预计可能合同": "estimated_possible_at_start",
            "月初预计确定合同": "estimated_confirmed_at_start",
            "可能合同": "possible_contract",
            "确定合同": "confirmed_contract",
            "实际合同": "actual_contract",
            "完成情况": "completion_status",
            "合同节点": "contract_node",
            "未完成合同金额": "incomplete_contract_amount",
            "未完成合同原因": "incomplete_contract_reason",
        }
        self.init_db()
    
    def _translate_fields(self, data):
        """将中文字段名转换为英文字段名"""
        translated = {}
        for key, value in data.items():
            # 如果字段名是中文，转换为英文；否则保持原样
            translated_key = self.field_mapping.get(key, key)
            translated[translated_key] = value
        return translated

    # 1. 链接数据库
    def get_conn(self):
        return pymysql.connect(**self.config, cursorclass=pymysql.cursors.DictCursor)

    def _drop_unique_constraint(self, cur, table_name):
        """删除 UNIQUE 约束"""
        try:
            cur.execute("""
                SELECT CONSTRAINT_NAME FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND CONSTRAINT_TYPE = 'UNIQUE'
            """, (self.config["database"], table_name))
            constraints = cur.fetchall()
            
            for constraint in constraints:
                constraint_name = constraint["CONSTRAINT_NAME"]
                # 检查这个约束是否包含我们关心的列
                cur.execute(f"""
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                    WHERE TABLE_SCHEMA = %s 
                    AND TABLE_NAME = %s 
                    AND CONSTRAINT_NAME = %s
                    ORDER BY ORDINAL_POSITION
                """, (self.config["database"], table_name, constraint["CONSTRAINT_NAME"]))
                columns = {row["COLUMN_NAME"] for row in cur.fetchall()}
                if columns == {"responsible_person", "company_name", "project_name"}:
                    cur.execute(f"ALTER TABLE `{table_name}` DROP INDEX `{constraint['CONSTRAINT_NAME']}`")
                    print(f"  已删除 UNIQUE 约束: {constraint['CONSTRAINT_NAME']}")
                    break
        except:
            for name in ["unique_key", "responsible_person"]:
                try:
                    cur.execute(f"ALTER TABLE `{table_name}` DROP INDEX `{name}`")
                    break
                except:
                    continue

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
            # 回款表（移除 UNIQUE 约束，允许重复记录，id 自动递增）
            cur.execute("""CREATE TABLE IF NOT EXISTS payment_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                responsible_person VARCHAR(50),
                company_name VARCHAR(100),
                project_type VARCHAR(50),
                project_name VARCHAR(100),
                date DATE DEFAULT (CURRENT_DATE),
                estimated_possible_payment_at_start DECIMAL(15,2),
                estimated_confirmed_payment_at_start DECIMAL(15,2),
                possible_payment DECIMAL(15,2),
                confirmed_payment DECIMAL(15,2),
                actual_payment DECIMAL(15,2),
                payment_node_confirmed VARCHAR(50),
                payment_node VARCHAR(50),
                unpaid_amount DECIMAL(15,2),
                incomplete_reason TEXT,
                solution TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)""")
            
            # 删除已存在的 UNIQUE 约束（如果存在）
            self._drop_unique_constraint(cur, "payment_records")
            
            # 合同表（移除 UNIQUE 约束，允许重复记录，id 自动递增）
            cur.execute("""CREATE TABLE IF NOT EXISTS contract_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                responsible_person VARCHAR(50),
                company_name VARCHAR(100),
                project_type VARCHAR(50),
                project_name VARCHAR(100),
                date DATE DEFAULT (CURRENT_DATE),
                estimated_possible_at_start DECIMAL(15,2),
                estimated_confirmed_at_start DECIMAL(15,2),
                possible_contract DECIMAL(15,2),
                confirmed_contract DECIMAL(15,2),
                actual_contract DECIMAL(15,2),
                completion_status TEXT,
                contract_node VARCHAR(50),
                incomplete_contract_amount DECIMAL(15,2),
                incomplete_contract_reason TEXT,
                solution TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)""")
            
            # 删除已存在的 UNIQUE 约束（如果存在）
            self._drop_unique_constraint(cur, "contract_records")
        conn.commit()
        conn.close()
    # 3. 插入数据（新增记录，id 自动递增）
    def insert(self, category, data):
        """
        插入新数据（新增记录）
        :param category: 数据类别（"payment" 或 "contract"）
        :param data: 数据字典
        :return: 是否成功
        """
        table = self.table_map.get(category)
        if not table:
            print(f"⚠️ 未知的数据类别: {category}")
            return False
        
        # 将中文字段名转换为英文
        translated_data = self._translate_fields(data)
        
        # 检查必需字段
        required_fields = ['responsible_person', 'company_name', 'project_name']
        missing_fields = [f for f in required_fields if not translated_data.get(f)]
        if missing_fields:
            print(f"⚠️ 缺少必需字段: {missing_fields}")
            print(f"   输入数据: {data}")
            print(f"   转换后数据: {translated_data}")
            return False
        
        keys = list(translated_data.keys())
        placeholders = ", ".join(["%s"] * len(keys))
        
        # 纯 INSERT，不更新已存在的记录
        sql = f"""
            INSERT INTO {table} ({', '.join([f'`{k}`' for k in keys])})
            VALUES ({placeholders})
        """
        
        return self._execute(sql, [translated_data[k] for k in keys], show_sql=True)


    # 4. 修改数据 (根据 responsible_person+company_name+project_name 定位)
    def update(self, category, data):
        """更新数据"""
        table = self.table_map.get(category)
        if not table:
            return False
        
        translated = self._translate_fields(data)
        fields = ", ".join([f"`{k}`=%s" for k in translated.keys()])
        person = translated.get('responsible_person')
        company = translated.get('company_name')
        project = translated.get('project_name')
        sql = f"UPDATE {table} SET {fields} WHERE responsible_person=%s AND company_name=%s AND project_name=%s"
        params = list(translated.values()) + [person, company, project]
        return self._execute(sql, params)

    # 5. 删除数据
    def delete(self, category, data):
        """
        根据提供的字段匹配删除数据（支持中英文字段名）
        示例：db.delete("payment", {"负责人": "张三", "项目名称": "ERP"})
        """
        table = self.table_map.get(category)
        print(type_nullable)
        data = {k: v for k, v in self._translate_fields(data).items() if v is not None and v != ''}
        
        if not table or not data:
            print("⚠️ 缺少分类或删除条件")
            return False

        where_sql = " AND ".join([f"`{k}`=%s" for k in data.keys()])
        sql = f"DELETE FROM {table} WHERE {where_sql}"
        return self._execute(sql, list(data.values()), show_sql=True)

    # 6. 查找功能
    def select(self, category, data=None):
            """
            动态查询：传入什么字段就查什么字段。
            示例：
            - db.select("payment", {"负责人": "张三"})
            - db.select("payment", {"公司名称": "A公司", "项目名称": "ERP"})
            - db.select("payment") # 查全表
            """
            table = self.table_map.get(category)
            sql = f"SELECT * FROM {table}"
            params = []

            # 如果提供了查询条件
            if data:
                data = self._translate_fields(data) # 自动中转英并过滤空值
                if data:
                    # 动态拼装 WHERE `key1`=%s AND `key2`=%s
                    where_sql = " AND ".join([f"`{k}`=%s" for k in data.keys()])
                    sql += f" WHERE {where_sql}"
                    params = list(data.values())

            # 执行查询
            with self.get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    return cur.fetchall()

    def _execute(self, sql, params, show_sql=False):
        """执行 SQL"""
        conn = self.get_conn()
        try:
            with conn.cursor() as cur:
                if show_sql:
                    print(f"SQL: {sql}\n参数: {params}")
                affected = cur.execute(sql, params)
                if show_sql and affected > 0:
                    msg = {"DELETE": "删除", "INSERT": "插入", "UPDATE": "更新"}.get(
                        sql.strip().upper().split()[0], "操作")
                    print(f"✅ {msg}成功，影响了 {affected} 条记录")
            conn.commit()
            return True
        except pymysql.err.IntegrityError as e:
            if e.args[0] == 1062:
                print(f"⚠️ 数据已存在")
            else:
                print(f"⚠️ 数据完整性错误: {e.args[1]}")
            return False
        except Exception as e:
            print(f"❌ 操作失败: {e}")
            return False
        finally:
            conn.close()

# ================= 使用示例 =================
if __name__ == "__main__":
    db_config = {
        "host": "localhost", "user": "root", "password": "qwer1234", "database": "sell_report"
    }
    db = SimpleDBManager(db_config)
    
    # 插入示例（使用中文字段名，会自动转换为英文）
    test_data = {
        "负责人": "张三",
        "公司名称": "A公司",
        "项目类型": "软件",
        "项目名称": "ERP",
        "实际回款": 5000
    }
    print("=" * 60)
    result = db.insert("回款", test_data)

  
    print("\n" + "=" * 60)
    print("查询数据")
    print("=" * 60)
    results = db.select("回款", {"负责人": "张三"})
    print(f"查询到 {len(results)} 条记录")
    for row in results:
        print(f"  ID: {row['id']}, 负责人: {row['responsible_person']}, 公司: {row['company_name']}, 项目: {row['project_name']}, 回款: {row['actual_payment']}")

