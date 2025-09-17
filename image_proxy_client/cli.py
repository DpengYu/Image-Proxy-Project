"""
Image Proxy Client - 命令行接口
提供命令行工具来使用图片代理客户端
"""

import argparse
import sys
import os
from pathlib import Path

from .client import quick_upload, ImageProxyClient
from .config import ImageProxyConfig, create_config_template


def main():
    """命令行主函数"""
    parser = argparse.ArgumentParser(
        description="Image Proxy Client - 图片代理客户端命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s upload -s http://server.com -u user -p pass image.jpg
  %(prog)s upload --config config.json image.jpg
  %(prog)s health -s http://server.com
  %(prog)s create-config my_config.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # upload 子命令
    upload_parser = subparsers.add_parser('upload', help='上传图片')
    upload_parser.add_argument('image_path', help='图片文件路径')
    upload_parser.add_argument('-s', '--server', help='服务器地址')
    upload_parser.add_argument('-u', '--username', help='用户名')
    upload_parser.add_argument('-p', '--password', help='密码')
    upload_parser.add_argument('-c', '--config', help='配置文件路径')
    upload_parser.add_argument('-t', '--timeout', type=int, default=30, help='超时时间')
    upload_parser.add_argument('--no-ssl-verify', action='store_true', help='跳过SSL验证')
    upload_parser.add_argument('-q', '--quiet', action='store_true', help='静默模式')
    
    # health 子命令  
    health_parser = subparsers.add_parser('health', help='检查服务健康状态')
    health_parser.add_argument('-s', '--server', help='服务器地址')
    health_parser.add_argument('-c', '--config', help='配置文件路径')
    
    # create-config 子命令
    config_parser = subparsers.add_parser('create-config', help='创建配置文件模板')
    config_parser.add_argument('config_file', nargs='?', default='image_proxy_config.json', 
                              help='配置文件路径')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'create-config':
            create_config_template(args.config_file)
            return 0
        
        elif args.command == 'upload':
            # 获取配置
            if args.config:
                config = ImageProxyConfig(args.config)
                server_url = config.get('server_url')
                username = config.get('username')
                password = config.get('password')
                timeout = config.get('timeout', 30)
                verify_ssl = config.get('verify_ssl', True)
            else:
                server_url = args.server
                username = args.username
                password = args.password
                timeout = args.timeout
                verify_ssl = not args.no_ssl_verify
            
            # 验证必要参数
            if not all([server_url, username, password]):
                print("错误: 缺少必要参数 (server_url, username, password)", file=sys.stderr)
                print("请使用 -s/-u/-p 参数或 -c 配置文件", file=sys.stderr)
                return 1
            
            # 检查图片文件
            if not Path(args.image_path).exists():
                print(f"错误: 图片文件不存在: {args.image_path}", file=sys.stderr)
                return 1
            
            # 上传图片
            try:
                url = quick_upload(server_url, username, password, args.image_path, timeout)
                if args.quiet:
                    print(url)
                else:
                    print(f"✅ 上传成功!")
                    print(f"图片URL: {url}")
                return 0
            except Exception as e:
                if not args.quiet:
                    print(f"❌ 上传失败: {e}", file=sys.stderr)
                return 1
        
        elif args.command == 'health':
            # 获取配置
            if args.config:
                config = ImageProxyConfig(args.config)
                server_url = config.get('server_url')
            else:
                server_url = args.server
            
            if not server_url:
                print("错误: 缺少服务器地址", file=sys.stderr)
                return 1
            
            # 检查健康状态
            client = ImageProxyClient(server_url, "", "", 5, True)  # 健康检查不需要认证
            try:
                is_healthy = client.is_healthy()
                if is_healthy:
                    print("✅ 服务正常")
                    return 0
                else:
                    print("❌ 服务异常")
                    return 1
            finally:
                client.close()
    
    except KeyboardInterrupt:
        print("\n用户中断操作", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())