"""
极净奢护 - AI智能检测模块
当前版本使用模拟数据，后续可接入腾讯云图像识别API
"""

import random
import json
from datetime import datetime
from config import Config


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
    def detect(cls, image_paths, use_real_api=False, garment_type=None):
        """
        对上传的图片进行智能识别
        参数 garment_type: 衣物类型（上衣/裤子/裙子/外套/连衣裙/西装），用于精准过滤位置描述
        返回：品牌、材质、品类、颜色、成色、估价、瑕疵列表
        """
        if use_real_api and Config.TENCENT_SECRET_ID:
            return cls._tencent_detect(image_paths, garment_type)
        return cls._mock_detect(image_paths, garment_type)

    @classmethod
    def _mock_detect(cls, image_paths, garment_type=None):
        """模拟AI检测，产生合理的随机结果"""
        brand = random.choice(cls.MOCK_BRANDS)
        material = random.choice(cls.MOCK_MATERIALS)
        category = random.choice(cls.MOCK_CATEGORIES)
        color = random.choice(cls.MOCK_COLORS)

        # 生成瑕疵（传入衣物类型，精准过滤位置）
        defects = cls._generate_defects(len(image_paths), garment_type)
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
            "garment_type": garment_type or "",
        }

        brand_info = Config.BRAND_VALUE_MAP.get(brand["name"], {})
        result["brand_tier"] = brand_info.get("tier", "未知")

        return result

    @classmethod
    def _generate_defects(cls, image_count, garment_type=None):
        """生成模拟瑕疵列表（每件衣物0-5个瑕疵），根据衣物类型精准过滤位置"""
        # 80%概率有瑕疵
        if random.random() < 0.2:
            return []

        count = random.choices([1, 2, 3, 4, 5], weights=[30, 25, 20, 15, 10])[0]
        used_types = set()
        defects = []

        # 根据衣物类型选择位置列表，避免跨类别错误
        if garment_type and garment_type in cls.GARMENT_TYPE_POSITIONS:
            allowed_positions = cls.GARMENT_TYPE_POSITIONS[garment_type]
        else:
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
    def _tencent_detect(cls, image_paths):
        """腾讯云图像识别API（后续实现）"""
        return cls._mock_detect(image_paths)
