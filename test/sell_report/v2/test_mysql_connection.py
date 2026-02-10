"""
直接测试MySQL数据库连接
"""

import sys

# MySQL数据库配置
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "qwer1234",
    "database": "sell_report",
    "charset": "utf8mb4"
}

# 检查pymysql是否安装
try:
    import pymysql
    print("[OK] pymysql已安装")
except ImportError:
    print("[ERROR] pymysql未安装，请运行: pip install pymysql")
    sys.exit(1)

# 测试连接
print("\n" + "="*50)
print("测试MySQL数据库连接")
print("="*50)
print(f"数据库配置:")
print(f"  主机: {DB_CONFIG['host']}")
print(f"  端口: {DB_CONFIG['port']}")
print(f"  用户: {DB_CONFIG['user']}")
print(f"  数据库: {DB_CONFIG['database']}")
print(f"  字符集: {DB_CONFIG['charset']}")
print()

try:
    # 先尝试连接MySQL服务器（不指定数据库）
    print("步骤1: 连接MySQL服务器...")
    temp_config = DB_CONFIG.copy()
    database_name = temp_config.pop("database")
    
    conn = pymysql.connect(**temp_config)
    print("[OK] MySQL服务器连接成功")
    
    # 检查数据库是否存在
    cursor = conn.cursor()
    cursor.execute("SHOW DATABASES LIKE %s", (database_name,))
    db_exists = cursor.fetchone()
    
    if db_exists:
        print(f"[OK] 数据库 '{database_name}' 已存在")
    else:
        print(f"[INFO] 数据库 '{database_name}' 不存在，将创建")
        cursor.execute(f"CREATE DATABASE `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
        print(f"[OK] 数据库 '{database_name}' 创建成功")
    
    cursor.close()
    conn.close()
    
    # 连接到指定数据库
    print("\n步骤2: 连接到指定数据库...")
    conn = pymysql.connect(**DB_CONFIG)
    print("[OK] 数据库连接成功")
    
    cursor = conn.cursor()
    
    # 检查表是否存在
    print("\n步骤3: 检查数据表...")
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print(f"[OK] 数据库中有 {len(tables)} 个表:")
    for table in tables:
        print(f"   - {table[0]}")
    
    # 检查回款表
    if ('payment_records',) in tables:
        cursor.execute("SELECT COUNT(*) FROM payment_records")
        payment_count = cursor.fetchone()[0]
        print(f"\n[OK] payment_records 表中有 {payment_count} 条记录")
        
        # 显示表结构
        cursor.execute("DESCRIBE payment_records")
        columns = cursor.fetchall()
        print(f"   表结构 ({len(columns)} 列):")
        for col in columns[:5]:  # 只显示前5列
            print(f"     - {col[0]} ({col[1]})")
    else:
        print("\n[WARN] payment_records 表不存在")
    
    # 检查合同表
    if ('contract_records',) in tables:
        cursor.execute("SELECT COUNT(*) FROM contract_records")
        contract_count = cursor.fetchone()[0]
        print(f"[OK] contract_records 表中有 {contract_count} 条记录")
        
        # 显示表结构
        cursor.execute("DESCRIBE contract_records")
        columns = cursor.fetchall()
        print(f"   表结构 ({len(columns)} 列):")
        for col in columns[:5]:  # 只显示前5列
            print(f"     - {col[0]} ({col[1]})")
    else:
        print("[WARN] contract_records 表不存在")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*50)
    print("[OK] 所有测试通过！MySQL连接正常")
    print("="*50)
    
except pymysql.Error as e:
    print(f"\n[ERROR] MySQL错误: {e}")
    print("\n错误代码:", e.args[0] if e.args else "未知")
    print("错误信息:", e.args[1] if len(e.args) > 1 else str(e))
    sys.exit(1)
    
except Exception as e:
    print(f"\n[ERROR] 连接失败: {e}")
    print("\n请检查:")
    print("1. MySQL服务是否运行")
    print("2. 用户名和密码是否正确 (当前密码: qwer1234)")
    print("3. 是否有权限创建数据库")
    print("4. 网络连接是否正常")
    print("5. 端口3306是否开放")
    import traceback
    traceback.print_exc()
    sys.exit(1)
