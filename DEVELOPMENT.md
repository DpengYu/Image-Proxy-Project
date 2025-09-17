# 开发环境设置指南

## 快速开始

1. **克隆项目**
   ```bash
   git clone <repo_url>
   cd image_proxy_project
   ```

2. **设置Python虚拟环境**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或 venv\Scripts\activate  # Windows
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境**
   ```bash
   # 复制配置模板
   cp config/config.template.json config/config.json
   cp .env.example .env
   
   # 编辑配置文件，设置域名、端口、用户等
   vim config/config.json
   vim .env
   ```

5. **运行开发服务器**
   ```bash
   cd server
   python -m uvicorn server:app --reload --host 0.0.0.0 --port 8000
   ```

6. **测试客户端**
   ```bash
   cd client
   python client.py
   ```

## 目录结构

```
image_proxy_project/
├── client/                 # 客户端代码
│   ├── client.py          # 主要客户端接口
│   └── download_db.py     # 数据库下载工具
├── server/                # 服务器端代码
│   ├── server.py          # FastAPI 主服务
│   ├── cleanup.py         # 清理脚本
│   ├── config_validator.py # 配置验证
│   └── security_utils.py  # 安全工具
├── config/                # 配置文件
│   ├── config.template.json # 配置模板
│   └── config.json        # 实际配置 (gitignore)
├── scripts/               # 部署脚本
├── tests/                 # 测试代码
└── docs/                  # 文档
```

## 开发工作流

1. **代码修改** - 修改代码后服务器会自动重载
2. **测试** - 运行测试确保功能正常
3. **提交** - 遵循提交信息规范

## 常见问题

### 配置文件找不到
确保已复制 `config.template.json` 为 `config.json` 并填入正确信息。

### 权限错误
检查用户名密码是否正确配置在 `config.json` 中。

### 端口被占用
修改 `config.json` 中的端口号。

## 生产部署

参考 `scripts/install.sh` 脚本进行自动化部署。