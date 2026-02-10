#!/usr/bin/env python3
"""
输入地区、日期和时间，输出该时段的天气以及根据天气给出的穿衣建议。
用法: python weather_clothing.py <地区> [日期] [--api-key KEY] 或 python weather_clothing.py -i
"""

import argparse
import sys
from pathlib import Path
from typing import Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from get_weather import get_weather_for_day

TIME_MAP = {
    "今天": 0, "今日": 0, "0": 0,
    "明天": 1, "明日": 1, "1": 1,
    "后天": 2, "2": 2,
}


def parse_time(time_str: str) -> int:
    s = (time_str or "今天").strip()
    return TIME_MAP.get(s, 0)


def get_clothing_advice_with_llm(
    weather_summary: str,
    api_key: str,
    model_name: str = "qwen-turbo",
    time_of_day: str = "",
) -> str:
    try:
        from langchain_community.chat_models import ChatTongyi
    except ImportError:
        return _fallback_clothing_advice(weather_summary)

    llm = ChatTongyi(model_name=model_name, api_key=api_key or "")
    time_hint = ""
    if (t := (time_of_day or "").strip()):
        time_hint = f"\n用户关心的是「{t}」时段，请在该时段下给穿衣建议。\n"

    prompt = f"""你是一个贴心的生活小助手。请根据下面的【天气信息】，
给出简洁、实用的一小段穿衣建议（2～4 句即可），考虑温度、降水、紫外线等。
不要复述天气，只输出穿衣与出行装备建议。
{time_hint}
【天气信息】：
{weather_summary}

请直接输出穿衣建议，不要加「穿衣建议：」等前缀。"""

    messages = [
        {"role": "system", "content": "你只根据天气信息给出简短、实用的穿衣建议。"},
        {"role": "user", "content": prompt},
    ]
    try:
        response = llm.invoke(messages)
        return (response.content or "").strip()
    except Exception as e:
        print(f"LLM 调用失败，使用规则建议: {e}", file=sys.stderr)
        return _fallback_clothing_advice(weather_summary)


def _fallback_clothing_advice(weather_summary: str) -> str:
    text = weather_summary
    if "–" in text or "°C" in text:
        parts = text.replace("°C", " ").replace("–", " ").split()
        nums = [int(x) for x in parts if x.lstrip("-").isdigit()]
        max_temp = max(nums) if nums else 15
        if max_temp >= 28:
            return "建议短袖短裤，注意防晒和补水。"
        if max_temp >= 20:
            return "长袖或薄外套即可，早晚可加一件薄外套。"
        if max_temp >= 10:
            return "建议外套或针织衫，注意早晚保暖。"
        if max_temp >= 0:
            return "建议毛衣加厚外套或薄羽绒，注意保暖。"
        return "建议羽绒服、帽子围巾，注意防寒。"
    return "根据当日气温适当增减衣物，有雨请带伞。"


def run_interactive(api_key: str = "", model_name: str = "qwen-turbo") -> None:
    print("--- 天气穿衣小助手（交互） ---\n")
    region = input("请输入地区（城市名，如 北京 / Shanghai）：").strip()
    if not region:
        print("未输入地区，已退出。", file=sys.stderr)
        sys.exit(1)
    date_str = input("请输入日期（今天/明天/后天 或 0/1/2，回车默认今天）：").strip() or "今天"
    day_index = parse_time(date_str)
    time_of_day = input("请输入时间（可选：上午/下午/中午/晚上，回车跳过）：").strip()

    try:
        weather = get_weather_for_day(region, day_index)
    except Exception as e:
        print(f"获取天气失败: {e}", file=sys.stderr)
        sys.exit(1)

    summary = weather["summary_text"]
    print("\n【天气】")
    print(summary)
    print()
    if api_key:
        advice = get_clothing_advice_with_llm(summary, api_key, model_name, time_of_day=time_of_day)
    else:
        advice = _fallback_clothing_advice(summary)
    print("【穿衣建议】")
    print(advice)


def main():
    parser = argparse.ArgumentParser(description="按地区、日期与时间查询天气并给出穿衣建议")
    parser.add_argument("region", nargs="?", default="", help="地区/城市；不填则进入交互")
    parser.add_argument("date", nargs="?", default="", help="日期：今天/明天/后天 或 0/1/2")
    parser.add_argument("-i", "--interactive", action="store_true", help="交互式输入地区、日期、时间")
    parser.add_argument("--api-key", default="", help="通义千问 API Key")
    parser.add_argument("--model", default="qwen-turbo", help="模型名")
    args = parser.parse_args()

    if args.interactive or (not (args.region or "").strip() and not (args.date or "").strip()):
        run_interactive(api_key=args.api_key, model_name=args.model)
        return

    region = (args.region or "").strip()
    if not region:
        print("请提供地区，或使用 -i 进入交互模式。", file=sys.stderr)
        sys.exit(1)

    date_str = (args.date or "今天").strip()
    day_index = parse_time(date_str)
    try:
        weather = get_weather_for_day(region, day_index)
    except Exception as e:
        print(f"获取天气失败: {e}", file=sys.stderr)
        sys.exit(1)

    summary = weather["summary_text"]
    print("【天气】")
    print(summary)
    print()
    if args.api_key:
        advice = get_clothing_advice_with_llm(summary, args.api_key, args.model)
    else:
        advice = _fallback_clothing_advice(summary)
    print("【穿衣建议】")
    print(advice)


def weather_and_clothing(
    region: str,
    time_str: str = "今天",
    api_key: str = "",
    model_name: str = "qwen-turbo",
) -> Tuple[str, str]:
    day_index = parse_time(time_str)
    weather = get_weather_for_day(region.strip(), day_index)
    summary = weather["summary_text"]
    if api_key:
        advice = get_clothing_advice_with_llm(summary, api_key, model_name)
    else:
        advice = _fallback_clothing_advice(summary)
    return summary, advice


if __name__ == "__main__":
    main()
