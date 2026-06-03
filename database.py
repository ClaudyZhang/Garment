"""
极净奢护 - 数据库模块
SQLite 存储收衣/交衣订单记录
"""

import sqlite3
from datetime import datetime
from config import Config


def get_db():
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS garments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            customer_address TEXT DEFAULT '',
            status TEXT DEFAULT 'received',
            brand TEXT,
            material TEXT,
            category TEXT,
            color TEXT,
            size TEXT,
            condition_notes TEXT,
            estimated_value REAL,
            brand_tier TEXT,
            ai_detection_raw TEXT,
            intake_photos TEXT,
            intake_video TEXT,
            intake_report_path TEXT,
            sms_sent INTEGER DEFAULT 0,
            sms_confirmed INTEGER DEFAULT 0,
            verification_code TEXT,
            verified_at TIMESTAMP,
            cleaned_photos TEXT,
            cleaned_video TEXT,
            cleaned_condition TEXT,
            cleaned_brightness INTEGER,
            cleaned_color_fidelity INTEGER,
            cleaned_fabric_integrity INTEGER,
            delivery_report_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS detection_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            garment_id INTEGER,
            stage TEXT,
            raw_response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (garment_id) REFERENCES garments(id)
        );
    """)
    conn.commit()

    # 兼容旧数据库：补建缺失列
    try:
        conn.execute("ALTER TABLE garments ADD COLUMN verification_code TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE garments ADD COLUMN verified_at TIMESTAMP")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE garments ADD COLUMN customer_address TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE garments ADD COLUMN intake_video TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE garments ADD COLUMN garment_type TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass

    conn.close()


def generate_order_no():
    """生成订单号: CL+年月日+序号"""
    conn = get_db()
    today = datetime.now().strftime("%Y%m%d")
    count = conn.execute(
        "SELECT COUNT(*) FROM garments WHERE order_no LIKE ?",
        (f"CL{today}%",)
    ).fetchone()[0]
    conn.close()
    return f"CL{today}{count + 1:03d}"
