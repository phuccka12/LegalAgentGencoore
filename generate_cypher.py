import json
import re
import os

VIOLATIONS_FILE = "nghidinh168_violations_labeled.json"
AUTHORITIES_FILE = "nghidinh168_authorities_final.json"
OUTPUT_CYPHER = "import_to_neo4j.cypher"

def escape_cypher(text):
    if text is None: return "null"
    # Dung ensure_ascii=False de giu nguyen tieng Viet, de doc va de import
    safe_text = json.dumps(str(text), ensure_ascii=False)
    return safe_text

def parse_reference(text, current_art):
    # Regex de tim cac tham chieu nhu: "diem a khoan 2 Dieu 6" hoac "khoan 3 Dieu nay"
    # Day la logic de tao Reasoning Edges
    found_ids = []
    
    # Mau 1: diem [x] khoan [y] Dieu [z]
    matches = re.findall(r"điểm ([a-zđ]) khoản (\d+) Điều (\d+)", text)
    for m in matches:
        found_ids.append(f"ND168_Art{m[2]}_C{m[1]}_p{m[0]}")
    
    # Mau 2: khoan [y] Dieu [z]
    matches = re.findall(r"khoản (\d+) Điều (\d+)", text)
    for m in matches:
        found_ids.append(f"ND168_Art{m[1]}_C{m[0]}")

    # Mau 3: diem [x] khoan [y] Dieu nay
    matches = re.findall(r"điểm ([a-zđ]) khoản (\d+) Điều này", text)
    for m in matches:
        found_ids.append(f"ND168_Art{current_art}_C{m[1]}_p{m[0]}")

    return found_ids

