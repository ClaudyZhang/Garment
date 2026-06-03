"""
极净奢护 CLARITY LUXURY GARMENT CARE
收交衣智能检测系统 - 配置文件
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "clarity-dev-key-2026")
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    REPORT_FOLDER = os.path.join(BASE_DIR, "reports")
    DATABASE = os.path.join(BASE_DIR, "data", "garments.db")
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "mp4"}

    # 通义千问 VL 视觉识别（阿里云百炼）
    # 获取 API Key: https://bailian.console.aliyun.com → 模型广场 → qwen-vl-max → API-KEY
    QWEN_API_KEY = os.environ.get("QWEN_API_KEY", "sk-cd4b27c0632f4c7dbcef21984a40d981")
    QWEN_MODEL = os.environ.get("QWEN_MODEL", "qwen-vl-max")

    # 阿里云短信（后续配置真实密钥）
    ALIYUN_SMS_ACCESS_KEY = os.environ.get("ALIYUN_SMS_ACCESS_KEY", "")
    ALIYUN_SMS_SECRET = os.environ.get("ALIYUN_SMS_SECRET", "")
    ALIYUN_SMS_SIGN = "极净奢护"
    ALIYUN_SMS_TEMPLATE = os.environ.get("ALIYUN_SMS_TEMPLATE", "")
    ALIYUN_SMS_VERIFY_TEMPLATE = os.environ.get("ALIYUN_SMS_VERIFY_TEMPLATE", "")

    # 品牌估价数据库
    BRAND_VALUE_MAP = {
        "Hermes": {"tier": "顶奢", "multiplier": 5.0},
        "Chanel": {"tier": "顶奢", "multiplier": 4.5},
        "Louis Vuitton": {"tier": "顶奢", "multiplier": 4.0},
        "Dior": {"tier": "顶奢", "multiplier": 4.0},
        "Gucci": {"tier": "奢侈", "multiplier": 3.5},
        "Prada": {"tier": "奢侈", "multiplier": 3.0},
        "Burberry": {"tier": "奢侈", "multiplier": 2.8},
        "Max Mara": {"tier": "轻奢", "multiplier": 2.5},
        "Armani": {"tier": "奢侈", "multiplier": 3.2},
        "Zegna": {"tier": "奢侈", "multiplier": 3.0},
        "Moncler": {"tier": "奢侈", "multiplier": 3.3},
        "Canada Goose": {"tier": "轻奢", "multiplier": 2.5},
        "Loro Piana": {"tier": "顶奢", "multiplier": 5.5},
        "Brunello Cucinelli": {"tier": "顶奢", "multiplier": 5.0},
        "Thom Browne": {"tier": "奢侈", "multiplier": 3.0},
        "Balenciaga": {"tier": "奢侈", "multiplier": 3.2},
        "Fendi": {"tier": "奢侈", "multiplier": 3.5},
        "Celine": {"tier": "奢侈", "multiplier": 3.3},
    }

    # 材质基础估价（元）
    MATERIAL_BASE_VALUE = {
        "羊绒": 3000,
        "真丝": 2500,
        "羊皮": 4000,
        "牛皮": 2500,
        "鳄鱼皮": 15000,
        "鸵鸟皮": 8000,
        "羊毛": 1800,
        "亚麻": 1200,
        "棉": 800,
        "化纤": 500,
        "混纺": 1200,
        "羽绒": 2000,
        "皮草": 6000,
        "马海毛": 2500,
        "羊驼毛": 2800,
    }

    # 店铺寄件信息（快递面单用）
    STORE_INFO = {
        "name": "极净奢护 CLARITY LUXURY GARMENT CARE",
        "short_name": "极净奢护",
        "address": "上海市徐汇区漕河泾开发区",
        "phone": "021-xxxxxxxx",
        "contact": "可云",
        "zip": "200233",
    }

    # 品类基础估价（元）
    CATEGORY_BASE_VALUE = {
        "大衣": 3000,
        "西装": 2500,
        "连衣裙": 2000,
        "皮衣": 5000,
        "羽绒服": 3000,
        "毛衣": 1500,
        "衬衫": 1200,
        "裤子": 1500,
        "半身裙": 1500,
        "风衣": 2500,
        "夹克": 2000,
        "旗袍": 3000,
        "礼服": 4000,
        "围巾": 800,
    }
