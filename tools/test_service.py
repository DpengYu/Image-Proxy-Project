#!/usr/bin/env python3
"""
Image Proxy Project 快速测试工具
用于验证服务器和客户端的基本功能
"""
import requests
import json
import sys
import time
import tempfile
from pathlib import Path
from typing import Optional
import argparse

class ImageProxyTester:
    """图片代理测试器"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config/config.json"
        self.config = self._load_config()
        # 确保端口包含在URL中
        domain = self.config['server']['domain'].rstrip('/')
        port = self.config['server']['port']
        if ':' not in domain.split('//')[1] and port != 80:
            self.server_url = f"{domain}:{port}"
        else:
            self.server_url = domain
        self.username = self.config['users'][0]['username']
        self.password = self.config['users'][0]['password']
        
    def _load_config(self) -> dict:
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 读取配置文件失败: {e}")
            sys.exit(1)
    
    def _create_test_image(self) -> str:
        """创建测试图片"""
        # 创建一个简单的测试文件
        img_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        # 简单的PNG文件头
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x64\x00\x00\x00\x64\x08\x02\x00\x00\x00\xff\x80\xb8\x00\x00\x00\x00IEND\xaeB`\x82'
        img_file.write(png_data)
        img_file.close()
        return img_file.name
    
    def test_health(self) -> bool:
        """测试健康检查接口"""
        print("🔍 测试健康检查...")
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 服务正常运行，版本: {data.get('version', 'unknown')}")
                return True
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 无法连接服务器: {e}")
            return False
    
    def test_auth(self) -> bool:
        """测试认证"""
        print("🔐 测试用户认证...")
        try:
            # 使用查询参数进行认证
            params = {"username": self.username, "password": self.password}
            response = requests.get(f"{self.server_url}/stats", params=params, timeout=5)
            if response.status_code == 200:
                print("✅ 用户认证成功")
                return True
            elif response.status_code == 403:
                print("❌ 用户认证失败，请检查用户名密码")
                return False
            else:
                print(f"❌ 认证测试异常: {response.status_code}")
                print(f"   响应内容: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 认证测试失败: {e}")
            return False
    
    def test_upload(self) -> bool:
        """测试图片上传"""
        print("📤 测试图片上传...")
        test_image = self._create_test_image()
        
        try:
            params = {"username": self.username, "password": self.password}
            with open(test_image, 'rb') as f:
                files = {"file": ("test.png", f, "image/png")}
                response = requests.post(
                    f"{self.server_url}/upload", 
                    files=files, 
                    params=params, 
                    timeout=10
                )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 图片上传成功")
                print(f"   📎 URL: {data.get('url', 'N/A')}")
                print(f"   📊 状态: {data.get('status', 'N/A')}")
                print(f"   📏 尺寸: {data.get('width', 0)}x{data.get('height', 0)}")
                
                # 测试图片访问
                if 'url' in data:
                    return self._test_image_access(data['url'])
                return True
            else:
                print(f"❌ 图片上传失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 上传测试失败: {e}")
            return False
        finally:
            # 清理测试文件
            try:
                Path(test_image).unlink(missing_ok=True)
            except:
                pass
    
    def _test_image_access(self, image_url: str) -> bool:
        """测试图片访问"""
        print("🖼️ 测试图片访问...")
        try:
            response = requests.get(image_url, timeout=5)
            if response.status_code == 200:
                print("✅ 图片访问成功")
                print(f"   📦 大小: {len(response.content)} bytes")
                print(f"   🎭 类型: {response.headers.get('content-type', 'unknown')}")
                return True
            else:
                print(f"❌ 图片访问失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 图片访问测试失败: {e}")
            return False
    
    def test_stats(self) -> bool:
        """测试统计信息"""
        print("📊 测试系统统计...")
        try:
            params = {"username": self.username, "password": self.password}
            response = requests.get(f"{self.server_url}/stats", params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("✅ 统计信息获取成功")
                print(f"   📁 总图片数: {data.get('total_images', 0)}")
                print(f"   👀 总访问数: {data.get('total_access', 0)}")
                print(f"   💾 存储大小: {data.get('total_size_bytes', 0)} bytes")
                return True
            else:
                print(f"❌ 统计信息获取失败: {response.status_code}")
                print(f"   响应内容: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 统计测试失败: {e}")
            return False
    
    def test_client(self) -> bool:
        """测试客户端功能"""
        print("🖥️ 测试客户端...")
        test_image = None
        try:
            # 尝试导入客户端
            sys.path.insert(0, str(Path(__file__).parent.parent / "client"))
            import importlib
            client_module = importlib.import_module("client")
            get_image_url = getattr(client_module, "get_image_url", None)
            
            if get_image_url is None:
                print("⚠️ 客户端模块缺少 get_image_url 函数，跳过客户端测试")
                return True
            
            # 创建测试图片
            test_image = self._create_test_image()
            
            # 测试客户端上传
            url = get_image_url(test_image)
            if url and not url.startswith("❌"):
                print("✅ 客户端测试成功")
                print(f"   📎 URL: {url}")
                return True
            else:
                print(f"❌ 客户端测试失败: {url}")
                return False
                
        except ImportError:
            print("⚠️ 客户端模块导入失败，跳过客户端测试")
            return True
        except Exception as e:
            print(f"❌ 客户端测试失败: {e}")
            return False
        finally:
            # 清理测试文件
            if test_image is not None:
                try:
                    Path(test_image).unlink(missing_ok=True)
                except:
                    pass
    
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("🚀 开始Image Proxy Project功能测试")
        print("=" * 50)
        
        tests = [
            ("健康检查", self.test_health),
            ("用户认证", self.test_auth),
            ("图片上传", self.test_upload),
            ("系统统计", self.test_stats),
            ("客户端功能", self.test_client),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name}测试:")
            try:
                if test_func():
                    passed += 1
                else:
                    print(f"   ⏭️ {test_name}测试未通过")
            except Exception as e:
                print(f"   💥 {test_name}测试异常: {e}")
            
            time.sleep(0.5)  # 避免请求过快
        
        print("\n" + "=" * 50)
        print(f"📈 测试结果: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有测试通过！服务运行正常")
            return True
        else:
            print("⚠️ 部分测试失败，请检查配置和服务状态")
            return False


def main():
    parser = argparse.ArgumentParser(description='Image Proxy Project 测试工具')
    parser.add_argument('--config', '-c', type=str, help='配置文件路径')
    parser.add_argument('--quick', '-q', action='store_true', help='仅运行快速测试（健康检查+认证）')
    
    args = parser.parse_args()
    
    tester = ImageProxyTester(args.config)
    
    if args.quick:
        print("⚡ 运行快速测试...")
        success = tester.test_health() and tester.test_auth()
        print(f"\n✅ 快速测试{'通过' if success else '失败'}")
    else:
        success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()