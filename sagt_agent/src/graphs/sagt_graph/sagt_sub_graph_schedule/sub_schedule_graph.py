"""客户日程子图定义文件

本文件定义了客户日程子图的控制流程，使用LangGraph构建状态图。

业务流程：
1. 发送欢迎消息
2. 调用LLM生成日程建议（标题、时间、时长）
3. 调用企业微信API创建日程
4. 返回结果

核心特点：
- 与企业微信日历深度集成
- 生成建议后自动创建，无需人工确认
- 提高销售人员工作效率

业务背景：该子图为销售人员提供智能日程安排建议，
帮助销售人员更高效地管理客户跟进日程。
"""

# 导入LangGraph核心组件
from langgraph.graph import START, END, StateGraph
# 导入子图状态定义
from graphs.sagt_graph.sagt_sub_graph_schedule.sub_schedule_state import (
    SubScheduleState,       # 子图完整状态
    SubScheduleInputState,  # 子图输入状态
    SubScheduleOutputState  # 子图输出状态
)
# 导入子图节点函数
from graphs.sagt_graph.sagt_sub_graph_schedule.sub_schedule_node import (
    generate_schedule_node,  # 生成日程建议节点
    create_schedule_node,    # 创建日程节点
    welcome_message_node     # 欢迎消息节点
)
# 导入节点名称枚举
from graphs.sagt_graph.sagt_sub_graph_schedule.sub_schedule_node import NodeName
# 导入配置定义
from graphs.sagt_graph.sagt_state import SagtConfig

"""构建客户日程子图

使用StateGraph创建子图，定义状态模式、输入模式、输出模式和配置模式。
子图与主图通过状态字段名称映射实现数据共享。
"""
builder = StateGraph(
    state_schema=SubScheduleState,      # 子图完整状态结构
    input_schema=SubScheduleInputState, # 输入数据结构
    output_schema=SubScheduleOutputState, # 输出数据结构
    config_schema=SagtConfig           # 配置结构（user_id, external_id）
)

"""注册子图节点

将各个节点函数注册到状态图中，每个节点对应一个业务操作。
"""
builder.add_node(NodeName.WELCOME_MESSAGE.value, welcome_message_node)  # 欢迎消息节点
builder.add_node(NodeName.GENERATE_SCHEDULE.value, generate_schedule_node)  # 生成日程建议节点
builder.add_node(NodeName.CREATE_SCHEDULE.value, create_schedule_node)      # 创建日程节点

"""定义子图流程（边的连接）

定义节点之间的执行顺序和流转关系，形成完整的业务流程。
"""
# 开始 → 欢迎消息节点
builder.add_edge(START, NodeName.WELCOME_MESSAGE.value)
# 欢迎消息 → 生成日程建议节点
builder.add_edge(NodeName.WELCOME_MESSAGE.value, NodeName.GENERATE_SCHEDULE.value)
# 生成日程建议 → 创建日程节点（调用企业微信API）
builder.add_edge(NodeName.GENERATE_SCHEDULE.value, NodeName.CREATE_SCHEDULE.value)
# 创建日程 → 结束节点
builder.add_edge(NodeName.CREATE_SCHEDULE.value, END)

"""编译子图

将状态图编译为可执行的图实例，供主图调用。
"""
sub_schedule_graph = builder.compile()