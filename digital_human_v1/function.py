# -*- coding: utf-8 -*-
"""
工具函数：当地时间、当地天气。默认城市为烟台。
"""
from datetime import datetime
import requests

# 默认城市：烟台（可改为其他城市名，用于天气查询）
DEFAULT_CITY = "烟台"

# 烟台大致经纬度（用于开放天气 API）
CITY_COORDS = {
    "烟台": (37.45, 121.43),
}


def current_time():
    """获取当地当前时间（本机时区）。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _coords_for_city(city):
    """获取城市经纬度，无则返回烟台。"""
    if city in CITY_COORDS:
        return CITY_COORDS[city]
    return CITY_COORDS[DEFAULT_CITY]


def get_weather(city=None):
    """
    获取当地天气，默认烟台。
    使用 Open-Meteo 免费 API，无需 key。
    返回简短描述字符串，失败返回错误提示。
    """
    city = city or DEFAULT_CITY
    lat, lon = _coords_for_city(city)
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,weather_code"
            "&timezone=Asia/Shanghai"
        )
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        cur = data.get("current", {})
        temp = cur.get("temperature_2m")
        humidity = cur.get("relative_humidity_2m")
        code = cur.get("weather_code", 0)
        # 常见 weather_code 简化为描述
        if code in (0,): desc = "晴"
        elif code in (1, 2, 3): desc = "少云/多云"
        elif code in (45, 48): desc = "雾"
        elif code in (51, 53, 55, 56, 57): desc = "毛毛雨"
        elif code in (61, 63, 65, 66, 67): desc = "雨"
        elif code in (71, 73, 75, 77): desc = "雪"
        elif code in (80, 81, 82): desc = "阵雨"
        elif code in (95, 96, 99): desc = "雷雨"
        else: desc = "未知"
        parts = [f"{city}：{desc}"]
        if temp is not None:
            parts.append(f"{temp}°C")
        if humidity is not None:
            parts.append(f"湿度{humidity}%")
        return "，".join(parts)
    except Exception as e:
        return f"{city}天气获取失败：{e}"
