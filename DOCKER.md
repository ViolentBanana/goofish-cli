# Docker 部署

本 fork 的完整安装入口：`bash scripts/setup-docker-codex.sh`，或在 Mac 双击 `安装并接入Codex.command`。自动完成容器部署、Codex MCP 注册和 Mac Chrome 登录态导入；Linux / 暂不登录时使用 `--skip-login`。使用提示词见 [README.md](./README.md)。

镜像按上游 uv.lock 安装依赖，并额外固定安装 filelock 3.16.1（上游 pyproject.toml 声明了它，但锁文件遗漏）。

源码版本：0.5.3，commit `fc8d1bbe36b2e66289331694bf3850bcddb47f3e`。

```sh
docker compose up -d --build
docker compose ps
docker exec goofish-cli goofish version
docker exec goofish-cli goofish --help
```

这是 CLI / MCP stdio 项目，没有 HTTP 地址或网页界面。容器常驻以供 `docker exec` 调用，健康检查验证 CLI 可以加载，不代表闲鱼账号已经登录。

## 一键导入 Mac Chrome 登录态（推荐）

1. 在 Mac Chrome 中打开 https://www.goofish.com 并登录。
2. 双击项目目录中的 `一键导入闲鱼登录.command`。
3. 如果 macOS 弹出 Chrome Safe Storage 钥匙串访问提示，请允许。等待窗口显示“成功：闲鱼登录有效”。

第一次会自动创建项目内的独立 Python 环境，并安装 browser-cookie3 0.20.1 和 TOML 配置解析依赖，以后复用。无需浏览器插件或手动复制 Cookie。仅提取闲鱼和淘宝域的 Cookie，通过标准输入传入容器，再用容器的密钥加密保存；没有明文 Cookie 导出文件。

如果读取失败，先在 Chrome 重新登录，再完全退出 Chrome 后重试。脚本会检查 Default 和 Profile 配置；要指定某个 Chrome 配置目录，可在终端运行：

```sh
./一键导入闲鱼登录.command --profile "Profile 1"
```

仅检查容器，不读取浏览器 Cookie：

```sh
./一键导入闲鱼登录.command --check-only
```

如果 macOS 阻止打开 `.command` 文件，可以右键选择“打开”，或者在终端进入项目目录，运行 `bash 一键导入闲鱼登录.command`。

## 手动导入登录态

先在你自己的浏览器登录 https://www.goofish.com，再将 Cookie 导出为 JSON 文件（支持 name/value/domain/path 列表或键值字典）。在终端运行，把第一行文件路径替换为实际路径：

```sh
docker cp /absolute/path/cookies.json goofish-cli:/tmp/import-cookies.json
docker exec --user root goofish-cli chown goofish:goofish /tmp/import-cookies.json
docker exec --user root goofish-cli chmod 600 /tmp/import-cookies.json
docker exec goofish-cli goofish auth login /tmp/import-cookies.json
docker exec goofish-cli rm -f /tmp/import-cookies.json
docker exec goofish-cli goofish auth status
```

容器无法直接读取 Mac 浏览器的登录态。不要导入在宿主机已加密的 goofish Cookie 文件，项目的加密密钥和主机名、用户名绑定。

登录态、设备 ID、限流和熔断状态均保存在 `goofish-cli-state` Docker volume。容器固定主机名和用户，使重建后仍可以解密。普通 `docker compose down` 会保留数据；`docker compose down -v` 会删除登录态。

## 调用命令

```sh
docker exec goofish-cli goofish list-commands --format json
docker exec goofish-cli goofish item get <商品ID>
docker exec -it goofish-cli goofish message watch
```

## MCP 客户端配置

容器启动后，将以下内容加入支持 stdio MCP 的客户端配置：

```json
{
  "mcpServers": {
    "goofish": {
      "command": "docker",
      "args": ["exec", "-i", "goofish-cli", "goofish-cli"]
    }
  }
}
```

MCP 使用 `-i`，不要加 `-t`。上面的 JSON 用于其他兼容客户端。安装入口会注册本机 Codex MCP；直接运行 docker compose 则不会修改客户端设置。

## 浏览器与平台

项目明确调用 Google Chrome（`channel="chrome"`）。镜像安装 Chrome、Node.js 和 Xvfb 虚拟显示器，保留项目默认的有窗口浏览器运行方式。Chrome Linux 版本需要 amd64，因此 Apple Silicon 上用 Docker 的 amd64 模拟运行，浏览器操作可能较慢。Xvfb 不提供可访问的桌面，项目的扫码登录窗口不会显示到 Mac；本部署使用 JSON Cookie 导入。

## 管理

```sh
docker compose stop
docker compose start
docker compose logs --tail 100
```

CLI 和 MCP 调用的错误直接输出在调用它们的终端或 MCP 客户端中。

## 运行验证

```sh
docker exec goofish-cli python /usr/local/lib/goofish/verify_runtime.py
# 登录后：
docker exec goofish-cli python /usr/local/lib/goofish/verify_runtime.py --require-login
```

验证 Chrome + Xvfb 启动和真实 MCP 握手/工具清单；加上 `--require-login` 后，调用 MCP 的 auth_status 检查账号是否有效。验证输出不包含 Cookie 或账号 ID。
