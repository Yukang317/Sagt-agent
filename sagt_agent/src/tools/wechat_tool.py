"""企业微信API工具模块

本模块封装企业微信官方API，提供以下核心功能：
1. 创建日程安排
2. 发送自建应用消息通知
3. 更新客户标签
4. 获取员工信息

业务背景：智能体需要与企业微信进行交互，实现自动化的日程管理、
消息通知和客户标签维护功能。

技术实现：
- 采用单例模式确保全局唯一的API客户端实例
- 实现access_token自动刷新机制（提前5分钟刷新）
- 使用环境变量管理敏感配置信息（企业ID、应用ID、应用密钥）

错误处理：
- 所有API调用都包含完整的异常处理和日志记录
- 失败时抛出异常，由上层业务逻辑决定如何处理

依赖环境变量：
- WXWORK_CORP_ID: 企业微信企业ID
- WXWORK_APP_ID: 自建应用ID
- WXWORK_APP_SECRET: 自建应用密钥
"""

# 导入系统模块
import sys
import os

# 将当前模块所在目录的父目录加入Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入时间处理模块
import time
# 导入HTTP请求库
import requests
# 导入环境变量加载工具
from dotenv import load_dotenv
# 导入类型定义
from typing import List
# 导入日志工具
from utils.agent_logger import get_logger
# 导入日期时间转换工具
from utils.datetime_string import datetime2timestamp
# 导入调试装饰器
from utils.debug_aspect import debug
# 导入线程锁用于单例模式
import threading
from typing import Optional

# 加载环境变量（从.env文件读取配置）
load_dotenv()

# 初始化日志记录器
logger = get_logger("wechat_tool")


