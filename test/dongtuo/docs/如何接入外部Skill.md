# 如何接入别人的 Skills（如 skillsmp 上的天气 Skill）

## 1. 技能放在哪里

Cursor 会从下面两个位置加载技能：

| 位置 | 路径 | 作用范围 |
|------|------|----------|
| **项目技能** | 项目根目录 `.cursor/skills/<技能名>/` | 仅当前项目 |
| **个人技能** | `~/.cursor/skills/<技能名>/` | 所有项目 |

接入别人的 skill 时，任选其一即可（例如只用当前项目就选「项目技能」）。

---

## 2. 接入步骤（以 skillsmp 天气技能为例）

### 步骤 1：打开技能页面并拿到内容

1. 打开：<https://skillsmp.com/zh/skills/moltbot-moltbot-skills-weather-skill-md>
2. 页面上会有该技能的 **SKILL.md** 全文（或「复制」「下载」按钮）。
3. 复制整份 **SKILL.md** 内容，或下载后得到的内容。

### 步骤 2：在本地建一个技能目录

在项目里用项目技能时：

```bash
mkdir -p .cursor/skills/weather-skill
```

若要用个人技能（所有项目都能用）：

```bash
mkdir -p ~/.cursor/skills/weather-skill
```

### 步骤 3：把内容保存成 SKILL.md

- 把步骤 1 里复制的**完整内容**（包含开头的 `---` 和 `name`、`description` 等）保存为：
  - 项目技能：`.cursor/skills/weather-skill/SKILL.md`
  - 个人技能：`~/.cursor/skills/weather-skill/SKILL.md`
- 若页面上还有「脚本」「参考文档」等文件，按页面说明放到同一目录下，例如：
  - `scripts/xxx.py`
  - `reference.md`

### 步骤 4：让 Cursor 识别到新技能

- 保存好 `SKILL.md` 后，Cursor 会自动扫描 `.cursor/skills/` 或 `~/.cursor/skills/`。
- 若没立刻出现，可：关掉再打开项目，或重启 Cursor。

---

## 3. 怎么「用」这个天气 Skill

接入后**不需要**在设置里再点选一次（只要放在上述目录即可）：

- 在对话里直接问和天气相关的问题，例如：
  - 「今天北京天气怎么样」
  - 「上海明天会下雨吗」
- Cursor 会根据技能里的 **description** 和内容，在合适的时候自动应用这个天气技能来回答。

技能里如果写了要调用的 API、脚本或 MCP，Agent 会按技能说明去执行（例如查天气接口、跑脚本等）。

---

## 4. 本项目里已为你准备的天气技能目录

当前项目里已经建好了一个空壳目录，方便你粘贴 skillsmp 的内容：

- **路径**：`.cursor/skills/weather-skill/`
- **你需要做的**：把 skillsmp 上该天气技能的 **SKILL.md** 全文复制进去，保存为  
  `.cursor/skills/weather-skill/SKILL.md`  
  若有其它文件（如脚本），按技能说明放到同目录下即可。

保存后，在该项目里问天气相关问题时，就会用到这个天气 Skill。

---

## 5. 小结

1. 从 skillsmp（或别处）**拿到** SKILL.md 全文。
2. 在 **`.cursor/skills/<技能名>/`**（或 `~/.cursor/skills/<技能名>/`）下新建目录，把内容存成 **SKILL.md**。
3. 若有脚本或参考文档，一并放进该目录。
4. 在对话里**直接问**技能相关的问题（如天气），Cursor 会自动按技能回答。

这样就算接入了别人的 skill，并正常使用。
