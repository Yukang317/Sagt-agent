"""
调度建议功能集成测试

测试 src/llm/llm_suggest_schedule.py 中的 schedule_suggest 函数与真实LLM的集成
"""

import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.append("/root/project/sagt_agent/src")

from models.sagt_models import (
    ChatHistory, ChatMessage, CustomerInfo
)
from llm.llm_suggest_schedule import llm_schedule_suggest


def create_test_data():
    """创建测试数据"""
    # 构造客户信息 - 使用 CustomerInfo 模型
    customer_info = CustomerInfo(
        external_id="wmE8gRKQAArnVDJ84bNuOK3KVjy_7-Wg",
        union_id="union_123456",
        follow_user_id="ChengJianZhang",
        nick_name="程总"
    )
    
    # 构造包含日程信息的聊天记录
    chat_history = ChatHistory(
        chat_msgs=[
            ChatMessage(
                sender="销售人员",
                receiver="客户",
                content="程总您好！新到的五粮液1618已经到货了，您之前预定的那两瓶可以安排送货。",
                msg_time="2024-12-01 09:15:00"
            ),
            ChatMessage(
                sender="客户",
                receiver="销售人员",
                content="太好了！明天下午3点我在公司，你直接送到华润大厦A座28楼就行。",
                msg_time="2024-12-01 09:20:00"
            ),
            ChatMessage(
                sender="销售人员",
                receiver="客户",
                content="好的程总，明天下午3点准时送达。对了，您上次提到的年会用酒，12月15号那天需要吗？",
                msg_time="2024-12-01 09:25:00"
            ),
            ChatMessage(
                sender="客户",
                receiver="销售人员",
                content="对的，年会是12月15号晚上7点开始，大概需要10瓶茅台飞天。你12月13号下午来一趟，我们具体商量一下。",
                msg_time="2024-12-01 09:30:00"
            ),
            ChatMessage(
                sender="销售人员",
                receiver="客户",
                content="没问题！12月13号下午2点我过去找您，到时候详细沟通年会用酒的安排。",
                msg_time="2024-12-01 09:35:00"
            ),
            ChatMessage(
                sender="客户",
                receiver="销售人员",
                content="好的，那就这么定了。另外，下周三上午10点我有个重要客户要招待，你看能不能提前准备一瓶30年茅台？",
                msg_time="2024-12-01 14:20:00"
            ),
            ChatMessage(
                sender="销售人员",
                receiver="客户",
                content="30年茅台我需要调货，下周二晚上8点前能给您送到。",
                msg_time="2024-12-01 14:25:00"
            )
        ]
    )
    
    return customer_info, chat_history


