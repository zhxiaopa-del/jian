#!/usr/bin/env python3
"""查询城市当前天气（Open-Meteo 免费 API，无需 Key）。用法: python get_weather.py <城市名>"""
import sys
import json

try:
    import httpx
except ImportError:
    try:
        import urllib.request
        import urllib.parse
    except Exception:
        pass
    httpx = None

# 常见城市经纬度
CITY_LATLON = {
    "北京": (39.9042, 116.4074),
    "上海": (31.2304, 121.4737),
    "深圳": (22.5431, 114.0579),
    "广州": (23.1291, 113.2644),
    "杭州": (30.2741, 120.1551),
    "成都": (30.5728, 104.0668),
    "武汉": (30.5928, 114.3055),
    "西安": (34.3416, 108.9398),
    "南京": (32.0603, 118.7969),
    "苏州": (31.2989, 120.5853),
}


def geocode_city(name: str) -> tuple[float, float] | None:
    """用 Open-Meteo 地理编码 API 查城市经纬度。"""
    if not name or not name.strip():
        return None
    name = name.strip()
    if name in CITY_LATLON:
        return CITY_LATLON[name]
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": name, "count": 1, "language": "zh"}
    try:
        if httpx:
            r = httpx.get(url, params=params, timeout=8)
            data = r.json()
        else:
            qs = urllib.parse.urlencode({"name": name, "count": 1, "language": "zh"})
            req = urllib.request.Request(f"{url}?{qs}")
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
        results = data.get("results") or []
        if not results:
            return None
        lat = results[0].get("latitude")
        lon = results[0].get("longitude")
        if lat is not None and lon is not None:
            return (float(lat), float(lon))
    except Exception:
        pass
    return None


def get_weather(lat: float, lon: float) -> dict | None:
    """用 Open-Meteo 获取当前天气。"""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code",
    }
    try:
        if httpx:
            r = httpx.get(url, params=params, timeout=8)
            data = r.json()
        else:
            q = urllib.parse.urlencode(params)
            req = urllib.request.Request(f"{url}?{q}")
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
        return data.get("current")
    except Exception as e:
        if "--debug" in sys.argv:
            print(json.dumps({"error": "get_weather failed", "detail": str(e)}, ensure_ascii=False), file=sys.stderr)
        return None


WEATHER_DESC = {
    0: "晴", 1: "大部晴", 2: "少云", 3: "多云",
    45: "雾", 48: "雾",
    51: "毛毛雨", 53: "毛毛雨", 55: "毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    71: "小雪", 73: "中雪", 75: "大雪",
    80: "阵雨", 81: "阵雨", 82: "强阵雨",
    95: "雷雨", 96: "雷雨伴冰雹", 99: "强雷雨伴冰雹",
}


def main():
    city = " ".join(sys.argv[1:]).strip() or "北京"
    coords = geocode_city(city)
    if not coords:
        print(json.dumps({"error": f"未找到城市: {city}"}, ensure_ascii=False))
        sys.exit(1)
    lat, lon = coords
    cur = get_weather(lat, lon)
    if not cur:
        print(json.dumps({"error": "获取天气失败（请检查网络或稍后重试）"}, ensure_ascii=False))
        sys.exit(1)
    code = cur.get("weather_code", 0)
    desc = WEATHER_DESC.get(code, f"天气码{code}")
    out = {
        "city": city,
        "temperature_2m": cur.get("temperature_2m"),
        "apparent_temperature": cur.get("apparent_temperature"),
        "relative_humidity_2m": cur.get("relative_humidity_2m"),
        "weather_desc": desc,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
