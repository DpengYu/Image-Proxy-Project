#!/usr/bin/env python3
"""
Image Proxy 修复验证脚本
用于验证健康检查和认证功能是否正常工作
"""
import requests
import json
import time
from pathlib import Path

def test_health_check(server_url):
    """测试健康检查接口"""
    print("🔍 测试健康检查接口...")
    try:
        response = requests.get(f"{server_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查成功")
            print(f"   状态: {data.get('status')}")
            print(f"   版本: {data.get('version')}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        return False

def test_auth(server_url, username, password):
    """测试认证接口"""
    print("\n🔐 测试认证接口...")
    try:
        params = {"username": username, "password": password}
        response = requests.get(f"{server_url}/stats", params=params, timeout=5)
        if response.status_code == 200:
            print("✅ 用户认证成功")
            data = response.json()
            print(f"   总图片数: {data.get('total_images', 0)}")
            print(f"   总访问数: {data.get('total_access', 0)}")
            return True
        elif response.status_code == 403:
            print("❌ 用户认证失败，请检查用户名密码")
            return False
        else:
            print(f"❌ 认证测试异常: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 认证测试失败: {e}")
        return False

def main():
    # 服务器配置
    server_url = "http://localhost:8000"
    username = "admin"
    password = "admin123"
    
    print("🚀 Image Proxy 修复验证")
    print("=" * 40)
    
    # 测试健康检查
    if not test_health_check(server_url):
        print("\n❌ 健康检查失败，请确保服务器正在运行")
        return
    
    # 测试认证
    if not test_auth(server_url, username, password):
        print("\n❌ 认证测试失败，请检查配置")
        return
    
    print("\n🎉 所有测试通过！健康检查和认证功能正常工作")

if __name__ == "__main__":
    main()