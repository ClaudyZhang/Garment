"""
极净奢护 CLARITY LUXURY GARMENT CARE
收交衣智能检测系统 - 主应用
"""

import os
import re
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from config import Config
from database import init_db, get_db, generate_order_no
from ai_detector import AIDetector
from sms_service import SMSService
from report_generator import ReportGenerator

app = Flask(__name__)
app.config.from_object(Config)
app.config["TEMPLATES_AUTO_RELOAD"] = True  # 开发阶段强制模板实时重载
app.jinja_env.auto_reload = True

os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.REPORT_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(Config.DATABASE), exist_ok=True)

init_db()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS


# ─── 页面路由 ───────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/intake")
def intake_page():
    """收衣页面"""
    return render_template("intake.html")


@app.route("/delivery")
def delivery_page():
    """交衣页面"""
    return render_template("delivery.html")


@app.route("/report/<order_no>")
def report_page(order_no):
    """查看报告"""
    conn = get_db()
    garment = conn.execute("SELECT * FROM garments WHERE order_no = ?", (order_no,)).fetchone()
    conn.close()
    if not garment:
        return "订单不存在", 404

    g = dict(garment)
    # 手机号脱敏
    phone = g.get("customer_phone", "")
    g["phone_masked"] = phone[:3] + "****" + phone[-4:] if len(phone) == 11 else phone
    g["is_verified"] = bool(g.get("verified_at"))
    g["verified_time"] = g.get("verified_at", "")

    return render_template("report.html", garment=g)


@app.route("/dashboard")
def dashboard():
    """后台仪表盘"""
    return render_template("dashboard.html")


# ─── API 路由 ───────────────────────────────────────────

@app.route("/api/upload", methods=["POST"])
def upload_photo():
    """上传照片"""
    if "file" not in request.files:
        return jsonify({"error": "未选择文件"}), 400

    files = request.files.getlist("file")
    saved = []
    for f in files:
        if f and allowed_file(f.filename):
            ext = f.filename.rsplit(".", 1)[1].lower()
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(f.filename)}"
            filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
            f.save(filepath)
            saved.append(filename)

    return jsonify({"success": True, "files": saved})


