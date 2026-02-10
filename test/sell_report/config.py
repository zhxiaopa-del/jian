"""
统一配置文件
包含数据库配置、OpenAI配置等公共配置
"""

# ================= 数据库配置 =================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "qwer1234",
    "database": "sell_report",
    "charset": "utf8mb4"
}

# ================= OpenAI 配置 =================
OPENAI_CONFIG = {
    "base_url": "http://10.3.0.16:8100/v1",
    "api_key": "222442bb160d5081b9e38506901d6889",
    "model": "qwen3-14b",
    "timeout": 60.0
}

# ================= 列名映射：英文 -> 中文（用于表格显示）=================
COLUMN_MAPPING = {
    'responsible_person': '负责人',
    'company_name': '公司名称',
    'project_type': '项目类型',
    'project_name': '项目名称',
    'date': '日期',
    'estimated_possible_payment_at_start': '月初预计可能回款',
    'estimated_confirmed_payment_at_start': '月初预计确定回款',
    'possible_payment': '可能回款',
    'confirmed_payment': '确定回款',
    'actual_payment': '实际回款',
    'payment_node_confirmed': '回款节点确定',
    'payment_node': '回款节点',
    'unpaid_amount': '未回款金额',
    'incomplete_reason': '未完成原因',
    'solution': '解决办法',
    'estimated_possible_at_start': '月初预计可能合同',
    'estimated_confirmed_at_start': '月初预计确定合同',
    'possible_contract': '可能合同',
    'confirmed_contract': '确定合同',
    'actual_contract': '实际合同',
    'completion_status': '完成情况',
    'contract_node': '合同节点',
    'incomplete_contract_amount': '未完成合同金额',
    'incomplete_contract_reason': '未完成合同原因',
}

# ================= 列名映射：中文 -> 英文（用于数据输入和显示）=================
CHINESE_TO_ENGLISH_MAPPING = {
    '负责人': 'responsible_person',
    '公司名称': 'company_name',
    '项目类型': 'project_type',
    '项目名称': 'project_name',
    '日期': 'date',
    '月初预计可能回款': 'estimated_possible_payment_at_start',
    '月初预计确定回款': 'estimated_confirmed_payment_at_start',
    '可能回款': 'possible_payment',
    '确定回款': 'confirmed_payment',
    '实际回款': 'actual_payment',
    '回款节点确定': 'payment_node_confirmed',
    '回款节点': 'payment_node',
    '未回款金额': 'unpaid_amount',
    '未完成原因': 'incomplete_reason',
    '解决办法': 'solution',
    '月初预计可能合同': 'estimated_possible_at_start',
    '月初预计确定合同': 'estimated_confirmed_at_start',
    '可能合同': 'possible_contract',
    '确定合同': 'confirmed_contract',
    '实际合同': 'actual_contract',
    '完成情况': 'completion_status',
    '合同节点': 'contract_node',
    '未完成合同金额': 'incomplete_contract_amount',
    '未完成合同原因': 'incomplete_contract_reason',
}

