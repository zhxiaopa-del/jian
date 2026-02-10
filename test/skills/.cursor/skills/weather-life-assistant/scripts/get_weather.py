#!/usr/bin/env python3
"""从 wttr.in 获取天气 JSON，输出简要摘要供生活小助手使用。用法: get_weather.py [城市名]"""

import json
import ssl
import sys
import urllib.request
from urllib.error import URLError
from urllib.parse import quote

def fetch(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": "curl/7.64.1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except URLError as e:
        if "CERTIFICATE_VERIFY_FAILED" in str(e) or "SSL" in str(e):
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                return resp.read().decode("utf-8")
        raise

def fetch_weather_data(location: str = ""):
    """请求 wttr.in 并返回解析后的天气 JSON。location 为空则按 IP 定位。"""
    url = f"https://wttr.in/{quote(location)}?format=j1" if location else "https://wttr.in/?format=j1"
    raw = fetch(url)
    return json.loads(raw)


def get_weather_for_day(location: str, day_index: int = 0):
    """
    获取指定地区、指定日期的天气摘要（供穿衣建议等使用）。
    day_index: 0=今天，1=明天，2=后天
    """
    data = fetch_weather_data(location)
    try:
        area = data.get("nearest_area", [{}])[0]
        location_name = (area.get("areaName", [{}])[0] or {}).get("value", location or "当前定位")
    except (KeyError, IndexError, TypeError):
        location_name = location or "当前定位"

    weather = data.get("weather", [])
    if day_index >= len(weather):
        day_index = 0
    day = weather[day_index]
    date = day.get("date", "?")
    maxtemp = day.get("maxtempC", "?")
    mintemp = day.get("mintempC", "?")
    hourly = day.get("hourly", [])
    chance = "?"
    if hourly:
        mid = min(12, len(hourly) - 1)
        chance = hourly[mid].get("chanceofrain", hourly[mid].get("chanceofprecip", "?"))
    desc = "—"
    feel = maxtemp
    if hourly:
        h = hourly[mid]
        desc = (h.get("weatherDesc", [{}])[0] or {}).get("value", "—")
        feel = h.get("FeelsLikeC", maxtemp)
    cur = data.get("current_condition", [{}])[0] if data.get("current_condition") else {}
    humidity = cur.get("humidity", "?")
    uv = cur.get("uvIndex", "?")

    summary_text = (
        f"{location_name} {date}：{desc}，气温 {mintemp}–{maxtemp}°C，体感约 {feel}°C，"
        f"降水概率 {chance}%，湿度 {humidity}%，紫外线指数 {uv}。"
    )
    return {
        "location_name": location_name,
        "date": date,
        "desc": desc,
        "temp_min": mintemp,
        "temp_max": maxtemp,
        "feel": feel,
        "precip_chance": chance,
        "humidity": humidity,
        "uv": uv,
        "summary_text": summary_text,
    }


def main():
    location = sys.argv[1].strip() if len(sys.argv) > 1 else ""
    if location:
        url = f"https://wttr.in/{quote(location)}?format=j1"
    else:
        url = "https://wttr.in/?format=j1"

    try:
        raw = fetch(url)
        data = json.loads(raw)
    except Exception as e:
        print(f"获取天气失败: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        cur = data.get("current_condition", [{}])[0]
        temp = cur.get("temp_C", "?")
        feelf = cur.get("FeelsLikeC", temp)
        desc = (cur.get("weatherDesc", [{}])[0] or {}).get("value", "—")
        precip = cur.get("precipMM", "0")
        humidity = cur.get("humidity", "?")
        uv = cur.get("uvIndex", "?")
        location_name = data.get("nearest_area", [{}])[0].get("areaName", [{}])[0].get("value", location or "当前定位")

        print(f"【位置】{location_name}")
        print(f"【当前】{desc}，{temp}°C，体感 {feelf}°C")
        print(f"【降水】{precip} mm，湿度 {humidity}%")
        print(f"【紫外线】{uv}")

        weather = data.get("weather", [])
        for i, day in enumerate(weather[:2]):
            date = day.get("date", "?")
            maxtemp = day.get("maxtempC", "?")
            mintemp = day.get("mintempC", "?")
            hourly = day.get("hourly", [])
            chance = "?"
            if hourly:
                mid = min(12, len(hourly) - 1)
                chance = hourly[mid].get("chanceofrain", hourly[mid].get("chanceofprecip", "?"))
            label = "今日" if i == 0 else "明日"
            print(f"【{label} {date}】{mintemp}–{maxtemp}°C，降水概率 {chance}%")
    except (KeyError, IndexError, TypeError) as e:
        print(f"解析天气数据异常: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
