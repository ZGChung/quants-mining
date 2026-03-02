"""
异常处理和日志模块
"""

import logging
import traceback
from functools import wraps
from datetime import datetime
from pathlib import Path
import sys

# 配置日志
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "quantmining.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("QuantMining")


class QuantMiningError(Exception):
    """QuantMining 基础异常"""
    pass


class DataFetchError(QuantMiningError):
    """数据获取异常"""
    pass


class StrategyError(QuantMiningError):
    """策略执行异常"""
    pass


class BacktestError(QuantMiningError):
    """回测异常"""
    pass


def error_handler(func):
    """
    错误处理装饰器
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DataFetchError as e:
            logger.error(f"数据获取错误: {e}")
            raise
        except StrategyError as e:
            logger.error(f"策略执行错误: {e}")
            raise
        except BacktestError as e:
            logger.error(f"回测错误: {e}")
            raise
        except Exception as e:
            logger.error(f"未知错误 in {func.__name__}: {e}")
            logger.debug(traceback.format_exc())
            raise QuantMiningError(f"执行失败: {e}") from e
    return wrapper


def log_execution(func):
    """
    日志装饰器 - 记录函数执行
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"▶️ 开始执行: {func.__name__}")
        start_time = datetime.now()
        
        try:
            result = func(*args, **kwargs)
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ 完成: {func.__name__} ({elapsed:.2f}s)")
            return result
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ 失败: {func.__name__} ({elapsed:.2f}s) - {e}")
            raise
    
    return wrapper


class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, total: int, desc: str = "Processing"):
        self.total = total
        self.desc = desc
        self.current = 0
        self.start_time = datetime.now()
    
    def update(self, n: int = 1):
        """更新进度"""
        self.current += n
        elapsed = (datetime.now() - self.start_time).total_seconds()
        pct = (self.current / self.total) * 100 if self.total > 0 else 0
        
        if self.current % 10 == 0 or self.current == self.total:
            logger.info(f"{self.desc}: {self.current}/{self.total} ({pct:.1f}%) - {elapsed:.1f}s")
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass


class Cache:
    """简单缓存"""
    
    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size
        self.access_count = {}
    
    def get(self, key: str):
        """获取缓存"""
        if key in self.cache:
            self.access_count[key] = self.access_count.get(key, 0) + 1
            return self.cache[key]
        return None
    
    def set(self, key: str, value):
        """设置缓存"""
        if len(self.cache) >= self.max_size:
            # 删除最少使用的
            lru_key = min(self.access_count, key=self.access_count.get)
            del self.cache[lru_key]
            del self.access_count[lru_key]
        
        self.cache[key] = value
        self.access_count[key] = 1
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.access_count.clear()


# 全局缓存实例
data_cache = Cache(max_size=50)


def retry(max_attempts: int = 3, delay: float = 1.0):
    """
    重试装饰器
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"重试 {attempt + 1}/{max_attempts}: {e}")
                        time.sleep(delay)
                    else:
                        logger.error(f"重试失败: {e}")
            
            raise last_exception
        
        return wrapper
    return decorator


if __name__ == "__main__":
    # 测试错误处理
    @error_handler
    @log_execution
    def test_function(x):
        return x * 2
    
    result = test_function(5)
    print(f"Result: {result}")
