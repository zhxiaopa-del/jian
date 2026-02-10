"""
数据库列名迁移脚本：将中文列名改为英文列名
"""
import pymysql

# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "qwer1234",
    "database": "sell_report"
}

# 回款表列名映射
PAYMENT_COLUMN_MAPPING = {
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
    "创建时间": "created_at",
    "更新时间": "updated_at"
}

# 合同表列名映射
CONTRACT_COLUMN_MAPPING = {
    "负责人": "responsible_person",
    "公司名称": "company_name",
    "项目类型": "project_type",
    "项目名称": "project_name",
    "月初预计可能合同": "estimated_possible_at_start",
    "月初预计确定合同": "estimated_confirmed_at_start",
    "可能合同": "possible_contract",
    "确定合同": "confirmed_contract",
    "实际合同": "actual_contract",
    "完成情况": "completion_status",
    "合同节点": "contract_node",
    "未完成合同金额": "incomplete_contract_amount",
    "未完成合同原因": "incomplete_contract_reason",
    "解决办法": "solution",
    "创建时间": "created_at",
    "更新时间": "updated_at"
}


def get_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)


def check_column_exists(conn, table_name, column_name):
    """检查列是否存在"""
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT COUNT(*) as count 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = %s 
            AND COLUMN_NAME = %s
        """, (DB_CONFIG["database"], table_name, column_name))
        result = cur.fetchone()
        return result["count"] > 0


def rename_column(conn, table_name, old_name, new_name, column_type):
    """重命名列"""
    with conn.cursor() as cur:
        # 检查旧列是否存在，新列是否不存在
        old_exists = check_column_exists(conn, table_name, old_name)
        new_exists = check_column_exists(conn, table_name, new_name)
        
        if old_exists and not new_exists:
            sql = f"ALTER TABLE `{table_name}` CHANGE `{old_name}` `{new_name}` {column_type}"
            print(f"  重命名: {old_name} -> {new_name}")
            try:
                cur.execute(sql)
                return True
            except Exception as e:
                print(f"  错误: 重命名失败 - {e}")
                print(f"  SQL: {sql}")
                raise
        elif new_exists:
            print(f"  跳过: {new_name} 已存在（旧列 {old_name} 不存在）")
            return False
        else:
            print(f"  警告: {old_name} 不存在")
            return False


def get_column_type(conn, table_name, column_name):
    """获取列的数据类型"""
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, EXTRA
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = %s 
            AND COLUMN_NAME = %s
        """, (DB_CONFIG["database"], table_name, column_name))
        result = cur.fetchone()
        if result:
            col_type = result["COLUMN_TYPE"]
            nullable = result["IS_NULLABLE"]
            default = result["COLUMN_DEFAULT"]
            extra = result.get("EXTRA", "")
            
            # 构建完整的列定义
            type_def = col_type
            if nullable == "NO":
                type_def += " NOT NULL"
            
            # 处理默认值
            if default is not None:
                # CURRENT_TIMESTAMP 是函数，不需要引号
                if str(default).upper() == "CURRENT_TIMESTAMP":
                    type_def += " DEFAULT CURRENT_TIMESTAMP"
                elif isinstance(default, str):
                    # 检查是否是日期时间相关的默认值
                    if default.upper() in ("CURRENT_TIMESTAMP", "NOW()"):
                        type_def += f" DEFAULT {default.upper()}"
                    else:
                        type_def += f" DEFAULT '{default}'"
                else:
                    type_def += f" DEFAULT {default}"
            
            # 处理 ON UPDATE CURRENT_TIMESTAMP
            if extra and "on update CURRENT_TIMESTAMP" in extra.lower():
                type_def += " ON UPDATE CURRENT_TIMESTAMP"
            
            return type_def
        return None


def add_date_column(conn, table_name, column_name="date", after_column="project_name"):
    """添加日期列到表中，默认值为当天"""
    with conn.cursor() as cur:
        # 检查列是否已存在
        if check_column_exists(conn, table_name, column_name):
            print(f"  跳过: {column_name} 列已存在")
            return False
        
        # 检查 after_column 是否存在
        if not check_column_exists(conn, table_name, after_column):
            # 如果指定的列不存在，尝试使用 created_at
            if check_column_exists(conn, table_name, "created_at"):
                after_column = "created_at"
            else:
                after_column = None
        
        # 构建 SQL，设置默认值为当前日期
        # MySQL 5.7+ 支持 DEFAULT (CURRENT_DATE)，MySQL 8.0+ 支持 DEFAULT (CURRENT_DATE)
        if after_column:
            sql = f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` DATE DEFAULT (CURRENT_DATE) AFTER `{after_column}`"
        else:
            sql = f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` DATE DEFAULT (CURRENT_DATE)"
        
        try:
            print(f"  添加列: {column_name} (DATE, 默认值: 当天)")
            cur.execute(sql)
            return True
        except Exception as e:
            # 如果 DEFAULT (CURRENT_DATE) 不支持，尝试使用触发器方式
            # 或者使用 DEFAULT NULL，然后在应用层处理
            print(f"  警告: 使用 DEFAULT (CURRENT_DATE) 失败，尝试使用 DEFAULT NULL: {e}")
            try:
                if after_column:
                    sql = f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` DATE DEFAULT NULL AFTER `{after_column}`"
                else:
                    sql = f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` DATE DEFAULT NULL"
                cur.execute(sql)
                print(f"  添加列: {column_name} (DATE, 默认值: NULL)")
                return True
            except Exception as e2:
                print(f"  错误: 添加列失败 - {e2}")
                print(f"  SQL: {sql}")
                raise


def migrate_table(conn, table_name, column_mapping):
    """迁移表的列名"""
    print(f"\n迁移表: {table_name}")
    print("=" * 60)
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for old_name, new_name in column_mapping.items():
        try:
            # 检查旧列是否存在
            if check_column_exists(conn, table_name, old_name):
                # 获取列类型
                col_type = get_column_type(conn, table_name, old_name)
                if col_type:
                    if rename_column(conn, table_name, old_name, new_name, col_type):
                        success_count += 1
                    else:
                        skip_count += 1
                else:
                    print(f"  错误: 无法获取 {old_name} 的类型")
                    error_count += 1
            else:
                # 检查新列是否已存在
                if check_column_exists(conn, table_name, new_name):
                    print(f"  跳过: {new_name} 已存在（旧列 {old_name} 不存在）")
                    skip_count += 1
                else:
                    print(f"  警告: {old_name} 和 {new_name} 都不存在")
        except Exception as e:
            print(f"  错误: 处理 {old_name} -> {new_name} 时出错: {e}")
            error_count += 1
    
    print(f"\n完成: 成功 {success_count} 个，跳过 {skip_count} 个，错误 {error_count} 个")
    return success_count, skip_count, error_count


def main():
    """主函数"""
    print("=" * 60)
    print("数据库列名迁移：中文 -> 英文")
    print("=" * 60)
    
    try:
        conn = get_connection()
        
        # 迁移回款表
        migrate_table(conn, "payment_records", PAYMENT_COLUMN_MAPPING)
        
        # 迁移合同表
        migrate_table(conn, "contract_records", CONTRACT_COLUMN_MAPPING)
        
        # 添加日期列
        print("\n" + "=" * 60)
        print("添加日期列")
        print("=" * 60)
        add_date_column(conn, "payment_records", "date", "project_name")
        add_date_column(conn, "contract_records", "date", "project_name")
        
        # 提交更改
        conn.commit()
        print("\n" + "=" * 60)
        print("迁移完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n错误: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
