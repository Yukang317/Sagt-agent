"""SAGT Agent 主图定义文件

本文件定义了 SAGT Agent 的核心控制流，使用 LangGraph 构建状态图系统，
整合数据加载、意图检测和各种业务子图，实现完整的智能助手功能。
"""

# 导入 LangGraph 核心组件
from langgraph.graph import START, END, StateGraph
# 导入状态定义
from graphs.sagt_graph.sagt_state import SagtState, InputState, OutputState, SagtConfig

# 导入各功能子图
from graphs.sagt_graph.sagt_sub_graph_profile.sub_profile_graph import sub_profile_graph  # 客户画像子图
from graphs.sagt_graph.sagt_sub_graph_chat_suggestion.sub_chat_suggestion_graph import sub_chat_suggestion_graph  # 客户聊天建议子图
from graphs.sagt_graph.sagt_sub_graph_kf_chat_suggestion.sub_kf_chat_suggestion_graph import sub_kf_chat_suggestion_graph  # 客服聊天建议子图
from graphs.sagt_graph.sagt_sub_graph_tag.sub_tag_graph import sub_tag_graph  # 客户标签子图
from graphs.sagt_graph.sagt_sub_graph_schedule.sub_schedule_graph import sub_schedule_graph  # 客户日程子图
from graphs.sagt_graph.sagt_sub_graph_talk.sub_talk_graph import sub_talk_graph  # 闲聊子图

# 导入核心节点
from graphs.sagt_graph.sagt_node import NodeName, intent_detection, task_result_confirm, welcome_message, cleanup_state_node
# 导入数据加载节点
from graphs.sagt_graph.sagt_node_load_data import NodeName as LoadDataNodeName
from graphs.sagt_graph.sagt_node_load_data import (
    load_welcome_message_node,  # 加载欢迎消息节点
    load_employee_info_node,    # 加载员工信息节点
    load_tag_setting_node,      # 加载标签设置节点
    load_customer_info_node,    # 加载客户信息节点
    load_chat_history_node,     # 加载聊天历史节点
    load_kf_chat_history_node,  # 加载微信客服聊天历史节点
    load_order_history_node     # 加载订单历史节点
)

# 导入环境变量处理模块
import os
from dotenv import load_dotenv
# 加载环境变量
load_dotenv()

"""构建主状态图

使用 StateGraph 创建 SAGT Agent 的主控制流，定义状态模式、输入模式、输出模式和配置模式。
"""
builder = StateGraph(
    state_schema=SagtState,      # 主状态模式
    input_schema=InputState,     # 输入模式
    output_schema=OutputState,   # 输出模式
    config_schema=SagtConfig     # 配置模式
)

"""添加核心节点

添加主图的核心处理节点，包括状态清理、欢迎消息、意图检测和任务结果确认。
"""
builder.add_node(NodeName.CLEANUP_STATE.value, cleanup_state_node)  # 清理状态节点
builder.add_node(NodeName.WELCOME_MESSAGE.value, welcome_message)    # 欢迎消息节点
builder.add_node(NodeName.INTENT_DETECTION.value, intent_detection)  # 意图检测节点
builder.add_node(NodeName.TASK_RESULT_CONFIRM.value, task_result_confirm)  # 任务结果确认节点

"""添加数据加载节点

添加各类数据加载节点，为后续业务处理提供数据基础。
"""
builder.add_node(LoadDataNodeName.LOAD_WELCOME_MESSAGE.value, load_welcome_message_node)  # 加载欢迎消息节点
builder.add_node(LoadDataNodeName.LOAD_EMPLOYEE_INFO.value, load_employee_info_node)      # 加载员工信息节点
builder.add_node(LoadDataNodeName.LOAD_TAG_SETTING.value, load_tag_setting_node)          # 加载标签设置节点
builder.add_node(LoadDataNodeName.LOAD_CUSTOMER_INFO.value, load_customer_info_node)      # 加载客户信息节点
builder.add_node(LoadDataNodeName.LOAD_CHAT_HISTORY.value, load_chat_history_node)         # 加载聊天历史节点
builder.add_node(LoadDataNodeName.LOAD_KF_CHAT_HISTORY.value, load_kf_chat_history_node)  # 加载微信客服聊天历史节点
builder.add_node(LoadDataNodeName.LOAD_ORDER_HISTORY.value, load_order_history_node)       # 加载订单历史节点

