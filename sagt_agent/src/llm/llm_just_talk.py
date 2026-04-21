"""闲聊回复生成LLM模块

本模块负责调用LLM处理用户的自由对话请求（JustTalkOutput）。

业务背景：当用户没有明确的业务意图（如生成客户画像、标签建议等），
或者只是想进行普通对话时，系统会路由到该模块进行处理。

核心功能：
1. 处理用户的自由对话请求
2. 提供有趣、友好的回答
3. 支持各种话题的讨论
4. 作为系统的"兜底"处理模块

数据来源：
- 用户输入（input）：用户的问题或聊天内容

输出：
- JustTalkOutput：闲聊回复内容

设计特点：
- 最简单的LLM调用模块，仅需用户输入
- 不依赖任何业务数据
- 作为意图无法识别时的兜底方案
"""

# 导入初始化好的LLM实例
from llm.llm_setting import chat_model as llm
# 导入LangChain的AIMessage类型
from langchain_core.messages import AIMessage
# 导入日志工具
from utils.agent_logger import get_logger
# 导入闲聊输出模型
from models.sagt_models import JustTalkOutput

# 获取本模块的日志实例
logger = get_logger("llm_just_talk")

def llm_just_talk(input: str) -> JustTalkOutput:
    """
    处理用户的自由对话请求

    作为系统的"兜底子模块"，处理所有未明确意图的用户请求。
    
    处理流程：
    1. 构建提示词（包含角色定义、数据结构、示例、用户输入）
    2. 调用LLM生成回复
    3. 解析LLM输出为结构化的JustTalkOutput对象
    4. 返回结果（失败时返回空对象）

    适用场景：
    - 用户没有明确的业务意图
    - 用户想进行普通聊天
    - 用户咨询非业务相关问题
    - 意图检测无法识别用户意图

    Args:
        input: 用户输入的问题或聊天内容

    Returns:
        JustTalkOutput: 闲聊回复内容
    """

    # 构建完整的提示词
    prompt = _just_talk_instructions.format(
        input=input,                              # 用户输入内容
        schema_json=JustTalkOutput.get_schema_json(),  # 数据结构定义
        example_json=JustTalkOutput.get_example_json(),# 示例数据
    )

    # 记录调试日志
    logger.debug(f"prompt: {prompt}")

    # 调用LLM生成闲聊回复
    generated_result: AIMessage = llm.invoke(prompt)
    logger.debug(f"generated_result: {generated_result}")

    # 提取LLM输出内容（处理空结果情况）
    if generated_result and generated_result.content:
        just_talk_json = generated_result.content
    else:
        just_talk_json = "{}"

    # 记录调试日志
    logger.debug(f"just_talk_json: {just_talk_json}")

    # 解析JSON并返回结果
    try:
        # 使用Pydantic验证JSON并转换为模型对象
        just_talk = JustTalkOutput.model_validate_json(just_talk_json)
    except Exception as e:
        # 解析失败时返回空对象
        logger.error(f"解析JustTalkOutput失败: {e}")
        just_talk = JustTalkOutput()

    # 记录结果日志
    logger.info(f"just_talk: {just_talk.model_dump_json()}")

    return just_talk


_just_talk_instructions = """
你是一个出色的助手，可以帮助公司员工解决/回答各种问题。如果是其他讨论/闲聊的内容，你也可以提供有意思的回答或者建议。

下面是你需要回答的问题，你需要回答这个问题，并按照 JustTalkOutput 数据结构定义返回JSON。

【注意】请不要在JSON对象前后包含任何文本。也不要包含“```json”或者“```”这样的文本。
【注意】请不要在json对象中包含任何未定义的字段。

这里是JustTalkOutput的数据结构定义：
-------------------
{schema_json}
-------------------

json对象示例：
-------------------
{example_json}
-------------------

员工输入的问题：
-------------------
{input}
-------------------

"""