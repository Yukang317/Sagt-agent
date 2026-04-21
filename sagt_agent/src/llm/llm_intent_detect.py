"""意图检测LLM模块

本模块负责调用LLM进行用户意图识别（Intent Detection）。

业务背景：系统需要根据销售人员的输入，判断其业务意图，
然后路由到对应的处理子图（客户画像、标签建议、聊天建议等）。

核心功能：
1. 接收用户输入的任务描述
2. 根据预定义的意图列表进行匹配
3. 返回识别到的意图
4. 后续流程根据意图调用对应的子图

支持的意图类型：
- chat_suggestion: 生成聊天建议
- kf_chat_suggestion: 生成客服聊天建议
- tag_suggestion: 生成客户标签建议
- profile_suggestion: 生成客户画像建议
- schedule_suggestion: 生成日程建议
- no_clear_intention: 未明确意图（闲聊）

数据来源：
- task_input: 用户输入的任务描述
- intents: 系统支持的意图列表

输出：
- Intent: 识别到的意图对象

注意：当前代码中意图检测被注释掉，默认路由到闲聊子图。
"""

# 导入JSON处理模块
import json
# 导入类型定义模块
from typing import List
# 导入意图模型
from models.sagt_models import Intent
# 导入初始化好的LLM实例
from llm.llm_setting import chat_model as llm
# 导入LangChain的AIMessage类型
from langchain_core.messages import AIMessage
# 导入日志工具
from utils.agent_logger import get_logger

# 获取本模块的日志实例
logger = get_logger("llm_intent_detect")


def llm_intent_detect(task_input: str, intents: List[Intent]) -> Intent:
    """
    意图检测函数

    根据用户输入的任务描述，识别其业务意图。
    
    处理流程：
    1. 构建提示词（包含角色定义、意图列表、数据结构、示例、用户输入）
    2. 调用LLM进行意图识别
    3. 解析LLM输出为结构化的Intent对象
    4. 返回结果（失败时返回空对象）

    业务规则：
    - 指令的都是公司内部销售人员，不是客户
    - 客户相关信息在后续流程中从系统加载
    - 返回的意图ID必须在预定义的意图列表中

    Args:
        task_input: 用户输入的任务描述
        intents: 系统支持的意图列表

    Returns:
        Intent: 识别到的意图对象（包含intent_id和intent_description）
    """

    # 构建完整的提示词
    prompt = _intent_detection_instructions.format(
        task_input=task_input,  # 用户输入的任务描述
        # 将意图列表转换为JSON格式字符串
        intents=json.dumps([intent.model_dump() for intent in intents], ensure_ascii=False, indent=4),
        schema_json=Intent.get_schema_json(),   # 数据结构定义
        example_json=Intent.get_example_json(), # 示例数据
    )

    # 记录调试日志
    logger.debug(f"prompt: {prompt}")

    # 调用LLM进行意图检测
    generated_result: AIMessage = llm.invoke(prompt)
    logger.debug(f"generated_result: {generated_result}")
    
    # 提取LLM输出内容（处理空结果情况）
    if generated_result and generated_result.content:
        intent_json = generated_result.content  
    else:
        intent_json = "{}"
    
    # 记录调试日志
    logger.debug(f"intent_json: {intent_json}")
    
    # 解析JSON并返回结果
    try:
        # 使用Pydantic验证JSON并转换为模型对象
        intent = Intent.model_validate_json(intent_json)
    except Exception as e:
        # 解析失败时返回空对象
        logger.error(f"解析意图检测结果失败: {e}")
        intent = Intent()
    
    # 记录结果日志
    logger.info(f"intent: {intent.model_dump_json()}")

    return intent

_intent_detection_instructions = """
你是一个出色的面向公司内部销售人员的智能助手。
给你指令的都是公司内部销售人员，不是客户。
【客户相关信息是在后续的流程中从系统中加载进来的】

现在需要根据销售人员输入的任务信息，判断员工的意图。


以下是意图列表：
-------------------
{intents}
-------------------

你需要根据任务描述，返回意图 Intent 对象，后续流程会根据你返回的意图调用对应的流程。

【重要】你必须回复一个有效的JSON对象
【重要】请不要在JSON对象前后包含任何文本。也不要包含“```json”或者“```”这样的文本。
【重要】请不要在json对象中包含任何未定义的字段。

这里是Intent的数据结构定义：
-------------------
{schema_json}
-------------------

JSON 对象样例：
-------------------
{example_json}
-------------------

任务描述：
-------------------
{task_input}
-------------------

"""