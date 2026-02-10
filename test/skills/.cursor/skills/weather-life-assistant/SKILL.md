---
name: weather-life-assistant
description: 对接天气预报并基于天气给出生活建议。在用户询问天气、穿衣、是否带伞、适宜运动、洗车晾晒等时使用。支持城市名或留空（按 IP 定位）。
---

# 天气生活小助手

本技能位于项目内 `.cursor/skills/weather-life-assistant/`，在本项目中打开 Cursor 对话时会被自动加载；回答天气、穿衣等问题时请按下面方式使用本技能。

## 何时使用

- 用户问「今天天气怎么样」「明天会下雨吗」「要不要带伞」
- 用户问「穿什么」「适合跑步吗」「能洗车/晾衣服吗」
- 用户需要出行、运动、穿衣、雨具等生活建议

## 输入地区 + 日期 + 时间，输出天气 + 穿衣建议

### 在项目根目录执行

项目根目录即本仓库 `skills` 的根。以下命令均在项目根目录执行：

**交互式（推荐）**：按提示输入地区、日期、时间

```bash
python3 .cursor/skills/weather-life-assistant/scripts/weather_clothing.py -i
# 可选：python3 .cursor/skills/weather-life-assistant/scripts/weather_clothing.py -i --api-key sk-xxx
```

**命令行**：直接传地区与日期

```bash
python3 .cursor/skills/weather-life-assistant/scripts/weather_clothing.py <地区> [日期] [--api-key KEY]
# 示例：python3 .cursor/skills/weather-life-assistant/scripts/weather_clothing.py 北京 明天
```

**仅查天气**：

```bash
python3 .cursor/skills/weather-life-assistant/scripts/get_weather.py [城市名]
```

输出：该时段的【天气】摘要 + 【穿衣建议】。传入 `--api-key` 时使用通义千问生成穿衣建议，否则用规则生成。穿衣与生活建议规则见本技能下的 [reference.md](reference.md)。

## 根据天气给生活建议（不跑脚本时）

若不便执行脚本，可根据用户描述或已有天气数据，按 [reference.md](reference.md) 的规则给出简短建议：

1. **穿衣**：按当日最高/最低或体感温度给一两条建议（见 reference 温度区间）。
2. **雨具**：有降水或降水概率高则提醒带伞/雨具。
3. **户外与运动**：雨、高温、严寒时提醒注意；适宜时鼓励户外/运动。
4. **洗车 / 晾晒**：有雨或高降水概率则建议改期；晴好可建议适宜。

回复保持简短、一条条列出。

## 回复示例结构

```
【天气】北京 晴，15°C，体感 14°C，紫外线中等。
【穿衣】长袖 + 薄外套即可。
【雨具】无需带伞。
【运动】适合户外跑步、散步。
【洗车/晾晒】适宜洗车和晾晒。
```

若用户只问某一项（如「要带伞吗」），只答该项即可。
