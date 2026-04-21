"""调试切面装饰器模块

本模块提供强大的函数调试功能，通过装饰器模式自动打印函数的入参、出参、执行时间和异常信息。

核心功能：
1. @debug 装饰器：自动记录函数调用信息
2. @debug_class 装饰器：为类的所有方法添加调试功能
3. DebugContext 上下文管理器：调试代码块执行
4. 多种预配置调试器：默认、简化、详细、性能调试

设计模式：
- 装饰器模式（Decorator Pattern）：无侵入式添加调试功能
- 切面编程（Aspect-Oriented Programming）：将调试逻辑与业务逻辑分离
- 单例思想：预定义的调试器实例可全局复用

功能特性：
- 支持递归调用的缩进显示
- 支持参数和返回值的格式化显示
- 支持自定义显示选项（参数、返回值、执行时间、异常）
- 支持输出长度限制，避免大量数据刷屏
- 异常捕获和记录，不影响业务代码执行

使用示例：
```python
from utils.debug_aspect import debug, debug_class, debug_context

# 函数调试
@debug
def my_function(x, y=10):
    return x + y

# 类调试（排除特定方法）
@debug_class(exclude_methods=["__init__"])
class MyClass:
    def method(self):
        pass

# 上下文调试
with debug_context("处理数据"):
    # 代码块
    pass
```
"""

# 导入functools用于保留函数元信息
import functools
# 导入inspect用于获取函数签名
import inspect
# 导入json用于数据序列化
import json
# 导入time用于计算执行时间
import time
# 导入类型提示
from typing import Any, Callable, Dict, List, Optional, Union
# 导入datetime用于时间戳显示
from datetime import datetime
# 导入pformat用于格式化复杂数据结构
from pprint import pformat

# 导入系统模块
import os
import sys
# 将当前模块所在目录的父目录加入Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入日志工具
from utils.agent_logger import get_logger


