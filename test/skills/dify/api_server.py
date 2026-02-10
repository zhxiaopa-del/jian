"""
将本仓库 .cursor/skills 下的能力暴露为 HTTP API，供 Dify 通过 OpenAPI 自定义工具接入。
从项目根目录启动: uvicorn dify.api_server:app --host 0.0.0.0 --port 8000 --app-dir .
"""
import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

# 项目根目录（skills 仓库根）
PROJECT_ROOT = Path(__file__).resolve().parent.parent

app = FastAPI(
    title="Skills API for Dify",
    description="暴露天气、酒店查询等 skills，供 Dify Agent 作为自定义工具调用。",
    version="1.0.0",
)


def _run_script(script_path: Path, args: list[str], cwd: Path = PROJECT_ROOT) -> str:
    if not script_path.exists():
        return f"错误：脚本不存在 {script_path}"
    try:
        r = subprocess.run(
            [sys.executable, str(script_path)] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        out = (r.stdout or "").strip() or (r.stderr or "").strip()
        return out if out else f"退出码: {r.returncode}"
    except subprocess.TimeoutExpired:
        return "请求超时"
    except Exception as e:
        return f"执行异常: {e}"


# ---------- 天气 ----------
@app.get(
    "/weather",
    summary="查询天气",
    description="根据城市名查询当前及今明两日天气（温度、体感、降水、紫外线等）。用于用户问某地天气、今天明天天气时调用。",
)
def weather(city: str = Query(..., description="城市名，如 北京、烟台、Shanghai")) -> dict:
    script = PROJECT_ROOT / ".cursor/skills/weather-life-assistant/scripts/get_weather.py"
    out = _run_script(script, [city])
    return {"result": out}


class WeatherClothingBody(BaseModel):
    region: str = Field(..., description="地区/城市名")
    date: str = Field("今天", description="日期：今天/明天/后天 或 0/1/2")
    api_key: str = Field("", description="通义千问 API Key，不填则用规则生成穿衣建议")


@app.post(
    "/weather_clothing",
    summary="天气与穿衣建议",
    description="根据地区和日期返回该时段天气摘要及穿衣建议。用于用户问某地穿什么、明天天气怎么样时调用。",
)
def weather_clothing(body: WeatherClothingBody) -> dict:
    script = PROJECT_ROOT / ".cursor/skills/weather-life-assistant/scripts/weather_clothing.py"
    args = [body.region, body.date]
    if body.api_key:
        args.extend(["--api-key", body.api_key])
    out = _run_script(script, args)
    return {"result": out}


# ---------- 酒店 ----------
@app.get(
    "/hotels",
    summary="酒店查询",
    description="根据城市和入住退房日期生成酒店查询摘要与携程链接。用于用户问某地住哪、酒店价格、订房时调用。",
)
def hotels(
    city: str = Query(..., description="城市/目的地"),
    check_in: str = Query("", description="入住日期 YYYY-MM-DD"),
    check_out: str = Query("", description="退房日期 YYYY-MM-DD"),
) -> dict:
    script = PROJECT_ROOT / ".cursor/skills/hotel-query/scripts/search_hotels.py"
    args = [city]
    if check_in:
        args.append(check_in)
    if check_out:
        args.append(check_out)
    out = _run_script(script, args)
    return {"result": out}


# ---------- 健康检查（供 Dify 或负载均衡探测） ----------
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


# OpenAPI 会由 FastAPI 自动生成，Dify 填写 http://<host>:8000/openapi.json 即可导入