def main():
    # BAT CHE DO BAO TRI
    with open(".maintenance", "w") as f:
        f.write("ON")
    print("[!] HE THONG DANG TRONG CHE DO BAO TRI (MAINTENANCE MODE: ON)")

    if not os.path.exists(VIOLATIONS_FILE):
        print("Khong tim thay file violations!")
        return

    with open(VIOLATIONS_FILE, "r", encoding="utf-8") as f:
        violations = json.load(f)
    with open(AUTHORITIES_FILE, "r", encoding="utf-8") as f:
        authorities = json.load(f)

    cypher_commands = []

    # 1. Khoi tao cac Node Category va Topic (Unique)
    cypher_commands.append("// --- TAO CAC NODE PHAN LOAI ---")
    categories = set()
    topics = set()
    for v in violations:
        categories.add(v["labels"]["vehicle_category"])
        for t in v["labels"]["violation_groups"]:
            topics.add(t)
    
    for c in categories:
        cypher_commands.append(f"MERGE (c:Category {{name: {escape_cypher(c)}}});")
    for t in topics:
        cypher_commands.append(f"MERGE (t:Topic {{name: {escape_cypher(t)}}});")

    # 2. Tao Node Violation va cac quan he co ban
    cypher_commands.append("\n// --- TAO NODE VIOLATION VA QUAN HE ---")
    for v in violations:
        v_id = v["node_id"]
        meta = v["metadata"]
        behav = v["behavior"]
        cons = v["consequences"]
        labels = v["labels"]
        
        # Create Violation Node
        fine_min = cons['fine_range']['min'] if cons.get('fine_range') and cons['fine_range'].get('min') is not None else "null"
        fine_max = cons['fine_range']['max'] if cons.get('fine_range') and cons['fine_range'].get('max') is not None else "null"
        summary_val = escape_cypher(behav.get('summary'))
        severity_val = escape_cypher(labels.get('severity_level'))
        
        # Bo sung tu long va dong nghia de tim kiem thong minh
        slangs = escape_cypher(", ".join(behav.get("semantic_expansion", {}).get("slang", [])))
        synonyms = escape_cypher(", ".join(behav.get("semantic_expansion", {}).get("synonyms", [])))

        cypher_commands.append(
            f"MERGE (v:Violation {{id: '{v_id}'}}) "
            f"SET v.summary = {summary_val}, "
            f"v.article = {meta['article']}, v.clause = {meta['clause']}, "
            f"v.fine_min = {fine_min}, "
            f"v.fine_max = {fine_max}, "
            f"v.severity = {severity_val}, "
            f"v.slang = {slangs}, "
            f"v.synonyms = {synonyms};"
        )

        # Connect Category & Topic
        cypher_commands.append(f"MATCH (v:Violation {{id: '{v_id}'}}), (c:Category {{name: {escape_cypher(labels['vehicle_category'])}}}) MERGE (v)-[:APPLIES_TO]->(c);")
        for t in labels["violation_groups"]:
            cypher_commands.append(f"MATCH (v:Violation {{id: '{v_id}'}}), (t:Topic {{name: {escape_cypher(t)}}}) MERGE (v)-[:TAGGED_AS]->(t);")

        # Tao Node Evidence (Cong cu)
        for tool in v["legal_procedure"]["evidence_requirements"].get("tools", []):
            cypher_commands.append(f"MERGE (e:Evidence {{name: {escape_cypher(tool)}}});")
            cypher_commands.append(f"MATCH (v:Violation {{id: '{v_id}'}}), (e:Evidence {{name: {escape_cypher(tool)}}}) MERGE (v)-[:REQUIRES_EVIDENCE]->(e);")

        # REASONING EDGES: Except If / Overridden By
        for exc in v["inference_logic"].get("exceptions", []):
            ref_ids = parse_reference(exc, meta["article"])
            for r_id in ref_ids:
                cypher_commands.append(f"MATCH (v1:Violation {{id: '{v_id}'}}), (v2:Violation {{id: '{r_id}'}}) MERGE (v1)-[:EXCEPT_IF]->(v2);")

    # 3. Tao Node Authority va lien ket voi Violation theo dung LUAT & HAN MUC
    cypher_commands.append("\n// --- TAO NODE AUTHORITY VA CAN_SANCTION ---")
    for auth in authorities:
        a_id = auth["node_id"]
        title = auth["authority"]["title"]
        raw_text = auth["authority"].get("raw_text", "")
        
        # Dung Regex boc tach cac Dieu tu raw_text
        articles = [int(a) for a in re.findall(r"Điều (\d+)", raw_text)]
        articles = list(set(articles)) # Loai trung

        limit = None
        if auth.get("authority") and auth["authority"].get("max_fine_limit"):
            limit = auth["authority"]["max_fine_limit"].get("max")
        
        limit_val = limit if limit is not None else "null"
        
        # Nạp Authority voi day du raw_text va danh sach Dieu duoc phat
        cypher_commands.append(
            f"MERGE (a:Authority {{id: '{a_id}'}}) "
            f"SET a.title = {escape_cypher(title)}, "
            f"a.limit = {limit_val}, "
            f"a.raw_text = {escape_cypher(raw_text)}, "
            f"a.applicable_articles = {articles};"
        )
        
        # Logic NOI QUAN HE [:CAN_SANCTION]:
        # Phai khop so Dieu VA nam trong han muc phat
        if articles:
            cypher_commands.append(
                f"MATCH (a:Authority {{id: '{a_id}'}}), (v:Violation) "
                f"WHERE v.article IN a.applicable_articles "
                f"AND (a.limit = 0 OR v.fine_max <= a.limit) "
                f"MERGE (a)-[:CAN_SANCTION]->(v);"
            )

    # Luu file
    with open(OUTPUT_CYPHER, "w", encoding="utf-8") as f:
        f.write("\n".join(cypher_commands))

    print(f"--- DA TAO XONG FILE CYPHER ---")
    print(f"File: {OUTPUT_CYPHER}")
    
    # TAT CHE DO BAO TRI
    if os.path.exists(".maintenance"):
        os.remove(".maintenance")
    print("[*] HE THONG DA MO LAI (MAINTENANCE MODE: OFF)")

if __name__ == "__main__":
    main()
