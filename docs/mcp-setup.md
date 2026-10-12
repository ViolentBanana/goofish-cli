# MCP 接入指南

<a id="codex-docker"></a>

## Codex：连接 Docker 中的闲鱼

如果已运行本 fork 的 `安装并接入Codex.command` 或 `scripts/setup-docker-codex.sh`，脚本已自动配置，直接重启 Codex，发送下面的测试提示词即可。不要重复添加同名服务。

### 桌面端：在设置中填写

1. 打开设置，找到 **MCP servers / MCP 服务器**。
2. 选择 **Add server / 添加服务器**。
3. 按下表填写，并保存、启用该服务器。

| 字段 | 内容 |
|---|---|
| Name | `goofish` |
| Transport | `STDIO` |
| Command | 终端运行 `command -v docker` 后得到的绝对路径；Mac Docker Desktop 常见为 `/usr/local/bin/docker` |
| Arguments | `exec`、`-i`、`goofish-cli`、`goofish-cli`，共 4 项 |

参数是多行输入时，每行填一项；单行输入时填 `exec -i goofish-cli goofish-cli`。不要把参数拼到 Command 里，不要添加 `-t`，也不要选择 HTTP 或填写服务器网址。

保存后完全退出并重新打开 Codex，新建一个本地聊天。桌面端和 CLI 使用同一台主机的 Codex 配置；不用在每个项目中重新添加。

### CLI：一条命令注册

已安装 Codex CLI、Docker 容器已运行的用户，可以在本机终端运行：

```bash
codex mcp add goofish -- "$(command -v docker)" exec -i goofish-cli goofish-cli
codex mcp list
```

列表中应出现 `goofish`，并处于启用状态。然后新开 Codex 会话；CLI 会话中可输入 `/mcp` 检查服务状态。

此命令只注册连接，不能代替 Docker 部署或账号登录。自动安装脚本另外设置了更长的调用超时和工具限制，完整设置见下方。已有自动配置时不要再执行注册命令，以免替换这些设置。

### 配置文件：复制 TOML

只有需要手动编辑时才使用此方法。打开 `~/.codex/config.toml`，在文件末尾追加下面这段，**保留已有内容**。如已设置 `CODEX_HOME`，则编辑该目录下的 `config.toml`。

```toml
[mcp_servers.goofish]
command = "/usr/local/bin/docker"
args = ["exec", "-i", "goofish-cli", "goofish-cli"]
startup_timeout_sec = 30
tool_timeout_sec = 180
default_tools_approval_mode = "prompt"
disabled_tools = ["auth_login", "auth_reset_guard", "message_watch", "skills_install"]
```

把 `command` 改成自己运行 `command -v docker` 得到的路径。如已有 `[mcp_servers.goofish]`，修改已有条目，不要追加第二个同名条目。保存后重启 Codex。

自动安装脚本会先备份现有配置，保留其他模型/MCP 设置；已有闲鱼配置被禁用，或连接、超时、权限设置不同时，会提示冲突并停止，避免覆盖你的设置。

上述 4 个管理或常驻工具留给用户在终端操作；正常的商品搜索、商品读取、发布、下架、会话查询及消息发送仍可用。写操作应先审核目标和内容，再由用户确认。

### 接入成功后怎么用？

在 Codex 的新聊天里发送：

```text
请使用 goofish MCP 检查我的闲鱼登录状态，再列出我的在售商品。
只查询，不修改或下架商品。
```

