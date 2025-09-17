#!/usr/bin/env python3
"""
Image Proxy Project 一键快速配置工具
自动化设置服务器和客户端配置
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import argparse


class QuickSetup:
    """快速配置工具"""
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.config_file = self.project_root / "config" / "config.json"
        self.config_template = self.project_root / "config" / "config.template.json"
        
    def check_requirements(self) -> bool:
        """检查系统要求"""
        print("🔍 检查系统要求...")
        
        # 检查Python版本
        if sys.version_info < (3, 10):
            print("❌ Python版本不足，需要3.10或更高版本")
            return False
        print(f"✅ Python版本: {sys.version}")
        
        # 检查必要的工具
        tools = ['pip', 'git']
        for tool in tools:
            if subprocess.run(['which', tool], capture_output=True).returncode != 0:
                print(f"❌ 缺少工具: {tool}")
                return False
            print(f"✅ {tool} 可用")
        
        return True
    
    def install_dependencies(self) -> bool:
        """安装依赖"""
        print("\n📦 安装依赖...")
        
        try:
            # 检查虚拟环境
            venv_path = self.project_root / "venv"
            if not venv_path.exists():
                print("📁 创建虚拟环境...")
                subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
            
            # 激活虚拟环境并安装依赖
            if os.name == 'nt':  # Windows
                pip_path = venv_path / "Scripts" / "pip"
            else:  # Linux/Mac
                pip_path = venv_path / "bin" / "pip"
            
            requirements_file = self.project_root / "requirements-prod.txt"
            if requirements_file.exists():
                print("📥 安装生产依赖...")
                subprocess.run([str(pip_path), "install", "-r", str(requirements_file)], check=True)
            else:
                print("📥 安装基础依赖...")
                subprocess.run([str(pip_path), "install", "-r", str(self.project_root / "requirements.txt")], check=True)
            
            print("✅ 依赖安装完成")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 依赖安装失败: {e}")
            return False
    
    def generate_config(self, domain: str, username: str, password: Optional[str] = None) -> bool:
        """生成配置文件"""
        print("\n⚙️ 生成配置文件...")
        
        try:
            # 生成安全密钥
            print("🔑 生成安全密钥...")
            secret_key_script = self.project_root / "tools" / "generate_secret_key.py"
            
            if secret_key_script.exists():
                cmd = [sys.executable, str(secret_key_script), "--config", str(self.config_file)]
                if username:
                    cmd.extend(["--username", username])
                if password:
                    cmd.extend(["--password"])
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ 安全密钥生成完成")
                else:
                    print(f"⚠️ 密钥生成失败: {result.stderr}")
                    return self._manual_config_generation(domain, username, password)
            else:
                return self._manual_config_generation(domain, username, password)
            
            # 更新域名
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                config['server']['domain'] = domain
                
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                print(f"✅ 配置文件已更新: {domain}")
                return True
            else:
                return self._manual_config_generation(domain, username, password)
                
        except Exception as e:
            print(f"❌ 配置生成失败: {e}")
            return self._manual_config_generation(domain, username, password)
    
    def _manual_config_generation(self, domain: str, username: str, password: Optional[str] = None) -> bool:
        """手动生成配置文件"""
        print("🔧 手动生成配置文件...")
        
        try:
            import secrets
            import string
            
            # 生成密钥
            alphabet = string.ascii_letters + string.digits
            secret_key = ''.join(secrets.choice(alphabet) for _ in range(32))
            
            if not password:
                password = ''.join(secrets.choice(alphabet + "!@#$%^&*") for _ in range(16))
            
            config = {
                "server": {
                    "domain": domain,
                    "port": 8000
                },
                "cleanup": {
                    "enable": True,
                    "expire_days": 30,
                    "cleanup_time": "03:00:00"
                },
                "security": {
                    "secret_key": secret_key,
                    "upload": {
                        "max_file_size_mb": 10,
                        "allowed_types": ["image/jpeg", "image/png", "image/gif", "image/webp"]
                    },
                    "rate_limit": {
                        "max_requests": 100,
                        "window_seconds": 60
                    }
                },
                "logging": {
                    "level": "INFO",
                    "file": "/var/log/image_proxy/fastapi.log",
                    "max_size_mb": 100,
                    "backup_count": 5
                },
                "users": [
                    {
                        "username": username,
                        "password": password
                    }
                ]
            }
            
            # 确保目录存在
            self.config_file.parent.mkdir(exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print("✅ 配置文件生成完成")
            print(f"👤 用户名: {username}")
            print(f"🔒 密码: {password}")
            
            return True
            
        except Exception as e:
            print(f"❌ 手动配置生成失败: {e}")
            return False
    
    def test_setup(self) -> bool:
        """测试配置"""
        print("\n🧪 测试配置...")
        
        try:
            test_script = self.project_root / "tools" / "test_service.py"
            if test_script.exists():
                # 启动服务进行测试
                print("🚀 启动临时服务进行测试...")
                
                # 这里应该启动服务并运行测试
                # 由于复杂性，暂时跳过自动启动
                print("⚠️ 请手动启动服务后运行测试:")
                print(f"   python {test_script} --quick")
                return True
            else:
                print("⚠️ 测试脚本不存在，跳过测试")
                return True
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return False
    
    def show_next_steps(self):
        """显示后续步骤"""
        print("\n🎉 配置完成！")
        print("=" * 50)
        print("📋 后续步骤:")
        print()
        print("1️⃣ 启动服务 (开发环境):")
        print("   cd server")
        print("   python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload")
        print()
        print("2️⃣ 启动服务 (生产环境):")
        print("   cd scripts && sudo ./install.sh")
        print()
        print("3️⃣ 测试服务:")
        print("   python tools/test_service.py")
        print()
        print("4️⃣ 使用客户端:")
        print("   cd client && python client.py")
        print()
        print("5️⃣ 查看API文档:")
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            domain = config['server']['domain']
            port = config['server']['port']
            if 'localhost' in domain or '127.0.0.1' in domain:
                print(f"   http://localhost:{port}/docs")
            else:
                print(f"   {domain}/docs")
        print()
        print("🔗 更多信息:")
        print("   📖 完整文档: README.md")
        print("   🚀 快速指南: QUICKSTART.md")
        print("   🔧 API文档: docs/API.md")
        print("   📦 部署指南: docs/DEPLOYMENT.md")


def main():
    parser = argparse.ArgumentParser(description='Image Proxy Project 一键配置工具')
    parser.add_argument('--domain', '-d', required=True, help='服务器域名或IP')
    parser.add_argument('--username', '-u', default='admin', help='管理员用户名')
    parser.add_argument('--password', '-p', help='管理员密码（不提供将自动生成）')
    parser.add_argument('--skip-deps', action='store_true', help='跳过依赖安装')
    parser.add_argument('--skip-test', action='store_true', help='跳过测试')
    
    args = parser.parse_args()
    
    print("🚀 Image Proxy Project 一键配置工具")
    print("=" * 50)
    
    setup = QuickSetup()
    
    # 检查系统要求
    if not setup.check_requirements():
        print("\n❌ 系统要求检查失败")
        sys.exit(1)
    
    # 安装依赖
    if not args.skip_deps:
        if not setup.install_dependencies():
            print("\n❌ 依赖安装失败")
            sys.exit(1)
    
    # 生成配置
    if not setup.generate_config(args.domain, args.username, args.password):
        print("\n❌ 配置生成失败")
        sys.exit(1)
    
    # 测试配置
    if not args.skip_test:
        setup.test_setup()
    
    # 显示后续步骤
    setup.show_next_steps()


if __name__ == "__main__":
    main()