# 天气 Skill（示范）

本技能用于**示范**：在 Cursor 里接入一个可用的天气技能，通过脚本调用 Open-Meteo 免费 API 查询城市天气。

## 使用方法

1. **在对话里直接问天气**，例如：
   - 「今天北京天气怎么样」
   - 「上海现在多少度」
   - 「深圳明天会下雨吗」
2. Agent 会按 `.cursor/skills/weather-skill/SKILL.md` 的说明，运行 `scripts/get_weather.py <城市名>` 获取数据，并整理成中文回复。

## 手动测试脚本

在项目根目录执行：

```bash
python .cursor/skills/weather-skill/scripts/get_weather.py 北京
```

成功时会输出 JSON，例如：

```json
{
  "city": "北京",
  "temperature_2m": 5.2,
  "apparent_temperature": 3.1,
  "relative_humidity_2m": 45,
  "weather_desc": "晴"
}
```

若输出 `"error": "获取天气失败"`，请检查本机网络；可加 `--debug` 查看详细错误：

```bash
python .cursor/skills/weather-skill/scripts/get_weather.py 北京 --debug
```

## 依赖

- Python 3
- 推荐安装 `httpx`：`pip install httpx`（未安装时会尝试使用标准库 `urllib`）
- 无需 API Key（使用 [Open-Meteo](https://open-meteo.com/) 免费接口）

## 文件说明

| 文件 | 说明 |
|------|------|
| `SKILL.md` | 技能说明：何时用、如何调脚本、如何组织回复 |
| `scripts/get_weather.py` | 查询脚本：根据城市名获取当前天气并输出 JSON |
| `README.md` | 本说明 |
