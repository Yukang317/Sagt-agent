"""客服聊天建议子图定义文件

本文件定义了客服聊天建议子图的控制流程，使用LangGraph构建状态图。

业务流程：
1. 发送欢迎消息
2. 调用LLM生成客服回复建议
3. 直接返回结果（无需人工确认）

核心特点：
- 流程简单，无需人工确认环节
- 直接生成建议并返回给用户
- 适用于客服即时聊天场景，需要快速响应

业务背景：该子图为企业客服人员提供与客户聊天的智能回复建议，
帮助客服人员更高效地与客户沟通。

与普通聊天建议的区别：
- 普通聊天建议：面向销售人员，处理私域聊天场景，使用ChatHistory
- 客服聊天建议：面向客服人员，处理微信客服聊天场景，使用KFChatHistory
"""

# 导入LangGraph核心组件
from langgraph.graph import START, END, StateGraph
# 导入子图状态定义
from graphs.sagt_graph.sagt_sub_graph_kf_chat_suggestion.sub_kf_chat_suggestion_state import SubKFChatSuggestionState
from graphs.sagt_graph.sagt_sub_graph_kf_chat_suggestion.sub_kf_chat_suggestion_state import SubKFChatSuggestionInputState
from graphs.sagt_graph.sagt_sub_graph_kf_chat_suggestion.sub_kf_chat_suggestion_state import SubKFChatSuggestionOutputState
# 导入子图节点函数
from graphs.sagt_graph.sagt_sub_graph_kf_chat_suggestion.sub_kf_chat_suggestion_node import generate_kf_chat_suggestion_node
from graphs.sagt_graph.sagt_sub_graph_kf_chat_suggestion.sub_kf_chat_suggestion_node import welcome_message_node
# 导入节点名称枚举
from graphs.sagt_graph.sagt_sub_graph_kf_chat_suggestion.sub_kf_chat_suggestion_node import NodeName
# 导入配置定义
from graphs.sagt_graph.sagt_state import SagtConfig

"""构建客服聊天建议子图

使用StateGraph创建子图，定义状态模式、输入模式、输出模式和配置模式。
子图与主图通过状态字段名称映射实现数据共享。
"""
builder = StateGraph(
    state_schema=SubKFChatSuggestionState,      # 子图完整状态结构
    input_schema=SubKFChatSuggestionInputState, # 输入数据结构
    output_schema=SubKFChatSuggestionOutputState, # 输出数据结构
    config_schema=SagtConfig                   # 配置结构（user_id, external_id）
)

"""注册子图节点

将各个节点函数注册到状态图中，每个节点对应一个业务操作。
"""
builder.add_node(NodeName.WELCOME_MESSAGE.value, welcome_message_node)                    # 欢迎消息节点
builder.add_node(NodeName.GENERATE_KF_CHAT_SUGGESTION.value, generate_kf_chat_suggestion_node)  # 生成客服聊天建议节点

"""定义子图流程（边的连接）

定义节点之间的执行顺序和流转关系，形成完整的业务流程。
"""
# 开始 → 欢迎消息节点
builder.add_edge(START, NodeName.WELCOME_MESSAGE.value)
# 欢迎消息 → 生成客服聊天建议节点
builder.add_edge(NodeName.WELCOME_MESSAGE.value, NodeName.GENERATE_KF_CHAT_SUGGESTION.value)
# 生成客服聊天建议 → 结束节点（直接返回结果，无需人工确认）
builder.add_edge(NodeName.GENERATE_KF_CHAT_SUGGESTION.value, END)

"""编译子图

将状态图编译为可执行的图实例，供主图调用。
"""
sub_kf_chat_suggestion_graph = builder.compile()