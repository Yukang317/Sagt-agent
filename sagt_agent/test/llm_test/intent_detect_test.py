"""
意图检测功能集成测试

测试 src/llm/llm_intent_detect.py 中的 intent_detection_prompt 函数与真实LLM的集成
"""

import sys
import os
from typing import List

# 添加项目路径
sys.path.append("/root/project/sagt_agent/src")

from models.sagt_models import Intent
from llm.llm_intent_detect import llm_intent_detect


def create_intent_list() -> List[Intent]:
    """创建意图列表"""
    return [
        Intent(intent_id="chat_suggestion", intent_description="生成聊天建议"),
        Intent(intent_id="kf_chat_suggestion", intent_description="生成客服回复建议"),
        Intent(intent_id="tag_suggestion", intent_description="生成客户标签"),
        Intent(intent_id="profile_suggestion", intent_description="生成客户画像"),
        Intent(intent_id="schedule_suggestion", intent_description="生成客户日程"),
        Intent(intent_id="no_clear_intention", intent_description="没有明确的意图")
    ]


def test_real_llm_intent_detection():
    """测试真实LLM的意图检测功能"""
    print("=" * 80)
    print("意图检测功能集成测试")
    print("=" * 80)
    print("测试目标: src/llm/llm_intent_detect.py 中的 intent_detection_prompt 函数")
    print("测试内容: 与真实LLM的集成调用")
    print("-" * 80)
    
    # 创建意图列表
    intents = create_intent_list()
    
    print("📋 可用意图列表:")
    for intent in intents:
        print(f"  - {intent.intent_id}: {intent.intent_description}")
    
    # 测试基础聊天建议意图
    task_input = "帮我生成一些和客户聊天的话题建议，让对话更自然"
    
    print(f"\n🎯 测试任务输入:")
    print(f"{task_input}")
    
    print("\n🤖 正在调用LLM进行意图检测...")
    print("请稍候，这可能需要几秒钟...")
    
    try:
        # 调用意图检测函数
        detected_intent = llm_intent_detect(task_input, intents)
        
        print("\n✅ 意图检测成功!")
        print(f"检测到的意图ID: {detected_intent.intent_id}")
        print(f"意图描述: {detected_intent.intent_description}")
        
        # 验证结果
        valid_intent_ids = [intent.intent_id for intent in intents]
        if detected_intent.intent_id in valid_intent_ids:
            print("✅ 检测结果有效: 意图ID在预定义列表中")
        else:
            print("❌ 检测结果无效: 意图ID不在预定义列表中")
        
        return detected_intent
        
    except Exception as e:
        print(f"❌ 意图检测失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        return None


def test_different_intent_scenarios():
    """测试不同意图场景下的检测"""
    print("\n" + "=" * 80)
    print("测试不同意图场景")
    print("=" * 80)
    
    intents = create_intent_list()
    
    # 场景1：客服回复建议
    print("\n💬 场景1: 客服回复建议")
    task_input1 = "客户问我们茅台酒的价格和库存情况，帮我生成一个专业的客服回复"
    
    try:
        result1 = llm_intent_detect(task_input1, intents)
        print(f"检测结果: {result1.intent_id} - {result1.intent_description}")
        expected = "kf_chat_suggestion"
        if result1.intent_id == expected:
            print("✅ 检测正确")
        else:
            print(f"⚠️ 检测结果与预期不符，预期: {expected}")
    except Exception as e:
        print(f"场景1测试失败: {e}")
    
    # 场景2：客户标签建议
    print("\n🏷️ 场景2: 客户标签建议")
    task_input2 = "根据这个客户的购买历史和聊天记录，帮我分析应该给他打什么标签"
    
    try:
        result2 = llm_intent_detect(task_input2, intents)
        print(f"检测结果: {result2.intent_id} - {result2.intent_description}")
        expected = "tag_suggestion"
        if result2.intent_id == expected:
            print("✅ 检测正确")
        else:
            print(f"⚠️ 检测结果与预期不符，预期: {expected}")
    except Exception as e:
        print(f"场景2测试失败: {e}")
    
    # 场景3：客户画像生成
    print("\n👤 场景3: 客户画像生成")
    task_input3 = "帮我分析这个客户的消费偏好、购买能力和兴趣爱好，生成详细的客户画像"
    
    try:
        result3 = llm_intent_detect(task_input3, intents)
        print(f"检测结果: {result3.intent_id} - {result3.intent_description}")
        expected = "profile_suggestion"
        if result3.intent_id == expected:
            print("✅ 检测正确")
        else:
            print(f"⚠️ 检测结果与预期不符，预期: {expected}")
    except Exception as e:
        print(f"场景3测试失败: {e}")
    
    # 场景4：客户日程建议
    print("\n📅 场景4: 客户日程建议")
    task_input4 = "根据客户的购买周期和重要节日，帮我制定一个营销日程安排"
    
    try:
        result4 = llm_intent_detect(task_input4, intents)
        print(f"检测结果: {result4.intent_id} - {result4.intent_description}")
        expected = "schedule_suggestion"
        if result4.intent_id == expected:
            print("✅ 检测正确")
        else:
            print(f"⚠️ 检测结果与预期不符，预期: {expected}")
    except Exception as e:
        print(f"场景4测试失败: {e}")
    
    # 场景5：聊天建议
    print("\n💭 场景5: 聊天建议")
    task_input5 = "我想和客户聊一些轻松的话题，帮我想几个聊天的切入点"
    
    try:
        result5 = llm_intent_detect(task_input5, intents)
        print(f"检测结果: {result5.intent_id} - {result5.intent_description}")
        expected = "chat_suggestion"
        if result5.intent_id == expected:
            print("✅ 检测正确")
        else:
            print(f"⚠️ 检测结果与预期不符，预期: {expected}")
    except Exception as e:
        print(f"场景5测试失败: {e}")


def test_edge_cases():
    """测试边界情况"""
    print("\n" + "=" * 80)
    print("测试边界情况")
    print("=" * 80)
    
    intents = create_intent_list()
    
    # 边界情况1：模糊不清的任务描述
    print("\n❓ 边界情况1: 模糊不清的任务描述")
    task_input1 = "帮我处理一下"
    
    try:
        result1 = llm_intent_detect(task_input1, intents)
        print(f"模糊任务检测结果: {result1.intent_id} - {result1.intent_description}")
        expected = "no_clear_intention"
        if result1.intent_id == expected:
            print("✅ 正确识别为无明确意图")
        else:
            print(f"⚠️ 检测结果: {result1.intent_id}，可能需要更明确的任务描述")
    except Exception as e:
        print(f"边界情况1测试失败: {e}")
    
    # 边界情况2：空任务输入
    print("\n📭 边界情况2: 空任务输入")
    task_input2 = ""
    
    try:
        result2 = llm_intent_detect(task_input2, intents)
        print(f"空任务检测结果: {result2.intent_id} - {result2.intent_description}")
        expected = "no_clear_intention"
        if result2.intent_id == expected:
            print("✅ 正确识别为无明确意图")
        else:
            print(f"⚠️ 检测结果: {result2.intent_id}")
    except Exception as e:
        print(f"边界情况2测试失败: {e}")
    
    # 边界情况3：包含多个意图的复合任务
    print("\n🔀 边界情况3: 包含多个意图的复合任务")
    task_input3 = "帮我生成客服回复，同时分析客户画像，还要制定营销日程"
    
    try:
        result3 = llm_intent_detect(task_input3, intents)
        print(f"复合任务检测结果: {result3.intent_id} - {result3.intent_description}")
        print("注意: 复合任务应该被识别为主要意图或无明确意图")
    except Exception as e:
        print(f"边界情况3测试失败: {e}")
    
    # 边界情况4：与业务无关的任务
    print("\n🚫 边界情况4: 与业务无关的任务")
    task_input4 = "帮我写一首诗"
    
    try:
        result4 = llm_intent_detect(task_input4, intents)
        print(f"无关任务检测结果: {result4.intent_id} - {result4.intent_description}")
        expected = "no_clear_intention"
        if result4.intent_id == expected:
            print("✅ 正确识别为无明确意图")
        else:
            print(f"⚠️ 检测结果: {result4.intent_id}，业务无关任务应识别为无明确意图")
    except Exception as e:
        print(f"边界情况4测试失败: {e}")
    
    # 边界情况5：很长的任务描述
    print("\n📚 边界情况5: 很长的任务描述")
    task_input5 = """我们公司是一家专业的酒类销售公司，主要经营茅台、五粮液等高端白酒产品。
    最近我们接到一个客户的咨询，他想了解我们的产品价格、库存情况、配送方式、售后服务等多个方面的信息。
    这个客户之前在我们这里购买过几次产品，是我们的老客户，消费能力比较强，通常购买的都是高端产品。
    现在他又来咨询新的产品，我需要给他一个专业、详细、有针对性的回复，
    既要体现我们的专业性，又要让客户感受到我们的服务态度，
    请帮我生成一个合适的客服回复内容。"""
    
    try:
        result5 = llm_intent_detect(task_input5, intents)
        print(f"长任务描述检测结果: {result5.intent_id} - {result5.intent_description}")
        expected = "kf_chat_suggestion"
        if result5.intent_id == expected:
            print("✅ 正确识别为客服回复建议")
        else:
            print(f"⚠️ 检测结果: {result5.intent_id}，预期: {expected}")
    except Exception as e:
        print(f"边界情况5测试失败: {e}")


def test_intent_consistency():
    """测试意图检测的一致性"""
    print("\n" + "=" * 80)
    print("测试意图检测一致性")
    print("=" * 80)
    
    intents = create_intent_list()
    
    # 相同任务多次检测，验证结果一致性
    task_input = "根据客户的购买记录和聊天历史，帮我生成合适的客户标签"
    results = []
    
    print(f"🔄 对同一任务进行3次意图检测:")
    print(f"任务: {task_input}")
    
    for i in range(3):
        try:
            result = llm_intent_detect(task_input, intents)
            results.append(result.intent_id)
            print(f"第{i+1}次检测: {result.intent_id}")
        except Exception as e:
            print(f"第{i+1}次检测失败: {e}")
            results.append(None)
    
    # 检查一致性
    unique_results = set(filter(None, results))
    if len(unique_results) == 1:
        print("✅ 检测结果完全一致")
    elif len(unique_results) <= 2:
        print("⚠️ 检测结果基本一致，存在少量差异")
    else:
        print("❌ 检测结果不一致，可能存在问题")
    
    print(f"结果统计: {dict(zip(['结果1', '结果2', '结果3'], results))}")


if __name__ == "__main__":
    # 运行基础功能测试
    result = test_real_llm_intent_detection()
    
    # 如果基础测试成功，运行其他测试
    if result is not None:
        test_different_intent_scenarios()
        test_edge_cases()
        test_intent_consistency()
    
    print("\n" + "=" * 80)
    print("意图检测功能测试完成")
    print("=" * 80)