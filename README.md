# Image Proxy Project

> 高性能图片上传与代理服务，支持重复去重、自动过期、客户端缓存及安全访问管理。

---

## 目录

- [项目概述](#项目概述)  
- [核心功能](#核心功能)  
- [系统架构](#系统架构)  
- [文件结构](#文件结构)  
- [配置文件说明](#配置文件说明)  
- [系统要求](#系统要求)  
- [安装指南](#安装指南)  
- [客户端使用](#客户端使用)  
- [外部接口调用](#外部接口调用)  
- [维护与扩展](#维护与扩展)  
- [快速示例](#快速示例)  
- [特性总结](#特性总结)  
- [常见问题](#常见问题)  

---

## 项目概述

Image Proxy Project 是一套高性能、轻量化的图片上传与代理系统，专为图片管理与访问场景设计。支持本地上传、服务器存储、URL 生成及缓存管理，可用于 API 调用、网页展示或内部服务。

主要目标：

- 提高图片上传与访问效率  
- 避免重复上传和存储  
- 自动管理图片生命周期  
- 保证服务稳定与安全  

---

## 核心功能

| 功能 | 描述 |
|------|------|
| 图片上传与访问 | 本地图片上传至服务器，返回可访问 URL，可直接用于 API 或网页调用 |
| 重复去重 | 客户端和服务器端使用 MD5 双重去重，避免重复上传和存储 |
| 自动过期 | 图片及缓存可配置过期天数（默认 30 天），自动清理 |
| 高性能服务 | FastAPI + Uvicorn 异步处理大量并发请求 |
| 客户端缓存 | 使用 SQLite 存储图片 URL 和 MD5，提升访问效率 |
| 定时清理 | 每日自动清理过期图片，可自定义时间与开关 |
| 数据库下载 | 可从服务器下载 SQLite 数据库备份 |
| 安全与权限 | 用户权限控制，权限不足时返回提示而非报错 |
| 系统稳定性 | systemd 管理服务，支持自动重启和开机自启 |

---

## 系统架构

```text
+-----------------+         +-------------------+
|                 |  HTTP   |                   |
|  客户端 Client  +-------->+   FastAPI Server  |
|                 |         |                   |
+--------+--------+         +--------+----------+
^                           |
| SQLite Cache              | SQLite DB + Uploads/
|                           |
+---------------------------+
````

* **客户端**：上传图片、缓存 URL、防止重复上传。
* **服务器端**：接收图片、存储、生成 URL、维护 SQLite 数据库。
* **Nginx（可选）**：反向代理 FastAPI 服务，可用于域名访问。
* **定时清理**：systemd Timer 每日执行 `cleanup.py`，删除过期图片和缓存。

---

## 文件结构

```text
image_proxy_project/
├─ config/
│  └─ config.json           # 全局配置文件
├─ server/
│  ├─ server.py             # FastAPI 服务
│  ├─ cleanup.py            # 自动清理脚本
│  ├─ images.db             # SQLite 数据库（首次运行自动生成）
│  └─ uploads/              # 上传图片存储目录
├─ client/
│  ├─ client.py             # 图片上传客户端
│  └─ download_db.py        # 下载服务器数据库
├─ scripts/
│  ├─ install.sh            # 一键安装脚本
│  ├─ reset.sh              # 重置数据库和上传目录
│  └─ uninstall.sh          # 服务器一键卸载脚本
└─ README.md
```

---
## 配置文件说明

路径：`config/config.json`

示例：

```json
{
  "server": {
    "domain": "yourDomain",
    "port": 8000
  },
  "cleanup": {
    "enable": true,
    "expire_days": 30,
    "cleanup_time": "03:00:00"
  },
  "users": [
    {
      "username": "alice",
      "password": "alice123"
    }
  ]
}
```

**参数说明**

| 参数                     | 说明                                      |
| ---------------------- | --------------------------------------- |
| `server.domain`        | 客户端访问服务器的域名或 IP，用于生成图片 URL              |
| `server.port`          | FastAPI 服务端口                            |
| `cleanup.enable`       | 是否开启每日自动清理过期图片                          |
| `cleanup.expire_days`  | 图片和缓存的过期天数                              |
| `cleanup.cleanup_time` | 每日清理时间（HH\:MM\:SS），仅在 `enable=true` 时生效 |
| `users`                | 允许访问客户端功能的账号列表，权限不足时返回友好提示              |

---

## 系统要求

* **操作系统**：Linux (Ubuntu/CentOS)
* **Python**：3.10+
* **systemd**：管理服务和定时任务
* **jq**：安装脚本读取 JSON 配置（Debian/Ubuntu 安装：`sudo apt install jq -y`）

---

## 安装指南

### 1. 克隆项目

```bash
git clone <repo_url>
cd image_proxy_project
```

### 2. 配置服务器

编辑 `config/config.json`，设置 `domain`、`port` 和用户信息。

### 3. 执行安装脚本

```bash
cd scripts
chmod +x install.sh
./install.sh
```

* FastAPI 服务将启动，由 systemd 管理。
* 支持自动重启和开机自启。
* 定时清理服务将每日按配置执行。

### 4. 查看日志

* FastAPI 服务日志：`/var/log/image_proxy/fastapi.log`
* 定时清理日志：

```bash
journalctl -u fastapi-cleanup --no-pager -f
```

---

## 客户端使用

```bash
cd client
python3 client.py
```

* 自动读取 `config.json` 中的 `server.domain` 和 `port`
* 上传图片后返回 URL，可直接用于 API 或网页访问
* 客户端缓存图片 URL，避免重复上传
* 用户权限不足时返回 `"该用户权限不足，请联系管理员"`

### 下载服务器数据库

```bash
python3 download_db.py
```

* 默认保存为 `images_server.db`
* 需要用户权限足够，否则返回提示信息

---

## 外部接口调用

客户端提供了 Python 模块化接口，方便在其他工程中直接调用，无需通过 CLI。

### 1. 上传图片并获取完整 URL

```python
from image_proxy_project.client.client import get_image_url

file_path = "example.png"
url = get_image_url(file_path)

if url:
    print(f"✅ 图片 URL: {url}")
else:
    print("❌ 无法获取图片 URL，可能权限不足或上传失败")
```

**说明**：

* `get_image_url(file_path: str) -> Optional[str]`

  * 输入：本地图片路径
  * 输出：图片在服务器上的完整 URL（字符串），失败时返回 `None`
  * 内部会先查询服务器是否已存在该图片，若不存在则上传
  * 权限不足或网络异常时，不抛异常，只返回 `None`

---

### 2. 获取完整图片信息（字典）

```python
from image_proxy_project.client.client import upload_or_get

info = upload_or_get("example.png")

if "error" in info:
    print(info["error"])
else:
    print("图片信息:")
    print(f"Status: {info.get('status')}")
    print(f"URL: {info.get('url')}")
    print(f"Original Name: {info.get('name')}")
    print(f"Size: {info.get('width')}x{info.get('height')}")
    print(f"Access Count: {info.get('access_count')}")
    print(f"Expire At: {info.get('expire_at')}")
```

**说明**：

* `upload_or_get(file_path: str) -> dict`

  * 返回包含完整图片信息的字典
  * 失败时包含 `"error"` 字段
  * 可用于开发者获取更多元数据或做二次处理

---

### 3. 外部调用示例

```python
from image_proxy_project.client.client import get_image_url

url = get_image_url("/absolute/path/to/image.png")
print(url)
```

---

## 维护与扩展

* **修改过期时间或清理间隔**：

```bash
vim config/config.json
```

* **修改服务器域名或端口**：

```bash
sudo systemctl restart fastapi
```

* **修改定时清理时间或开关**：

```bash
sudo systemctl daemon-reload
sudo systemctl restart fastapi-cleanup.timer
```

---

## 快速示例

### 上传图片并获取 URL

```python
from client.client import upload_or_get

info = upload_or_get("example.png")
print("图片信息:")
print(f"Status: {info.get('status')}")
print(f"URL: {info.get('url')}")
print(f"Original Name: {info.get('name')}")
print(f"Size: {info.get('width')}x{info.get('height')}")
print(f"Access Count: {info.get('access_count')}")
print(f"Expire At: {info.get('expire_at')}")
```

### 下载服务器数据库

```bash
python3 client/download_db.py
```

---

## 特性总结

* **高性能**：异步 FastAPI + Uvicorn 支持大并发
* **稳定可靠**：systemd 管理服务，开机自启，自动重启
* **安全防重复**：MD5 去重，自动过期管理
* **易配置**：所有参数统一放在 `config.json`，无需修改代码
* **轻量化**：客户端缓存 SQLite，无需额外数据库
* **友好提示**：权限不足时返回提示而非报错，提升可用性

---

## 常见问题

1. **客户端提示权限不足怎么办？**

   * 请检查 `config.json` 中 `users` 配置的账号密码是否正确。

2. **访问域名显示 404？**

   * 确认 Nginx 或系统防火墙端口是否正确开放
   * 检查 `server.domain` 与实际访问域名是否一致

3. **定时清理未执行？**

   * 使用 `systemctl status fastapi-cleanup.timer` 查看 timer 状态
   * 确认 `cleanup.enable` 是否为 `true`，以及时间格式是否正确

```
