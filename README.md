# Image Proxy Project

## 功能

- 本地图片上传到服务器，返回 URL，可直接用于 API 调用。
- 避免重复上传同一图片（客户端和服务器端双重去重）。
- 图片及缓存 30 天后自动过期（可通过配置修改）。
- 高性能服务器：FastAPI + Uvicorn。
- 客户端缓存使用 SQLite，避免 JSON 文件过大。
- 自动定时清理过期图片（可配置开启/关闭）。
- 稳定运行：systemd 管理，自动重启服务，开机自启。

---

## 文件结构

image_proxy_project/
├─ config/
│ └─ config.json # 全局配置文件
├─ server/
│ ├─ server.py # FastAPI 服务
│ ├─ cleanup.py # 服务器清理脚本
│ ├─ images.db # SQLite 数据库（首次运行自动生成）
│ └─ uploads/ # 上传图片存储目录
├─ client/
│ ├─ client.py # 客户端脚本
│ └─ cache.db # 客户端缓存数据库（首次运行自动生成）
├─ scripts/
│ └─ install.sh # 一键安装脚本
└─ README.md

---

## 配置文件说明

路径：`config/config.json`  

示例：
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "domain": "127.0.0.1"
  },
  "cleanup": {
    "enable": true,
    "interval_days": 1,
    "expire_days": 30,
    "cleanup_time": "03:00"
  }
}
```
__参数说明__
- server.host: FastAPI 服务绑定的 IP 地址。
- server.port: FastAPI 服务端口。
- server.domain: 客户端访问服务器的域名或 IP，用于生成图片 URL。
- cleanup.enable: 是否开启定期清理过期图片。
- cleanup.interval_days: 清理任务执行间隔（天）。
- cleanup.expire_days: 图片和缓存过期天数。
- cleanup.cleanup_time: 每日清理时间（HH:MM 格式），仅当 enable=true 时生效。
---
## 项目安装 
__克隆或下载项目：__

```bash
git clone <repo_url>
cd image_proxy_project
```
---
## 服务器端使用
1. __编辑 config/config.json 配置服务器和清理参数。__
2. __执行一键安装脚本：__
  ```bash
  cd scripts
  chmod +x install.sh
  ./install.sh
  ```
  FastAPI 服务将启动，并由 systemd 管理，自动重启和开机自启。
  如果开启了定期清理，systemd timer 将每天按配置时间执行。
3. __日志__
FastAPI 服务日志：/var/log/image_proxy/fastapi.log
定时清理日志：通过 systemd journal 查看
```bash
journalctl -u fastapi-cleanup --no-pager -f
```
---
## 客户端使用
``` bash
cd client
python3 client.py
```
    可将上述示例代码集成到自己的项目中。
    客户端将读取 config.json 中的 server.domain 和 port。
    上传图片后返回 URL，可直接用于你的 API。
    客户端会自动缓存图片 URL，避免重复上传。
---
## 系统要求
- Linux (Ubuntu/CentOS)
- Python 3.8+
- systemd
- jq 工具（安装脚本读取 JSON 配置使用）
安装 jq（Debian/Ubuntu）：
```bash
复制代码
sudo apt install jq -y
```
---
## 维护与扩展
调整过期时间或清理间隔，只需修改 config/config.json。
若需修改服务器域名或端口，需要修改配置文件并重启服务：
```bash
sudo systemctl restart fastapi
```
清理任务开关或时间修改后，重载定时器：
```bash
sudo systemctl daemon-reload
sudo systemctl restart fastapi-cleanup.timer
```
## 特性总结
- 高性能：FastAPI + Uvicorn 异步处理大量并发请求。
- 稳定：systemd 管理服务，自动重启，开机自启。
- 安全：客户端和服务端均使用 MD5 去重，30 天自动过期，防止重复占用空间。
- 易配置：所有参数统一放到 config.json，无需修改代码。
- 轻量化：客户端缓存 SQLite，无需额外数据库，适合轻量服务器。