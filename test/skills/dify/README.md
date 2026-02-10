# 将 Skills 部署到 Dify，让 Dify 自动识别并调用

Dify **不会**自动扫描本仓库的 `.cursor/skills/` 目录。要让 Dify 使用这些 skills，需要把每个 skill 的能力暴露成 **Dify 可调用的工具**，常用有两种方式。

---

## 方式一：OpenAPI 自定义工具（推荐，零插件开发）

把 skills 通过 **HTTP API + OpenAPI 描述** 暴露出去，在 Dify 里添加为「自定义工具」，Agent 会根据接口的 `description` 自动选择何时调用。

### 1. 启动本仓库自带的 API 服务

从**项目根目录**（`skills/`）执行：

```bash
# 进入项目根
cd /path/to/skills

# 安装依赖（可选，仅运行 API 时需要）
pip install -r dify/requirements.txt

# 启动服务（默认 http://0.0.0.0:8000）
uvicorn dify.api_server:app --host 0.0.0.0 --port 8000 --app-dir .
```

或：

```bash
python -m uvicorn dify.api_server:app --host 0.0.0.0 --port 8000 --app-dir .
```

注意：`--app-dir .` 表示以当前目录为应用根目录，请务必在 **skills 项目根** 下执行上述命令，否则脚本路径会找不到。

服务启动后：

- **OpenAPI JSON**：`http://<你的主机>:8000/openapi.json`
- **文档**：`http://<你的主机>:8000/docs`

### 2. 在 Dify 里添加自定义工具

1. 打开 Dify → **工具** → **自定义工具** → **通过 OpenAPI Schema 导入**。
2. 填写 **Schema URL**：`http://<部署 API 的机器 IP 或域名>:8000/openapi.json`  
   （若 Dify 与 API 同机，可用 `http://127.0.0.1:8000/openapi.json`；云上部署则填公网 URL。）
3. 导入后，Dify 会根据 Schema 里的每个 `path` 生成一个工具，并利用其中的 `description`、`summary` 供 Agent 选择。
4. 在 **Agent 应用** 或 **工作流** 中，把这些工具加入「可用工具」，Agent 即可在对话中**自动识别**并调用（例如用户问天气时调用天气接口、问酒店时调用酒店接口）。

这样，Dify 的「自动识别」体现在：**由 LLM 根据工具描述和用户问题，决定调用哪个接口**，无需手写 if/else。

---

## 方式二：Dify Tool Plugin（开发插件，适合上架/复用）

把每个 skill 做成 Dify 的 **Tool 插件** 里的一个工具（一个 Provider 下可挂多个 Tool），在插件代码里调用本仓库的脚本或逻辑。

- 需要按照 [Dify 工具插件文档](https://docs.dify.ai/en/develop-plugin/dev-guides-and-walkthroughs/tool-plugin) 使用脚手架创建插件项目。
- 每个 skill 对应一个 Tool 的 YAML（name、description、parameters）+ 一段 Python `_invoke`，在 `_invoke` 里用 `subprocess` 或直接 import 调用 `.cursor/skills/xxx/scripts/` 下的脚本。
- 插件打包为 `.difypkg` 后在 Dify 中安装，即可在 Agent 里使用这些工具。

适合希望把「天气 / 酒店 / 订餐」等作为**独立插件**发布或复用的场景；若只是自用，方式一更简单。

---

## 小结

| 方式 | Dify 如何「识别」skills | 你需要做的 |
|------|--------------------------|------------|
| **OpenAPI 自定义工具** | Agent 根据 OpenAPI 里各接口的 description 自动选工具 | 启动 `dify/api_server.py`，在 Dify 里导入 `openapi.json`，把工具加到 Agent |
| **Tool Plugin** | 每个 skill 做成一个 Tool，Agent 看到的是插件里的工具列表 | 开发 Dify 插件并调用本仓库脚本，安装插件后在 Agent 中勾选工具 |

推荐先用 **方式一** 跑通，确认 Dify 能自动选到并调用「天气、酒店」等接口后，再按需考虑方式二。
