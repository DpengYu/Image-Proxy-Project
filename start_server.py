#!/usr/bin/env python3
"""
Image Proxy Server 启动脚本
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "server"))

if __name__ == "__main__":
    # 确保配置文件存在
    config_file = project_root / "config" / "config.json"
    if not config_file.exists():
        print("❌ 配置文件不存在，请先创建 config/config.json")
        print("可以复制 config/config.template.json 并重命名为 config.json，然后修改其中的配置")
        sys.exit(1)
    
    # 启动服务器
    try:
        # 更改当前工作目录到server目录
        os.chdir(project_root / "server")
        
        # 直接运行uvicorn
        import uvicorn
        
        print("🚀 启动 Image Proxy Server...")
        print("📝 服务器地址: http://localhost:8000")
        print("📄 API文档: http://localhost:8000/docs")
        print(".health 接口: http://localhost:8000/health")
        print(".stats 接口: http://localhost:8000/stats (需要认证)")
        print("按 Ctrl+C 停止服务器")
        
        uvicorn.run(
            "server:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ 启动服务器失败: {e}")
        sys.exit(1)