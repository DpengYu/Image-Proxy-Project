"""
Image Proxy Server - 重构版本
高性能图片上传与代理服务，支持安全认证、文件验证、速率限制等功能
"""
import os
import json
import time
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, UploadFile, HTTPException, Query, Request, Depends
from fastapi.responses import FileResponse
from PIL import Image

# 导入自定义模块
from config_validator import validate_config_file, ConfigValidationError
from security_utils import SecurityManager, FileValidator, RateLimiter
from database import DatabaseManager
from logger_config import setup_logger, get_logger

# -------------------------------
# 全局变量
# -------------------------------
app = FastAPI(
    title="Image Proxy API",
    description="高性能图片上传与代理服务",
    version="2.0.0"
)

# 全局组件
config: Dict[str, Any] = {}
security_manager: Optional[SecurityManager] = None
file_validator: Optional[FileValidator] = None
rate_limiter: Optional[RateLimiter] = None
db_manager: Optional[DatabaseManager] = None
logger = None

# 常量
UPLOAD_DIR = "uploads"

# -------------------------------
# 启动事件
# -------------------------------
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化所有组件"""
    global config, security_manager, file_validator, rate_limiter, db_manager, logger
    
    try:
        # 1. 加载并验证配置
        config_file = os.path.join(os.path.dirname(__file__), "../config/config.json")
        config = validate_config_file(config_file)
        
        # 2. 设置日志
        logger = setup_logger(config)
        logger.info("=== Image Proxy Server 启动 ===")
        
        # 3. 创建上传目录
        upload_path = Path(UPLOAD_DIR)
        upload_path.mkdir(exist_ok=True)
        logger.info(f"上传目录: {upload_path.absolute()}")
        
        # 4. 初始化安全管理器
        security_config = config.get("security", {})
        secret_key = security_config.get("secret_key")
        if not secret_key:
            raise ValueError("配置中缺少 security.secret_key")
        
        security_manager = SecurityManager(secret_key)
        logger.info("安全管理器初始化完成")
        
        # 5. 初始化文件验证器
        upload_config = security_config.get("upload", {})
        file_validator = FileValidator(
            max_size_mb=upload_config.get("max_file_size_mb", 10),
            allowed_types=upload_config.get("allowed_types", ["image/jpeg", "image/png", "image/gif", "image/webp"])
        )
        logger.info("文件验证器初始化完成")
        
        # 6. 初始化速率限制器
        rate_config = security_config.get("rate_limit", {})
        rate_limiter = RateLimiter(
            max_requests=rate_config.get("max_requests", 100),
            window_seconds=rate_config.get("window_seconds", 60)
        )
        logger.info("速率限制器初始化完成")
        
        # 7. 初始化数据库
        db_manager = DatabaseManager()
        logger.info("数据库初始化完成")
        
        logger.info("=== 所有组件初始化完成 ===")
        
    except Exception as e:
        print(f"启动失败: {e}")
        raise

# -------------------------------
# 依赖注入
# -------------------------------
def get_current_user(username: str = Query(...), password: str = Query(...)) -> Dict[str, str]:
    """验证用户身份"""
    users = {u['username']: u['password'] for u in config.get("users", [])}
    
    if users.get(username) != password:
        logger.warning(f"用户认证失败: {username}")
        raise HTTPException(status_code=403, detail="权限不足，请联系管理员")
    
    return {"username": username, "password": password}

def check_rate_limit(request: Request):
    """检查速率限制"""
    client_ip = request.client.host
    if not rate_limiter.is_allowed(client_ip):
        logger.warning(f"速率限制触发: {client_ip}")
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")

# -------------------------------
# 工具函数
# -------------------------------
def get_image_size(data: bytes) -> tuple:
    """获取图片尺寸"""
    try:
        image = Image.open(BytesIO(data))
        return image.size
    except Exception as e:
        logger.warning(f"无法获取图片尺寸: {e}")
        return None, None

def generate_image_url(md5: str, username: str, password: str) -> str:
    """生成图片访问URL"""
    expire_days = config["cleanup"]["expire_days"]
    expire_time = int(time.time()) + expire_days * 86400
    token = security_manager.generate_token(username, password, md5, expire_time)
    
    server_domain = config["server"]["domain"].rstrip("/")
    return f"{server_domain}/secure_get/{md5}?token={token}"

# -------------------------------
# API 端点
# -------------------------------
@app.post("/upload")
async def upload_image(
    request: Request,
    file: UploadFile,
    current_user: Dict[str, str] = Depends(get_current_user)
):
    """上传图片接口"""
    # 速率限制检查
    check_rate_limit(request)
    
    logger.info(f"用户 {current_user['username']} 开始上传文件: {file.filename}")
    
    try:
        # 读取文件内容
        content = await file.read()
        
        # 文件验证
        validation_result = file_validator.validate_file(content, file.filename or "unknown")
        if not validation_result["valid"]:
            logger.warning(f"文件验证失败: {validation_result['errors']}")
            raise HTTPException(status_code=400, detail=f"文件验证失败: {', '.join(validation_result['errors'])}")
        
        # 计算MD5
        md5 = security_manager.get_data_md5(content)
        
        # 检查数据库中是否已存在
        existing_image = db_manager.get_image(md5)
        if existing_image:
            logger.info(f"图片已存在: {md5}")
            
            # 更新访问计数
            db_manager.update_access_count(md5)
            
            return {
                "url": generate_image_url(md5, current_user['username'], current_user['password']),
                "expire_at": existing_image["created_at"] + config["cleanup"]["expire_days"] * 86400,
                "name": existing_image["original_name"],
                "width": existing_image["width"],
                "height": existing_image["height"],
                "access_count": existing_image["access_count"] + 1,
                "status": "existing"
            }
        
        # 保存新文件
        filename = f"{md5}.png"  # 统一使用PNG格式
        file_path = Path(UPLOAD_DIR) / filename
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 获取图片信息
        width, height = get_image_size(content)
        file_size = len(content)
        
        # 保存到数据库
        success = db_manager.insert_image(
            md5=md5,
            path=str(file_path),
            original_name=file.filename or "unknown",
            width=width or 0,
            height=height or 0,
            file_size=file_size
        )
        
        if not success:
            logger.error(f"数据库插入失败: {md5}")
            raise HTTPException(status_code=500, detail="保存图片信息失败")
        
        logger.info(f"新图片上传成功: {md5}, 大小: {file_size} bytes")
        
        return {
            "url": generate_image_url(md5, current_user['username'], current_user['password']),
            "expire_at": int(time.time()) + config["cleanup"]["expire_days"] * 86400,
            "name": file.filename,
            "width": width,
            "height": height,
            "access_count": 0,
            "status": "uploaded"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传处理失败: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

@app.get("/secure_get/{md5}")
async def secure_get(md5: str, token: str, request: Request):
    """安全图片访问接口"""
    # 速率限制检查
    check_rate_limit(request)
    
    try:
        # 验证token
        result = security_manager.verify_token(token)
        if not result:
            logger.warning(f"Token验证失败: {md5}")
            raise HTTPException(status_code=403, detail="无效或过期的 token")
        
        username, password, md5_token = result
        if md5 != md5_token:
            logger.warning(f"Token与图片不匹配: {md5} != {md5_token}")
            raise HTTPException(status_code=403, detail="Token与图片不匹配")
        
        # 获取图片信息
        image_info = db_manager.get_image(md5)
        if not image_info:
            logger.warning(f"图片不存在: {md5}")
            raise HTTPException(status_code=404, detail="图片不存在")
        
        file_path = Path(image_info["path"])
        if not file_path.exists():
            logger.error(f"图片文件丢失: {file_path}")
            raise HTTPException(status_code=404, detail="图片文件不存在")
        
        # 更新访问计数
        db_manager.update_access_count(md5)
        
        logger.debug(f"图片访问: {md5}, 用户: {username}")
        return FileResponse(file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"图片访问失败: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

@app.get("/info/{md5}")
async def get_image_info(
    md5: str,
    request: Request,
    current_user: Dict[str, str] = Depends(get_current_user)
):
    """获取图片信息接口"""
    check_rate_limit(request)
    
    try:
        image_info = db_manager.get_image(md5)
        if not image_info:
            raise HTTPException(status_code=404, detail="图片不存在")
        
        return {
            "url": generate_image_url(md5, current_user['username'], current_user['password']),
            "expire_at": image_info["created_at"] + config["cleanup"]["expire_days"] * 86400,
            "name": image_info["original_name"],
            "width": image_info["width"],
            "height": image_info["height"],
            "access_count": image_info["access_count"],
            "file_size": image_info["file_size"],
            "status": "existing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取图片信息失败: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

@app.get("/download_db")
async def download_db(
    request: Request,
    current_user: Dict[str, str] = Depends(get_current_user)
):
    """下载数据库接口"""
    check_rate_limit(request)
    
    try:
        db_file = db_manager.db_file
        if not db_file.exists():
            raise HTTPException(status_code=404, detail="数据库文件不存在")
        
        logger.info(f"用户 {current_user['username']} 下载数据库")
        return FileResponse(
            db_file, 
            filename="images.db", 
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载数据库失败: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

@app.get("/stats")
async def get_stats(
    request: Request,
    current_user: Dict[str, str] = Depends(get_current_user)
):
    """获取系统统计信息"""
    check_rate_limit(request)
    
    try:
        stats = db_manager.get_stats()
        logger.info(f"用户 {current_user['username']} 查看系统统计")
        return stats
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": int(time.time()),
        "version": "2.0.0"
    }

# -------------------------------
# 关闭事件
# -------------------------------
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    if logger:
        logger.info("=== Image Proxy Server 关闭 ===")
    
    # 清理速率限制器
    if rate_limiter:
        rate_limiter.cleanup()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)