from neo4j import GraphDatabase
import os
import sys

# Ep terminal hien thi tieng Viet chuan
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- DIEN THONG TIN TU NEO4J AURA CUA BAN VAO DAY ---
AURA_URI = "neo4j+s://f5fc20b1.databases.neo4j.io"
AURA_USER = "f5fc20b1"
AURA_PASSWORD = "liHxH9XxpFYpFJzXic1olpUHDEMvTQTEbryOUqJHNpE"

CYPHER_FILE = "import_to_neo4j.cypher"

def run_import():
    if not os.path.exists(CYPHER_FILE):
        print(f"Khong tim thay file {CYPHER_FILE}!")
        return

    print(f"[*] Dang ket noi toi Neo4j Aura: {AURA_URI}...")
    driver = GraphDatabase.driver(
        AURA_URI.strip(), 
        auth=(AURA_USER.strip(), AURA_PASSWORD.strip())
    )
    
    try:
        with driver.session() as session:
            print("[*] Dang doc file Cypher...")
            with open(CYPHER_FILE, "r", encoding="utf-8") as f:
                # Tach cac cau lenh theo dau cham phay O CUOI DONG
                commands = f.read().split(";\n")
            
            print(f"[*] Bat dau import {len(commands)} cau lenh...")
            count = 0
            for cmd in commands:
                cmd = cmd.strip()
                if cmd and not cmd.startswith("//"):
                    session.run(cmd)
                    count += 1
                    if count % 100 == 0:
                        print(f"   -> Da xong {count} cau lenh...")
            
            print(f"\n[SUCCESS] Chuc mung! Da nạp thanh cong {count} lenh len Neo4j Aura.")
            
    except Exception as e:
        # Ep kieu ve chuoi de tranh loi encoding khi in
        error_msg = str(e).encode('utf-8', errors='ignore').decode('utf-8')
        print(f"\n[ERROR] Co loi xay ra: {error_msg}")
    finally:
        driver.close()

if __name__ == "__main__":
    run_import()