class DebugAspect:
    """
    调试切面类
    
    提供可配置的函数调试功能，支持：
    - 显示函数签名
    - 显示位置参数和关键字参数
    - 显示返回值
    - 显示执行时间
    - 显示异常信息
    - 递归调用的缩进显示
    """
    
    def __init__(self, 
                 enable: bool = True,
                 max_length: int = 500,
                 show_args: bool = True,
                 show_kwargs: bool = True,
                 show_return: bool = True,
                 show_execution_time: bool = True,
                 show_exception: bool = True,
                 indent: int = 2):
        """
        初始化调试切面
        
        Args:
            enable: 是否启用调试功能
            max_length: 参数/返回值的最大显示长度（超过则截断）
            show_args: 是否显示位置参数
            show_kwargs: 是否显示关键字参数
            show_return: 是否显示返回值
            show_execution_time: 是否显示执行时间（毫秒）
            show_exception: 是否显示异常信息
            indent: 缩进空格数（用于递归调用显示）
        """
        self.enable = enable                    # 调试开关
        self.max_length = max_length            # 输出长度限制
        self.show_args = show_args              # 是否显示位置参数
        self.show_kwargs = show_kwargs          # 是否显示关键字参数
        self.show_return = show_return          # 是否显示返回值
        self.show_execution_time = show_execution_time  # 是否显示执行时间
        self.show_exception = show_exception    # 是否显示异常
        self.indent = indent                    # 缩进空格数
        self._call_depth = 0  # 调用深度，用于递归调用时的缩进显示
    
    def _format_value(self, value: Any, max_length: Optional[int] = None) -> str:
        """
        格式化值为字符串
        
        支持JSON序列化（字典、列表、元组），复杂对象使用pformat。
        超过长度限制时自动截断。
        
        Args:
            value: 要格式化的值
            max_length: 最大长度限制，默认使用实例的max_length
            
        Returns:
            str: 格式化后的字符串
        """
        # 使用默认或指定的最大长度
        if max_length is None:
            max_length = self.max_length
        
        try:
            # 尝试JSON序列化（更清晰的格式）
            if isinstance(value, (dict, list, tuple)):
                formatted = json.dumps(value, ensure_ascii=False, indent=2)
            else:
                # 其他类型直接转字符串
                formatted = str(value)
        except (TypeError, ValueError):
            # JSON序列化失败时，使用pformat格式化
            formatted = pformat(value, width=80, depth=3)
        
        # 长度限制处理
        if len(formatted) > max_length:
            formatted = formatted[:max_length] + "..."
        
        return formatted
    
    def _get_function_signature(self, func: Callable) -> str:
        """
        获取函数签名字符串
        
        Args:
            func: 函数对象
            
        Returns:
            str: 函数签名（如 func_name(arg1, arg2=default)）
        """
        try:
            # 使用inspect获取函数签名
            sig = inspect.signature(func)
            return f"{func.__name__}{sig}"
        except (ValueError, TypeError):
            # 获取签名失败时返回简化形式
            return f"{func.__name__}(...)"
    
    def _print_with_indent(self, message: str, extra_indent: int = 0):
        """
        带缩进打印消息
        
        根据调用深度和额外缩进参数，生成带缩进的日志消息。
        
        Args:
            message: 要打印的消息
            extra_indent: 额外的缩进级别（用于子项）
        """
        # 如果未启用调试，直接返回
        if not self.enable:
            return
        
        # 获取日志器实例
        logger = get_logger("debug_aspect")
        
        # 计算总缩进空格数
        total_indent = (self._call_depth + extra_indent) * self.indent
        indent_str = " " * total_indent
        
        # 处理多行消息，每行都添加缩进
        lines = message.split('\n')
        for line in lines:
            formatted_line = f"{indent_str}{line}"
            logger.info(formatted_line)
    
    def debug_function(self, 
                      prefix: str = "",
                      show_signature: bool = True,
                      custom_formatter: Optional[Callable] = None):
        """
        创建函数调试装饰器
        
        返回一个装饰器，用于包装函数并添加调试日志。
        
        Args:
            prefix: 日志前缀（用于区分不同模块）
            show_signature: 是否显示函数签名
            custom_formatter: 自定义格式化函数（可选）
            
        Returns:
            Callable: 装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            # 使用functools.wraps保留原函数的元信息
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # 如果未启用调试，直接执行原函数
                if not self.enable:
                    return func(*args, **kwargs)
                
                # 增加调用深度（用于递归缩进）
                self._call_depth += 1
                
                try:
                    # 构建函数名称（带前缀）
                    func_name = f"{prefix}{func.__name__}" if prefix else func.__name__
                    # 获取当前时间戳
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    
                    # 打印函数开始标记
                    self._print_with_indent(f"🔍 [{timestamp}] ➤ {func_name}")
                    
                    # 显示函数签名
                    if show_signature:
                        signature = self._get_function_signature(func)
                        self._print_with_indent(f"📝 签名: {signature}", 1)
                    
                    # 显示位置参数
                    if self.show_args and args:
                        self._print_with_indent("📥 位置参数:", 1)
                        for i, arg in enumerate(args):
                            formatted_arg = self._format_value(arg)
                            self._print_with_indent(f"  [{i}]: {formatted_arg}", 1)
                    
                    # 显示关键字参数
                    if self.show_kwargs and kwargs:
                        self._print_with_indent("📥 关键字参数:", 1)
                        for key, value in kwargs.items():
                            formatted_value = self._format_value(value)
                            self._print_with_indent(f"  {key}: {formatted_value}", 1)
                    
                    # 执行函数并计时
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    end_time = time.time()
                    
                    # 显示返回值
                    if self.show_return:
                        formatted_result = self._format_value(result)
                        self._print_with_indent(f"📤 返回值: {formatted_result}", 1)
                    
                    # 显示执行时间
                    if self.show_execution_time:
                        execution_time = (end_time - start_time) * 1000
                        self._print_with_indent(f"⏱️ 执行时间: {execution_time:.2f}ms", 1)
                    
                    # 打印函数完成标记
                    end_timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    self._print_with_indent(f"✅ [{end_timestamp}] ✓ {func_name}")
                    
                    return result
                    
                except Exception as e:
                    # 显示异常信息
                    if self.show_exception:
                        error_timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        self._print_with_indent(f"❌ [{error_timestamp}] ✗ {func_name}", 0)
                        self._print_with_indent(f"🚨 异常: {type(e).__name__}: {str(e)}", 1)
                    
                    # 重新抛出异常，不影响业务逻辑
                    raise
                    
                finally:
                    # 减少调用深度
                    self._call_depth -= 1
            
            return wrapper
        return decorator
    
    def debug_class(self, 
                   include_private: bool = False,
                   include_magic: bool = False,
                   exclude_methods: Optional[List[str]] = None):
        """
        创建类调试装饰器
        
        为类的所有方法添加调试功能，可配置是否包含私有方法和魔术方法。
        
        Args:
            include_private: 是否包含私有方法（以_开头）
            include_magic: 是否包含魔术方法（以__开头和结尾）
            exclude_methods: 排除的方法名称列表
            
        Returns:
            Callable: 装饰器函数
        """
        # 处理默认排除列表
        exclude_methods = exclude_methods or []
        
        def decorator(cls):
            # 遍历类的所有属性
            for attr_name in dir(cls):
                attr = getattr(cls, attr_name)
                
                # 跳过非方法属性
                if not callable(attr):
                    continue
                
                # 跳过排除的方法
                if attr_name in exclude_methods:
                    continue
                
                # 跳过私有方法（除非明确包含）
                if attr_name.startswith('_') and not include_private:
                    # 魔术方法特殊处理
                    if attr_name.startswith('__') and attr_name.endswith('__'):
                        if not include_magic:
                            continue
                    else:
                        continue
                
                # 为方法应用调试装饰器
                debug_method = self.debug_function(
                    prefix=f"{cls.__name__}.",
                    show_signature=True
                )(attr)
                
                # 替换原方法
                setattr(cls, attr_name, debug_method)
            
            return cls
        return decorator


# ========== 预定义的调试实例 ==========

# 默认调试器（显示完整信息）
default_debug = DebugAspect()

# 简化调试器（只显示函数名和返回值）
simple_debug = DebugAspect(
    show_args=False,
    show_kwargs=False,
    show_execution_time=False,
    max_length=100
)

# 详细调试器（显示所有信息，更长的输出）
verbose_debug = DebugAspect(
    max_length=1000,
    show_args=True,
    show_kwargs=True,
    show_return=True,
    show_execution_time=True,
    show_exception=True
)

# 性能调试器（主要关注执行时间）
performance_debug = DebugAspect(
    show_args=False,
    show_kwargs=False,
    show_return=False,
    show_execution_time=True,
    max_length=50
)


# ========== 便捷装饰器 ==========

def debug(func: Callable = None, *, 
         enable: bool = True,
         show_args: bool = True,
         show_return: bool = True,
         max_length: int = 300):
    """
    便捷的函数调试装饰器
    
    支持两种使用方式：
    1. @debug（无参数）
    2. @debug(show_args=False, max_length=100)（带参数）
    
    Args:
        func: 被装饰的函数（当无参数调用时）
        enable: 是否启用调试
        show_args: 是否显示参数
        show_return: 是否显示返回值
        max_length: 最大显示长度
        
    Returns:
        Callable: 装饰后的函数或装饰器
    """
    def decorator(f):
        # 创建调试切面实例
        aspect = DebugAspect(
            enable=enable,
            show_args=show_args,
            show_return=show_return,
            max_length=max_length
        )
        # 应用调试装饰器
        return aspect.debug_function()(f)
    
    # 判断是否为带参数调用
    if func is None:
        # 被当作带参数的装饰器使用
        return decorator
    else:
        # 被当作无参数的装饰器使用
        return decorator(func)


def debug_class(cls=None, *, 
               include_private: bool = False,
               exclude_methods: Optional[List[str]] = None):
    """
    便捷的类调试装饰器
    
    支持两种使用方式：
    1. @debug_class（无参数）
    2. @debug_class(exclude_methods=["__init__"])（带参数）
    
    Args:
        cls: 被装饰的类（当无参数调用时）
        include_private: 是否包含私有方法
        exclude_methods: 排除的方法列表
        
    Returns:
        Callable: 装饰后的类或装饰器
    """
    def decorator(c):
        # 创建调试切面实例
        aspect = DebugAspect()
        # 应用类调试装饰器
        return aspect.debug_class(
            include_private=include_private,
            exclude_methods=exclude_methods
        )(c)
    
    # 判断是否为带参数调用
    if cls is None:
        return decorator
    else:
        return decorator(cls)


# ========== 上下文管理器 ==========

class DebugContext:
    """
    调试上下文管理器
    
    用于调试代码块的执行，记录开始时间、结束时间和执行时长。
    支持嵌套使用，自动处理缩进。
    
    使用方式：
    with debug_context("数据处理"):
        # 代码块
        pass
    """
    
    def __init__(self, name: str, debug_aspect: Optional[DebugAspect] = None):
        """
        初始化调试上下文
        
        Args:
            name: 上下文名称（用于标识代码块）
            debug_aspect: 调试切面实例（可选，默认使用default_debug）
        """
        self.name = name
        self.aspect = debug_aspect or default_debug
        self.start_time = None
    
    def __enter__(self):
        """
        进入上下文时记录开始信息
        
        Returns:
            DebugContext: 上下文实例
        """
        if self.aspect.enable:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.aspect._print_with_indent(f"🎯 [{timestamp}] 开始: {self.name}")
            self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        退出上下文时记录完成信息或异常
        
        Args:
            exc_type: 异常类型（如果有）
            exc_val: 异常值（如果有）
            exc_tb: 异常追踪（如果有）
            
        Returns:
            bool: False（不抑制异常）
        """
        if self.aspect.enable:
            end_time = time.time()
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            if exc_type is None:
                # 正常结束
                if self.start_time:
                    duration = (end_time - self.start_time) * 1000
                    self.aspect._print_with_indent(
                        f"✅ [{timestamp}] 完成: {self.name} ({duration:.2f}ms)"
                    )
                else:
                    self.aspect._print_with_indent(f"✅ [{timestamp}] 完成: {self.name}")
            else:
                # 异常结束
                self.aspect._print_with_indent(
                    f"❌ [{timestamp}] 异常: {self.name} - {exc_type.__name__}: {exc_val}"
                )


