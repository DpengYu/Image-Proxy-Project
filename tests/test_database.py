"""
测试数据库模块
"""
import unittest
import tempfile
import os
from pathlib import Path
import sys

# 添加服务器模块到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "server"))

from database import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    """数据库管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_init_db(self):
        """测试数据库初始化"""
        # 数据库应该已经初始化
        self.assertTrue(Path(self.temp_db.name).exists())
        
        # 检查表是否存在
        stats = self.db_manager.get_stats()
        self.assertEqual(stats["total_images"], 0)
    
    def test_insert_image(self):
        """测试插入图片记录"""
        # 插入测试数据
        success = self.db_manager.insert_image(
            md5="test_md5_hash",
            path="/test/path.png",
            original_name="test.png",
            width=100,
            height=200,
            file_size=1024
        )
        self.assertTrue(success)
        
        # 验证数据
        image = self.db_manager.get_image("test_md5_hash")
        self.assertIsNotNone(image)
        self.assertEqual(image["md5"], "test_md5_hash")
        self.assertEqual(image["original_name"], "test.png")
        self.assertEqual(image["width"], 100)
        self.assertEqual(image["height"], 200)
        self.assertEqual(image["file_size"], 1024)
    
    def test_duplicate_insert(self):
        """测试重复插入"""
        # 首次插入
        success1 = self.db_manager.insert_image(
            md5="duplicate_md5",
            path="/test/path1.png",
            original_name="test1.png",
            width=100,
            height=200,
            file_size=1024
        )
        self.assertTrue(success1)
        
        # 重复插入应该失败
        success2 = self.db_manager.insert_image(
            md5="duplicate_md5",
            path="/test/path2.png",
            original_name="test2.png",
            width=150,
            height=250,
            file_size=2048
        )
        self.assertFalse(success2)
    
    def test_update_access_count(self):
        """测试更新访问计数"""
        # 插入测试数据
        self.db_manager.insert_image(
            md5="access_test",
            path="/test/access.png",
            original_name="access.png",
            width=100,
            height=100,
            file_size=1024
        )
        
        # 初始访问计数为0
        image = self.db_manager.get_image("access_test")
        self.assertEqual(image["access_count"], 0)
        
        # 更新访问计数
        updated = self.db_manager.update_access_count("access_test")
        self.assertTrue(updated)
        
        # 验证访问计数增加
        image = self.db_manager.get_image("access_test")
        self.assertEqual(image["access_count"], 1)
        
        # 再次更新
        self.db_manager.update_access_count("access_test")
        image = self.db_manager.get_image("access_test")
        self.assertEqual(image["access_count"], 2)
    
    def test_get_stats(self):
        """测试获取统计信息"""
        # 空数据库统计
        stats = self.db_manager.get_stats()
        self.assertEqual(stats["total_images"], 0)
        self.assertEqual(stats["total_access"], 0)
        self.assertEqual(stats["total_size_bytes"], 0)
        
        # 插入一些测试数据
        for i in range(3):
            self.db_manager.insert_image(
                md5=f"test_md5_{i}",
                path=f"/test/path_{i}.png",
                original_name=f"test_{i}.png",
                width=100 + i * 10,
                height=100 + i * 10,
                file_size=1024 * (i + 1)
            )
            # 增加一些访问计数
            for _ in range(i + 1):
                self.db_manager.update_access_count(f"test_md5_{i}")
        
        # 检查统计信息
        stats = self.db_manager.get_stats()
        self.assertEqual(stats["total_images"], 3)
        self.assertEqual(stats["total_access"], 6)  # 1+2+3
        self.assertEqual(stats["total_size_bytes"], 6144)  # 1024+2048+3072
        self.assertIsNotNone(stats["latest_image"])
    
    def test_delete_images(self):
        """测试删除图片记录"""
        # 插入测试数据
        md5_list = []
        for i in range(5):
            md5 = f"delete_test_{i}"
            md5_list.append(md5)
            self.db_manager.insert_image(
                md5=md5,
                path=f"/test/delete_{i}.png",
                original_name=f"delete_{i}.png",
                width=100,
                height=100,
                file_size=1024
            )
        
        # 验证插入成功
        stats = self.db_manager.get_stats()
        self.assertEqual(stats["total_images"], 5)
        
        # 删除前3个
        deleted = self.db_manager.delete_images(md5_list[:3])
        self.assertEqual(deleted, 3)
        
        # 验证删除结果
        stats = self.db_manager.get_stats()
        self.assertEqual(stats["total_images"], 2)
        
        # 验证剩余的图片
        for i in range(3, 5):
            image = self.db_manager.get_image(f"delete_test_{i}")
            self.assertIsNotNone(image)
        
        # 验证删除的图片不存在
        for i in range(3):
            image = self.db_manager.get_image(f"delete_test_{i}")
            self.assertIsNone(image)


if __name__ == "__main__":
    unittest.main()