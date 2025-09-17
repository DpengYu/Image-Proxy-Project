#!/usr/bin/env python3
"""
32位安全密钥生成工具
用于生成Image Proxy Project所需的安全密钥
"""
import secrets
import string
import sys
import argparse
from pathlib import Path


from typing import Optional


def generate_secret_key(length: int = 32) -> str:
    """生成指定长度的安全密钥"""
    # 使用字母和数字的组合
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_strong_password(length: int = 16) -> str:
    """生成强密码（包含特殊字符）"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def update_config_file(config_path: str, secret_key: str, username: Optional[str] = None, password: Optional[str] = None) -> bool:
    """更新配置文件中的密钥和用户信息"""
    import json
    
    config_file = Path(config_path)
    if not config_file.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 更新密钥
        if 'security' not in config:
            config['security'] = {}
        config['security']['secret_key'] = secret_key
        
        # 更新用户信息（如果提供）
        if username and password:
            if 'users' not in config:
                config['users'] = []
            if config['users']:
                config['users'][0]['username'] = username
                config['users'][0]['password'] = password
            else:
                config['users'].append({'username': username, 'password': password})
        
        # 保存配置
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 配置文件已更新: {config_path}")
        return True
        
    except Exception as e:
        print(f"❌ 更新配置文件失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Image Proxy Project 密钥生成工具')
    parser.add_argument('--length', '-l', type=int, default=32, help='密钥长度 (默认: 32)')
    parser.add_argument('--password', '-p', action='store_true', help='同时生成强密码')
    parser.add_argument('--config', '-c', type=str, help='自动更新指定的配置文件')
    parser.add_argument('--username', '-u', type=str, help='设置用户名 (配合--config使用)')
    parser.add_argument('--env', '-e', action='store_true', help='生成环境变量格式')
    
    args = parser.parse_args()
    
    print("🔐 Image Proxy Project 密钥生成工具")
    print("=" * 50)
    
    # 生成密钥
    secret_key = generate_secret_key(args.length)
    print(f"🔑 安全密钥 ({args.length}位): {secret_key}")
    
    # 生成密码
    password = None
    if args.password:
        password = generate_strong_password()
        print(f"🔒 强密码 (16位): {password}")
    
    print()
    
    # 环境变量格式
    if args.env:
        print("📝 环境变量格式:")
        print(f"export SECRET_KEY=\"{secret_key}\"")
        if password:
            username = args.username or "admin"
            print(f"export DEFAULT_USERNAME=\"{username}\"")
            print(f"export DEFAULT_PASSWORD=\"{password}\"")
        print()
    
    # 更新配置文件
    if args.config:
        username = args.username or "admin"
        user_password = password or generate_strong_password()
        success = update_config_file(args.config, secret_key, username, user_password)
        if success:
            print(f"👤 用户名: {username}")
            print(f"🔒 密码: {user_password}")
    
    # 使用说明
    print("💡 使用说明:")
    print("1. 将密钥复制到 config/config.json 的 security.secret_key 字段")
    print("2. 确保密钥长度至少32位")
    print("3. 生产环境必须使用随机生成的密钥")
    print("4. 定期更换密钥以提高安全性")
    
    if not args.config:
        print("\n🚀 快速配置:")
        print(f"python tools/generate_secret_key.py --config config/config.json --username admin --password")


if __name__ == "__main__":
    main()