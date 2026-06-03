"""
极净奢护 - AI智能检测模块
当前版本使用模拟数据，后续可接入腾讯云图像识别API
"""

import random
import json
import base64
import os
from datetime import datetime
from config import Config
from openai import OpenAI


class AIDetector:
    """服装智能检测引擎"""

    MOCK_BRANDS = [
        {"name": "Max Mara", "confidence": 0.92},
        {"name": "Burberry", "confidence": 0.88},
        {"name": "Loro Piana", "confidence": 0.85},
        {"name": "Hermes", "confidence": 0.91},
        {"name": "Chanel", "confidence": 0.90},
        {"name": "Gucci", "confidence": 0.87},
        {"name": "Prada", "confidence": 0.86},
        {"name": "Armani", "confidence": 0.84},
        {"name": "Zegna", "confidence": 0.85},
        {"name": "Dior", "confidence": 0.89},
        {"name": "Louis Vuitton", "confidence": 0.88},
        {"name": "Moncler", "confidence": 0.86},
        {"name": "Brunello Cucinelli", "confidence": 0.87},
        {"name": "Celine", "confidence": 0.85},
        {"name": "Thom Browne", "confidence": 0.83},
    ]

    MOCK_MATERIALS = [
        {"name": "羊绒", "confidence": 0.90},
        {"name": "真丝", "confidence": 0.85},
        {"name": "羊毛", "confidence": 0.88},
        {"name": "羊皮", "confidence": 0.82},
        {"name": "牛皮", "confidence": 0.80},
        {"name": "亚麻", "confidence": 0.78},
        {"name": "混纺", "confidence": 0.75},
        {"name": "马海毛", "confidence": 0.83},
        {"name": "羽绒", "confidence": 0.85},
        {"name": "羊驼毛", "confidence": 0.84},
        {"name": "皮草", "confidence": 0.80},
        {"name": "棉", "confidence": 0.90},
    ]

    MOCK_CATEGORIES = [
        {"name": "大衣", "confidence": 0.92},
        {"name": "西装", "confidence": 0.88},
        {"name": "连衣裙", "confidence": 0.90},
        {"name": "皮衣", "confidence": 0.85},
        {"name": "羽绒服", "confidence": 0.93},
        {"name": "毛衣", "confidence": 0.91},
        {"name": "风衣", "confidence": 0.87},
        {"name": "夹克", "confidence": 0.84},
        {"name": "礼服", "confidence": 0.86},
        {"name": "衬衫", "confidence": 0.89},
        {"name": "裤子", "confidence": 0.90},
        {"name": "旗袍", "confidence": 0.85},
    ]

    MOCK_COLORS = [
        "黑色", "白色", "米色", "灰色", "藏青", "驼色",
        "酒红", "深蓝", "墨绿", "卡其", "烟灰", "象牙白",
        "炭灰", "海军蓝", "巧克力棕"
    ]

    # 衣物类型 → 合理品类映射（约束品类不会离谱，如西装识别成羽绒服）
    GARMENT_TYPE_TO_CATEGORY = {
        "上衣": ["衬衫", "毛衣"],
        "裤子": ["裤子"],
        "裙子": ["连衣裙"],
        "外套": ["大衣", "风衣", "夹克", "羽绒服", "皮衣"],
        "连衣裙": ["连衣裙", "礼服"],
        "西装": ["西装"],
    }

    # 衣物类型 → 合理材质映射（西装不可能是羽绒/亚麻）
    GARMENT_TYPE_TO_MATERIALS = {
        "上衣": ["羊绒", "羊毛", "真丝", "棉", "混纺", "马海毛", "羊驼毛"],
        "裤子": ["羊毛", "混纺", "棉", "真丝", "亚麻"],
        "裙子": ["真丝", "羊毛", "混纺", "棉", "羊绒"],
        "外套": ["羊绒", "羊毛", "羊皮", "牛皮", "羽绒", "混纺", "马海毛", "羊驼毛", "皮草"],
        "连衣裙": ["真丝", "羊绒", "羊毛", "混纺", "棉"],
        "西装": ["羊毛", "羊绒", "混纺", "马海毛", "真丝"],
    }

    # 衣物类型 → 合理颜色映射（西装以深色正装色为主）
    GARMENT_TYPE_TO_COLORS = {
        "上衣": ["黑色", "白色", "米色", "灰色", "藏青", "酒红", "深蓝", "墨绿", "烟灰", "象牙白", "炭灰", "海军蓝"],
        "裤子": ["黑色", "灰色", "藏青", "深蓝", "卡其", "炭灰", "海军蓝", "巧克力棕"],
        "裙子": ["黑色", "白色", "米色", "灰色", "藏青", "酒红", "深蓝", "墨绿", "烟灰", "象牙白", "海军蓝"],
        "外套": ["黑色", "米色", "灰色", "藏青", "驼色", "酒红", "深蓝", "墨绿", "卡其", "炭灰", "海军蓝", "巧克力棕"],
        "连衣裙": ["黑色", "白色", "米色", "灰色", "藏青", "酒红", "深蓝", "墨绿", "烟灰", "象牙白", "海军蓝"],
        "西装": ["黑色", "藏青", "灰色", "深蓝", "炭灰", "海军蓝"],
    }

    MOCK_CONDITIONS = [
        {"level": "excellent", "label": "全新/近乎全新", "desc": "无明显穿着痕迹，面料光泽度好", "deduction": 0},
        {"level": "good", "label": "良好", "desc": "轻微使用痕迹，局部细微磨损", "deduction": 0.1},
        {"level": "fair", "label": "一般", "desc": "明显使用痕迹，局部污渍或起球", "deduction": 0.25},
        {"level": "poor", "label": "需特别护理", "desc": "有明显污渍/破损/褪色，需谨慎处理", "deduction": 0.4},
    ]

    # 瑕疵类型库
    MOCK_DEFECT_TYPES = [
        {
            "type": "stain_oil", "name": "油渍",
            "icon": "🫗", "severity": "medium",
            "desc_templates": [
                "{position}处有{size}油渍，呈{color_desc}",
                "{position}可见{size}油性污渍，边界清晰",
                "{position}分布{size}油渍斑块，触感略黏",
            ],
            "risk": "需预处理去油，深色面料需警惕褪色风险",
        },
        {
            "type": "stain_drink", "name": "饮料渍",
            "icon": "☕", "severity": "medium",
            "desc_templates": [
                "{position}有{size}饮料泼溅痕迹，呈{color_desc}",
                "{position}可见{size}液体渍渍扩散痕迹",
                "{position}分布{size}饮料色素沉淀",
            ],
            "risk": "含糖/色素类需尽快处理，防止色素固着",
        },
        {
            "type": "stain_ink", "name": "墨渍/笔渍",
            "icon": "🖊", "severity": "high",
            "desc_templates": [
                "{position}有{size}墨水/笔迹污染",
                "{position}可见{size}墨渍渗透",
            ],
            "risk": "墨水类污渍需溶剂处理，可能留下轻微痕迹",
        },
        {
            "type": "stain_blood", "name": "血渍/蛋白渍",
            "icon": "🩸", "severity": "high",
            "desc_templates": [
                "{position}有{size}疑似蛋白类污渍",
                "{position}可见{size}陈旧性蛋白沉淀",
            ],
            "risk": "需低温酶处理，热水会导致蛋白凝固",
        },
        {
            "type": "stain_mud", "name": "泥渍/灰尘",
            "icon": "🧹", "severity": "low",
            "desc_templates": [
                "{position}有{size}泥污/灰尘附着",
                "{position}可见{size}干涸泥渍",
            ],
            "risk": "干刷预处理后正常清洗即可",
        },
        {
            "type": "stain_cosmetic", "name": "化妆品渍",
            "icon": "💄", "severity": "medium",
            "desc_templates": [
                "{position}有{size}粉底/口红等化妆品残留",
                "{position}可见{size}化妆品蹭痕",
            ],
            "risk": "含油脂/色素成分，需针对性溶剂处理",
        },
        {
            "type": "tear_hole", "name": "破洞/撕裂",
            "icon": "🕳", "severity": "high",
            "desc_templates": [
                "{position}存在{size}破洞，边缘{edge_desc}",
                "{position}有{size}撕裂伤，{edge_desc}",
                "{position}可见{size}穿透性破损",
            ],
            "risk": "洗护过程可能扩大破损，需提前告知客户并注明免责",
        },
        {
            "type": "tear_seam", "name": "开线/脱缝",
            "icon": "🧵", "severity": "medium",
            "desc_templates": [
                "{position}缝线开裂，长约{size}",
                "{position}接缝处脱线，可见{size}裂口",
            ],
            "risk": "清洗前需先缝合加固，防止进一步扩大",
        },
        {
            "type": "wear_fabric", "name": "面料磨损",
            "icon": "🪥", "severity": "medium",
            "desc_templates": [
                "{position}面料{size}区域有明显磨损，{edge_desc}",
                "{position}织物表面{size}范围内出现磨毛/变薄",
            ],
            "risk": "磨损区域洗后可能更明显，需轻柔处理",
        },
        {
            "type": "wear_pilling", "name": "起球",
            "icon": "⚪", "severity": "low",
            "desc_templates": [
                "{position}有{size}范围起球现象",
                "{position}可见{size}毛球聚集",
            ],
            "risk": "洗后可进行去球处理，但可能无法完全恢复",
        },
        {
            "type": "fade_color", "name": "褪色/色差",
            "icon": "🎨", "severity": "medium",
            "desc_templates": [
                "{position}存在{size}区域褪色，与周围形成色差",
                "{position}可见{size}日晒/洗涤导致的颜色减淡",
            ],
            "risk": "干洗过程存在持续褪色风险，需做色牢度测试",
        },
        {
            "type": "fade_uneven", "name": "不均匀褪色",
            "icon": "🌈", "severity": "medium",
            "desc_templates": [
                "{position}出现{size}不均匀褪色斑块",
                "{position}颜色分布不均匀，有{size}斑驳痕迹",
            ],
            "risk": "原有色差无法通过洗护逆转，需告知客户",
        },
        {
            "type": "missing_button", "name": "缺扣/松扣",
            "icon": "🔘", "severity": "low",
            "desc_templates": [
                "{position}纽扣{status}",
                "{position}{size}范围内纽扣{status}",
            ],
            "risk": "清洗前需取下松脱纽扣单独保管",
        },
        {
            "type": "missing_accessory", "name": "配件缺失",
            "icon": "📎", "severity": "medium",
            "desc_templates": [
                "{position}{accessory}缺失/脱落",
                "{position}原有{accessory}已不在位",
            ],
            "risk": "需与客户确认配件去向，收衣时已缺失",
        },
        {
            "type": "deformation", "name": "变形/缩水",
            "icon": "↔", "severity": "high",
            "desc_templates": [
                "{position}存在{size}变形/缩水痕迹",
                "{position}版型异常，{size}区域已产生不可逆形变",
            ],
            "risk": "洗护无法修复已发生的不可逆形变，仅能防止恶化",
        },
        {
            "type": "odor", "name": "异味",
            "icon": "👃", "severity": "low",
            "desc_templates": [
                "检测到{size}霉味/烟味/汗味等异味",
                "面料吸附有{size}异味分子",
            ],
            "risk": "需深度除味处理，部分顽固异味可能残留",
        },
    ]

    # 位置描述（按衣物类型分组，避免跨类别错误）
    GARMENT_TYPE_POSITIONS = {
        "上衣": [
            "左前襟", "右前襟", "左袖口", "右袖口", "左肩部", "右肩部",
            "领口", "前胸", "后背", "左腋下", "右腋下", "左肘部", "右肘部",
            "下摆", "左口袋", "右口袋", "内衬", "后领窝", "前襟下摆",
        ],
        "裤子": [
            "左裤腿", "右裤腿", "臀部", "膝部", "腰带部位", "左口袋", "右口袋",
            "裤脚", "腰部", "裆部",
        ],
        "裙子": [
            "腰部", "臀部", "裙摆", "左裙摆", "右裙摆", "前裙摆", "后裙摆",
            "侧缝", "内衬",
        ],
        "外套": [
            "左前襟", "右前襟", "左袖口", "右袖口", "左肩部", "右肩部",
            "领口", "前胸", "后背", "下摆", "左口袋", "右口袋", "内衬", "帽檐",
        ],
        "连衣裙": [
            "领口", "前胸", "腰部", "裙摆", "左肩", "右肩", "后背",
            "左袖口", "右袖口", "内衬",
        ],
        "西装": [
            "左前襟", "右前襟", "左袖口", "右袖口", "左肩部", "右肩部",
            "领口", "后背", "下摆", "左口袋", "右口袋", "袖扣", "内衬",
        ],
    }
    # 兜底：未匹配类型时使用通用位置
    GENERIC_POSITIONS = [
        "前襟", "后背", "左肩部", "右肩部", "领口", "下摆", "内衬", "局部",
    ]

    POSITIONS = [  # 保留向后兼容
        "左前襟", "右前襟", "左袖口", "右袖口", "左肩部", "右肩部",
        "领口", "前胸", "后背", "左腋下", "右腋下", "左肘部", "右肘部",
        "下摆", "左口袋", "右口袋", "左裤腿", "右裤腿", "臀部", "膝部",
        "腰带部位", "内衬", "领标附近", "前襟下摆", "后领窝",
    ]

    SIZE_DESCRIPTIONS = {
        "stain_oil": ["直径约1cm的", "约2×3cm的", "零星", "小块", "多处点状"],
        "stain_drink": ["约3cm直径的", "一片", "多处飞溅的"],
        "stain_ink": ["约0.5cm的", "一条", "多处斑点的"],
        "stain_blood": ["约1cm的", "几处点状"],
        "stain_mud": ["大片", "零星", "成片的"],
        "stain_cosmetic": ["约2cm的", "一道", "多处蹭痕的"],
        "tear_hole": ["直径约0.5cm", "约1cm裂口", "米粒大小", "约2cm不规则"],
        "tear_seam": ["约3cm", "约1.5cm", "约5cm"],
        "wear_fabric": ["约3×3cm", "约5×5cm", "局部"],
        "wear_pilling": ["大面积", "局部", "约5cm范围"],
        "fade_color": ["约5cm区域", "局部", "条状"],
        "fade_uneven": ["约8cm", "多块不规则"],
        "missing_button": ["松动", "已脱落并遗失", "仅剩线头"],
        "missing_accessory": ["腰带", "帽檐毛领", "装饰纽扣", "胸针", "袖扣"],
        "deformation": ["局部", "整体", "约10cm范围"],
        "odor": ["轻微", "明显", "较重"],
    }

    EDGE_DESCRIPTIONS = ["边缘有毛茬", "边缘较整齐", "纤维断裂明显", "有轻微抽丝"]

    @classmethod
    def detect(cls, image_paths, use_real_api=True):
        """
        对上传的图片进行智能识别
        有 QWEN_API_KEY 时自动走通义千问 VL 真实识别，否则降级为 mock 数据
        返回：品牌、材质、品类、颜色、成色、估价、瑕疵列表
        """
        if use_real_api and Config.QWEN_API_KEY:
            return cls._qwen_vl_detect(image_paths)
        return cls._mock_detect(image_paths)

    @classmethod
    def _mock_detect(cls, image_paths):
        """模拟AI检测，产生合理的随机结果（仅在千问API不可用时作为降级方案）"""
        brand = random.choice(cls.MOCK_BRANDS)
        material = random.choice(cls.MOCK_MATERIALS)
        category = random.choice(cls.MOCK_CATEGORIES)
        color = random.choice(cls.MOCK_COLORS)

        # 生成瑕疵
        defects = cls._generate_defects(len(image_paths))
        defect_count = len(defects)

        # 根据瑕疵情况判定成色
        if defect_count == 0:
            condition = cls.MOCK_CONDITIONS[0]
        elif defect_count <= 2:
            condition = random.choice(cls.MOCK_CONDITIONS[1:3])
        else:
            condition = cls.MOCK_CONDITIONS[3]

        # 计算估价（瑕疵会影响估价）
        estimated_value = cls._calculate_value(
            brand["name"], material["name"], category["name"], condition["level"]
        )
        # 每多一个严重瑕疵，再扣一点
        severe_count = sum(1 for d in defects if d["severity"] == "high")
        estimated_value = round(estimated_value * (1 - severe_count * 0.03), -2)

        result = {
            "timestamp": datetime.now().isoformat(),
            "image_count": len(image_paths),
            "brand": {"name": brand["name"], "confidence": brand["confidence"]},
            "material": {"name": material["name"], "confidence": material["confidence"]},
            "category": {"name": category["name"], "confidence": category["confidence"]},
            "color": {"name": color, "confidence": 0.95},
            "condition": condition,
            "estimated_value": estimated_value,
            "defects": defects,
            "defect_count": defect_count,
            "garment_type": category.get("name", ""),
        }

        brand_info = Config.BRAND_VALUE_MAP.get(brand["name"], {})
        result["brand_tier"] = brand_info.get("tier", "未知")

        return result

    @classmethod
    def _generate_defects(cls, image_count):
        """生成模拟瑕疵列表（每件衣物0-5个瑕疵）"""
        # 80%概率有瑕疵
        if random.random() < 0.2:
            return []

        count = random.choices([1, 2, 3, 4, 5], weights=[30, 25, 20, 15, 10])[0]
        used_types = set()
        defects = []

        allowed_positions = cls.GENERIC_POSITIONS

        # 优先保证瑕疵类型不重复
        available = [d for d in cls.MOCK_DEFECT_TYPES if d["type"] not in used_types]
        random.shuffle(available)

        for i in range(min(count, len(cls.MOCK_DEFECT_TYPES))):
            defect_type = available[i]
            used_types.add(defect_type["type"])

            position = random.choice(allowed_positions)
            size_list = cls.SIZE_DESCRIPTIONS.get(defect_type["type"], ["局部"])
            size = random.choice(size_list)

            # 构建描述
            desc_template = random.choice(defect_type["desc_templates"])
            color_desc = random.choice(["淡黄色", "深色", "浅褐色", "不规则"])
            edge_desc = random.choice(cls.EDGE_DESCRIPTIONS)
            status = random.choice(["松动即将脱落", "已缺失"])
            accessory = random.choice(["腰带", "装饰扣", "帽檐毛领", "胸针"])

            description = desc_template.format(
                position=position, size=size,
                color_desc=color_desc, edge_desc=edge_desc,
                status=status, accessory=accessory,
            )

            # 生成标注位置（百分比坐标，用于前端CSS定位）
            annotation = {
                "x": random.randint(15, 85),
                "y": random.randint(10, 80),
                "width": random.randint(12, 30),
                "height": random.randint(12, 30),
            }

            defects.append({
                "id": f"defect_{i+1}",
                "type": defect_type["type"],
                "name": defect_type["name"],
                "icon": defect_type["icon"],
                "severity": defect_type["severity"],
                "description": description,
                "risk": defect_type["risk"],
                "position": position,
                "annotation": annotation,
                "photo_index": random.randint(0, max(image_count - 1, 0)),
            })

        return defects

    @classmethod
    def detect_after_cleaning(cls, image_paths, intake_result):
        """
        洗后检测：在收衣检测基础上，模拟洗后改善
        """
        old_condition = intake_result.get("condition", {})
        old_defects = intake_result.get("defects", [])

        condition_map = {"poor": "fair", "fair": "good", "good": "excellent", "excellent": "excellent"}
        new_level = condition_map.get(old_condition.get("level", "good"), "good")

        # 洗后瑕疵改善情况
        resolved_defects = []
        remaining_defects = []
        for d in old_defects:
            if d["severity"] == "low":
                # 轻微瑕疵大概率洗掉
                if random.random() < 0.8:
                    resolved_defects.append({**d, "status": "resolved", "note": "经洗护已清除"})
                else:
                    remaining_defects.append({**d, "status": "improved", "note": "明显改善，仍有轻微痕迹"})
            elif d["severity"] == "medium":
                # 中等瑕疵部分清除
                if random.random() < 0.5:
                    resolved_defects.append({**d, "status": "resolved", "note": "经专业处理已清除"})
                else:
                    remaining_defects.append({**d, "status": "improved", "note": "已大幅改善，尚存极淡痕迹"})
            else:
                # 严重瑕疵（破损类）无法清除
                remaining_defects.append({**d, "status": "unchanged", "note": "此为结构性损伤，洗护不影响"})

        result = {
            "timestamp": datetime.now().isoformat(),
            "image_count": len(image_paths),
            "before_condition": old_condition,
            "after_condition": {
                "level": new_level,
                "label": cls.MOCK_CONDITIONS[[c["level"] for c in cls.MOCK_CONDITIONS].index(new_level)]["label"],
                "desc": "经过专业洗护，面料恢复光泽，污渍已清除",
                "deduction": cls.MOCK_CONDITIONS[[c["level"] for c in cls.MOCK_CONDITIONS].index(new_level)]["deduction"],
            },
            "brightness_improvement": random.randint(15, 40),
            "color_fidelity": random.randint(80, 98),
            "fabric_integrity": random.randint(85, 100),
            "estimated_value": intake_result.get("estimated_value", 0),
            "defects_before": old_defects,
            "defects_resolved": resolved_defects,
            "defects_remaining": remaining_defects,
        }
        return result

    @classmethod
    def _calculate_value(cls, brand_name, material_name, category_name, condition_level):
        """计算市场估价"""
        brand_info = Config.BRAND_VALUE_MAP.get(brand_name, {"tier": "普通", "multiplier": 1.0})
        material_value = Config.MATERIAL_BASE_VALUE.get(material_name, 1000)
        category_value = Config.CATEGORY_BASE_VALUE.get(category_name, 1500)
        condition_deduction = {
            "excellent": 0, "good": 0.1, "fair": 0.25, "poor": 0.4
        }.get(condition_level, 0)

        base = max(material_value, category_value)
        value = base * brand_info["multiplier"] * (1 - condition_deduction)
        return round(value, -2)

    @classmethod
    def _qwen_vl_detect(cls, image_paths):
        """
        通义千问 VL 真实视觉识别
        对上传的衣物照片进行品牌、材质、品类、颜色、成色、瑕疵检测
        """
        # 图片 base64 编码
        image_contents = []
        for i, path in enumerate(image_paths[:4]):  # 最多4张，控制成本
            if not os.path.isfile(path):
                continue
            ext = os.path.splitext(path)[1].lower()
            mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(ext, "jpeg")
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            image_contents.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/{mime};base64,{b64}"},
            })

        if not image_contents:
            return cls._mock_detect(image_paths)

        # 系统提示
        system_prompt = (
            "你是一个专业的高端服装鉴定师，服务于奢侈品干洗店的收衣检测环节。"
            "你需要仔细观察上传的衣物照片，识别品牌、材质、品类、颜色、成色等级，以及所有可见的瑕疵/污渍/磨损。"
            "必须严格按JSON格式输出，不要有任何额外文字。"
        )

        # 用户提示
        user_text = f"""请仔细观察以下{len(image_paths)}张衣物照片。

输出严格的JSON（不要```json```包裹，不要任何其他文字）：
{{
  "brand": {{"name": "品牌英文名，如Hermes/Gucci/Zegna/Uniqlo，若图中无品牌标识则填'未识别'", "confidence": 0.0~1.0}},
  "material": {{"name": "材质如羊绒/真丝/羊毛/棉/亚麻/混纺/羽绒/皮革/化纤", "confidence": 0.0~1.0}},
  "category": {{"name": "品类如西装/大衣/连衣裙/羽绒服/毛衣/衬衫/裤子/风衣/夹克/礼服/旗袍", "confidence": 0.0~1.0}},
  "color": {{"name": "颜色如黑色/白色/藏青/灰色/酒红/驼色/墨绿/米色/深蓝/卡其/巧克力棕/烟灰/象牙白/海军蓝/炭灰", "confidence": 0.0~1.0}},
  "condition": {{"level": "excellent|good|fair|poor之一", "label": "中文标签如全新/近乎全新|良好|一般|需特别护理", "desc": "简短描述整体成色状态"}},
  "defects": [
    {{
      "type": "瑕疵类型(stain_oil油渍/stain_drink饮料渍/stain_ink墨渍/stain_blood血渍/stain_mud泥渍/stain_cosmetic化妆品渍/tear_hole破洞/tear_seam开线/wear_fabric磨损/wear_pilling起球/fade_color褪色/missing_button缺扣/missing_accessory配件缺失/deformation变形/odor异味)",
      "name": "中文名称",
      "severity": "low|medium|high",
      "description": "详细描述瑕疵的位置、大小、颜色等",
      "position": "瑕疵部位如左前襟/右袖口/领口/后背/下摆/左裤腿",
      "risk": "护洗风险提示"
    }}
  ]
}}

要求：
- condition.level 只能是 excellent/good/fair/poor
- 如果照片中无明显瑕疵，defects 为空数组 []
- 瑕疵 severity：low轻微/medium中等/high严重
- 每个瑕疵必须有 type/name/severity/description/position/risk 全部字段
- 只输出JSON，不要任何其他文字！"""

        client = OpenAI(
            api_key=Config.QWEN_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

        try:
            response = client.chat.completions.create(
                model=Config.QWEN_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": image_contents + [{"type": "text", "text": user_text}],
                    },
                ],
                max_tokens=2000,
                temperature=0.1,  # 低温度，输出更稳定
            )

            raw_text = response.choices[0].message.content.strip()
            # 清理可能的 markdown 包裹
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[-1]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()

            result = json.loads(raw_text)

            # 规范化字段
            brand = result.get("brand", {})
            material = result.get("material", {})
            category = result.get("category", {})
            color = result.get("color", {})
            condition_raw = result.get("condition", {})
            defects = result.get("defects", [])

            # 确保 condition 格式正确
            valid_levels = {"excellent": "全新/近乎全新", "good": "良好", "fair": "一般", "poor": "需特别护理"}
            level = condition_raw.get("level", "good")
            if level not in valid_levels:
                level = "good"
            condition = {
                "level": level,
                "label": condition_raw.get("label", valid_levels[level]),
                "desc": condition_raw.get("desc", ""),
                "deduction": {"excellent": 0, "good": 0.1, "fair": 0.25, "poor": 0.4}[level],
            }

            # 为每个瑕疵补充 annotation（前端标注用）
            for i, d in enumerate(defects):
                if "id" not in d:
                    d["id"] = f"defect_{i+1}"
                if "annotation" not in d:
                    d["annotation"] = {
                        "x": random.randint(15, 85),
                        "y": random.randint(10, 80),
                        "width": random.randint(12, 30),
                        "height": random.randint(12, 30),
                    }
                d["photo_index"] = d.get("photo_index", 0)
                if "icon" not in d:
                    d["icon"] = "⚠"

            # 计算估价
            estimated_value = cls._calculate_value(
                brand.get("name", ""),
                material.get("name", ""),
                category.get("name", ""),
                level,
            )
            severe_count = sum(1 for d in defects if d.get("severity") == "high")
            estimated_value = round(estimated_value * (1 - severe_count * 0.03), -2)

            # 品牌等级
            brand_info = Config.BRAND_VALUE_MAP.get(brand.get("name", ""), {})
            brand_tier = brand_info.get("tier", "普通")

            return {
                "timestamp": datetime.now().isoformat(),
                "image_count": len(image_paths),
                "brand": {"name": brand.get("name", "未识别"), "confidence": brand.get("confidence", 0)},
                "material": {"name": material.get("name", "未知"), "confidence": material.get("confidence", 0)},
                "category": {"name": category.get("name", "未知"), "confidence": category.get("confidence", 0)},
                "color": {"name": color.get("name", "未知"), "confidence": color.get("confidence", 0)},
                "condition": condition,
                "estimated_value": estimated_value,
                "defects": defects,
                "defect_count": len(defects),
                "garment_type": category.get("name", ""),
                "brand_tier": brand_tier,
                "ai_model": Config.QWEN_MODEL,
                "ai_raw": raw_text,
            }

        except json.JSONDecodeError as e:
            # LLM 返回了非标准 JSON，降级到 mock
            print(f"[QWEN VL] JSON解析失败: {e}")
            print(f"[QWEN VL] 原始返回: {raw_text[:500]}")
            result = cls._mock_detect(image_paths)
            result["ai_error"] = f"JSON解析失败: {str(e)}"
            return result

        except Exception as e:
            # 网络/API 错误，降级到 mock
            print(f"[QWEN VL] API调用失败: {e}")
            result = cls._mock_detect(image_paths)
            result["ai_error"] = f"API调用失败: {str(e)}"
            return result
