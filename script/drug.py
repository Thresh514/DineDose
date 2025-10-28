import json
import pymysql

# === 数据库配置 ===
conn = pymysql.connect(
    host='dinedose.cds2osi82wxl.us-east-1.rds.amazonaws.com',
    user='admin',
    password='8Q8aA18WrlwUmnDPwnGh',
    database='db',
    charset='utf8mb4',
    port=3306
)
cur = conn.cursor()

# === 创建表结构 ===
create_tables = """
CREATE TABLE IF NOT EXISTS drugs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_ndc VARCHAR(50) UNIQUE,
    brand_name VARCHAR(255),
    brand_name_base VARCHAR(255),
    generic_name TEXT,
    labeler_name VARCHAR(255),
    dosage_form VARCHAR(255),
    route VARCHAR(255),
    marketing_category VARCHAR(255),
    product_type VARCHAR(255),
    application_number VARCHAR(255),
    marketing_start_date VARCHAR(20),
    listing_expiration_date VARCHAR(20),
    finished BOOLEAN
);

CREATE TABLE IF NOT EXISTS active_ingredients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    drug_ndc VARCHAR(50),
    name VARCHAR(255),
    strength VARCHAR(100),
    FOREIGN KEY (drug_ndc) REFERENCES drugs(product_ndc)
        ON DELETE CASCADE
);
"""
for stmt in create_tables.strip().split(';'):
    if stmt.strip():
        cur.execute(stmt)

# === 导入 JSON 数据 ===
with open("./drug.json", "r") as f:
    data = json.load(f)["results"]

for d in data:
    product_ndc = d.get("product_ndc")
    cur.execute("""
        INSERT IGNORE INTO drugs
        (product_ndc, brand_name, brand_name_base, generic_name, labeler_name,
         dosage_form, route, marketing_category, product_type, application_number,
         marketing_start_date, listing_expiration_date, finished)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        product_ndc,
        d.get("brand_name"),
        d.get("brand_name_base"),
        d.get("generic_name"),
        d.get("labeler_name"),
        d.get("dosage_form"),
        ",".join(d.get("route", [])),
        d.get("marketing_category"),
        d.get("product_type"),
        d.get("application_number"),
        d.get("marketing_start_date"),
        d.get("listing_expiration_date"),
        1 if d.get("finished") else 0
    ))

    for ai in d.get("active_ingredients", []):
        cur.execute("""
            INSERT INTO active_ingredients (drug_ndc, name, strength)
            VALUES (%s, %s, %s)
        """, (product_ndc, ai.get("name"), ai.get("strength")))

conn.commit()
cur.close()
conn.close()
print("✅ JSON 数据已成功导入 AWS MySQL！")