class WxWorkAPI:
    """
    企业微信API服务类
    
    提供企业微信API的封装接口，支持：
    - access_token自动管理（缓存、刷新）
    - 日程创建
    - 消息通知
    - 客户标签更新
    - 员工信息查询
    
    采用单例模式实现，确保全局共享一个API客户端实例。
    """
    
    # 类级别的单例实例
    _instance: Optional['WxWorkAPI'] = None
    # 线程锁，确保单例创建的线程安全
    _lock = threading.Lock()
    
    def __new__(cls):
        """
        单例模式实现（线程安全）
        
        使用双重检查锁定（Double-Checked Locking）确保高效且线程安全的单例创建。
        """
        # 第一次检查（不加锁）
        if cls._instance is None:
            # 获取锁
            with cls._lock:
                # 第二次检查（加锁后）
                if cls._instance is None:
                    # 创建实例
                    cls._instance = super().__new__(cls)
        return cls._instance


    def __init__(self):
        """
        初始化WxWorkAPI客户端
        
        注意：由于采用单例模式，__init__方法可能被多次调用，
        通过_initialized标志确保初始化逻辑只执行一次。
        """
        # 检查是否已初始化
        if hasattr(self, '_initialized'):
            return
        
        # 标记已初始化
        self._initialized = True
        
        # 从环境变量读取配置
        self.corp_id = os.getenv('WXWORK_CORP_ID')
        self.app_id = os.getenv('WXWORK_APP_ID')
        self.app_secret = os.getenv('WXWORK_APP_SECRET')
        
        # 初始化access_token相关变量
        self.access_token = None
        self.token_expires_time = 0
        
        # 校验必需的配置项
        if not self.corp_id or not self.app_id or not self.app_secret:
            raise ValueError("请在环境变量中设置WXWORK_CORP_ID、WXWORK_APP_ID和WXWORK_APP_SECRET")


    def get_access_token(self):
        """
        获取企业微信access_token
        
        access_token是调用企业微信API的凭证，有效期为7200秒（2小时）。
        本方法实现了自动缓存和刷新机制：
        1. 如果当前token有效（未过期），直接返回缓存的token
        2. 如果token即将过期（提前5分钟）或已过期，重新获取
        
        Returns:
            str: 有效的access_token
            
        Raises:
            Exception: 获取access_token失败时抛出异常
        """
        # 检查token是否有效（提前5分钟刷新，避免网络延迟导致过期）
        if self.access_token and time.time() < (self.token_expires_time - 300):
            return self.access_token
        
        # 企业微信access_token获取接口
        url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        params = {
            'corpid': self.corp_id,
            'corpsecret': self.app_secret
        }
        
        try:
            # 发送GET请求获取access_token
            response = requests.get(url, params=params, timeout=30)
            # 检查HTTP状态码
            response.raise_for_status()
            
            # 解析JSON响应
            data = response.json()
            
            # 检查API调用是否成功
            if data.get('errcode') == 0:
                # 更新access_token和过期时间
                self.access_token = data['access_token']
                self.token_expires_time = time.time() + data.get('expires_in', 7200)
                logger.info(f"获取access_token成功，有效期：{data.get('expires_in', 7200)}秒")
                return self.access_token
            else:
                # API返回错误
                errmsg = data.get('errmsg', '未知错误')
                errcode = data.get('errcode', 'unknown')
                error_msg = f"获取access_token失败: {errmsg} (错误码: {errcode})"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.RequestException as e:
            # 网络请求失败
            error_msg = f"请求access_token失败: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)


    @debug
    def create_schedule(self, user_id: str, title: str, start_time: str, duration_minutes: int = 30) -> bool: 
        """
        创建企业微信日程
        
        调用企业微信OA日程API，为指定员工创建日程安排。
        
        Args:
            user_id: 员工ID（企业微信用户ID）
            title: 日程标题
            start_time: 日程开始时间（格式：YYYY-MM-DD HH:MM:SS）
            duration_minutes: 日程持续时长（分钟），默认30分钟
            
        Returns:
            bool: 创建是否成功
            
        Raises:
            ValueError: 参数缺失时抛出
            Exception: API调用失败时抛出
            
        日程数据格式示例：
        {
            "schedule": {
                "admins": ["ChengJianZhang"],
                "summary": "告知客户白酒到货",
                "start_time": 1752836258,
                "end_time": 1752839258,
                "attendees": [{"userid": "ChengJianZhang"}]
            }
        }
        """
        # 参数校验
        if not user_id or not title or not start_time:
            raise ValueError("user_id, title, start_time不能为空")

        # 将开始时间转换为时间戳
        start_time_timestamp = datetime2timestamp(start_time)
        # 计算结束时间戳
        end_time_timestamp = start_time_timestamp + duration_minutes * 60

        # 获取access_token
        access_token = self.get_access_token()
        
        # 企业微信创建日程API地址
        url = f"https://qyapi.weixin.qq.com/cgi-bin/oa/schedule/add"
        params = {
            'access_token': access_token
        }

        # 构建请求数据
        data = {
            'schedule': {
                'admins': [user_id],           # 日程管理员
                'summary': title,              # 日程标题
                'start_time': start_time_timestamp,  # 开始时间戳
                'end_time': end_time_timestamp,      # 结束时间戳
                'attendees': [                  # 参会人员
                    {
                        'userid': user_id
                    }
                ]
            }
        }
        
        # 设置请求头
        headers = {
            'Content-Type': 'application/json'
        }
        
        try:
            # 发送POST请求创建日程
            response = requests.post(url, params=params, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            
            # 检查API调用是否成功
            if result.get('errcode') == 0:
                return True
            else:
                errmsg = result.get('errmsg', '未知错误')
                errcode = result.get('errcode', 'unknown')
                error_msg = f"创建日程失败: {errmsg} (错误码: {errcode})"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.RequestException as e:
            error_msg = f"请求创建日程失败: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)


    @debug
    def notify_user(self, user_id: str, content: str, title: str = 'Sagt 操作确认', msgtype: str = 'text') -> bool:
        """
        向指定员工发送企业微信消息通知
        
        支持两种消息类型：
        - text: 纯文本消息
        - textcard: 卡片消息（支持HTML格式）
        
        Args:
            user_id: 员工ID（企业微信用户ID）
            content: 通知内容
            title: 通知标题（仅textcard类型有效），默认"Sagt 操作确认"
            msgtype: 消息类型，可选值：'text' 或 'textcard'，默认'text'
            
        Returns:
            bool: 通知是否发送成功
            
        Raises:
            ValueError: 参数无效时抛出
            Exception: API调用失败时抛出
            
        消息体数据格式示例：
        
        文本类型：
        {
            "touser": "ChengJianZhang",
            "msgtype": "text",
            "agentid": 1000004,
            "text": {"content": "我为您创建的日程需您确认，您可以打开应用查看确认。"},
            "safe": 1,
            "enable_id_trans": 1,
            "enable_duplicate_check": 1,
            "duplicate_check_interval": 300
        }

        卡片类型：
        {
            "touser": "ChengJianZhang",
            "msgtype": "textcard",
            "agentid": 1000004,
            "textcard": {
                "title": "Sagt 操作确认",
                "description": "<div class=\"gray\">2025年08月26日</div> <div class=\"normal\">我为您创建的日程需您确认...</div><div class=\"highlight\">请及时确认</div>",
                "url": "URL",
                "btntxt": "详情"
            },
            "enable_id_trans": 1,
            "enable_duplicate_check": 1,
            "duplicate_check_interval": 300
        }
        """
        # 参数校验
        if not user_id or not content:
            raise ValueError("user_id, content不能为空")

        # 校验消息类型
        if msgtype not in ['text', 'textcard']:
            raise ValueError("msgtype必须为 'text' 或 'textcard'")

        # 获取access_token
        access_token = self.get_access_token()

        # 企业微信消息发送API地址
        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send"

        params = {
            'access_token': access_token,
            'debug': 1  # 调试模式
        }

        # 构建纯文本消息数据
        data_text = {
            'touser': user_id,
            'msgtype': 'text',
            'agentid': self.app_id,
            'text': {
                'content': content
            },
            'safe': 1,                           # 安全消息（仅企业内部可见）
            'enable_id_trans': 1,                 # 开启ID转译
            'enable_duplicate_check': 1,          # 开启重复消息检查
            'duplicate_check_interval': 300       # 重复检查间隔（秒）
        }

        # 构建卡片消息数据
        data_card = {
            'touser': user_id,
            'msgtype': 'textcard',
            'agentid': self.app_id,
            'textcard': {
                'title': title,
                'description': content,
                'url': 'URL'
            },
            'enable_id_trans': 1,
            'enable_duplicate_check': 1,
            'duplicate_check_interval': 300
        }

        # 根据消息类型选择对应的数据结构
        if msgtype == 'text':
            data = data_text
        elif msgtype == 'textcard':
            data = data_card
        else:
            logger.error(f"无效的消息类型: {msgtype}")
            raise ValueError("msgtype必须为 'text' 或 'textcard'")

        # 设置请求头
        headers = {
            'Content-Type': 'application/json'
        }

        try:
            # 发送POST请求
            response = requests.post(url, params=params, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            
            # 检查API调用是否成功
            if result.get('errcode') == 0:
                return True
            else:
                errcode = result.get('errcode', 'unknown')
                errmsg = result.get('errmsg', '未知错误')
                error_msg = f"发送通知失败: {errmsg} (错误码: {errcode})"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.RequestException as e:
            error_msg = f"请求发送通知失败: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)


    @debug
    def update_customer_tag(self, user_id: str, external_id: str, tag_ids_add: List[str] = [], tag_ids_remove: List[str] = []) -> bool:
        """
        更新客户标签（通过企业微信API）
        
        调用企业微信外部联系人标签管理API，为指定客户添加或移除标签。
        
        Args:
            user_id: 员工ID（操作人）
            external_id: 外部联系人ID（客户ID）
            tag_ids_add: 需要添加的标签ID列表，默认为空列表
            tag_ids_remove: 需要删除的标签ID列表，默认为空列表
            
        Returns:
            bool: 更新是否成功
            
        Raises:
            ValueError: 参数缺失或无效时抛出
            Exception: API调用失败时抛出
            
        注意：当tag_ids_add和tag_ids_remove都为空时，抛出异常（视为调用错误）
        
        请求数据结构示例：
        {
            "userid": "zhangsan",
            "external_userid": "woAJ2GCAAAd1NPGHKSD4wKmE8Aabj9AAA",
            "add_tag": ["TAGID1", "TAGID2"],
            "remove_tag": ["TAGID3", "TAGID4"]
        }
        """
        # 参数校验
        if not user_id or not external_id:
            logger.error("user_id, external_id不能为空")
            raise ValueError("user_id, external_id不能为空")

        # 校验至少有一个操作
        if not tag_ids_add and not tag_ids_remove:
            logger.error("tag_ids_add和tag_ids_remove不能同时为空")
            raise ValueError("tag_ids_add和tag_ids_remove不能同时为空")

        # 获取access_token
        access_token = self.get_access_token()
        
        # 企业微信外部联系人标签API地址
        url = f"https://qyapi.weixin.qq.com/cgi-bin/externalcontact/mark_tag"
        params = {
            'access_token': access_token
        }
        
        # 构建请求数据
        data = {
            'userid': user_id,              # 操作人ID
            'external_userid': external_id, # 外部联系人ID
            'add_tag': tag_ids_add,         # 要添加的标签ID列表
            'remove_tag': tag_ids_remove    # 要移除的标签ID列表
        }
        
        # 设置请求头
        headers = {
            'Content-Type': 'application/json'
        }
        
        try:
            # 发送POST请求
            response = requests.post(url, params=params, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            
            # 检查API调用是否成功
            if result.get('errcode') == 0:
                return True
            else:
                errmsg = result.get('errmsg', '未知错误')
                errcode = result.get('errcode', 'unknown')
                error_msg = f"更新客户标签失败: {errmsg} (错误码: {errcode})"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.RequestException as e:
            error_msg = f"请求更新客户标签失败: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)


    @debug
    def get_user_info(self, user_id: str) -> dict:
        """
        获取指定员工的信息（姓名）
        
        调用企业微信用户信息API，获取员工的基本信息。
        
        Args:
            user_id: 员工ID（企业微信用户ID）
            
        Returns:
            dict: 包含员工信息的字典，格式：{"user_id": "zhangsan", "name": "张三"}
            
        Raises:
            Exception: API调用失败时抛出
        """
        # 获取access_token
        access_token = self.get_access_token()
        
        # 企业微信用户信息API地址
        url = f"https://qyapi.weixin.qq.com/cgi-bin/user/get"
        params = {
            'access_token': access_token,
            'userid': user_id
        }
        
        try:
            # 发送GET请求
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            
            # 检查API调用是否成功
            if result.get('errcode') == 0:
                # 返回员工ID和姓名
                return {
                    "user_id": result.get('userid', ''),
                    "name": result.get('name', '')
                }
            else:
                errcode = result.get('errcode', 'unknown')
                errmsg = result.get('errmsg', '未知错误')
                error_msg = f"获取员工信息失败: {errmsg} (错误码: {errcode})"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.RequestException as e:
            error_msg = f"请求员工信息失败: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)


def main():
    """
    企业微信API测试函数
    
    用于测试WxWorkAPI类的各项功能，包括：
    1. 获取access_token
    2. 获取员工信息
    3. 创建日程
    4. 发送通知
    5. 更新客户标签（注释掉，需要实际客户ID）
    """
    try:
        # 初始化API客户端（单例模式）
        api = WxWorkAPI()
        
        print("企业微信API测试")
        print("请确保已在.env文件中设置正确的WXWORK_CORP_ID、WXWORK_APP_ID和WXWORK_APP_SECRET")
        print("=" * 50)
        
        # 测试获取access_token
        print("1. 测试获取access_token...")
        token = api.get_access_token()
        print(f"Access Token: {token[:20]}...")
        
        # 测试获取员工信息
        print("2. 测试获取员工信息...")
        user_info = api.get_user_info('ChengJianZhang')
        print(f"员工信息: {user_info}")
        
        # 测试创建日程
        print("3. 测试创建日程...")
        schedule_info = api.create_schedule('ChengJianZhang', '告知客户白酒到货', '2025-09-15 17:00:00', 30)
        print(f"日程信息: {schedule_info}")

        # 测试发送通知
        print("4. 测试发送通知...")
        notify_info = api.notify_user(
           user_id='ChengJianZhang', 
           msgtype='text',
           title='Sagt 操作确认', 
           content='$userName=ChengJianZhang$，您好，我为您的客户创建了新的企业标签，您可以打开应用查看确认。')
        print(f"通知信息: {notify_info}")
        
        # 测试更新客户标签（需要实际的外部联系人ID，默认注释掉）
        # print("5. 测试更新客户标签...")
        # update_info = api.update_customer_tag(
        #     user_id='ChengJianZhang', 
        #     external_id='wmE8gRKQAANU9ioysMc87Qd83d9bcO6g', 
        #     tag_ids_remove=['stE8gRKQAADGVLGdmyeAyART92z5BPdQ', 'stE8gRKQAAnI1bwMxf_tvALaL5tubl8A'], 
        #     tag_ids_add=['etE8gRKQAAs5EIsdA7PTiTsn8GoUSkqg', 'etE8gRKQAAFomsLb5ePOTLlSb_p-Y9mA'])
        # print(f"更新客户标签信息: {update_info}")

    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == "__main__":
    # 当脚本直接运行时执行测试函数
    main()