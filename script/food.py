import ijson
import pymysql
from tqdm import tqdm
import psycopg
from psycopg.rows import dict_row

# Database connection
conn = psycopg.connect(
    host="ep-long-glitter-a8i7t160-pooler.eastus2.azure.neon.tech",
    dbname="neondb",
    user="neondb_owner",
    password="npg_0v8JkWHesVTq",
    sslmode="require"
)
cur = conn.cursor()

def cursor(conn):
    return conn.cursor(row_factory=dict_row)

# Create table structure (run once)
create_tables = """
CREATE TABLE IF NOT EXISTS foods (
    id BIGSERIAL PRIMARY KEY,
    fdc_id BIGINT UNIQUE,
    description TEXT,
    fat DOUBLE PRECISION,
    carbonhydrate DOUBLE PRECISION,
    calories DOUBLE PRECISION,
    data_type VARCHAR(24),
    food_category_id VARCHAR(700),
    publication_date VARCHAR(10),
    food_category_num INT
);
"""
for stmt in create_tables.strip().split(';'):
    if stmt.strip():
        cur.execute(stmt)

# SQL template
insert_food = """
    INSERT INTO foods
    (fdc_id, description, fat, carbonhydrate, calories,
     data_type, food_category_id, publication_date, food_category_num)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT (fdc_id) DO NOTHING;
"""

# Batch buffers
food_buffer = []
ingredient_buffer = []
BATCH_SIZE = 1000

# Stream parse JSON with ijson
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

        # Batch commit every BATCH_SIZE records
        if len(food_buffer) >= BATCH_SIZE:
            cur.executemany(insert_food, food_buffer)
            conn.commit()
            food_buffer.clear()
            ingredient_buffer.clear()

# Commit remaining records
if food_buffer:
    cur.executemany(insert_food, food_buffer)
    #cur.executemany(insert_ingredient, ingredient_buffer)
    conn.commit()

cur.close()
conn.close()
print("✅ Import completed successfully!")