"""添加业务子图节点

添加各功能子图作为节点，用于处理具体的业务逻辑。
"""
builder.add_node(NodeName.CHAT_SUGGESTION.value, sub_chat_suggestion_graph)      # 生成客户聊天建议子图
builder.add_node(NodeName.KF_CHAT_SUGGESTION.value, sub_kf_chat_suggestion_graph)  # 生成客服聊天建议子图
builder.add_node(NodeName.TAG_SUGGESTION.value, sub_tag_graph)                    # 生成客户标签子图
builder.add_node(NodeName.PROFILE_SUGGESTION.value, sub_profile_graph)            # 生成客户画像子图
builder.add_node(NodeName.SCHEDULE_SUGGESTION.value, sub_schedule_graph)          # 生成客户日程子图
builder.add_node(NodeName.NO_CLEAR_INTENTION.value, sub_talk_graph)               # 未明确意图时的闲聊子图

"""定义主图流程

定义节点之间的流转关系，形成完整的处理流程：
1. 清理状态
2. 发送欢迎消息
3. 按顺序加载各类数据
4. 执行意图检测
5. 根据意图路由到对应子图
"""
# 从开始节点到清理状态节点
builder.add_edge(START, NodeName.CLEANUP_STATE.value)
# 清理状态后发送欢迎消息
builder.add_edge(NodeName.CLEANUP_STATE.value, NodeName.WELCOME_MESSAGE.value)
# 欢迎消息后加载欢迎信息
builder.add_edge(NodeName.WELCOME_MESSAGE.value, LoadDataNodeName.LOAD_WELCOME_MESSAGE.value)
# 按顺序加载各类数据
builder.add_edge(LoadDataNodeName.LOAD_WELCOME_MESSAGE.value, LoadDataNodeName.LOAD_EMPLOYEE_INFO.value)
builder.add_edge(LoadDataNodeName.LOAD_EMPLOYEE_INFO.value, LoadDataNodeName.LOAD_TAG_SETTING.value)
builder.add_edge(LoadDataNodeName.LOAD_TAG_SETTING.value, LoadDataNodeName.LOAD_CUSTOMER_INFO.value)
builder.add_edge(LoadDataNodeName.LOAD_CUSTOMER_INFO.value, LoadDataNodeName.LOAD_CHAT_HISTORY.value)
builder.add_edge(LoadDataNodeName.LOAD_CHAT_HISTORY.value, LoadDataNodeName.LOAD_KF_CHAT_HISTORY.value)
builder.add_edge(LoadDataNodeName.LOAD_KF_CHAT_HISTORY.value, LoadDataNodeName.LOAD_ORDER_HISTORY.value)
# 数据加载完成后执行意图检测
builder.add_edge(LoadDataNodeName.LOAD_ORDER_HISTORY.value, NodeName.INTENT_DETECTION.value)

"""定义子图执行后的流程

各子图执行完成后，统一跳转到任务结果确认节点，然后结束流程。
"""
builder.add_edge(NodeName.CHAT_SUGGESTION.value, NodeName.TASK_RESULT_CONFIRM.value)      # 客户聊天建议完成后确认结果
builder.add_edge(NodeName.KF_CHAT_SUGGESTION.value, NodeName.TASK_RESULT_CONFIRM.value)   # 客服聊天建议完成后确认结果
builder.add_edge(NodeName.TAG_SUGGESTION.value, NodeName.TASK_RESULT_CONFIRM.value)       # 客户标签完成后确认结果
builder.add_edge(NodeName.PROFILE_SUGGESTION.value, NodeName.TASK_RESULT_CONFIRM.value)   # 客户画像完成后确认结果
builder.add_edge(NodeName.SCHEDULE_SUGGESTION.value, NodeName.TASK_RESULT_CONFIRM.value) # 客户日程完成后确认结果
builder.add_edge(NodeName.NO_CLEAR_INTENTION.value, NodeName.TASK_RESULT_CONFIRM.value)  # 闲聊完成后确认结果
builder.add_edge(NodeName.TASK_RESULT_CONFIRM.value, END)  # 任务结果确认后结束流程

"""编译图实例

根据环境配置，决定是否启用 Langfuse 监控，然后编译图实例。
"""
if os.getenv("LANGFUSE_ENABLED", "false").lower() == "true":
    # 启用 Langfuse 监控
    from langfuse.langchain import CallbackHandler
    langfuse_handler = CallbackHandler()
    graph = builder.compile().with_config({"callbacks": [langfuse_handler]})
else:
    # 不启用 Langfuse 监控
    graph = builder.compile()