看到实际工具调用并返回登录状态、商品列表，才证明连接及登录都有效。若账号没有在售商品，返回空列表也是正常结果。更多可复制提示词见 [README](../README.md#可以直接复制给-codex-的-prompt)。

### 常见问题

| 现象 | 怎么处理 |
|---|---|
| Codex 没有看到 `goofish` | 确认已经保存并启用配置，然后重启、新建本地会话 |
| 找不到 `docker` | 在终端运行 `command -v docker`，把结果填入 Command |
| 容器没有运行 | 启动 Docker Desktop；在项目目录运行 `docker compose up -d` |
| MCP 已连接，但提示未登录 | Mac Chrome 登录闲鱼后，运行 `一键导入闲鱼登录.command`；其他系统参考 DOCKER.md |
| 搜索超时 | 在 MCP 配置中设置 `tool_timeout_sec = 180`，再重新加载 |
| 提示同名配置冲突 | 在 MCP 设置中检查旧的 `goofish`，确认容器命令、启用状态和工具限制；不要覆盖整个配置文件 |

官方配置说明：[OpenAI MCP 文档](https://learn.chatgpt.com/docs/extend/mcp?surface=app)。Docker 部署及 Cookie 导入：[DOCKER.md](../DOCKER.md)。

---


## OpenClaw / ClawHub

要求：OpenClaw `2026.6.1` 及以上，且 PATH 中可以执行 `uvx`。

ClawHub 发布后安装：

<!-- x-release-please-start-version -->
```bash
openclaw plugins install clawhub:openclaw-goofish
uvx --from goofish-cli==0.5.3 goofish auth login --qr
openclaw plugins inspect goofish --json
openclaw gateway restart
```
<!-- x-release-please-end -->

本地开发使用 link 安装：

```bash
openclaw plugins install -l /path/to/goofish-cli
openclaw plugins inspect goofish --json
```

`inspect` 应显示 `Format: bundle`、Codex subtype，以及 skills 和 MCP server 能力。
Gateway 重启后新会话中，工具名为 `goofish__<逻辑名>`，例如
`goofish__auth_status` 和 `goofish__item_get`。

bundle 默认过滤以下工具：

| 工具 | 原因 |
|---|---|
| `auth_login` | 会覆盖磁盘登录态，应由用户在终端执行 |
| `auth_reset_guard` | 恢复动作需要用户判断，且不能解除服务端风控 |
| `message_watch` | 常驻阻塞式连接，不适合作为单次 Agent tool |
| `skills_install` | bundle 已直接提供 skills，无需 Agent 再安装 |

OpenClaw `2026.7.1` 的 `openclaw mcp doctor` 只读取 `openclaw.json` 中的
`mcp.servers`，不会读取 bundle 的 `.mcp.json`；因此插件验收应使用 `plugins inspect`
和 embedded agent 新会话的 trajectory 工具目录，不要重复配置同一个 server
只为运行 doctor。验收时应看到 13 个 Goofish 业务工具，且不应看到上表的
4 个过滤工具。OpenClaw 还会为 MCP prompts/resources 生成
`goofish__prompts_*` 和 `goofish__resources_*` 4 个桥接工具，因此按
`goofish__*` 前缀统计的总数是 17，不代表 `toolFilter` 失效。

## Claude Code

在 `~/.claude/settings.json` 或项目 `.claude/settings.json` 加：

```json
{
  "mcpServers": {
    "goofish": {
      "command": "uvx",
      "args": ["goofish-cli"]
    }
  }
}
```

或本地开发版：

```json
{
  "mcpServers": {
    "goofish": {
      "command": "/Users/you/Desktop/goofish-cli/.venv/bin/goofish-cli"
    }
  }
}
```

## Cursor

`~/.cursor/mcp.json`：同上格式。

## 可用工具

启动后 Claude 获得以下 tool；skills 中使用 Claude 的
`mcp__goofish__<逻辑名>` 前缀：

| Tool 名 | 说明 |
|---|---|
| `auth_login` | 导入 cookie |
| `auth_status` | 检查登录态 |
| `auth_reset_guard` | 解除风控熔断 |
| `item_get` | 查询商品（只读） |
| `item_publish` | 发布商品（写） |
| `item_delete` | 下架商品（写） |
| `media_upload` | 上传图片 |
| `category_recommend` | AI 类目识别 |
| `location_default` | 获取默认地址 |

## 首次使用

1. 从 Chrome DevTools 导出 goofish.com cookie（JSON 数组）到本地文件
2. 跑一次 CLI 导入：`goofish auth login ~/Downloads/goofish-cookies.json`
3. Claude 会话里问："帮我查一下 itemId 1046118265141 的商品信息"
4. Claude 会自动调用 `item_get` tool

## 调试

列出所有注册的 tool：

```bash
python -c "
from goofish_cli.mcp_server import mcp, _register_all
import asyncio
_register_all()
for t in asyncio.run(mcp.list_tools()):
    print(t.name)
"
```