@app.route("/api/intake", methods=["POST"])
def process_intake():
    """处理收衣：AI检测 + 生成报告 + 发送短信"""
    data = request.form.to_dict()
    photos = json.loads(data.get("photos", "[]"))

    # 处理视频文件
    video_filename = ""
    if "video" in request.files:
        video_file = request.files["video"]
        if video_file and video_file.filename:
            ext = os.path.splitext(video_file.filename)[1] or ".mp4"
            video_filename = f"intake_video_{uuid.uuid4().hex}{ext}"
            video_path = os.path.join(Config.UPLOAD_FOLDER, video_filename)
            video_file.save(video_path)

    if not photos and not video_filename:
        return jsonify({"success": False, "error": "请至少上传一张照片或录制一段视频"}), 400

    # 验证手机号码
    phone = data.get("customer_phone", "").strip()
    if not phone:
        return jsonify({"success": False, "error": "请输入手机号码"}), 400
    if not re.match(r'^1[3-9]\d{9}$', phone):
        return jsonify({"success": False, "error": "手机号码格式不正确，请输入有效的11位手机号"}), 400

    # AI检测（千问VL真实视觉识别，品类由AI从照片识别）
    image_paths = [os.path.join(Config.UPLOAD_FOLDER, p) for p in photos]
    detection = AIDetector.detect(image_paths)

    # 品类由 AI 从照片中识别（不再依赖用户手动输入）
    garment_type = detection["category"]["name"]

    # 1. AI检测

    # 2. 生成订单号并保存
    order_no = generate_order_no()
    conn = get_db()
    conn.execute("""
        INSERT INTO garments (order_no, customer_name, customer_phone, customer_address, garment_type, status,
            brand, material, category, color, condition_notes, estimated_value, brand_tier,
            ai_detection_raw, intake_photos, intake_video)
        VALUES (?, ?, ?, ?, ?, 'received', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        order_no,
        data.get("customer_name", ""),
        data.get("customer_phone", ""),
        data.get("customer_address", ""),
        garment_type,
        detection["brand"]["name"],
        detection["material"]["name"],
        detection["category"]["name"],
        detection["color"]["name"],
        detection["condition"]["desc"],
        detection["estimated_value"],
        detection.get("brand_tier", ""),
        json.dumps(detection, ensure_ascii=False),
        json.dumps(photos),
        video_filename,
    ))
    conn.commit()

    # 3. 生成收衣报告
    report_data = {
        "order_no": order_no,
        "customer_name": data.get("customer_name", ""),
        "customer_phone": data.get("customer_phone", ""),
        "customer_address": data.get("customer_address", ""),
        "garment_type": garment_type,
        "brand": detection["brand"]["name"],
        "material": detection["material"]["name"],
        "category": detection["category"]["name"],
        "color": detection["color"]["name"],
        "condition_label": detection["condition"]["label"],
        "condition_desc": detection["condition"]["desc"],
        "estimated_value": detection["estimated_value"],
        "brand_tier": detection.get("brand_tier", "普通"),
        "photos": photos,
        "intake_video": video_filename,
        "defects": detection.get("defects", []),
        "verified_at": "",  # 初始为空，短信确认后才有值
    }
    report_html = ReportGenerator.generate_intake_report(report_data)
    report_filename = f"intake_{order_no}.html"
    report_path = os.path.join(Config.REPORT_FOLDER, report_filename)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_html)

    conn.execute("UPDATE garments SET intake_report_path = ? WHERE order_no = ?",
                 (report_filename, order_no))
    conn.commit()

    # 4. 生成验证码并发送确认短信
    phone = data.get("customer_phone", "")
    verification_code = SMSService.generate_verification_code()
    sms_result = {"success": False, "code": ""}
    if phone:
        sms_result = SMSService.send_verification_code(
            phone, order_no, data.get("customer_name", ""), verification_code
        )
        conn.execute(
            "UPDATE garments SET sms_sent = 1, verification_code = ? WHERE order_no = ?",
            (verification_code, order_no)
        )
        conn.commit()

    conn.close()

    return jsonify({
        "success": True,
        "order_no": order_no,
        "detection": detection,
        "report_url": f"/report/{order_no}",
        "sms_sent": sms_result.get("success", False),
    })


@app.route("/api/intake/confirm-defects", methods=["POST"])
def confirm_defects():
    """确认/删除瑕疵后重新生成收衣报告"""
    confirmed_ids = json.loads(request.form.get("confirmed_defects", "[]"))
    deleted_ids = json.loads(request.form.get("deleted_defects", "[]"))

    # 从数据库获取原始检测结果
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM garments ORDER BY id DESC LIMIT 1"
    ).fetchone()

    if not row:
        conn.close()
        return jsonify({"success": False, "error": "未找到最近的收衣记录"}), 404

    # 解析原始AI检测数据
    ai_raw = json.loads(row["ai_detection_raw"]) if row["ai_detection_raw"] else {}
    all_defects = ai_raw.get("defects", [])

    # 过滤：只保留已确认的瑕疵
    confirmed_defects = [d for d in all_defects if d.get("id") in confirmed_ids]
    deleted_defects = [d for d in all_defects if d.get("id") in deleted_ids]

    # 重新生成报告
    intake_photos = json.loads(row["intake_photos"]) if row["intake_photos"] else []
    detection = json.loads(row["ai_detection_raw"]) if row["ai_detection_raw"] else {}
    detection["defects"] = confirmed_defects

    report_data = {
        "order_no": row["order_no"],
        "customer_name": row["customer_name"],
        "customer_phone": row["customer_phone"],
        "customer_address": row["customer_address"] or "",
        "garment_type": row["garment_type"] or "",
        "brand": row["brand"],
        "material": row["material"],
        "category": row["category"],
        "color": row["color"],
        "condition_label": detection.get("condition", {}).get("label", "良好"),
        "condition_desc": detection.get("condition", {}).get("desc", ""),
        "estimated_value": row["estimated_value"],
        "brand_tier": row["brand_tier"],
        "photos": intake_photos,
        "intake_video": row["intake_video"] or "",
        "defects": confirmed_defects,
        "verified_at": row["verified_at"] or "",
    }
    report_html = ReportGenerator.generate_intake_report(report_data)
    report_filename = f"intake_{row['order_no']}.html"
    report_path = os.path.join(Config.REPORT_FOLDER, report_filename)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_html)

    conn.close()
    return jsonify({"success": True, "report_url": f"/report/{row['order_no']}"})


@app.route("/api/intake/send-verification", methods=["POST"])
def send_verification():
    """发送/重新发送验证码短信"""
    order_no = request.form.get("order_no", "")
    if not order_no:
        return jsonify({"success": False, "error": "缺少订单号"}), 400

    conn = get_db()
    garment = conn.execute("SELECT * FROM garments WHERE order_no = ?", (order_no,)).fetchone()
    if not garment:
        conn.close()
        return jsonify({"success": False, "error": "订单不存在"}), 404

    if garment["verified_at"]:
        conn.close()
        return jsonify({"success": False, "error": "该订单已确认，无需再次发送验证码"}), 400

    # 生成新验证码
    verification_code = SMSService.generate_verification_code()
    phone = garment["customer_phone"]

    result = SMSService.send_verification_code(
        phone, order_no, garment["customer_name"], verification_code
    )

    conn.execute(
        "UPDATE garments SET verification_code = ? WHERE order_no = ?",
        (verification_code, order_no)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "phone_masked": phone[:3] + "****" + phone[-4:],
        "code": verification_code if result.get("mode") == "mock" else "",
    })


@app.route("/api/intake/verify", methods=["POST"])
def verify_intake():
    """客户通过短信验证码确认收衣报告"""
    order_no = request.form.get("order_no", "")
    code = request.form.get("code", "").strip()

    if not order_no or not code:
        return jsonify({"success": False, "error": "缺少订单号或验证码"}), 400
    if len(code) != 6 or not code.isdigit():
        return jsonify({"success": False, "error": "验证码为6位数字"}), 400

    conn = get_db()
    garment = conn.execute("SELECT * FROM garments WHERE order_no = ?", (order_no,)).fetchone()
    if not garment:
        conn.close()
        return jsonify({"success": False, "error": "订单不存在"}), 404

    if garment["verified_at"]:
        conn.close()
        return jsonify({"success": True, "message": "该订单已确认", "already_verified": True})

    db_code = garment["verification_code"]
    if not db_code:
        conn.close()
        return jsonify({"success": False, "error": "未发送验证码，请先发送"}), 400

    if code != db_code:
        conn.close()
        return jsonify({"success": False, "error": "验证码错误，请重新输入"}), 400

    now = datetime.now().isoformat()
    conn.execute(
        "UPDATE garments SET sms_confirmed = 1, verified_at = ? WHERE order_no = ?",
        (now, order_no)
    )
    conn.commit()

    # 重新生成收衣报告（此时 verified_at 已有值，盖章会显示）
    row = conn.execute("SELECT * FROM garments WHERE order_no = ?", (order_no,)).fetchone()
    if row:
        intake_photos = json.loads(row["intake_photos"]) if row["intake_photos"] else []
        detection = json.loads(row["ai_detection_raw"]) if row["ai_detection_raw"] else {}
        confirmed_defects = json.loads(row["confirmed_defects"]) if row["confirmed_defects"] else []
        detection["defects"] = confirmed_defects

        report_data = {
            "order_no": row["order_no"],
            "customer_name": row["customer_name"],
            "customer_phone": row["customer_phone"],
            "customer_address": row["customer_address"] or "",
            "garment_type": row["garment_type"] or "",
            "brand": row["brand"],
            "material": row["material"],
            "category": row["category"],
            "color": row["color"],
            "condition_label": detection.get("condition", {}).get("label", "良好"),
            "condition_desc": detection.get("condition", {}).get("desc", ""),
            "estimated_value": row["estimated_value"],
            "brand_tier": row["brand_tier"],
            "photos": intake_photos,
            "intake_video": row["intake_video"] or "",
            "defects": confirmed_defects,
            "verified_at": row["verified_at"],
        }
        report_html = ReportGenerator.generate_intake_report(report_data)
        report_filename = f"intake_{row['order_no']}.html"
        report_path = os.path.join(Config.REPORT_FOLDER, report_filename)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_html)

        conn.execute("UPDATE garments SET intake_report_path = ? WHERE order_no = ?",
                     (report_filename, order_no))
        conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "收衣报告已确认，具有法律效力",
        "verified_at": now,
    })


@app.route("/api/intake/send-report-link", methods=["POST"])
def send_report_link():
    """发送收衣报告链接短信给客户"""
    order_no = request.form.get("order_no", "")
    if not order_no:
        return jsonify({"success": False, "error": "缺少订单号"}), 400

    conn = get_db()
    garment = conn.execute("SELECT * FROM garments WHERE order_no = ?", (order_no,)).fetchone()
    if not garment:
        conn.close()
        return jsonify({"success": False, "error": "订单不存在"}), 404

    if not garment["verified_at"]:
        conn.close()
        return jsonify({"success": False, "error": "订单尚未确认，无法发送报告链接"}), 400

    phone = garment["customer_phone"]
    if not phone:
        conn.close()
        return jsonify({"success": False, "error": "该订单未登记手机号"}), 400

    # 构造完整报告链接
    report_url = f"{request.host_url}report/{order_no}"

    result = SMSService.send_report_link(
        phone, order_no, garment["customer_name"], report_url
    )
    conn.close()

    return jsonify({
        "success": True,
        "phone_masked": phone[:3] + "****" + phone[-4:],
        "report_url": report_url if result.get("mode") == "mock" else "",
    })


@app.route("/api/delivery", methods=["POST"])
def process_delivery():
    """处理交衣：洗后检测 + 对比报告"""
    data = request.form.to_dict()
    order_no = data.get("order_no", "")
    photos = json.loads(data.get("photos", "[]"))

    if not order_no:
        return jsonify({"error": "缺少订单号"}), 400
    if not photos:
        return jsonify({"error": "请至少上传一张洗后照片"}), 400

    conn = get_db()
    garment = conn.execute("SELECT * FROM garments WHERE order_no = ?", (order_no,)).fetchone()

    if not garment:
        conn.close()
        return jsonify({"error": "订单不存在"}), 404

    # 1. 获取收衣时的检测数据
    intake_detection = json.loads(garment["ai_detection_raw"])

    # 2. 洗后AI检测
    image_paths = [os.path.join(Config.UPLOAD_FOLDER, p) for p in photos]
    detection = AIDetector.detect_after_cleaning(image_paths, intake_detection)

    # 3. 生成交衣对比报告
    report_data = {
        "order_no": order_no,
        "customer_name": garment["customer_name"],
        "customer_phone": garment["customer_phone"],
        "brand": garment["brand"],
        "material": garment["material"],
        "category": garment["category"],
        "estimated_value": garment["estimated_value"],
        "condition_label": intake_detection["condition"]["label"],
        "condition_desc": intake_detection["condition"]["desc"],
        "cleaned_condition_label": detection["after_condition"]["label"],
        "brightness_improvement": detection["brightness_improvement"],
        "color_fidelity": detection["color_fidelity"],
        "fabric_integrity": detection["fabric_integrity"],
        "cleaned_photos": photos,
        "defects_resolved": detection.get("defects_resolved", []),
        "defects_remaining": detection.get("defects_remaining", []),
    }
    report_html = ReportGenerator.generate_delivery_report(report_data)
    report_filename = f"delivery_{order_no}.html"
    report_path = os.path.join(Config.REPORT_FOLDER, report_filename)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_html)

    # 4. 更新数据库
    conn.execute("""
        UPDATE garments SET status = 'ready', cleaned_photos = ?,
            cleaned_condition = ?, cleaned_brightness = ?, cleaned_color_fidelity = ?,
            cleaned_fabric_integrity = ?, delivery_report_path = ?, updated_at = CURRENT_TIMESTAMP
        WHERE order_no = ?
    """, (
        json.dumps(photos),
        detection["after_condition"]["label"],
        detection["brightness_improvement"],
        detection["color_fidelity"],
        detection["fabric_integrity"],
        report_filename,
        order_no,
    ))
    conn.commit()

    # 5. 发送交衣通知
    if garment["customer_phone"]:
        SMSService.send_delivery_notification(
            garment["customer_phone"], order_no, garment["customer_name"]
        )
        conn.execute("UPDATE garments SET sms_confirmed = 1 WHERE order_no = ?", (order_no,))
        conn.commit()

    conn.close()

    return jsonify({
        "success": True,
        "order_no": order_no,
        "detection": detection,
        "report_url": f"/report/{order_no}",
    })


@app.route("/api/orders", methods=["GET"])
def list_orders():
    """获取订单列表"""
    status_filter = request.args.get("status", "")
    conn = get_db()
    if status_filter:
        orders = conn.execute(
            "SELECT * FROM garments WHERE status = ? ORDER BY created_at DESC", (status_filter,)
        ).fetchall()
    else:
        orders = conn.execute("SELECT * FROM garments ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify({
        "orders": [dict(o) for o in orders],
        "counts": _get_status_counts(),
    })


@app.route("/api/orders/<order_no>", methods=["GET"])
def get_order(order_no):
    """获取单个订单详情"""
    conn = get_db()
    garment = conn.execute("SELECT * FROM garments WHERE order_no = ?", (order_no,)).fetchone()
    conn.close()
    if not garment:
        return jsonify({"error": "订单不存在"}), 404
    return jsonify(dict(garment))


@app.route("/api/orders/<order_no>/status", methods=["PUT"])
def update_order_status(order_no):
    """更新订单状态"""
    new_status = request.json.get("status", "")
    valid_statuses = ["received", "cleaning", "ready", "delivered"]
    if new_status not in valid_statuses:
        return jsonify({"error": f"无效状态，可选: {valid_statuses}"}), 400

    conn = get_db()
    conn.execute("UPDATE garments SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE order_no = ?",
                 (new_status, order_no))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "order_no": order_no, "status": new_status})


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """获取统计数据"""
    counts = _get_status_counts()
    conn = get_db()
    total_value = conn.execute("SELECT SUM(estimated_value) FROM garments").fetchone()[0] or 0
    conn.close()
    return jsonify({
        **counts,
        "total_value": total_value,
        "total_orders": sum(counts.values()),
    })


def _get_status_counts():
    conn = get_db()
    counts = {}
    for status in ["received", "cleaning", "ready", "delivered"]:
        c = conn.execute("SELECT COUNT(*) FROM garments WHERE status = ?", (status,)).fetchone()[0]
        counts[status] = c
    conn.close()
    return counts


# ─── 静态文件 ───────────────────────────────────────────

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(Config.UPLOAD_FOLDER, filename)


@app.route("/reports/<path:filename>")
def report_file(filename):
    return send_from_directory(Config.REPORT_FOLDER, filename)


# ─── 开发环境：禁用浏览器缓存 ─────────────────────────────

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print("\n  [CLARITY] 极净奢护 · 收交衣智能检测系统")
    print("  ========================================")
    print("  访问: http://localhost:5000")
    print("  收衣: http://localhost:5000/intake")
    print("  交衣: http://localhost:5000/delivery")
    print("  后台: http://localhost:5000/dashboard\n")
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    app.run(debug=args.debug, host="0.0.0.0", port=5000)
