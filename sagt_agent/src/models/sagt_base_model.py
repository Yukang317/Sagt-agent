"""SAGT Agent 基础模型基类定义

本文件定义了 SagtAgent 系统中所有业务模型的基类 SagtBaseModel，
封装了通用的模型操作方法，包括 JSON Schema 生成、示例数据生成等功能。

设计意图：
- 统一模型的序列化和反序列化行为
- 提供通用的 schema 和示例方法，减少重复代码
- 支持 API 文档自动生成
- 便于测试和 mock 数据生成
"""

# 导入 Pydantic 模型基类，所有业务模型都基于此构建
from pydantic import BaseModel
# 导入 JSON 处理模块，用于序列化操作
import json

class SagtBaseModel(BaseModel):
    """
    SagtAgent 自定义模型基类，继承自 Pydantic BaseModel
    
    业务背景：在 AI Agent 开发中，需要频繁进行以下操作：
    1. 生成模型的 JSON Schema（用于 LLM 提示词、API 文档）
    2. 生成示例数据（用于 LLM 示例输出、测试用例、文档展示）
    3. 将模型实例序列化为 JSON（用于日志记录、数据传输）
    
    通过基类封装这些通用逻辑，所有业务模型只需继承即可直接使用，无需重复实现。
    
    设计特点：
    - 提供类方法用于生成 schema 和示例
    - 提供实例方法用于序列化
    - 支持中文内容（ensure_ascii=False）
    - 格式化输出（indent=2）便于阅读
    """
    
    @classmethod
    def get_schema_json(cls) -> str:
        """
        获取模型的 JSON Schema 字符串
        
        JSON Schema 包含模型的完整字段定义、类型约束、默认值等信息，
        主要用途：
        - 作为 LLM 的输出格式约束（引导模型输出符合预期格式的 JSON）
        - 生成 API 接口文档
        - 数据验证和类型检查
        
        Returns:
            str: 格式化的 JSON Schema 字符串
        """
        # 调用 Pydantic 内置方法生成 JSON Schema 字典
        # model_json_schema() 返回包含字段定义、类型、约束的字典
        schema_dict = cls.model_json_schema()
        # 将字典序列化为格式化的 JSON 字符串
        # ensure_ascii=False 确保中文正常显示，indent=2 格式化输出
        return json.dumps(schema_dict, indent=2, ensure_ascii=False)
    
    @classmethod
    def get_example_instance(cls):
        """
        获取模型的示例实例
        
        子类应重写此方法提供符合业务场景的示例数据。
        默认实现返回所有字段为默认值的实例。
        
        业务用途：
        - LLM 提示词中的示例输出（帮助模型理解期望格式）
        - 单元测试的 mock 数据
        - API 文档中的示例响应
        - 前端开发的 mock 数据
        
        Returns:
            cls: 当前模型类的实例，包含示例数据
        """
        # 默认返回空实例（所有字段使用默认值）
        return cls()
    
    @classmethod
    def get_example_json(cls) -> str:
        """
        获取模型示例数据的 JSON 字符串
        
        先调用 get_example_instance() 获取示例实例，
        然后将其序列化为格式化的 JSON 字符串。
        
        主要用途：
        - LLM 提示词中的示例输出
        - API 文档中的示例响应展示
        
        Returns:
            str: 格式化的示例 JSON 字符串
        """
        # 获取示例实例（子类可重写提供自定义示例）
        example_instance = cls.get_example_instance()
        # 将示例实例转换为字典（model_dump() 是 Pydantic 的序列化方法）
        example_dict = example_instance.model_dump()
        # 序列化为格式化的 JSON 字符串
        return json.dumps(example_dict, indent=2, ensure_ascii=False)

    def model_dump_json(self) -> str:
        """
        将当前模型实例中的各个字段内容序列化为格式化的 JSON 字符串
        
        实例方法，用于将已有数据的模型实例转换为 JSON，
        主要用途：
        - 日志记录（结构化日志）
        - 数据持久化
        - API 响应序列化
        
        Returns:
            str: 格式化的 JSON 字符串
        """
        # 将当前实例转换为字典
        instance_dict = self.model_dump()
        # 序列化为格式化的 JSON 字符串
        return json.dumps(instance_dict, indent=2, ensure_ascii=False)