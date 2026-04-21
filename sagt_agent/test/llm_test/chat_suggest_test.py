"""
聊天建议功能集成测试

测试 src/llm/llm_suggest_chat.py 中的 chat_suggest 函数与真实LLM的集成
"""

import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.append("/root/project/sagt_agent/src")

from models.sagt_models import (
    ReplySuggestion, ChatHistory, CustomerInfo, ChatMessage, EmployeeInfo
)
from llm.llm_suggest_chat import llm_chat_suggest


def create_test_data():
    """创建测试数据"""
    # 构造客户信息 - 使用 CustomerInfo 模型
    customer_info = CustomerInfo(
        external_id="wmE8gRKQAArnVDJ84bNuOK3KVjy_7-Wg",
        union_id="union_123456",
        follow_user_id="ChengJianZhang",
        nick_name="程总"
    )

    employee_info = EmployeeInfo(
        user_id="ChengJianZhang",
        name="小张",
    )
    
    # 构造聊天记录数据（客户刚发了消息，需要销售回复）
    chat_history = ChatHistory(
        chat_msgs=[
            ChatMessage(
                sender="销售人员",
                receiver="客户",
                content="大程哥，今天刚到两箱飞天茅台，给您留了一箱，需要的话随时联系！",
                msg_time="2024-09-22 09:15:00"
            ),
            ChatMessage(
                sender="客户",
                receiver="销售人员",
                content="太好了小张！正好中秋节要用，这箱给我留着，下午我来拿。",
                msg_time="2024-09-22 09:20:00"
            ),
            ChatMessage(
                sender="销售人员",
                receiver="客户",
                content="程哥，您上次说老爷子十月生日？需要寿宴用酒的话提前说，我调货。",
                msg_time="2024-10-08 11:05:00"
            ),
            ChatMessage(
                sender="客户",
                receiver="销售人员",
                content="对的，十月二十号老爷子八十大寿，到时候要办个寿宴，大概需要十几瓶好酒。",
                msg_time="2024-10-08 11:10:00"
            ),
            ChatMessage(
                sender="销售人员",
                receiver="客户",
                content="明白了，寿宴用酒我来安排，既要有面子又要寓意好。我推荐茅台加五粮液的组合怎么样？",
                msg_time="2024-10-08 11:15:00"
            ),
            ChatMessage(
                sender="客户",
                receiver="销售人员",
                content="小张你看着办吧，我信任你的专业眼光。价格方面不用太担心，老爷子生日就这一次。",
                msg_time="2024-10-08 11:20:00"
            ),
            # 最新的客户消息，需要销售回复
            ChatMessage(
                sender="销售人员",
                receiver="客户",
                content="小张，寿宴的酒单你准备得怎么样了？还有两周就要用了。",
                msg_time="2024-10-10 14:30:00"
            )
        ]
    )
    
    return customer_info, employee_info, chat_history


