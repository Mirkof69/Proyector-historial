import psycopg2

conn = psycopg2.connect(
    dbname='Historial',
    user='postgres',
    password='25693',
    host='localhost',
    port='5433'
)

cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;")
tablas = cur.fetchall()

print(f"\n✅ TABLAS EN LA BASE DE DATOS ({len(tablas)}):\n")
for tabla in tablas:
    print(f"  - {tabla[0]}")

cur.close()
conn.close()