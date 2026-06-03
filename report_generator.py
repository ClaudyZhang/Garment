"""
极净奢护 - PDF报告生成模块
生成收衣报告和交衣对比报告
"""

import os
import json
from datetime import datetime
from config import Config

# 使用 reportlab 生成 PDF（后续安装）
# 当前版本生成 HTML 报告，可打印为 PDF


class ReportGenerator:
    """报告生成器"""

    BRAND_COLORS = {
        "顶奢": "#8B0000",
        "奢侈": "#C41E3A",
        "轻奢": "#B8860B",
        "普通": "#555555",
    }

    @classmethod
    def _build_defect_html(cls, defects):
        """构建瑕疵证据HTML"""
        if not defects:
            return """<div class="section">
    <div class="section-title" style="color:#4A7C59;border-color:#7BAF8A;">瑕疵检测</div>
    <div style="text-align:center;padding:20px;color:#4A7C59;font-size:13px;background:#F2FAF4;border-radius:4px;">未检测到明显瑕疵，衣物状态良好</div>
  </div>"""

        sev_order = {"high": 0, "medium": 1, "low": 2}
        sorted_defects = sorted(defects, key=lambda d: sev_order.get(d.get("severity", "low"), 2))
        high_count = sum(1 for d in defects if d.get("severity") == "high")
        medium_count = sum(1 for d in defects if d.get("severity") == "medium")

        warning = ""
        if high_count > 0:
            warning = f"""<div style="background:#FFF0F0;border:1px solid #F5C0C0;border-radius:4px;padding:10px 14px;margin-bottom:12px;font-size:12px;color:#C62828;">
    &#9888; 检测到 <strong>{high_count}</strong> 处严重瑕疵、<strong>{medium_count}</strong> 处中等瑕疵，已拍照存证
  </div>"""

        cards = ""
        sev_labels = {"low": "轻微", "medium": "中等", "high": "严重"}
        sev_colors = {"low": "#F57F17", "medium": "#E65100", "high": "#C62828"}
        sev_bg = {"low": "#FFF8E1", "medium": "#FFF0E0", "high": "#FFE0E0"}

        for i, d in enumerate(sorted_defects):
            sev = d.get("severity", "low")
            cards += f"""<div class="defect-card" style="display:flex;gap:14px;background:{sev_bg.get(sev, '#FFF8E1')};border:1px solid #E8DFD3;border-radius:4px;padding:14px;margin-bottom:10px;align-items:flex-start;">
    <div style="font-size:28px;width:40px;text-align:center;flex-shrink:0;">{d.get('icon', '&#9888;')}</div>
    <div style="flex:1;">
      <div style="font-size:14px;font-weight:600;color:#3D322B;margin-bottom:4px;">
        {d.get('name', '瑕疵')} · <span style="color:{sev_colors.get(sev, '#F57F17')};font-weight:500;">{sev_labels.get(sev, sev)}</span>
        <span style="font-size:10px;color:#A0927B;margin-left:8px;">位置: {d.get('position', '-')}</span>
      </div>
      <div style="font-size:12px;color:#6B5D4F;line-height:1.6;">{d.get('description', '')}</div>
      <div style="font-size:11px;color:#C44;margin-top:6px;padding:6px 8px;background:rgba(255,255,255,0.6);border-radius:3px;border-left:2px solid #E88;">&#9888; 洗护风险: {d.get('risk', '')}</div>
    </div>
  </div>"""

        return f"""<div class="section">
    <div class="section-title" style="color:#C44;border-color:#E88;">瑕疵证据 — 共 {len(defects)} 处</div>
    {warning}
    {cards}
    <div style="margin-top:12px;font-size:11px;color:#A0927B;text-align:center;padding:8px;background:#FFF8F0;border:1px solid #E8DFD3;border-radius:4px;">
      &#128274; 以上瑕疵照片已作为收衣证据存档，洗护前后如有争议可随时调取对比
    </div>
  </div>"""

    @classmethod
    def generate_intake_report(cls, garment_data):
        """生成收衣报告 HTML"""
        brand_tier = garment_data.get("brand_tier", "普通")
        tier_color = cls.BRAND_COLORS.get(brand_tier, "#555")
        defects = garment_data.get("defects", [])

        photos_html = ""
        for i, photo in enumerate(garment_data.get("photos", [])):
            photos_html += f"""
            <div class="photo-card">
                <img src="/uploads/{photo}" alt="收衣照片{i+1}" />
                <div class="photo-label">收衣照片 {i+1}</div>
            </div>"""

        defect_section = cls._build_defect_html(defects)

        # 根据 verified_at 决定是否显示"已确认收衣"盖章
        verified_at = garment_data.get('verified_at', '')
        if verified_at:
            stamp_section = f"""
  <div class="stamp">
    <div class="stamp-text">已确认收衣</div>
    <div style="font-size:10px;color:#A0927B;margin-top:4px;">确认时间: {verified_at[:16]}</div>
  </div>"""
        else:
            stamp_section = ''

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>收衣报告 - {garment_data['order_no']}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; color: #3D322B; background: #FAF7F2; }}
  .page {{ max-width: 800px; margin: 0 auto; padding: 40px; }}
  .header {{ text-align: center; border-bottom: 2px solid #C8B299; padding-bottom: 24px; margin-bottom: 32px; }}
  .header h1 {{ font-size: 24px; font-weight: 300; letter-spacing: 6px; color: #8B7355; }}
  .header .subtitle {{ font-size: 12px; color: #A0927B; margin-top: 8px; letter-spacing: 2px; }}
  .header .order-no {{ font-size: 14px; color: #6B5D4F; margin-top: 12px; font-family: monospace; }}
  .tier-badge {{ display: inline-block; padding: 4px 16px; border-radius: 2px; font-size: 12px; font-weight: 600; letter-spacing: 2px; color: #fff; background: {tier_color}; }}
  .section {{ margin-bottom: 32px; }}
  .section-title {{ font-size: 14px; font-weight: 600; color: #8B7355; border-left: 3px solid #C8B299; padding-left: 12px; margin-bottom: 16px; letter-spacing: 1px; }}
  .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
  .info-item {{ background: #FFF; border: 1px solid #E8DFD3; padding: 14px 18px; border-radius: 4px; }}
  .info-item .label {{ font-size: 11px; color: #A0927B; letter-spacing: 1px; margin-bottom: 4px; text-transform: uppercase; }}
  .info-item .value {{ font-size: 16px; color: #3D322B; font-weight: 500; }}
  .value-highlight {{ font-size: 28px; color: {tier_color}; font-weight: 300; }}
  .photos {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }}
  .photo-card {{ background: #FFF; border: 1px solid #E8DFD3; border-radius: 4px; overflow: hidden; }}
  .photo-card img {{ width: 100%; height: 200px; object-fit: cover; }}
  .photo-label {{ font-size: 11px; color: #A0927B; text-align: center; padding: 8px; }}
  .condition {{ background: #FFF8F0; border: 1px solid #E8DFD3; padding: 16px 20px; border-radius: 4px; }}
  .condition .level {{ font-size: 14px; font-weight: 600; color: #C4943A; }}
  .condition .desc {{ font-size: 12px; color: #8B7355; margin-top: 4px; }}
  .footer {{ text-align: center; border-top: 1px solid #E8DFD3; padding-top: 24px; margin-top: 40px; font-size: 11px; color: #B8A898; }}
  .stamp {{ text-align: right; margin-top: 20px; }}
  .stamp-text {{ display: inline-block; border: 2px solid #C8B299; color: #C8B299; padding: 8px 20px; font-size: 12px; letter-spacing: 4px; transform: rotate(-5deg); }}
  @media print {{ body {{ background: #fff; }} }}
</style>
</head>
<body>
<div class="page">
  <div class="header">
    <h1>CLARITY LUXURY</h1>
    <div class="subtitle">极 净 奢 护  ·  收 衣 报 告</div>
    <div class="order-no">订单编号: {garment_data['order_no']}</div>
    <div style="margin-top:12px"><span class="tier-badge">{brand_tier}品牌</span></div>
  </div>

  <div class="section">
    <div class="section-title">客户信息</div>
    <div class="info-grid">
      <div class="info-item">
        <div class="label">客户姓名</div>
        <div class="value">{garment_data.get('customer_name', '-')}</div>
      </div>
      <div class="info-item">
        <div class="label">联系电话</div>
        <div class="value">{garment_data.get('customer_phone', '-')}</div>
      </div>
      <div class="info-item">
        <div class="label">客户地址</div>
        <div class="value" style="font-size:13px;">{garment_data.get('customer_address', '-') or '-'}</div>
      </div>
      <div class="info-item">
        <div class="label">衣物品类</div>
        <div class="value">{garment_data.get('garment_type', '-') or '-'}</div>
      </div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">AI 智能检测结果</div>
    <div class="info-grid">
      <div class="info-item">
        <div class="label">识别品牌</div>
        <div class="value">{garment_data.get('brand', '-')}</div>
      </div>
      <div class="info-item">
        <div class="label">面料材质</div>
        <div class="value">{garment_data.get('material', '-')}</div>
      </div>
      <div class="info-item">
        <div class="label">服装品类</div>
        <div class="value">{garment_data.get('category', '-')}</div>
      </div>
      <div class="info-item">
        <div class="label">颜色</div>
        <div class="value">{garment_data.get('color', '-')}</div>
      </div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">收衣照片</div>
    <div class="photos">
      {photos_html}
    </div>
  </div>

  <div class="section">
    <div class="section-title">成色评估</div>
    <div class="condition">
      <div class="level">{garment_data.get('condition_label', '-')}</div>
      <div class="desc">{garment_data.get('condition_desc', '-')}</div>
    </div>
  </div>

  {defect_section}

  <div class="section" style="text-align:center;">
    <div class="section-title" style="border:none;text-align:center;">市场估价</div>
    <div class="value-highlight">¥ {garment_data.get('estimated_value', 0):,}</div>
    <div style="font-size:11px;color:#A0927B;margin-top:4px;">基于品牌、材质、品类、成色及瑕疵综合评估</div>
  </div>

        {stamp_section}

  <div class="footer">
    <div>极净奢护 CLARITY LUXURY GARMENT CARE</div>
    <div>上海市徐汇区漕河泾 · 报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
  </div>
</div>
</body>
</html>"""
        return html

    @classmethod
    def generate_delivery_report(cls, garment_data):
        """生成交衣对比报告 HTML"""
        photos_html = ""
        for i, photo in enumerate(garment_data.get("cleaned_photos", [])):
            photos_html += f"""
            <div class="photo-card">
                <img src="/uploads/{photo}" alt="洗后照片{i+1}" />
                <div class="photo-label">洗后照片 {i+1}</div>
            </div>"""

        # 对比数据
        before_condition = garment_data.get("condition_label", "良好")
        after_condition = garment_data.get("cleaned_condition_label", "极佳")
        brightness = garment_data.get("brightness_improvement", 25)
        color_fidelity = garment_data.get("color_fidelity", 92)
        fabric_integrity = garment_data.get("fabric_integrity", 95)
        defects_resolved = garment_data.get("defects_resolved", [])
        defects_remaining = garment_data.get("defects_remaining", [])

        # 瑕疵处理结果
        defect_section = ""
        total_defects = len(defects_resolved) + len(defects_remaining)
        if total_defects > 0:
            resolved_html = ""
            for d in defects_resolved:
                resolved_html += f"""<div style="display:flex;gap:8px;align-items:center;padding:8px 10px;margin-bottom:4px;background:#fff;border-left:3px solid #4A7C59;border-radius:3px;font-size:12px;">
    <span>{d.get('icon', '')}</span>
    <span style="flex:1;">{d.get('name', '')} · {d.get('position', '')}</span>
    <span style="color:#4A7C59;font-weight:500;">已清除</span>
    <span style="font-size:10px;color:#A0927B;">{d.get('note', '')}</span>
  </div>"""

            remaining_html = ""
            for d in defects_remaining:
                is_structural = d.get("severity") == "high"
                color = "#C62828" if is_structural else "#E65100"
                label = "结构性损伤" if is_structural else "已改善"
                remaining_html += f"""<div style="display:flex;gap:8px;align-items:center;padding:8px 10px;margin-bottom:4px;background:#fff;border-left:3px solid {color};border-radius:3px;font-size:12px;">
    <span>{d.get('icon', '')}</span>
    <span style="flex:1;">{d.get('name', '')} · {d.get('position', '')}</span>
    <span style="color:{color};font-weight:500;">{label}</span>
    <span style="font-size:10px;color:#A0927B;">{d.get('note', '')}</span>
  </div>"""

            defect_section = f"""<div class="section">
    <div class="section-title" style="color:#4A7C59;border-color:#7BAF8A;">瑕疵处理结果 — 收衣时共 {total_defects} 处</div>
    {resolved_html}
    {remaining_html}
    {"<div style='font-size:10px;color:#C62828;margin-top:6px;'>&#9888; 严重瑕疵（破损/撕裂/变形）为结构性损伤，洗护不改变其状态，收衣时已告知客户并存证</div>" if any(d.get("severity") == "high" for d in defects_remaining) else ""}
  </div>"""

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>交衣报告 - {garment_data['order_no']}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; color: #3D322B; background: #FAF7F2; }}
  .page {{ max-width: 800px; margin: 0 auto; padding: 40px; }}
  .header {{ text-align: center; border-bottom: 2px solid #4A7C59; padding-bottom: 24px; margin-bottom: 32px; }}
  .header h1 {{ font-size: 24px; font-weight: 300; letter-spacing: 6px; color: #4A7C59; }}
  .header .subtitle {{ font-size: 12px; color: #6B8F7A; margin-top: 8px; letter-spacing: 2px; }}
  .header .order-no {{ font-size: 14px; color: #5A7A65; margin-top: 12px; font-family: monospace; }}
  .section {{ margin-bottom: 32px; }}
  .section-title {{ font-size: 14px; font-weight: 600; color: #4A7C59; border-left: 3px solid #7BAF8A; padding-left: 12px; margin-bottom: 16px; letter-spacing: 1px; }}
  .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
  .info-item {{ background: #FFF; border: 1px solid #D8E8DC; padding: 14px 18px; border-radius: 4px; }}
  .info-item .label {{ font-size: 11px; color: #7BAF8A; letter-spacing: 1px; margin-bottom: 4px; }}
  .info-item .value {{ font-size: 16px; color: #3D322B; font-weight: 500; }}
  .compare-row {{ display: grid; grid-template-columns: 1fr 60px 1fr; gap: 0; align-items: center; margin: 20px 0; }}
  .compare-box {{ background: #FFF; border: 1px solid #D8E8DC; padding: 20px; border-radius: 4px; text-align: center; }}
  .compare-box.before {{ border-color: #E8DFD3; background: #FFF8F0; }}
  .compare-box.after {{ border-color: #A8D5B5; background: #F2FAF4; }}
  .compare-arrow {{ font-size: 28px; color: #4A7C59; text-align: center; }}
  .compare-box .title {{ font-size: 11px; letter-spacing: 2px; margin-bottom: 8px; }}
  .compare-box .val {{ font-size: 18px; font-weight: 500; }}
  .compare-box .sub {{ font-size: 11px; color: #888; margin-top: 6px; }}
  .score-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }}
  .score-item {{ background: #FFF; border: 1px solid #D8E8DC; padding: 16px; border-radius: 4px; text-align: center; }}
  .score-item .label {{ font-size: 11px; color: #7BAF8A; letter-spacing: 1px; margin-bottom: 8px; }}
  .score-bar {{ height: 6px; background: #E8EDE9; border-radius: 3px; margin: 8px 0; overflow: hidden; }}
  .score-fill {{ height: 100%; background: #4A7C59; border-radius: 3px; }}
  .score-num {{ font-size: 22px; font-weight: 300; color: #4A7C59; }}
  .photos {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }}
  .photo-card {{ background: #FFF; border: 1px solid #D8E8DC; border-radius: 4px; overflow: hidden; }}
  .photo-card img {{ width: 100%; height: 200px; object-fit: cover; }}
  .photo-label {{ font-size: 11px; color: #7BAF8A; text-align: center; padding: 8px; }}
  .footer {{ text-align: center; border-top: 1px solid #D8E8DC; padding-top: 24px; margin-top: 40px; font-size: 11px; color: #A8C5B2; }}
  .stamp {{ text-align: right; margin-top: 20px; }}
  .stamp-text {{ display: inline-block; border: 2px solid #4A7C59; color: #4A7C59; padding: 8px 20px; font-size: 12px; letter-spacing: 4px; transform: rotate(-5deg); }}
  @media print {{ body {{ background: #fff; }} }}
</style>
</head>
<body>
<div class="page">
  <div class="header">
    <h1>CLARITY LUXURY</h1>
    <div class="subtitle">极 净 奢 护  ·  交 衣 报 告</div>
    <div class="order-no">订单编号: {garment_data['order_no']}</div>
  </div>

  <div class="section">
    <div class="section-title">客户与衣物信息</div>
    <div class="info-grid">
      <div class="info-item"><div class="label">客户姓名</div><div class="value">{garment_data.get('customer_name', '-')}</div></div>
      <div class="info-item"><div class="label">品牌 / 品类</div><div class="value">{garment_data.get('brand', '-')} {garment_data.get('category', '-')}</div></div>
      <div class="info-item"><div class="label">面料材质</div><div class="value">{garment_data.get('material', '-')}</div></div>
      <div class="info-item"><div class="label">市场估价</div><div class="value">¥ {garment_data.get('estimated_value', 0):,}</div></div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">洗护前后对比</div>
    <div class="compare-row">
      <div class="compare-box before">
        <div class="title" style="color:#C4943A;">洗 护 前</div>
        <div class="val" style="color:#C4943A;">{before_condition}</div>
        <div class="sub">{garment_data.get('condition_desc', '')}</div>
      </div>
      <div class="compare-arrow">&rarr;</div>
      <div class="compare-box after">
        <div class="title" style="color:#4A7C59;">洗 护 后</div>
        <div class="val" style="color:#4A7C59;">{after_condition}</div>
        <div class="sub">经专业洗护，焕然一新</div>
      </div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">品质评分</div>
    <div class="score-grid">
      <div class="score-item">
        <div class="label">光泽度提升</div>
        <div class="score-num">{brightness}%</div>
        <div class="score-bar"><div class="score-fill" style="width:{brightness}%;"></div></div>
      </div>
      <div class="score-item">
        <div class="label">色彩保真度</div>
        <div class="score-num">{color_fidelity}%</div>
        <div class="score-bar"><div class="score-fill" style="width:{color_fidelity}%;"></div></div>
      </div>
      <div class="score-item">
        <div class="label">面料完整度</div>
        <div class="score-num">{fabric_integrity}%</div>
        <div class="score-bar"><div class="score-fill" style="width:{fabric_integrity}%;"></div></div>
      </div>
    </div>
  </div>
  {defect_section}
  <div class="section">
    <div class="section-title">洗后照片</div>
    <div class="photos">
      {photos_html}
    </div>
  </div>

  <div class="stamp">
    <div class="stamp-text">护理完成</div>
  </div>

  <div class="footer">
    <div>极净奢护 CLARITY LUXURY GARMENT CARE</div>
    <div>上海市徐汇区漕河泾 · 报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
  </div>
</div>
</body>
</html>"""
        return html