def test_real_llm_chat_suggest():
    """测试真实LLM的聊天建议功能"""
    print("=" * 80)
    print("聊天建议功能集成测试")
    print("=" * 80)
    print("测试目标: src/llm/llm_suggest_chat.py 中的 chat_suggest 函数")
    print("测试内容: 与真实LLM的集成调用")
    print("-" * 80)
    
    # 创建测试数据
    customer_info, employee_info, chat_history = create_test_data()
    
    print("📋 测试数据概览:")
    print(f"👤 客户: {customer_info.nick_name} ({customer_info.external_id})")
    
    print(f"\n💬 聊天记录: {len(chat_history.chat_msgs)} 条消息")
    print("最近3条对话:")
    for msg in chat_history.chat_msgs[-3:]:
        sender_name = msg.sender
        print(f"  - {sender_name}: {msg.content}")
    
    # 获取最后一条消息（客户发送的，需要回复）
    last_msg = chat_history.chat_msgs[-1]
    last_sender = last_msg.sender
    print(f"\n🎯 最新消息（需要回复）:")
    print(f"  {last_sender}: {last_msg.content}")
    
    print("\n🤖 调用LLM生成聊天建议...")
    print("-" * 50)
    
    try:
        # 调用真实的LLM服务
        result = llm_chat_suggest(
            customer_info=customer_info,
            employee_info=employee_info,
            chat_history=chat_history,
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        print("✅ LLM调用成功!")
        print("\n💬 聊天建议结果:")
        print(f"📝 建议回复内容:")
        print(f"   {result.reply_content}")
        print(f"\n💡 回复原因:")
        print(f"   {result.reply_reason}")
        
        # 分析回复质量
        print(f"\n📊 回复质量分析:")
        print(f"- 回复内容长度: {len(result.reply_content)} 字符")
        print(f"- 是否包含客户姓名: {'是' if '程' in result.reply_content else '否'}")
        print(f"- 是否涉及寿宴话题: {'是' if '寿' in result.reply_content or '生日' in result.reply_content else '否'}")
        print(f"- 是否提到酒类产品: {'是' if any(wine in result.reply_content for wine in ['茅台', '五粮液', '酒']) else '否'}")
        
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
    """测试不同场景下的聊天建议"""
    print("\n" + "=" * 80)
    print("测试不同场景下的聊天建议")
    print("=" * 80)
    
    # 场景1：客户询问价格
    print("\n💰 场景1: 客户询问价格")
    customer_info, employee_info, _ = create_test_data()
    price_inquiry_chat = ChatHistory(
        chat_msgs=[
            ChatMessage(
                sender="客户",
                receiver="销售人员",
                content="小张，现在飞天茅台什么价格？我想买几瓶收藏。",
                msg_time="2024-10-10 15:00:00"
            )
        ]
    )
    
    try:
        result1 = llm_chat_suggest(
            customer_info=customer_info,
            employee_info=employee_info,
            chat_history=price_inquiry_chat
        )
        print(f"价格询问场景回复: {result1.reply_content[:50]}...")
        print(f"回复原因: {result1.reply_reason[:50]}...")
    except Exception as e:
        print(f"场景1测试失败: {e}")
    
    # 场景2：客户表达不满
    print("\n😤 场景2: 客户表达不满")
    complaint_chat = ChatHistory(
        chat_msgs=[
            ChatMessage(
                sender="客户",
                receiver="销售人员",
                content="小张，上次买的那瓶酒有问题，开瓶后味道不对，这是怎么回事？",
                msg_time="2024-10-10 16:00:00"
            )
        ]
    )
    
    try:
        result2 = llm_chat_suggest(
            customer_info=customer_info,
            employee_info=employee_info,
            chat_history=complaint_chat
        )
        print(f"客户投诉场景回复: {result2.reply_content[:50]}...")
        print(f"回复原因: {result2.reply_reason[:50]}...")
    except Exception as e:
        print(f"场景2测试失败: {e}")
    
    # 场景3：节日祝福
    print("\n🎉 场景3: 节日祝福")
    festival_chat = ChatHistory(
        chat_msgs=[
            ChatMessage(
                sender="客户",
                receiver="销售人员",
                content="小张，中秋节快乐！感谢你一直以来的优质服务。",
                msg_time="2024-09-17 10:00:00"
            )
        ]
    )
    
    try:
        result3 = llm_chat_suggest(
            customer_info=customer_info,
            employee_info=employee_info,
            chat_history=festival_chat
        )
        print(f"节日祝福场景回复: {result3.reply_content[:50]}...")
        print(f"回复原因: {result3.reply_reason[:50]}...")
    except Exception as e:
        print(f"场景3测试失败: {e}")
    
    # 场景4：新产品推荐时机
    print("\n🆕 场景4: 新产品推荐时机")
    new_product_chat = ChatHistory(
        chat_msgs=[
            ChatMessage(
                sender="客户",
                receiver="销售人员",
                content="小张，最近有什么新品推荐吗？想尝试一些不同的。",
                msg_time="2024-10-10 17:00:00"
            )
        ]
    )
    
    try:
        result4 = llm_chat_suggest(
            customer_info=customer_info,
            employee_info=employee_info,
            chat_history=new_product_chat
        )
        print(f"新品推荐场景回复: {result4.reply_content[:50]}...")
        print(f"回复原因: {result4.reply_reason[:50]}...")
    except Exception as e:
        print(f"场景4测试失败: {e}")


def test_edge_cases():
    """测试边界情况"""
    print("\n" + "=" * 80)
    print("测试边界情况")
    print("=" * 80)
    
    customer_info, employee_info, _ = create_test_data()
    
    # 边界情况1：空聊天记录
    print("\n📭 边界情况1: 空聊天记录")
    empty_chat = ChatHistory(chat_msgs=[])
    
    try:
        result1 = llm_chat_suggest(
            customer_info=customer_info,
            employee_info=employee_info,
            chat_history=empty_chat
        )
        print(f"空聊天记录回复: {result1.reply_content[:50]}...")
    except Exception as e:
        print(f"边界情况1测试失败: {e}")
    
    # 边界情况2：只有一条消息
    print("\n1️⃣ 边界情况2: 只有一条消息")
    single_msg_chat = ChatHistory(
        chat_msgs=[
            ChatMessage(
                sender="客户",
                receiver="销售人员",
                content="你好",
                msg_time="2024-10-10 18:00:00"
            )
        ]
    )
    
    try:
        result2 = llm_chat_suggest(
            customer_info=customer_info,
            employee_info=employee_info,
            chat_history=single_msg_chat
        )
        print(f"单条消息回复: {result2.reply_content[:50]}...")
    except Exception as e:
        print(f"边界情况2测试失败: {e}")
    
    # 边界情况3：客户信息不完整
    print("\n❓ 边界情况3: 客户信息不完整")
    incomplete_customer = CustomerInfo(
        external_id="test_id",
        union_id="union_123456",
        follow_user_id="ChengJianZhang",
        nick_name=""
    )
    
    simple_chat = ChatHistory(
        chat_msgs=[
            ChatMessage(
                sender="客户",
                receiver="销售人员",
                content="有什么好酒推荐吗？",
                msg_time="2024-10-10 19:00:00"
            )
        ]
    )
    
    try:
        result3 = llm_chat_suggest(
            customer_info=incomplete_customer,
            employee_info=employee_info,
            chat_history=simple_chat
        )
        print(f"不完整客户信息回复: {result3.reply_content[:50]}...")
    except Exception as e:
        print(f"边界情况3测试失败: {e}")


if __name__ == "__main__":
    # 运行真实LLM测试
    result = test_real_llm_chat_suggest()
    
    # 如果基础测试成功，运行不同场景测试
    if result is not None:
        test_different_scenarios()
        test_edge_cases()