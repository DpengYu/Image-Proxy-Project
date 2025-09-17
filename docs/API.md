# API 文档

## 概述
Image Proxy API 提供了高性能的图片上传、存储和访问服务。支持去重、缓存、安全认证等功能。

## 基础信息
- **Base URL**: 配置文件中的 `server.domain`
- **认证方式**: 用户名密码认证（通过查询参数）
- **支持格式**: JSON
- **版本**: 2.0.0

## 认证
所有需要认证的接口都通过查询参数传递用户名和密码：
```
?username=your_username&password=your_password
```

## 接口列表

### 1. 上传图片
**POST** `/upload`

上传图片到服务器，支持自动去重。

#### 请求参数
- **Query参数**:
  - `username` (string, required): 用户名
  - `password` (string, required): 密码
- **Body参数**:
  - `file` (file, required): 图片文件

#### 请求示例
```bash
curl -X POST "http://localhost:8000/upload?username=admin&password=password123" \\
  -F "file=@/path/to/image.png"
```

#### 响应示例
```json
{
  "url": "http://localhost:8000/secure_get/abc123?token=xyz789",
  "expire_at": 1640995200,
  "name": "image.png",
  "width": 1920,
  "height": 1080,
  "access_count": 0,
  "status": "uploaded"
}
```

#### 响应字段
- `url` (string): 图片访问URL
- `expire_at` (integer): 过期时间戳
- `name` (string): 原始文件名
- `width` (integer): 图片宽度
- `height` (integer): 图片高度
- `access_count` (integer): 访问次数
- `status` (string): 状态，`uploaded`(新上传) 或 `existing`(已存在)

#### 错误响应
- **400**: 文件验证失败
- **403**: 权限不足
- **413**: 文件过大
- **429**: 请求过于频繁
- **500**: 服务器内部错误

---

### 2. 安全访问图片
**GET** `/secure_get/{md5}`

通过MD5和token安全访问图片。

#### 请求参数
- **Path参数**:
  - `md5` (string, required): 图片MD5值
- **Query参数**:
  - `token` (string, required): 访问token

#### 请求示例
```bash
curl "http://localhost:8000/secure_get/abc123def456?token=xyz789"
```

#### 响应
直接返回图片文件。

#### 错误响应
- **403**: Token无效或过期
- **404**: 图片不存在
- **429**: 请求过于频繁

---

### 3. 获取图片信息
**GET** `/info/{md5}`

获取图片的详细信息。

#### 请求参数
- **Path参数**:
  - `md5` (string, required): 图片MD5值
- **Query参数**:
  - `username` (string, required): 用户名
  - `password` (string, required): 密码

#### 请求示例
```bash
curl "http://localhost:8000/info/abc123def456?username=admin&password=password123"
```

#### 响应示例
```json
{
  "url": "http://localhost:8000/secure_get/abc123def456?token=xyz789",
  "expire_at": 1640995200,
  "name": "image.png",
  "width": 1920,
  "height": 1080,
  "access_count": 5,
  "file_size": 2048576,
  "status": "existing"
}
```

---

### 4. 下载数据库
**GET** `/download_db`

下载SQLite数据库文件备份。

#### 请求参数
- **Query参数**:
  - `username` (string, required): 用户名
  - `password` (string, required): 密码

#### 请求示例
```bash
curl "http://localhost:8000/download_db?username=admin&password=password123" \\
  -o images_backup.db
```

#### 响应
直接返回SQLite数据库文件。

---

### 5. 系统统计
**GET** `/stats`

获取系统统计信息。

#### 请求参数
- **Query参数**:
  - `username` (string, required): 用户名
  - `password` (string, required): 密码

#### 请求示例
```bash
curl "http://localhost:8000/stats?username=admin&password=password123"
```

#### 响应示例
```json
{
  "total_images": 1523,
  "total_access": 45678,
  "total_size_bytes": 1073741824,
  "latest_image": {
    "original_name": "latest.png",
    "created_at": 1640995200
  },
  "db_file_size": 2097152
}
```

---

### 6. 健康检查
**GET** `/health`

检查服务状态，无需认证。

#### 请求示例
```bash
curl "http://localhost:8000/health"
```

#### 响应示例
```json
{
  "status": "healthy",
  "timestamp": 1640995200,
  "version": "2.0.0"
}
```

## 错误处理

### 错误响应格式
```json
{
  "detail": "错误描述信息"
}
```

### 常见错误码
- **400 Bad Request**: 请求参数错误
- **403 Forbidden**: 权限不足或认证失败
- **404 Not Found**: 资源不存在
- **413 Payload Too Large**: 文件过大
- **429 Too Many Requests**: 请求过于频繁
- **500 Internal Server Error**: 服务器内部错误

## 安全注意事项

1. **Token安全**: 访问token有过期时间，请妥善保管
2. **文件验证**: 只支持指定格式的图片文件
3. **速率限制**: 每个IP有请求频率限制
4. **HTTPS**: 生产环境建议使用HTTPS
5. **密码安全**: 避免在URL中暴露密码，建议使用代理或API网关

## 客户端SDK

### Python客户端
```python
from client.client import ImageProxyClient

# 初始化客户端
client = ImageProxyClient()

# 上传图片
result = client.upload_or_get("/path/to/image.png")
if "url" in result:
    print(f"图片URL: {result['url']}")

# 简化接口
url = client.get_image_url("/path/to/image.png")
print(f"图片URL: {url}")

# 关闭客户端
client.close()
```

### 批量上传
```python
client = ImageProxyClient()
file_paths = ["/path/to/img1.png", "/path/to/img2.png"]
results = client.batch_upload(file_paths)
for result in results:
    print(f"文件: {result['file_path']}, URL: {result.get('url', 'Failed')}")
```

## 限制说明

1. **文件大小**: 默认最大10MB（可配置）
2. **文件类型**: 仅支持 JPEG, PNG, GIF, WebP
3. **并发请求**: 建议不超过100并发
4. **存储时间**: 默认30天过期（可配置）
5. **速率限制**: 默认每分钟100请求（可配置）