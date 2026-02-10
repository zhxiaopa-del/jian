---
name: weather-skill
description: 查询指定城市的当前天气（温度、体感、湿度、天气现象）。当用户问某地天气、气温、是否下雨、明天天气等时使用本技能。通过运行 scripts/get_weather.py 获取实时数据。
---

# 天气查询 Skill

## 何时使用

用户问题包含以下任一情况时使用本技能：
- 问「XX 天气」「XX 气温」「XX 明天会下雨吗」
- 问「今天/明天 北京/上海/深圳 天气」
- 问「某地多少度」「某地冷不冷」

## 操作步骤

1. **从用户问题中提取城市名**（如「北京」「上海」「深圳」；若未指明则默认「北京」）。
2. **运行天气脚本**（项目根目录下执行）：
   ```bash
   python .cursor/skills/weather-skill/scripts/get_weather.py <城市名>
   ```
   示例：`python .cursor/skills/weather-skill/scripts/get_weather.py 北京`
3. **根据脚本输出组织回复**：用简洁中文告诉用户当前温度、体感温度、相对湿度、天气现象（晴/阴/雨等），必要时加一句穿衣或出行建议。

## 脚本说明

- 脚本路径：`.cursor/skills/weather-skill/scripts/get_weather.py`
- 依赖：`httpx`（或 `requests`），无 API Key（使用 Open-Meteo 免费接口）。
- 若脚本报错（如网络超时、城市未找到），在回复中说明「暂时无法获取该城市天气」并建议稍后重试或换城市。

## 回复示例

脚本输出包含温度、天气现象时，可这样回复：

> **北京** 当前天气：晴，气温 **5°C**，体感 **3°C**，湿度 45%。早晚较冷，建议穿外套。
