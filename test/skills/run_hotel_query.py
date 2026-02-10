#!/usr/bin/env python3
"""
酒店查询入口：在项目根目录执行此脚本即可，会调用 .cursor/skills/hotel-query/scripts/search_hotels.py
用法: python3 run_hotel_query.py <城市> [入住日期] [退房日期]
示例: python3 run_hotel_query.py 北京 2025-02-01 2025-02-03
"""
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / ".cursor/skills/hotel-query/scripts/search_hotels.py"
if not SCRIPT.exists():
    print(f"未找到脚本: {SCRIPT}", file=sys.stderr)
    sys.exit(1)
sys.exit(subprocess.run([sys.executable, str(SCRIPT)] + sys.argv[1:]).returncode)
