"""
数据库管理模块
提供数据库操作的封装和管理
"""
import sqlite3
import time
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager


logger = logging.getLogger("image_proxy.database")


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_file: str = "images.db"):
        self.db_file = Path(db_file)
        self.init_db()
    
    def init_db(self) -> None:
        """初始化数据库"""
        try:
            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    CREATE TABLE IF NOT EXISTS images (
                        md5 TEXT PRIMARY KEY,
                        path TEXT NOT NULL,
                        created_at INTEGER NOT NULL,
                        original_name TEXT,
                        width INTEGER,
                        height INTEGER,
                        access_count INTEGER DEFAULT 0,
                        file_size INTEGER DEFAULT 0,
                        updated_at INTEGER DEFAULT 0
                    )
                """)
                
                # 添加索引
                c.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON images(created_at)")
                c.execute("CREATE INDEX IF NOT EXISTS idx_access_count ON images(access_count)")
                
                conn.commit()
                logger.info("数据库初始化完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row  # 支持字典式访问
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"数据库操作错误: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def insert_image(self, md5: str, path: str, original_name: str, 
                    width: int, height: int, file_size: int) -> bool:
        """插入图片记录"""
        try:
            now = int(time.time())
            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    INSERT INTO images 
                    (md5, path, created_at, original_name, width, height, file_size, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (md5, str(path), now, original_name, width, height, file_size, now))
                conn.commit()
                logger.info(f"新增图片记录: {md5}")
                return True
        except sqlite3.IntegrityError:
            logger.warning(f"图片已存在: {md5}")
            return False
        except Exception as e:
            logger.error(f"插入图片记录失败: {e}")
            raise
    
    def get_image(self, md5: str) -> Optional[Dict[str, Any]]:
        """获取图片信息"""
        try:
            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    SELECT md5, path, created_at, original_name, width, height, 
                           access_count, file_size, updated_at
                    FROM images WHERE md5=?
                """, (md5,))
                row = c.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"查询图片信息失败: {e}")
            raise
    
    def update_access_count(self, md5: str) -> bool:
        """更新访问计数"""
        try:
            now = int(time.time())
            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    UPDATE images 
                    SET access_count = access_count + 1, updated_at = ?
                    WHERE md5 = ?
                """, (now, md5))
                conn.commit()
                affected = c.rowcount
                if affected > 0:
                    logger.debug(f"更新访问计数: {md5}")
                    return True
                return False
        except Exception as e:
            logger.error(f"更新访问计数失败: {e}")
            raise
    
    def get_expired_images(self, expire_days: int) -> List[Dict[str, Any]]:
        """获取过期图片列表"""
        try:
            expire_time = int(time.time()) - expire_days * 86400
            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                    SELECT md5, path, created_at, original_name
                    FROM images WHERE created_at < ?
                """, (expire_time,))
                return [dict(row) for row in c.fetchall()]
        except Exception as e:
            logger.error(f"查询过期图片失败: {e}")
            raise
    
    def delete_images(self, md5_list: List[str]) -> int:
        """批量删除图片记录"""
        try:
            with self.get_connection() as conn:
                c = conn.cursor()
                placeholders = ','.join(['?'] * len(md5_list))
                c.execute(f"DELETE FROM images WHERE md5 IN ({placeholders})", md5_list)
                conn.commit()
                deleted = c.rowcount
                logger.info(f"删除图片记录数: {deleted}")
                return deleted
        except Exception as e:
            logger.error(f"删除图片记录失败: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        try:
            with self.get_connection() as conn:
                c = conn.cursor()
                
                # 总图片数
                c.execute("SELECT COUNT(*) as total FROM images")
                total = c.fetchone()['total']
                
                # 总访问次数
                c.execute("SELECT SUM(access_count) as total_access FROM images")
                total_access = c.fetchone()['total_access'] or 0
                
                # 总文件大小
                c.execute("SELECT SUM(file_size) as total_size FROM images")
                total_size = c.fetchone()['total_size'] or 0
                
                # 最新图片
                c.execute("""
                    SELECT original_name, created_at 
                    FROM images 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """)
                latest = c.fetchone()
                
                return {
                    "total_images": total,
                    "total_access": total_access,
                    "total_size_bytes": total_size,
                    "latest_image": dict(latest) if latest else None,
                    "db_file_size": self.db_file.stat().st_size if self.db_file.exists() else 0
                }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            raise


if __name__ == "__main__":
    # 测试数据库功能
    db = DatabaseManager("test.db")
    print("数据库统计:", db.get_stats())