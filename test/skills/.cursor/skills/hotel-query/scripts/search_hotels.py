#!/usr/bin/env python3
"""
酒店查询辅助：根据城市与日期生成查询摘要与搜索链接，供用户或 Agent 在平台查价。
用法: python3 search_hotels.py <城市> [入住日期] [退房日期]
日期格式: YYYY-MM-DD 或 今天/明天；不传则只按城市输出。
"""

import sys
from urllib.parse import quote

def main():
    args = [a.strip() for a in sys.argv[1:] if a.strip()]
    if not args:
        print("用法: python3 search_hotels.py <城市> [入住日期] [退房日期]", file=sys.stderr)
        print("示例: python3 search_hotels.py 北京 2025-02-01 2025-02-03", file=sys.stderr)
        sys.exit(1)

    city = args[0]
    check_in = args[1] if len(args) > 1 else ""
    check_out = args[2] if len(args) > 2 else ""

    print("【酒店查询】")
    print(f"目的地: {city}")
    if check_in:
        print(f"入住: {check_in}")
    if check_out:
        print(f"退房: {check_out}")
    print()

    # 生成可点击或复制的搜索链接（中文需编码）
    base = "https://www.ctrip.com"
    path = f"/hotels/list?city={quote(city)}"
    if check_in:
        path += f"&checkin={check_in}"
    if check_out:
        path += f"&checkout={check_out}"
    print("携程查询链接（仅供参考）:")
    print(f"  {base}{path}")
    print()
    print("建议同时到 美团酒店、飞猪、Booking 比价后下单。")

if __name__ == "__main__":
    main()
