"""日志工具模块

本模块提供统一的日志配置和获取方法，为智能体应用提供标准化的日志输出能力。

核心功能：
1. 配置全局日志格式和级别
2. 创建应用专用的日志器实例
3. 支持控制台输出

日志格式说明：
`%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- asctime: 日志时间戳
- name: 日志器名称（用于区分不同模块）
- levelname: 日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）
- message: 日志消息内容

使用方式：
```python
from utils.agent_logger import get_logger

logger = get_logger("my_module")
logger.info("这是一条信息日志")
logger.error("这是一条错误日志")
```
"""

# 导入Python标准日志库
import logging


def get_logger(name="default", level=logging.INFO):
    """
    创建并配置日志器
    
    该函数负责：
    1. 配置根日志器的格式和输出处理器
    2. 创建并返回指定名称的应用专用日志器
    3. 设置日志级别
    
    Args:
        name: 日志器名称，用于区分不同模块，默认为"default"
        level: 日志级别，默认为logging.INFO
        
    Returns:
        logging.Logger: 配置好的日志器实例
    """
    # 定义日志格式字符串
    # 格式包含：时间戳、日志器名称、日志级别、日志消息
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 配置根日志器
    logging.basicConfig(
        level=level,           # 设置日志级别
        format=log_format,     # 设置日志格式
        handlers=[
            # 添加控制台输出处理器（StreamHandler）
            logging.StreamHandler(),
        ]
    )
    
    # 创建应用专用日志器
    # 使用指定名称创建，便于区分不同模块的日志
    logger = logging.getLogger(name)
    # 设置日志级别（覆盖根日志器设置）
    logger.setLevel(level)
    
    return logger