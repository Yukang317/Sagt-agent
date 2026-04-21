"""
SAGT 演示数据初始化脚本

用于初始化企业标签、员工客户信息、聊天记录和订单数据的演示脚本。
"""

import logging
from datetime import datetime
from sagt_store_api import create_sagt_store_api
import sys
import os
from dotenv import load_dotenv

load_dotenv()


from datetime_string import datetime2timestamp

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

## 测试用的客户ID和员工ID
DEMO_EXTERNAL_ID = os.getenv("DEMO_EXTERNAL_ID")
DEMO_USER_ID = os.getenv("DEMO_USER_ID")

## sagt账号信息
SAGT_USER_ID = os.getenv("SAGT_USER_ID")
SAGT_USER_PASSWORD = os.getenv("SAGT_USER_PASSWORD")
SAGT_SERVER_URL = os.getenv("SAGT_SERVER_URL")


class DemoDataInitializer:
    """演示数据初始化器"""
    
    store_client = None

    def __init__(self, server_url: str, user_id: str, password: str):
        self.store_client = create_sagt_store_api(server_url, user_id, password)
        
    def init_all_data(self):
        """初始化所有演示数据"""
        logger.info("开始初始化演示数据...")
        
        try:
            # 1. 初始化标签
            self.init_tags() # 注意标签ID和企业微信中的不一致。测试期间可以使用。
            
            # 2. 初始化用户信息
            self.init_user_and_customer()
            
            # 3. 初始化聊天记录
            self.init_wxqy_messages()

            # 4. 初始化聊天记录
            self.init_wxkf_messages()
            
            # 5. 初始化订单记录
            self.init_orders()
            
            logger.info("演示数据初始化完成！")
            
        except Exception as e:
            logger.error(f"数据初始化失败: {e}")
            raise
    
    def init_tags(self):
        """初始化企业标签"""
        logger.info("正在初始化企业标签...")
        

        # {"tag_id": "tag_004","tag_name": "商务合作","strategy_id": 2,"group_id": "service_type","group_name": "服务类型","deleted": False}

        # 基础属性标签
        basic_tags = [
            {"tag_id": "stE8gRKQAA-dAKMiJZw1MP4s_drOAh2Q", "tag_name": "高净值客户",   "group_id": "stE8gRKQAA4U6yUFhEhAXQ1BHZ5jt0_Q", "group_name": "基础属性", "strategy_id": 2, "deleted": False},
            {"tag_id": "stE8gRKQAAA7TJ7kvuKMeAA7FmcDY8Wg", "tag_name": "中年男性",     "group_id": "stE8gRKQAA4U6yUFhEhAXQ1BHZ5jt0_Q", "group_name": "基础属性", "strategy_id": 2, "deleted": False},
            {"tag_id": "stE8gRKQAAdN5SvmZoNc5n6Up12dPp-A", "tag_name": "已婚有子女",   "group_id": "stE8gRKQAA4U6yUFhEhAXQ1BHZ5jt0_Q", "group_name": "基础属性", "strategy_id": 2, "deleted": False},
            {"tag_id": "stE8gRKQAAJvszKCI8cCQJ0paQP2u9Wg", "tag_name": "家有老人",     "group_id": "stE8gRKQAA4U6yUFhEhAXQ1BHZ5jt0_Q", "group_name": "基础属性", "strategy_id": 2, "deleted": False},
        ]
        
        # 消费行为标签
        buy_tags = [
            {"tag_id": "stE8gRKQAA3EbL1cO0YS0cyupiATvFqA", "tag_name": "酱香白酒偏好", "group_id": "stE8gRKQAAdkLtKRp5u1HBHTYaGDbHhA", "group_name": "消费行为", "strategy_id": 2, "deleted": False},
            {"tag_id": "stE8gRKQAAhRYl-8b_Z2hzcimwynFIEA", "tag_name": "茅台收藏",     "group_id": "stE8gRKQAAdkLtKRp5u1HBHTYaGDbHhA", "group_name": "消费行为", "strategy_id": 2, "deleted": False},
            {"tag_id": "stE8gRKQAASj3DlY9G97EkhUBZmlwgrg", "tag_name": "高频团购",     "group_id": "stE8gRKQAAdkLtKRp5u1HBHTYaGDbHhA", "group_name": "消费行为", "strategy_id": 2, "deleted": False},
            {"tag_id": "stE8gRKQAAEJGWP7O1vHTDZn4ep0fWxQ", "tag_name": "节日礼品采购", "group_id": "stE8gRKQAAdkLtKRp5u1HBHTYaGDbHhA", "group_name": "消费行为", "strategy_id": 2, "deleted": False},
            {"tag_id": "stE8gRKQAAo-zv5-_oEWt__adANrQK1Q", "tag_name": "高端红酒需求", "group_id": "stE8gRKQAAdkLtKRp5u1HBHTYaGDbHhA", "group_name": "消费行为", "strategy_id": 2, "deleted": False},
        ]
        
        # 社交关系标签
        social_tags = [
            {"tag_id": "stE8gRKQAAkgEe-7wvit1OPLqaUV55Hg", "tag_name": "商务宴请多",   "group_id": "stE8gRKQAA3IKjjLIzWF7sZ1gy8UJzYQ", "group_name": "社交关系", "strategy_id": 2, "deleted": False},
            {"tag_id": "stE8gRKQAA4yE1-7IkO8SzvIOsCQej9A", "tag_name": "家庭聚会多",   "group_id": "stE8gRKQAA3IKjjLIzWF7sZ1gy8UJzYQ", "group_name": "社交关系", "strategy_id": 2, "deleted": False},
        ]
        
        # 服务敏感度标签
        service_tags = [
            {"tag_id": "stE8gRKQAAT4k2ZHMxooZjfORj-AdH4A", "tag_name": "需优先预留",      "group_id": "stE8gRKQAAYywcJoxIOzqvDLm5XSXi_g", "group_name": "服务敏感度", "strategy_id": 2, "deleted": False},
            {"tag_id": "stE8gRKQAAzZCHpp3W4sDwt1vO_EQyVQ", "tag_name": "依赖专业鉴酒服务", "group_id": "stE8gRKQAAYywcJoxIOzqvDLm5XSXi_g", "group_name": "服务敏感度", "strategy_id": 2, "deleted": False},
        ]
        
        
        # 合并所有标签
        all_tags = basic_tags + buy_tags + social_tags + service_tags
        
        # 批量创建标签
        for tag in all_tags:
            try:
                self.store_client.upsert_tags_setting(
                    tag_id=tag["tag_id"],
                    tag_name=tag["tag_name"],
                    group_id=tag["group_id"],
                    group_name=tag["group_name"],
                    strategy_id=tag["strategy_id"],
                    deleted=tag["deleted"]
                )
                logger.info(f"创建标签: {tag['tag_id']} - {tag['tag_name']}")
            except Exception as e:
                logger.warning(f"标签 {tag['tag_id']} 可能已存在: {e}")
        
        logger.info(f"标签初始化完成，共处理 {len(all_tags)} 个标签")
    
    def init_user_and_customer(self):
        """初始化员工和客户信息"""
        logger.info("正在初始化用户信息...")
        
        # 1. 创建员工信息
        employee_data = {
            "user_id": DEMO_USER_ID,
            "name": "小张",
        }
        
        try:
            self.store_client.upsert_employee(
                user_id=employee_data["user_id"],
                name=employee_data["name"]
            )
            logger.info(f"创建员工: {employee_data['user_id']} - {employee_data['name']}")
        except Exception as e:
            logger.warning(f"员工 {employee_data['user_id']} 可能已存在: {e}")
        
        # 2. 创建客户信息
        customer_data = {
            "external_id": DEMO_EXTERNAL_ID,
            "name": "dacheng",
            "remark_name": "程哥",
            "union_id": "union001",
            "follow_user_id": DEMO_USER_ID,
            "tags": ["etE8gRKQAANeNZh8ttsqCe-S-XIEsPdQ", "etE8gRKQAA6xbQIT5mE62_WSKeiWVbAg", "etE8gRKQAAdm3IQ7SVSEtb5BrRzQJHnQ"]
        }
        
        try:
            self.store_client.upsert_external_user(
                external_id=customer_data["external_id"],
                union_id=customer_data["union_id"],
                follow_user_id=customer_data["follow_user_id"],
                name = customer_data["name"],
                remark_name = customer_data["remark_name"],
                tags = customer_data["tags"],
            )
            logger.info(f"创建客户: {customer_data['external_id']} - {customer_data['name']}")
        except Exception as e:
            logger.warning(f"客户 {customer_data['external_id']} 可能已存在: {e}")
        
        logger.info("员工和客户信息初始化完成")
    
    def init_wxqy_messages(self):
        """初始化企业微信聊天记录"""
        logger.info("正在初始化企业微信聊天记录...")
        
        # {"msg_id": "wxqy_002", "from_id": "ext_001", "to_id": "emp_001", "content": "请问贵公司的技术方案有哪些优势？", "msg_time": 3000, "seq": 2}

        # 企业微信聊天记录
        wxqy_messages = [
            # 中秋茅台预订对话
            {"seq": 1, "msg_id": "wxqy_001", "from_id": DEMO_USER_ID, "to_id": DEMO_EXTERNAL_ID, "msg_time": datetime2timestamp("2024-09-22 09:15:00"), "content": "大程哥，今天刚到两箱飞天茅台，给您留了一箱，需要的话随时联系！"},
            {"seq": 2, "msg_id": "wxqy_002", "from_id": DEMO_EXTERNAL_ID, "to_id": DEMO_USER_ID, "msg_time": datetime2timestamp("2024-09-22 09:20:00"), "content": "太好了小张！正好中秋节要用，这箱给我留着，下午我来拿。"},
            {"seq": 3, "msg_id": "wxqy_003", "from_id": DEMO_USER_ID, "to_id": DEMO_EXTERNAL_ID, "msg_time": datetime2timestamp("2024-09-22 09:22:00"), "content": "没问题！我帮您开好发票，还是老规矩走会员价。"},
            
            # 老爷子生日寿宴对话
            {"seq": 4, "msg_id": "wxqy_004", "from_id": DEMO_USER_ID, "to_id": DEMO_EXTERNAL_ID, "msg_time": datetime2timestamp("2024-10-08 11:05:00"), "content": "程哥，您上次说老爷子十月生日？需要寿宴用酒的话提前说，我调货。"},
            {"seq": 5, "msg_id": "wxqy_005", "from_id": DEMO_EXTERNAL_ID, "to_id": DEMO_USER_ID, "msg_time": datetime2timestamp("2024-10-08 11:15:00"), "content": "正想找你！六十大寿要办五桌，推荐下？"},
            {"seq": 6, "msg_id": "wxqy_006", "from_id": DEMO_USER_ID, "to_id": DEMO_EXTERNAL_ID, "msg_time": datetime2timestamp("2024-10-08 11:20:00"), "content": "建议主桌用茅台，其他桌用红花郎15年，喜庆又实惠，我按团购价算。"},
            
            # 寿宴醒酒服务对话
            {"seq": 7, "msg_id": "wxqy_007", "from_id": DEMO_EXTERNAL_ID, "to_id": DEMO_USER_ID, "msg_time": datetime2timestamp("2024-10-09 10:20:00"), "content": "老弟，老爷子寿宴想加个醒酒区，你们能提供解酒饮料吗？"},
            {"seq": 8, "msg_id": "wxqy_008", "from_id": DEMO_USER_ID, "to_id": DEMO_EXTERNAL_ID, "msg_time": datetime2timestamp("2024-10-09 10:25:00"), "content": "配套送三箱解酒灵和定制矿泉水，都印寿字，放心！"},
            
            # 五粮液新包装咨询
            {"seq": 9, "msg_id": "wxqy_009", "from_id": DEMO_EXTERNAL_ID, "to_id": DEMO_USER_ID, "msg_time": datetime2timestamp("2024-11-03 14:05:00"), "content": "小张，听说五粮液出新包装了？口感有变化吗？"},
            {"seq": 10, "msg_id": "wxqy_010", "from_id": DEMO_USER_ID, "to_id": DEMO_EXTERNAL_ID, "msg_time": datetime2timestamp("2024-11-03 14:10:00"), "content": "是的哥！新版防伪升级了，酒体还是第八代经典，我尝过和原来一样醇香。要给您带两瓶试试吗？"},
            
            # 酱香酒储存方法讨论
            {"seq": 11, "msg_id": "wxqy_011", "from_id": DEMO_EXTERNAL_ID, "to_id": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-01-07 10:12:00"), "content": "[转发文章《酱香酒储存方法》] 小张你看这说法靠谱不？"},
            {"seq": 12, "msg_id": "wxqy_012", "from_id": DEMO_USER_ID, "to_id": DEMO_EXTERNAL_ID, "msg_time": datetime2timestamp("2025-01-07 10:20:00"), "content": "哥，这文章第三点不对，茅台存放要避光但不需要裹保鲜膜，我给您发个专业指南。"},
            
            # 茅台生肖酒预订
            {"seq": 13, "msg_id": "wxqy_013", "from_id": DEMO_USER_ID, "to_id": DEMO_EXTERNAL_ID, "msg_time": datetime2timestamp("2025-01-12 09:30:00"), "content": "哥，今天到货两瓶茅台生肖酒，知道您收藏，优先问您。"},
            {"seq": 14, "msg_id": "wxqy_014", "from_id": DEMO_EXTERNAL_ID, "to_id": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-01-12 09:33:00"), "content": "要了！明天转账，千万别给别人。"},
            
            # 澳洲奔富红酒咨询
            {"seq": 15, "msg_id": "wxqy_015", "from_id": DEMO_EXTERNAL_ID, "to_id": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-04-03 14:22:00"), "content": "小张，你们公司红酒有澳洲奔富吗？领导夫人爱喝。"},
            {"seq": 16, "msg_id": "wxqy_016", "from_id": DEMO_USER_ID, "to_id": DEMO_EXTERNAL_ID, "msg_time": datetime2timestamp("2025-04-03 14:25:00"), "content": "有！Bin389和407都有现货，建议配个礼盒，送领导体面。"},
            
            # 茅台跑酒检测
            {"seq": 17, "msg_id": "wxqy_017", "from_id": DEMO_EXTERNAL_ID, "to_id": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-05-10 16:45:00"), "content": "[图片：酒柜照片] 小张帮我看看这瓶15年茅台是不是有点跑酒？"},
            {"seq": 18, "msg_id": "wxqy_018", "from_id": DEMO_USER_ID, "to_id": DEMO_EXTERNAL_ID, "msg_time": datetime2timestamp("2025-05-10 16:50:00"), "content": "看着封膜完好，重量标一下？我拿专业秤给您复核。"},
            
            # 女士甜酒推荐
            {"seq": 19, "msg_id": "wxqy_019", "from_id": DEMO_EXTERNAL_ID, "to_id": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-19 15:10:00"), "content": "小张，有没有适合女士的甜酒？媳妇闺蜜聚会要用。"},
            {"seq": 20, "msg_id": "wxqy_020", "from_id": DEMO_USER_ID, "to_id": DEMO_EXTERNAL_ID, "msg_time": datetime2timestamp("2025-06-19 15:15:00"), "content": "推荐冰酒或莫斯卡托，包装精美，我这有加拿大进口的。"},
            
            # 德国啤酒烧烤配酒
            {"seq": 21, "msg_id": "wxqy_021", "from_id": DEMO_USER_ID, "to_id": DEMO_EXTERNAL_ID, "msg_time": datetime2timestamp("2025-06-26 17:30:00"), "content": "程哥，您上次说的德国啤酒到货了，周末烧烤可以备上了。"},
            {"seq": 22, "msg_id": "wxqy_022", "from_id": DEMO_EXTERNAL_ID, "to_id": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-26 17:35:00"), "content": "来得正好！再配点下酒小食，明天一起拿。"},
            
            # 升职祝贺与客户关系维护
            {"seq": 23, "msg_id": "wxqy_023", "from_id": DEMO_EXTERNAL_ID, "to_id": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-26 18:15:00"), "content": "小张，听说你要升销售经理了？到时候别忘老客户啊！"},
            {"seq": 24, "msg_id": "wxqy_024", "from_id": DEMO_USER_ID, "to_id": DEMO_EXTERNAL_ID, "msg_time": datetime2timestamp("2025-06-26 18:20:00"), "content": "全靠程哥你们支持！放心，您的茅台配额只会多不会少。"},
            
            # 子女教育关怀与庆祝
            {"seq": 25, "msg_id": "wxqy_025", "from_id": DEMO_USER_ID, "to_id": DEMO_EXTERNAL_ID, "msg_time": datetime2timestamp("2025-08-03 10:30:00"), "content": "程哥，您儿子中考成绩出来了吧？听说考上重点高中了？"},
            {"seq": 26, "msg_id": "wxqy_026", "from_id": DEMO_EXTERNAL_ID, "to_id": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-08-03 10:35:00"), "content": "哈哈对！实验中学重点班，这小子比他爹强！"}
        ]
        
        # 批量创建企业微信消息
        for msg in wxqy_messages:
            try:
                self.store_client.upsert_wxqy_msg(
                    msg_id=msg["msg_id"],
                    from_id=msg["from_id"],
                    to_id=msg["to_id"],
                    content=msg["content"],
                    msg_time=msg["msg_time"],
                    seq=msg["seq"]
                )
                logger.info(f"创建企业微信消息: {msg['msg_id']}")
            except Exception as e:
                logger.warning(f"企业微信消息 {msg['msg_id']} 可能已存在: {e}")
        
        logger.info(f"企业微信聊天记录初始化完成，共处理 {len(wxqy_messages)} 条消息")

    def init_wxkf_messages(self):
        """初始化微信客服聊天记录"""
        logger.info("正在初始化微信客服聊天记录...")
        
        # {"msg_id": "msg_kf_001", "external_id": "dacheng001", "open_kfid": "kf001", "servicer_userid": "xiaozhang", "msg_time": 600, "origin": 5, msgtype": "text", "content": "关于定制化方案的详细信息，我已经发送到您的邮箱"}
        # 微信客服聊天记录
        wxkf_messages = [
            # 茅台现货咨询和酒价评估
            {"msg_id": "msg_kf_001", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-01 09:05:00"), "origin": 3, "msgtype": "text", "content": "请问现在53度飞天茅台有现货吗？需要两箱送客户。"},
            {"msg_id": "msg_kf_002", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-01 09:10:00"), "origin": 5, "msgtype": "text", "content": "程先生您好！目前飞天茅台需预约申购，本月批次预计下周到货。您是我们的VIP客户，可以优先为您登记需求~"},
            {"msg_id": "msg_kf_003", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-01 14:20:00"), "origin": 3, "msgtype": "text", "content": "这瓶2019年的茅台酒线在这里，现在值多少钱？"},
            {"msg_id": "msg_kf_004", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-01 14:25:00"), "origin": 5, "msgtype": "text", "content": "根据当前行情，您这瓶酒体保存完好（酒线在肩部以上），回收价约3800元。需要帮您联系专业鉴定师上门评估吗？"},
            
            # 到货通知和产品咨询
            {"msg_id": "msg_kf_005", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-02 11:00:00"), "origin": 5, "msgtype": "text", "content": "程先生，您预约的茅台到货通知已开启，到货后将第一时间短信提醒。另提醒您账户积分可兑换两瓶红酒哦~"},
            {"msg_id": "msg_kf_006", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-02 15:15:00"), "origin": 3, "msgtype": "text", "content": "你们店里的五粮液第八代和第七代有什么区别？包装能发图看看吗？"},
            {"msg_id": "msg_kf_007", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-02 15:20:00"), "origin": 5, "msgtype": "text", "content": "主要区别：1. 第八代瓶盖增加扫码防伪 2. 瓶身“五粮液”logo立体感更强 3. 酒体勾调更醇柔。建议您优先选择新版~"},
            
            # 售后服务和养护提醒
            {"msg_id": "msg_kf_008", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-03 10:05:00"), "origin": 3, "msgtype": "text", "content": "上次买的剑南春礼盒里开瓶器断了，能补发吗？"},
            {"msg_id": "msg_kf_009", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-03 10:10:00"), "origin": 5, "msgtype": "text", "content": "非常抱歉！已登记补发高端开瓶器套装（含醒酒器），另赠送小瓶品鉴酒作为补偿，预计明天送达。"},
            {"msg_id": "msg_kf_010", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-03 16:30:00"), "origin": 5, "msgtype": "text", "content": "温馨提示：您收藏的2017年茅台建议本月做一次专业养护，我们可安排免费上门密封检测服务。"},
            
            # 生肖酒价格咨询
            {"msg_id": "msg_kf_011", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-04 13:40:00"), "origin": 3, "msgtype": "text", "content": "问下茅台生肖酒马年和羊年的现在什么价？有回收渠道吗？"},
            {"msg_id": "msg_kf_012", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-04 13:45:00"), "origin": 5, "msgtype": "text", "content": "当前市场参考价：马年约1.8万/瓶，羊年约3.2万/瓶。公司合作拍卖行正在征集优质藏品，需提供您酒的重量和品相照片~"},

            # 红酒咨询
            {"msg_id": "msg_kf_013", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-05 18:10:00"), "origin": 3, "msgtype": "text", "content": "朋友送了箱红酒全是外文看不懂，帮忙查下什么档次？"},
            {"msg_id": "msg_kf_014", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-05 18:15:00"), "origin": 5, "msgtype": "text", "content": "查询到是意大利安东尼世家2016年份DOCG级，市场价约680元/瓶，适合搭配红肉饮用。需要帮您预约专业醒酒服务吗？"},

            # 新品通知和养生酒咨询
            {"msg_id": "msg_kf_015", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-06 09:20:00"), "origin": 5, "msgtype": "text", "content": "程先生，您关注的酱香型酒新品——习酒窖藏1988已到店，欢迎随时来品鉴！"},
            {"msg_id": "msg_kf_016", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-06 14:50:00"), "origin": 3, "msgtype": "text", "content": "你们有没有适合老人的养生酒？老爷子想要药酒类。"},
            {"msg_id": "msg_kf_017", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-06 14:55:00"), "origin": 5, "msgtype": "text", "content": "推荐两款：1. 茅台不老酒（含黄精等药材）2. 同仁堂国公酒。都可提供药材检测报告，支持货到验货~"},

            # 发票咨询
            {"msg_id": "msg_kf_018", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-07 10:30:00"), "origin": 3, "msgtype": "text", "content": "买茅台开发票抬头能开会议费吗？"},
            {"msg_id": "msg_kf_019", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-07 10:35:00"), "origin": 5, "msgtype": "text", "content": "按规定酒类发票需如实开具品名，但可以备注会议用酒。建议分单开具便于报销，具体可咨询您公司财务要求~"},

            # 到货通知和延期提货
            {"msg_id": "msg_kf_020", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-08 08:00:00"), "origin": 5, "msgtype": "text", "content": "您预约的茅台已到货！请于48小时内凭预约码到店提货，需携带身份证原件哦~"},
            {"msg_id": "msg_kf_021", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-08 08:05:00"), "origin": 3, "msgtype": "text", "content": "提货能不能晚两天？我在外地出差。"},
            {"msg_id": "msg_kf_022", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-08 08:10:00"), "origin": 5, "msgtype": "text", "content": "已为您特殊延长保留~需要安排送货上门服务吗？（需另付200元运费）"},

            # 防伪咨询
            {"msg_id": "msg_kf_023", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-15 19:15:00"), "origin": 3, "msgtype": "text", "content": "这个茅台防伪标怎么扫码没反应？"},
            {"msg_id": "msg_kf_024", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-15 19:20:00"), "origin": 5, "msgtype": "text", "content": "经核查该批次需用专用检测笔照射，建议您暂停饮用！明天上午10点鉴定师将上门服务，已同步通知门店经理。"},

            # 活动提醒和渠道咨询
            {"msg_id": "msg_kf_025", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-16 11:30:00"), "origin": 5, "msgtype": "text", "content": "程先生，您参加的老酒换新活动还剩3天，用空瓶兑换可享新品8折优惠~"},
            {"msg_id": "msg_kf_026", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-16 15:25:00"), "origin": 3, "msgtype": "text", "content": "你们和京东自营的茅台有什么区别？"},
            {"msg_id": "msg_kf_027", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-16 15:30:00"), "origin": 5, "msgtype": "text", "content": "核心区别：1. 我们是一级经销商直供 2. 全程恒温物流 3. 提供专业存酒指导 4. 可验货后付款。附上我们的渠道授权书供查验~"},

            # 年会用酒咨询
            {"msg_id": "msg_kf_028", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-17 12:40:00"), "origin": 3, "msgtype": "text", "content": "有没有适合年会用的中档白酒？预算500左右/瓶。"},
            {"msg_id": "msg_kf_029", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-06-17 12:45:00"), "origin": 5, "msgtype": "text", "content": "推荐三款：1. 红花郎15年（酱香）2. 品味舍得（浓香）3. 水井坊臻酿八号。可提供免费定制瓶身祝福语服务！"},

            # 珍藏酒咨询
            {"msg_id": "msg_kf_030", "external_id": DEMO_EXTERNAL_ID, "open_kfid": "kf001", "servicer_userid": DEMO_USER_ID, "msg_time": datetime2timestamp("2025-08-03 11:00:00"), "origin": 3, "msgtype": "text", "content": "现在有什么珍藏酒推荐吗？"}
        ]
                
        # 批量创建微信客服消息
        for msg in wxkf_messages:
            try:
                self.store_client.upsert_wxkf_msg(
                    msg_id=msg["msg_id"],
                    external_id=msg.get("external_id"),
                    open_kfid=msg.get("open_kfid"),
                    servicer_userid=msg.get("servicer_userid"),
                    msg_time=msg.get("msg_time"),
                    origin=msg.get("origin"),
                    msgtype=msg.get("msgtype"),
                    content=msg.get("content")
                )
                logger.info(f"创建微信客服消息: {msg['msg_id']}")
            except Exception as e:
                logger.warning(f"微信客服消息 {msg['msg_id']} 可能已存在: {e}")
        
        logger.info(f"聊天记录初始化完成，共处理 {len(wxkf_messages)} 条消息")
    
    def init_orders(self):
        """初始化订单记录"""
        logger.info("正在初始化订单记录...")
        

        # {"union_id": "union_001","order_id": "order_001","open_id": "open_001","order_status": 100,"order_products": ["企业级解决方案"],"order_price": 2999.99,"order_create_time": base_create_time, "order_raw_info": {"memo": ""}}
        # 微信小店订单记录
        orders = [
            {"union_id": "union001", "order_id": "WX20240905", "open_id": "open001", "order_status": 100,"order_create_time": datetime2timestamp("2024-09-05 10:00:00"), "order_price": 14999.00, "order_products": ["53度飞天茅台（2023年产-500ml×6瓶/箱）"], "order_raw_info": {"memo": "中秋礼品，需开礼品发票"}},
            {"union_id": "union001", "order_id": "WX20240912", "open_id": "open001", "order_status": 100,"order_create_time": datetime2timestamp("2024-09-12 10:00:00"), "order_price": 2598.00,  "order_products": ["五粮液第八代普五（500ml×2瓶）"], "order_raw_info": {"memo": "家宴用，要求原箱未拆封"}},
            {"union_id": "union001", "order_id": "WX20240918", "open_id": "open001", "order_status": 100,"order_create_time": datetime2timestamp("2024-09-15 10:00:00"), "order_price": 18240.00, "order_products": ["红花郎15年（500ml×4箱）"], "order_raw_info": {"memo": "父亲寿宴主用酒"}},
            {"union_id": "union001", "order_id": "WX20240922", "open_id": "open001", "order_status": 100,"order_create_time": datetime2timestamp("2024-09-22 10:00:00"), "order_price": 3588.00, "order_products": ["茅台王子酒（酱香经典-500ml×12瓶）"], "order_raw_info": {"memo": "公司员工福利，需开发票"}},
            {"union_id": "union001", "order_id": "WX20250328", "open_id": "open001", "order_status": 100,"order_create_time": datetime2timestamp("2025-03-28 10:00:00"), "order_price": 288.00, "order_products": ["德国爱士堡小麦啤酒（500ml×24听）"], "order_raw_info": {"memo": "家庭烧烤聚会用"}},
            {"union_id": "union001", "order_id": "WX20250322", "open_id": "open001", "order_status": 100,"order_create_time": datetime2timestamp("2025-03-22 10:00:00"), "order_price": 3198.00, "order_products": ["茅台1935（新上市-500ml×2瓶）"], "order_raw_info": {"memo": "收藏用，要求序列号连号"}},
            {"union_id": "union001", "order_id": "WX20250411", "open_id": "open001", "order_status": 100,"order_create_time": datetime2timestamp("2025-04-11 10:00:00"), "order_price": 5340.00, "order_products": ["奔富Bin407红酒（750ml×6瓶）"], "order_raw_info": {"memo": "送客户，配高档礼盒"}},
            {"union_id": "union001", "order_id": "WX20250525", "open_id": "open001", "order_status": 100,"order_create_time": datetime2timestamp("2025-05-25 10:00:00"), "order_price": 896.00, "order_products": ["同仁堂国公酒（500ml×2瓶）"], "order_raw_info": {"memo": "送父亲养生酒"}},
        ]
        
        # 批量创建订单
        for order in orders:
            try:
                self.store_client.upsert_wxxd_order(
                    union_id=order["union_id"],
                    order_id=order["order_id"],
                    open_id=order["open_id"],
                    order_status=order["order_status"],
                    order_products=order["order_products"],
                    order_price=order["order_price"],
                    order_create_time=order["order_create_time"],
                    order_raw_info=order["order_raw_info"],
                )
                logger.info(f"创建订单: {order['order_id']} - {order['order_products']}")
            except Exception as e:
                logger.warning(f"订单 {order['order_id']} 可能已存在: {e}")
        
        logger.info(f"订单记录初始化完成，共处理 {len(orders)} 个订单")


# 主函数和命令行入口
def main():
    """主函数"""
    initializer = DemoDataInitializer(SAGT_SERVER_URL, SAGT_USER_ID, SAGT_USER_PASSWORD)
    #initializer.init_tags()
    #initializer.init_user_and_customer()
    #initializer.init_wxqy_messages()
    #initializer.init_wxkf_messages()
    #initializer.init_orders()
    initializer.init_all_data()
    

if __name__ == "__main__":
    # 运行初始化脚本
    main()