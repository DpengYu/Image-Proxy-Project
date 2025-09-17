"""
Image Proxy Client 安装脚本
支持通过pip安装和使用
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README文件
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding='utf-8') if readme_path.exists() else ""

# 读取requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = requirements_path.read_text(encoding='utf-8').strip().split('\n')

setup(
    name="image-proxy-client",
    version="1.0.0",
    author="Image Proxy Project",
    author_email="",
    description="轻量级图片代理客户端，专为第三方项目集成设计",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DpengYu/Image-Proxy-Project",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
        ]
    },
    entry_points={
        "console_scripts": [
            "image-proxy-client=image_proxy_client.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "image_proxy_client": ["*.md", "*.txt"],
    },
    zip_safe=False,
)