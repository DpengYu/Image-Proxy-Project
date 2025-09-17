#!/usr/bin/env python3
"""
Image Proxy 数据库统计工具
用于查看服务器数据库的统计信息
"""
import requests
import json
import argparse
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

def load_config(config_file=None):
    """加载配置文件"""
    if config_file is None:
        config_file = project_root / "config" / "config.json"
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")
        sys.exit(1)

def get_database_stats(server_url, username, password):
    """获取数据库统计信息"""
    try:
        params = {"username": username, "password": password}
        response = requests.get(f"{server_url}/stats", params=params, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            print("❌ 认证失败，请检查用户名和密码")
            return None
        else:
            print(f"❌ 获取统计信息失败: {response.status_code}")
            print(f"   响应内容: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 网络请求失败: {e}")
        return None

def format_bytes(bytes_size):
    """格式化字节大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

def display_stats(stats):
    """显示统计信息"""
    print("📊 Image Proxy 数据库统计信息")
    print("=" * 50)
    
    print(f"📁 总图片数: {stats.get('total_images', 0):,}")
    print(f"👀 总访问数: {stats.get('total_access', 0):,}")
    print(f"💾 存储大小: {format_bytes(stats.get('total_size_bytes', 0))}")
    print(f"🗄️ 数据库大小: {format_bytes(stats.get('db_file_size', 0))}")
    
    latest = stats.get('latest_image')
    if latest:
        print(f"\n🆕 最新图片:")
        print(f"   名称: {latest.get('original_name', 'N/A')}")
        print(f"   时间: {latest.get('created_at', 'N/A')}")

def main():
    parser = argparse.ArgumentParser(description='Image Proxy 数据库统计工具')
    parser.add_argument('--config', '-c', type=str, help='配置文件路径')
    parser.add_argument('--server', '-s', type=str, help='服务器地址')
    parser.add_argument('--username', '-u', type=str, help='用户名')
    parser.add_argument('--password', '-p', type=str, help='密码')
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 获取服务器配置
    if args.server:
        server_url = args.server.rstrip('/')
    else:
        server_domain = config['server']['domain']
        server_port = config['server']['port']
        if ':' in server_domain or server_port == 80:
            server_url = server_domain
        else:
            server_url = f"{server_domain}:{server_port}"
    
    # 获取用户凭证
    if args.username and args.password:
        username = args.username
        password = args.password
    else:
        user = config['users'][0]
        username = user['username']
        password = user['password']
    
    # 获取统计信息
    stats = get_database_stats(server_url, username, password)
    if stats:
        display_stats(stats)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()