def test_real_llm_schedule_suggest():
    """测试真实LLM的调度建议功能"""
    print("="*80)
    print("调度建议功能集成测试")
    print("="*80)
    
    # 创建测试数据
    customer_info, chat_history = create_test_data()
    
    print("📋 测试数据概览:")
    print(f"客户ID: {customer_info.external_id}")
    print(f"客户昵称: {customer_info.nick_name}")
    print(f"Union ID: {customer_info.union_id}")
    print(f"Follow User ID: {customer_info.follow_user_id}")
    print(f"聊天消息数量: {len(chat_history.chat_msgs)}")
    
    print("\n💬 关键聊天内容:")
    for msg in chat_history.chat_msgs[-4:]:  # 显示最后4条消息
        sender_name = "客户" if msg.sender == "wmE8gRKQAArnVDJ84bNuOK3KVjy_7-Wg" else "销售"
        print(f"  - {sender_name} ({msg.msg_time}): {msg.content}")
    
    print("\n🤖 调用LLM生成调度建议...")
    print("-" * 50)
    
    try:
        # 调用真实的LLM服务
        result = llm_schedule_suggest(
            customer_info=customer_info,
            chat_history=chat_history,
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        print("✅ LLM调用成功!")
        print("\n📅 调度建议结果:")
        
        if result.title:  # 检查是否有日程建议
            print("\n📋 具体日程安排:")
            print(f"  标题: {result.title}")
            print(f"  时间: {result.start_time}")
            print(f"  持续时间: {result.duration}分钟")
            print(f"  建议原因: {result.schedule_reason}")
            print()
        else:
            print("ℹ️ LLM认为当前对话中没有明确的日程安排信息")
        
        print("=" * 80)
        print("测试完成!")
        print("=" * 80)
        
        return result
        
    except Exception as e:
        print(f"❌ LLM调用失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        import traceback
        print(f"详细错误信息:\n{traceback.format_exc()}")
        return None


def test_different_scenarios():
    """测试不同场景下的调度建议"""
    print("\n" + "=" * 80)
    print("测试不同场景下的调度建议")
    print("=" * 80)
    
    # 场景1：明确时间的会议安排
    print("\n📅 场景1: 明确时间的会议安排")
    customer_info, _ = create_test_data()
    
    meeting_chat = ChatHistory(
        chat_msgs=[
            ChatMessage(
                sender="销售人员",
                receiver="客户",
                content="程总，关于新品推介会的事情，您看明天上午10点在您公司会议室怎么样？",
                msg_time="2024-12-05 16:30:00"
            ),
            ChatMessage(
                sender="客户",
                receiver="销售人员",
                content="可以，明天上午10点，会议室A，大概需要1个小时。我会安排采购部的同事一起参加。",
                msg_time="2024-12-05 16:35:00"
            )
        ]
    )
    
    try:
        result1 = llm_schedule_suggest(
            customer_info=customer_info,
            chat_history=meeting_chat,
            current_time="2024-12-05 17:00:00"
        )
        if result1.title:
            print(f"明确会议安排建议: {result1.title}")
            print(f"  - 时间: {result1.start_time} (持续{result1.duration}分钟)")
            print(f"  - 原因: {result1.schedule_reason}")
        else:
            print("明确会议安排场景未生成日程建议")
    except Exception as e:
        print(f"场景1测试失败: {e}")
    
    # 场景2：模糊时间的约定
    print("\n⏰ 场景2: 模糊时间的约定")
    vague_chat = ChatHistory(
        chat_msgs=[
            ChatMessage(
                sender="销售人员",
                receiver="客户",
                content="小张，下周找个时间我们聊聊春节备货的事情。",
                msg_time="2024-12-05 14:20:00"
            ),
            ChatMessage(
                sender="客户",
                receiver="销售人员",
                content="好的程总，我下周二下午有空，您看怎么样？",
                msg_time="2024-12-05 14:25:00"
            )
        ]
    )
    
    try:
        result2 = llm_schedule_suggest(
            customer_info=customer_info,
            chat_history=vague_chat,
            current_time="2024-12-05 15:00:00"
        )
        if result2.title:
            print(f"模糊约定建议: {result2.title}")
            print(f"  - 时间: {result2.start_time}")
            print(f"  - 原因: {result2.schedule_reason}")
        else:
            print("模糊约定场景未生成日程建议")
    except Exception as e:
        print(f"场景2测试失败: {e}")
    
    # 场景3：无日程信息的普通对话
    print("\n💬 场景3: 无日程信息的普通对话")
    normal_chat = ChatHistory(
        chat_msgs=[
            ChatMessage(
                sender="销售人员",
                receiver="客户",
                content="程总，今天天气不错啊！",
                msg_time="2024-12-05 09:00:00"
            ),
            ChatMessage(
                sender="客户",
                receiver="销售人员",
                content="是的，很适合户外活动。最近工作挺忙的。",
                msg_time="2024-12-05 09:05:00"
            )
        ]
    )
    
    try:
        result3 = llm_schedule_suggest(
            customer_info=customer_info,
            chat_history=normal_chat,
            current_time="2024-12-05 10:00:00"
        )
        if result3.title:
            print(f"普通对话意外生成建议: {result3.title}")
            print(f"  - 时间: {result3.start_time}")
        else:
            print("  - 正确识别：无日程安排信息")
    except Exception as e:
        print(f"场景3测试失败: {e}")


if __name__ == "__main__":
    # 运行真实LLM测试
    result = test_real_llm_schedule_suggest()
    
    # 如果基础测试成功，运行不同场景测试
    if result is not None:
        test_different_scenarios()
