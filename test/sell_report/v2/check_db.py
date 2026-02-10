#!/usr/bin/env python3
"""验证数据库中的数据"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent / "jian_digitalhuman_mcp-dev"
sys.path.insert(0, str(project_root))

from database import get_session, CollectionRecord, ContractRecord

session = get_session()

try:
    month = "2026-02"
    
    # 统计2026-02月份的数据
    collection_count = session.query(CollectionRecord).filter(CollectionRecord.month == month).count()
    contract_count = session.query(ContractRecord).filter(ContractRecord.month == month).count()
    
    print(f"2026-02月份的回款记录: {collection_count} 条")
    print(f"2026-02月份的合同记录: {contract_count} 条")
    
    print("\n最新的5条回款记录:")
    collections = session.query(CollectionRecord).filter(CollectionRecord.month == month).order_by(CollectionRecord.id.desc()).limit(5).all()
    for r in collections:
        print(f"  ID:{r.id}, {r.responsible_person}, {r.project_name}, 实际回款:{r.actual_collection}")
    
    print("\n最新的5条合同记录:")
    contracts = session.query(ContractRecord).filter(ContractRecord.month == month).order_by(ContractRecord.id.desc()).limit(5).all()
    for r in contracts:
        print(f"  ID:{r.id}, {r.responsible_person}, {r.project_name}, 实际合同:{r.actual_contract}")
        
finally:
    session.close()
