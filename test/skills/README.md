# skills

本项目使用 **Cursor 技能（Skills）**：在 Cursor 中打开本仓库时，AI 会自动加载项目内技能，用于天气、酒店查询、桌面文件等生活与出行场景。

## 项目内技能

| 技能 | 路径 | 说明 |
|------|------|------|
| 天气生活小助手 | [.cursor/skills/weather-life-assistant/](.cursor/skills/weather-life-assistant/) | 对接天气预报，按地区/日期/时间给出天气与穿衣、雨具、运动、洗车晾晒等生活建议 |
| 酒店查询 | [.cursor/skills/hotel-query/](.cursor/skills/hotel-query/) | 按城市、入住退房日期收集需求，通过搜索或平台指引给出酒店建议与比价链接 |
| 桌面文件 | [.cursor/skills/desktop-files/](.cursor/skills/desktop-files/) | 查看、统计或整理桌面文件，按类型/日期分类、给出整理建议 |

在 Cursor 对话里问「北京明天天气」「穿什么」「北京有什么酒店」「2 月 1 号住两晚」「桌面有什么文件」等问题时，Agent 会按对应技能的说明执行。

## 快速使用（在项目根目录执行）

**天气 + 穿衣建议**
```bash
python3 .cursor/skills/weather-life-assistant/scripts/weather_clothing.py -i
python3 .cursor/skills/weather-life-assistant/scripts/weather_clothing.py 北京 明天
python3 .cursor/skills/weather-life-assistant/scripts/get_weather.py 北京
```

**酒店查询（生成查询摘要与携程链接）**  
在项目根目录任选一种方式：
```bash
# 方式一：根目录入口（推荐）
python3 run_hotel_query.py 北京 2025-02-01 2025-02-03

# 方式二：带完整路径
python3 .cursor/skills/hotel-query/scripts/search_hotels.py 北京 2025-02-01 2025-02-03
```

## 部署到 Dify

若希望 Dify 的 Agent 也能「自动识别」并调用这些 skills，请使用 **OpenAPI 自定义工具** 方式：启动本仓库提供的 HTTP API，在 Dify 中导入其 OpenAPI Schema 即可。详见 **[dify/README.md](dify/README.md)**。

## 目录说明

- **`.cursor/skills/`**：Cursor 项目技能目录，内含各技能的 SKILL.md、reference.md 与脚本；Cursor 在本项目中会自动加载这些技能。
- **`dify/`**：Dify 部署说明与 API 服务，供 Dify 以自定义工具形式调用本仓库 skills。