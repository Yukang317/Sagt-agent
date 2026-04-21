# 为 SAGT 系统提供了存储 API 客户端
# 1. 初始化：通过 `/sagt/get_token` 端点获取认证 token，然后使用该 token 创建客户端连接
# 2. 数据管理：为不同类型的数据提供了插入/更新、删除、获取和列表查询等操作
# 3. 命名空间管理：使用不同的命名空间来组织不同类型的数据
# 4. 数据过滤：支持根据不同条件过滤数据

from typing import List, Dict, Any, Optional, Union
from langgraph_sdk import get_sync_client
from datetime import datetime
from pprint import pprint
import os
from dotenv import load_dotenv
import requests

load_dotenv()

class SagtStoreAPI:
    """
    LangGraph Agent Store 客户端API
    提供对员工信息、外部客户信息、全局标签定义、聊天消息、客户订单、客户标签等数据的操作接口
    """
    
    def __init__(self, server_url: str, user_id: str, password: str):
        """
        初始化客户端
        
        Args:
            server_url: langgraph server 地址
            user_id: 用户ID
            password: 用户密码
        """
        
        if not server_url or not user_id or not password:
            raise ValueError("server_url, user_id, password are required")

        # 获取token和其他登录信息
        response = requests.post(f"{server_url}/sagt/get_token", json={"user_id": user_id, "password": password})
        if response.status_code == 200:
            token = response.json().get("token")
        else:
            raise ValueError("获取token失败")
        
        # 创建客户端连接
        headers = {"Authorization": "Bearer " + token}
        client = get_sync_client(url = server_url, headers = headers)

        self.store = client.store
    
    # ==================== 员工信息 ====================
    
    def upsert_employee(self, user_id: str, name: str) -> None:
        """插入或更新员工信息"""
        namespace = ["employee"]
        key = user_id
        value = {
            "user_id": user_id,
            "name": name
        }
        self.store.put_item(namespace, key, value)
    
    def delete_employee(self, user_id: str) -> None:
        """删除员工信息"""
        namespace = ["employee"]
        key = user_id
        self.store.delete_item(namespace, key)
    
    def get_employee_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根据user_id获取员工信息"""
        namespace = ["employee"]
        key = user_id
        result = self.store.get_item(namespace, key)
        if result:
            return result.get("value", {})
        else:
            return {}
    
    def list_all_employee(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取所有员工信息"""
        namespace = ["employee"]
        response = self.store.search_items(namespace, limit=limit)
        return [item["value"] for item in response["items"]]
    
    # ==================== 外部客户信息 ====================
    
    def upsert_external_user(self, external_id: str, union_id: str, 
                           follow_user_id: str, name: str, remark_name: str = "", tags: List[str] = []) -> None:
        """插入或更新外部客户信息"""
        namespace = ["external_user", follow_user_id]
        key = external_id
        value = {
            "external_id": external_id,             ## external_contact_list.external_contatct.external_userid
            "union_id": union_id,                   ## external_contact_list.external_contatct.unionid
            "follow_user_id": follow_user_id,       ## external_contact_list.follow_info.userid 跟进员工 userid
            "name": name,                           ## external_contact_list.external_contatct.name
            "remark_name": remark_name,             ## external_contact_list.follow_info.remark 每个员工给客户的备注不同
            "tags": tags,                           ## external_contact_list.follow_info.tag_id
        }
        self.store.put_item(namespace, key, value)
    
    def delete_external_user(self, external_id: str, follow_user_id: str) -> None:
        """删除外部客户信息"""
        namespace = ["external_user", follow_user_id]
        key = external_id
        self.store.delete_item(namespace, key)
    
    def get_external_user_by_external_id(self, external_id: str, follow_user_id: str) -> Optional[Dict[str, Any]]:
        """根据external_id获取外部客户信息"""
        namespace = ["external_user", follow_user_id]
        key = external_id
        result = self.store.get_item(namespace, key)
        if result:
            return result.get("value", {})
        else:
            return {}
    
    def list_external_user_by_follow_user_id(self, follow_user_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取所有外部客户信息"""
        namespace = ["external_user", follow_user_id]
        response = self.store.search_items(namespace, limit=limit)
        return [item["value"] for item in response["items"]]
    
    def get_external_user_by_union_id(self, union_id: str, follow_user_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """根据union_id获取外部客户信息列表"""
        namespace = ["external_user", follow_user_id]
        filter = {"union_id": union_id}
        response = self.store.search_items(namespace, filter=filter, limit=limit)

        items = response["items"] # 单个元素示例，每个元素包含一个外部用户的完整信息
        # [
        #     {
        #         "key": "external_id",
        #         "value": {
        #             "external_id": "外部客户ID",
        #             "union_id": "微信union_id",
        #             "follow_user_id": "跟进员工ID",
        #             "name": "客户名称",
        #             "remark_name": "备注名称",
        #             "tags": ["标签ID1", "标签ID2"]
        #         }
        #     }
        # ]

        if not items:
            return None
        if len(items) == 0:
            return None
        return items[0]["value"] # 返回第一个匹配的用户信息
    
    def get_external_user_tag_by_external_id(self, external_id: str, follow_user_id: str) -> List[Dict[str, Any]]:
        """根据external_id获取客户标签"""
        namespace = ["external_user", follow_user_id]
        key = external_id
        result = self.store.get_item(namespace, key)

        if result:
            tag_ids = result.get("value", {}).get("tags", [])
        else:
            tag_ids = []

        tag_details = []
        for tag_id in tag_ids:
            tag = self.get_tags_setting_by_tag_id(tag_id)
            if tag and tag.get("deleted") == False:
                tag_details.append(tag)

        return tag_details

    # ==================== 客户profile ====================
    
    def get_profile_by_external_id(self, external_id: str, follow_user_id: str) -> Dict[str, Any]:
        """根据external_id获取客户profile"""
        namespace = ["external_user_profile", follow_user_id]
        key = external_id
        result = self.store.get_item(namespace, key)
        if result:
            return result.get("value", {})
        else:
            return {}
    
    # ==================== 全局标签定义信息 ====================
    
    def upsert_tags_setting(self, tag_id: str, strategy_id: int, group_id: str, group_name: str,
                          tag_name: str, deleted:bool) -> None:
        """插入或更新全局标签定义信息"""
        namespace = ["tags_setting"]
        key = tag_id
        value = {                                  ## 非微信接口返回的对象格式（做过转换）
            "strategy_id": strategy_id,            ## strategy_id, (默认 0，即：企业标签)
            "group_id": group_id,                  ## group_id
            "group_name": group_name,              ## group_name
            "tag_id": tag_id,                      ## tag_id
            "tag_name": tag_name,                  ## tag_name
            "deleted": deleted                     ## deleted (默认 False)
        }
        self.store.put_item(namespace, key, value)
    
    def delete_tags_setting(self, tag_id: str) -> None:
        """删除全局标签定义信息"""
        namespace = ["tags_setting"]
        key = tag_id
        self.store.delete_item(namespace, key)
    
    def get_tags_setting_by_tag_id(self, tag_id: str) -> Optional[Dict[str, Any]]:
        """根据tag_id获取全局标签定义信息"""
        namespace = ["tags_setting"]
        key = tag_id
        result = self.store.get_item(namespace, key)
        if result:
            return result.get("value", {})
        else:
            return {}
    
    def list_all_tags_setting(self, limit: Optional[int] = None, 
                            strategy_id: Optional[int] = None,
                            group_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取所有全局标签定义信息，支持过滤条件"""
        namespace = ["tags_setting"]
        response = self.store.search_items(namespace, limit=limit)
        results = [item["value"] for item in response["items"]]
        
        # 应用过滤条件
        if strategy_id: # 指定企业
            results = [item for item in results if item.get("strategy_id") == strategy_id]
        if group_id:    # 特定标签组
            results = [item for item in results if item.get("group_id") == group_id]
 
        results = [item for item in results if item.get("deleted") == False] # 只返回未删除的标签
        
        return results
    
    # ==================== 聊天消息内容信息 ====================
    
    def upsert_wxqy_msg(self, msg_id: str, from_id: str, to_id: str, msg_time: int, content: str, seq: int) -> None:
        """插入或更新聊天消息内容信息"""

        from_to_sorted_key = "".join(sorted([from_id, to_id]))

        YYYYMMDD = datetime.fromtimestamp(msg_time).strftime("%Y%m%d")

        namespace = ["wxqy_msg", from_to_sorted_key]
        key = msg_id
        value = {
            "msg_id": msg_id,                       ## msgid，消息ID 微信接口返回的 msgid
            "from_to_sorted_key": from_to_sorted_key,   ## 排序后的fromlist和tolist的拼接，排序后的收发方ID组合 由 from_id 和 to_id 排序后拼接
            "from_id": from_id,                     ## from，发送方ID 微信接口返回的 from
            "to_id": to_id,                         ## tolist中的Id，仅当 tolist长度=1。接收方ID 微信接口返回的 tolist 中的ID（仅当 tolist 长度=1）
            "YYYYMMDD": YYYYMMDD,                   ## msgtime 格式化YYYYMMDD格式
            "msg_time": msg_time,                   ## msgtime，消息时间戳 微信接口返回的 msg_time
            "content": content,                     ## content，消息内容 微信接口返回的 content
            "seq": seq                              ## seq，消息序号 微信接口返回的 seq
        }
        self.store.put_item(namespace, key, value)
    
    def delete_wxqy_msg(self, msg_id: str, external_id: str, user_id: str) -> None:
        """删除聊天消息内容信息"""

        from_to_sorted_key = "".join(sorted([external_id, user_id]))
        namespace = ["wxqy_msg", from_to_sorted_key]
        key = msg_id
        self.store.delete_item(namespace, key)
    
    def get_wxqy_msg_by_msg_id(self, msg_id: str, external_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """根据msg_id获取聊天消息内容信息"""
        from_to_sorted_key = "".join(sorted([external_id, user_id]))
        namespace = ["wxqy_msg", from_to_sorted_key]
        key = msg_id
        result = self.store.get_item(namespace, key)
        if result:
            return result.get("value", {})
        else:
            return {}
    
    def list_last_wxqy_msg(self, external_id: str, user_id: str, after_yyyy_mm_dd: str, limit: Optional[int] = 100) -> List[Dict[str, Any]]:
        """获取所有聊天消息内容信息，支持过滤条件"""

        from_to_sorted_key = "".join(sorted([external_id, user_id]))
        namespace = ["wxqy_msg", from_to_sorted_key]
        filter = {"YYYYMMDD": {"$gte": after_yyyy_mm_dd}}
        response = self.store.search_items(namespace, filter=filter, limit=limit)
        results = [item["value"] for item in response["items"]]
        return results
        
    # ==================== 微信客服信息 ====================

    def upsert_wxkf_msg(self, msg_id: str, external_id: str, open_kfid: str, servicer_userid: str, msg_time: int, origin: int, msgtype: str, content: str) -> None:
        """插入或更新微信客服信息"""

        YYYYMMDD = datetime.fromtimestamp(msg_time).strftime("%Y%m%d")
        namespace = ["wxkf_msg", external_id]
        key = msg_id
        value = {
            "msg_id": msg_id,                   ## msgid。消息ID 微信接口返回的 msgid
            "external_id": external_id,         ## external_userid。外部客户ID 微信接口返回的 external_userid
            "open_kfid": open_kfid,             ## open_kfid。客服ID 微信接口返回的 open_kfid
            "servicer_userid": servicer_userid, ## servicer_userid。客服ID 微信接口返回的 servicer_userid
            "YYYYMMDD": YYYYMMDD,               ## send_time 格式化YYYYMMDD格式
            "msg_time": msg_time,               ## send_time，消息时间戳 微信接口返回的 send_time
            "origin": origin,                   ## origin。消息来源 仅当 origin = 3（客户发送）或者5（客服发送） 时有效
            "msg_type": msgtype,                ## msgtype。消息类型 仅当 msgtype = "text" 时有效
            "content": content                  ## text.content。消息内容 微信接口返回的 text.content
        }
        self.store.put_item(namespace, key, value)

    def delete_wxkf_msg(self, msg_id: str, external_id: str) -> None:
        """删除微信客服信息"""
        namespace = ["wxkf_msg", external_id]
        key = msg_id
        self.store.delete_item(namespace, key)

    def get_wxkf_msg_by_msg_id(self, msg_id: str, external_id: str) -> Optional[Dict[str, Any]]:
        """根据msg_id获取微信客服信息"""
        namespace = ["wxkf_msg", external_id]
        key = msg_id
        result = self.store.get_item(namespace, key)
        if result:
            return result.get("value")
        else:
            return {}
    
    def list_last_wxkf_msg(self, external_id: str, after_yyyy_mm_dd: str, limit: Optional[int] = 100) -> List[Dict[str, Any]]:
        """获取所有微信客服信息，支持过滤条件"""

        namespace = ["wxkf_msg", external_id]
        filter = {"YYYYMMDD": {"$gte": after_yyyy_mm_dd}}
        response = self.store.search_items(namespace, filter=filter, limit=limit)
        results = [item["value"] for item in response["items"]]
        return results
    # ==================== 客户订单信息 ====================
    
    def upsert_wxxd_order(self, union_id: str, order_id: str, open_id: str, 
                         order_status: int, order_products: List[str], order_price: float,
                         order_create_time: int, order_raw_info: Dict[str, Any]) -> None:
        """插入或更新客户订单信息"""
        """
        order_status:
            10	待付款
            12	礼物待收下
            13	凑单中
            20	待发货
            21	部分发货
            30	待收货
            100	完成
            200	售后结束订单取消
            250	用户主动取消
        """

        YYYYMMDD = datetime.fromtimestamp(order_create_time).strftime("%Y%m%d")
        namespace = ["wxxd_order", union_id]
        key = order_id
        value = {
            "order_id": order_id,                   ## order.order_id。订单ID 微信接口返回的 order_id
            "open_id": open_id,                     ## order.openid。微信用户客户ID 微信接口返回的 openid
            "union_id": union_id,                   ## order.unionid。客户统一ID 微信接口返回的 unionid
            "order_status": order_status,           ## order.status。订单状态 微信接口返回的 order_status
            "order_products": order_products,       ## order.order_detail.product_info[title], 商品名称组装成列表
            "order_price": order_price,             ## order.order_detail.price_info.order_price。订单金额 微信接口返回的 order_price
            "order_create_time": order_create_time, ## order.create_time。订单创建时间戳 微信接口返回的 create_time
            "YYYYMMDD": YYYYMMDD,                   ## order.create_time 格式化YYYYMMDD格式。订单日期
            "order_raw_info": order_raw_info        ## order json对象 接口返回的原始值。原始订单信息
        }
        self.store.put_item(namespace, key, value)
    
    def delete_wxxd_order(self, union_id: str, order_id: str) -> None:
        """删除客户订单信息"""
        namespace = ["wxxd_order", union_id]
        key = order_id
        self.store.delete_item(namespace, key)
    
    def get_wxxd_order_by_order_id(self, union_id: str, order_id: str) -> Optional[Dict[str, Any]]:
        """根据order_id获取客户订单信息"""
        namespace = ["wxxd_order", union_id]
        key = order_id
        result = self.store.get_item(namespace, key)
        if result:
            return result.get("value", {})
        else:
            return {}
    
    def list_wxxd_order_by_union_id(self, union_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """根据union_id获取客户订单信息列表"""
        namespace = ["wxxd_order", union_id]
        response = self.store.search_items(namespace, limit=limit)
        results = [item["value"] for item in response["items"]]
        return results
    
    def list_all_wxxd_order(self, after_yyyy_mm_dd: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取所有客户订单信息（忽略namespace中的union_id）"""

        namespace = ["wxxd_order"]
        filter = {"YYYYMMDD": {"$gte": after_yyyy_mm_dd}}
        response = self.store.search_items(namespace, filter=filter, limit=limit)
        results = [item["value"] for item in response["items"]]
        return results
        
    

    # ==================== 全局状态 ====================
    # 业务逻辑 ：

    # - 全局状态用途 ：
    
    # 1. 系统配置 ：存储系统级别的配置信息，如 API 密钥、默认参数等
    # 2. 运行状态 ：存储系统的运行状态，如服务启动时间、处理计数等
    # 3. 临时数据 ：存储需要跨会话共享的临时数据
    # 4. 缓存 ：存储频繁访问但不常变化的数据，减少重复计算
    # 5. 任务状态 ：存储异步任务的执行状态和结果
    # - 使用场景 ：
    
    # - 存储系统初始化时间
    # - 存储API调用次数限制
    # - 存储临时的计算结果
    # - 存储系统维护状态

    def upsert_sagt_global_state(self, key: str, value: Any) -> None:
        """插入或更新全局状态"""
        namespace = ["sagt_global_state"]
        key = key
        value = value
        self.store.put_item(namespace, key, value)
    
    def get_sagt_global_state(self, key: str) -> Optional[Any]:
        """根据key获取全局状态"""
        namespace = ["sagt_global_state"]
        key = key
        result = self.store.get_item(namespace, key)
        if result:
            return result.get("value", {})
        else:
            return {}
    
    # ==================== 通用方法 ====================
    
    def search_items(self, namespace: List[str], filter: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """搜索items"""
        return self.store.search_items(namespace, filter=filter, limit=limit)

    def list_all_namespace(self, prefix: Optional[list[str]] = None, suffix: Optional[list[str]] = None):
        """获取所有namespace"""
        return self.store.list_namespaces(prefix=prefix, suffix=suffix)
    
    def delete_item(self, namespace: List[str], key: str):
        """删除item"""
        return self.store.delete_item(namespace, key)

# 工厂函数，方便创建客户端实例
def create_sagt_store_api(url: str, user_id: str, password: str) -> SagtStoreAPI:
    """创建SagtStoreAPI实例"""

    return SagtStoreAPI(url, user_id, password)

