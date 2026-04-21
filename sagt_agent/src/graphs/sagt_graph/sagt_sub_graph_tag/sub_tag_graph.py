"""客户标签子图定义文件

本文件定义了客户标签子图的控制流程，使用LangGraph构建状态图。

业务流程：
1. 发送欢迎消息
2. 调用LLM生成客户标签建议（添加/删除）
3. 通过企业微信通知用户确认
4. 等待用户反馈（确认/放弃/重新生成）
5. 根据反馈路由：
   - 确认 → 更新客户标签到存储 → 通知结果 → 结束
   - 放弃 → 直接结束
   - 重新生成 → 回到步骤2

核心特点：
- 包含人工确认环节，确保数据准确性
- 支持循环重试（重新生成）
- 通过企业微信通知用户
- 使用SAGT自有存储而非企业微信标签（开发环境）
"""

# 导入LangGraph核心组件
from langgraph.graph import START, END, StateGraph
# 导入子图状态定义
from graphs.sagt_graph.sagt_sub_graph_tag.sub_tag_state import (
    SubTagState,       # 子图完整状态
    SubTagInputState,  # 子图输入状态
    SubTagOutputState  # 子图输出状态
)
# 导入子图节点函数
from graphs.sagt_graph.sagt_sub_graph_tag.sub_tag_node import (
    generate_customer_tag,  # 生成客户标签建议节点
    update_customer_tag,    # 更新客户标签节点
    human_feedback,         # 人工反馈节点
    welcome_message_node,   # 欢迎消息节点
    notify_human_feedback,  # 通知确认节点
    notify_human_result     # 通知结果节点
)
# 导入节点名称枚举
from graphs.sagt_graph.sagt_sub_graph_tag.sub_tag_node import NodeName
# 导入配置定义
from graphs.sagt_graph.sagt_state import SagtConfig

"""构建客户标签子图

使用StateGraph创建子图，定义状态模式、输入模式、输出模式和配置模式。
子图与主图通过状态字段名称映射实现数据共享。
"""
builder = StateGraph(
    state_schema=SubTagState,      # 子图完整状态结构
    input_schema=SubTagInputState, # 输入数据结构
    output_schema=SubTagOutputState, # 输出数据结构
    config_schema=SagtConfig       # 配置结构（user_id, external_id）
)

"""注册子图节点

将各个节点函数注册到状态图中，每个节点对应一个业务操作。
"""
builder.add_node(NodeName.WELCOME_MESSAGE.value, welcome_message_node)  # 欢迎消息节点
builder.add_node(NodeName.GENERATE_TAG.value, generate_customer_tag)   # 生成标签建议节点
builder.add_node(NodeName.NOTIFY_FEEDBACK.value, notify_human_feedback) # 通知确认节点
builder.add_node(NodeName.HUMAN_FEEDBACK.value, human_feedback)        # 人工反馈节点（含路由逻辑）
builder.add_node(NodeName.UPDATE_TAG.value, update_customer_tag)       # 更新标签节点
builder.add_node(NodeName.NOTIFY_RESULT.value, notify_human_result)    # 通知结果节点

"""定义子图流程（边的连接）

定义节点之间的执行顺序和流转关系，形成完整的业务流程。
"""
# 开始 → 欢迎消息节点
builder.add_edge(START, NodeName.WELCOME_MESSAGE.value)
# 欢迎消息 → 生成客户标签建议节点
builder.add_edge(NodeName.WELCOME_MESSAGE.value, NodeName.GENERATE_TAG.value)
# 生成标签建议 → 发送人工确认通知节点
builder.add_edge(NodeName.GENERATE_TAG.value, NodeName.NOTIFY_FEEDBACK.value)
# 发送通知 → 人工反馈节点（等待用户确认）
builder.add_edge(NodeName.NOTIFY_FEEDBACK.value, NodeName.HUMAN_FEEDBACK.value)

# 人工反馈节点内部包含动态路由逻辑：
# - confirmed="ok" → 跳转到 UPDATE_TAG
# - confirmed="discard" → 跳转到 END
# - confirmed="recreate" → 跳转到 GENERATE_TAG

# 更新标签 → 发送任务结果通知节点
builder.add_edge(NodeName.UPDATE_TAG.value, NodeName.NOTIFY_RESULT.value)
# 发送结果通知 → 结束节点
builder.add_edge(NodeName.NOTIFY_RESULT.value, END)

"""编译子图

将状态图编译为可执行的图实例，供主图调用。
"""
sub_tag_graph = builder.compile()