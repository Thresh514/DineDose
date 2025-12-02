import ijson
import psycopg
from tqdm import tqdm
from psycopg.rows import dict_row

# Database connection
conn = psycopg.connect(
    host="ep-long-glitter-a8i7t160-pooler.eastus2.azure.neon.tech",
    dbname="neondb",
    user="neondb_owner",
    password="npg_0v8JkWHesVTq",
    sslmode="require"
)
cur = conn.cursor(row_factory=dict_row)

# SQL templates
insert_drug = """
    INSERT INTO drugs
    (product_ndc, brand_name, brand_name_base, generic_name, labeler_name,
     dosage_form, route, marketing_category, product_type, application_number,
     marketing_start_date, listing_expiration_date, finished)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT (product_ndc) DO NOTHING;
"""
insert_ingredient = """
    INSERT INTO active_ingredients (drug_ndc, name, strength)
    VALUES (%s, %s, %s)
    ON CONFLICT (drug_ndc, name, strength) DO NOTHING;
"""

# Batch buffers
drug_buffer = []
ingredient_buffer = []
BATCH_SIZE = 1000

# Stream parse JSON with ijson
with open("./drug.json", "rb") as f:
    parser = ijson.items(f, "results.item")
    for d in tqdm(parser, desc="Importing"):
        product_ndc = d.get("product_ndc")
        if not product_ndc:
            continue
        
        finished_val = bool(d.get("finished"))
        drug_buffer.append((
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
            finished_val
        ))

        for ai in d.get("active_ingredients", []):
            ingredient_buffer.append((product_ndc, ai.get("name"), ai.get("strength")))

        # Batch commit every BATCH_SIZE records
        if len(drug_buffer) >= BATCH_SIZE:
            cur.executemany(insert_drug, drug_buffer)
            cur.executemany(insert_ingredient, ingredient_buffer)
            conn.commit()
            drug_buffer.clear()
            ingredient_buffer.clear()

# Commit remaining records
if drug_buffer:
    cur.executemany(insert_drug, drug_buffer)
    cur.executemany(insert_ingredient, ingredient_buffer)
    conn.commit()

cur.close()
conn.close()
print("✅ Import completed successfully!")
