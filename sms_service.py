"""
极净奢护 - 短信服务模块
当前版本为模拟发送，后续接入阿里云短信API
"""

import json
import random
from datetime import datetime
from config import Config


class SMSService:
    """短信发送服务"""

    @classmethod
    def generate_verification_code(cls):
        """生成6位数字验证码"""
        return f"{random.randint(100000, 999999)}"

    @classmethod
    def send_verification_code(cls, phone, order_no, customer_name, verification_code):
        """
        发送收衣确认验证码短信
        模板: 【极净奢护】尊敬的{customer_name}，您有一笔收衣待确认（单号:{order_no}）。
              验证码:{code}，30分钟内有效。确认即视为同意收衣报告内容，具有法律效力。
        """
        if Config.ALIYUN_SMS_ACCESS_KEY and Config.ALIYUN_SMS_VERIFY_TEMPLATE:
            return cls._aliyun_send(phone, {
                "customer_name": customer_name,
                "order_no": order_no,
                "code": verification_code,
            })

        # 模拟发送
        log = {
            "service": "aliyun-sms",
            "mode": "mock",
            "type": "verification",
            "to": phone,
            "order_no": order_no,
            "customer": customer_name,
            "code": verification_code,
            "sent_at": datetime.now().isoformat(),
            "status": "success",
        }
        print(f"[SMS Mock] 验证码短信已模拟发送: {json.dumps(log, ensure_ascii=False)}")
        print(f"[SMS Mock] ===> 验证码: {verification_code} <===")
        return {"success": True, "mode": "mock", "code": verification_code, "log": log}

    @classmethod
    def send_intake_confirmation(cls, phone, order_no, customer_name, brand, estimated_value):
        """
        发送收衣确认短信（旧版通知，建议使用 send_verification_code）
        """
        if Config.ALIYUN_SMS_ACCESS_KEY and Config.ALIYUN_SMS_TEMPLATE:
            return cls._aliyun_send(phone, {
                "customer_name": customer_name,
                "order_no": order_no,
                "brand": brand,
                "value": f"{estimated_value:,.0f}",
            })

        log = {
            "service": "aliyun-sms",
            "mode": "mock",
            "to": phone,
            "order_no": order_no,
            "customer": customer_name,
            "brand": brand,
            "value": estimated_value,
            "sent_at": datetime.now().isoformat(),
            "status": "success",
        }
        print(f"[SMS Mock] 短信已模拟发送: {json.dumps(log, ensure_ascii=False)}")
        return {"success": True, "mode": "mock", "log": log}

    @classmethod
    def send_report_link(cls, phone, order_no, customer_name, report_url):
        """
        发送收衣报告链接短信
        模板: 【极净奢护】尊敬的{customer_name}，您的收衣报告（单号:{order_no}）已确认生效。
              查看报告: {report_url}
        """
        if Config.ALIYUN_SMS_ACCESS_KEY:
            return cls._aliyun_send(phone, {
                "customer_name": customer_name,
                "order_no": order_no,
                "report_url": report_url,
            })

        log = {
            "service": "aliyun-sms",
            "mode": "mock",
            "type": "report_link",
            "to": phone,
            "order_no": order_no,
            "customer": customer_name,
            "report_url": report_url,
            "sent_at": datetime.now().isoformat(),
            "status": "success",
        }
        print(f"[SMS Mock] 报告链接短信已模拟发送: {json.dumps(log, ensure_ascii=False)}")
        print(f"[SMS Mock] ===> 报告链接: {report_url} <===")
        return {"success": True, "mode": "mock", "report_url": report_url, "log": log}

    @classmethod
    def send_delivery_notification(cls, phone, order_no, customer_name):
        """
        发送交衣通知短信
        模板: 【极净奢护】尊敬的{customer_name}，您的衣物（单号:{order_no}）已护理完成，
              请到店领取或确认配送。
        """
        if Config.ALIYUN_SMS_ACCESS_KEY:
            return cls._aliyun_send(phone, {
                "customer_name": customer_name,
                "order_no": order_no,
            })

        log = {
            "service": "aliyun-sms",
            "mode": "mock",
            "to": phone,
            "order_no": order_no,
            "customer": customer_name,
            "sent_at": datetime.now().isoformat(),
            "status": "success",
        }
        print(f"[SMS Mock] 交衣通知已模拟发送: {json.dumps(log, ensure_ascii=False)}")
        return {"success": True, "mode": "mock", "log": log}

    @classmethod
    def _aliyun_send(cls, phone, params):
        """阿里云短信API调用（后续实现）"""
        # TODO: 使用 aliyun-python-sdk-dysmsapi
        # from aliyunsdkcore.client import AcsClient
        # from aliyunsdkdysmsapi.request.v20170525 import SendSmsRequest
        return {"success": True, "mode": "aliyun", "request_id": "mock-request-id"}
