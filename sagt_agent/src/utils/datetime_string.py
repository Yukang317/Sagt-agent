"""日期时间转换工具模块

本模块提供时间戳与字符串之间的双向转换功能，专门处理东八区（UTC+8）时区转换。

核心功能：
1. timestamp2datetime: 将UTC时间戳转换为东八区时间字符串
2. datetime2timestamp: 将东八区时间字符串转换为UTC时间戳

业务背景：
- 企业微信API使用UTC时间戳作为时间参数
- 系统内部需要显示东八区时间给用户
- 需要确保时间转换的准确性和一致性

时区说明：
- 使用 pytz 库处理时区转换
- 目标时区：Asia/Shanghai（东八区，UTC+8）
- 输入/输出格式："%Y-%m-%d %H:%M:%S"

使用示例：
```python
from utils.datetime_string import timestamp2datetime, datetime2timestamp

# 时间戳转字符串
dt_str = timestamp2datetime(1752836258)  # 返回 "2025-09-17 10:37:38"

# 字符串转时间戳
timestamp = datetime2timestamp("2025-09-17 10:37:38")  # 返回 1752836258
```
"""

# 导入Python标准库的datetime模块和timezone
from datetime import datetime, timezone
# 导入pytz库用于时区处理
import pytz


def timestamp2datetime(timestamp: int) -> str:
    """
    将UTC时间戳转换为东八区时间字符串
    
    转换流程：
    1. 验证输入时间戳是否有效
    2. 创建UTC datetime对象
    3. 转换为东八区时间
    4. 格式化为指定字符串格式
    
    Args:
        timestamp: UTC时间戳（整数）
        
    Returns:
        str: 东八区时间字符串，格式为"%Y-%m-%d %H:%M:%S"
             如果输入无效或转换失败，返回空字符串
    """
    # 检查输入是否为空
    if not timestamp:
        return ""
    
    try:
        # 创建东八区时区对象
        tz_china = pytz.timezone('Asia/Shanghai')
        
        # 从UTC时间戳创建UTC datetime对象
        # 使用timezone.utc指定UTC时区
        dt_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        
        # 将UTC时间转换为东八区时间
        dt_china = dt_utc.astimezone(tz_china)
        
        # 格式化为字符串，格式：年-月-日 时:分:秒
        return dt_china.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        # 捕获所有异常，打印错误信息并返回空字符串
        print(f"时间转换失败: {e}")
        return ""


def datetime2timestamp(datatime: str) -> int:
    """
    将东八区时间字符串转换为UTC时间戳
    
    转换流程：
    1. 验证输入字符串是否有效
    2. 解析字符串为datetime对象
    3. 标记为东八区时间
    4. 转换为UTC时间戳
    
    Args:
        datatime: 东八区时间字符串，格式必须为"%Y-%m-%d %H:%M:%S"
        
    Returns:
        int: UTC时间戳（整数）
             如果输入无效或转换失败，返回0
    """
    # 检查输入是否为空
    if not datatime:
        return 0
    
    try:
        # 创建东八区时区对象
        tz_china = pytz.timezone('Asia/Shanghai')
        
        # 解析时间字符串为datetime对象
        # 输入字符串格式必须严格匹配 "%Y-%m-%d %H:%M:%S"
        dt = datetime.strptime(datatime, "%Y-%m-%d %H:%M:%S")
        
        # 将datetime对象标记为东八区时间
        # 使用localize方法确保时区信息正确
        dt_china = tz_china.localize(dt)
        
        # 转换为UTC时间戳（秒级）
        return int(dt_china.timestamp())
    except Exception as e:
        # 捕获所有异常，打印错误信息并返回0
        print(f"时间转换失败: {e}")
        return 0