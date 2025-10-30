import ijson
import pymysql
from tqdm import tqdm

# === 数据库连接配置 ===
conn = pymysql.connect(
    host='dinedose.cds2osi82wxl.us-east-1.rds.amazonaws.com',
    user='admin',
    password='8Q8aA18WrlwUmnDPwnGh',
    database='db',
    charset='utf8mb4',
    port=3306
)
cur = conn.cursor()

# === 创建表结构（只执行一次）===
create_tables = """
CREATE TABLE IF NOT EXISTS foods (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    fdc_id BIGINT,
    description TEXT,
    fat DOUBLE,
    carbonhydrate DOUBLE,
    calories DOUBLE,
    data_type VARCHAR(24),
    food_category_id VARCHAR(700),
    publication_date VARCHAR(10),
    food_category_num INT
);
"""
for stmt in create_tables.strip().split(';'):
    if stmt.strip():
        cur.execute(stmt)

# === SQL 模板 ===
insert_food = """
    INSERT IGNORE INTO foods
    (fdc_id, description, fat, carbonhydrate, calories,
     data_type, food_category_id, publication_date, food_category_num)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
"""
# insert_ingredient = """
#     INSERT INTO active_ingredients (drug_ndc, name, strength)
#     VALUES (%s, %s, %s)
# """

# === 批量缓冲区 ===
food_buffer = []
ingredient_buffer = []
BATCH_SIZE = 1000  # 每 1000 条提交一次

# === 使用 ijson 流式解析 JSON ===
with open("./output.json", "rb") as f:
    parser = ijson.items(f, "results.item")
    for d in tqdm(parser, desc="Importing"):
        food_buffer.append((
            d.get("fdc_id"),
            d.get("description"),
            d.get("fat"),
            d.get("carbonhydrate"),
            d.get("calories"),
            d.get("data_type"),
            d.get("food_category_id"),
            d.get("publication_date"),
            d.get("food_category_num")
        ))

        # === 每 1000 条批量提交一次 ===
        if len(food_buffer) >= BATCH_SIZE:
            cur.executemany(insert_food, food_buffer)
            #cur.executemany(insert_ingredient, ingredient_buffer)
            conn.commit()
            food_buffer.clear()
            ingredient_buffer.clear()

# === 写入最后剩余部分 ===
if food_buffer:
    cur.executemany(insert_food, food_buffer)
    #cur.executemany(insert_ingredient, ingredient_buffer)
    conn.commit()

cur.close()
conn.close()
print("✅ Import completed successfully!")