def debug_context(name: str, debug_aspect: Optional[DebugAspect] = None):
    """
    创建调试上下文管理器的便捷函数
    
    Args:
        name: 上下文名称
        debug_aspect: 调试切面实例（可选）
        
    Returns:
        DebugContext: 上下文管理器实例
    """
    return DebugContext(name, debug_aspect)


# ========== 使用示例 ==========

if __name__ == "__main__":
    # 示例1: 基本函数调试
    @debug
    def example_function(x: int, y: str = "default") -> dict:
        """示例函数"""
        time.sleep(0.1)  # 模拟耗时操作
        return {"result": x * 2, "message": f"Hello {y}"}
    
    # 示例2: 类调试
    @debug_class(exclude_methods=["__init__"])
    class ExampleClass:
        def __init__(self, name: str):
            self.name = name
        
        def method1(self, value: int) -> str:
            return f"{self.name}: {value}"
        
        def method2(self, data: dict) -> list:
            return list(data.keys())
    
    # 示例3: 上下文管理器
    def demo_context():
        with debug_context("数据处理流程"):
            time.sleep(0.05)
            with debug_context("子任务1"):
                time.sleep(0.02)
            with debug_context("子任务2"):
                time.sleep(0.03)
    
    # 使用logger输出演示信息
    logger = get_logger("debug_aspect")
    logger.info("🚀 调试切面演示")
    logger.info("=" * 50)
    
    # 测试函数调试
    result = example_function(5, "World")
    
    # 测试类调试
    obj = ExampleClass("测试对象")
    obj.method1(42)
    obj.method2({"a": 1, "b": 2})
    
    # 测试上下文管理器
    demo_context()
    
    logger.info("✅ 演示完成！")