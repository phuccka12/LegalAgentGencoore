import json
import sys
import os
import re

def remove_accents(s):
    # Ham don gian de bo dau tieng Viet
    s = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
    s = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', s)
    s = re.sub(r'[ìíịỉĩ]', 'i', s)
    s = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', s)
    s = re.sub(r'[ùúụủũưừứựửữ]', 'u', s)
    s = re.sub(r'[ỳýỵỷỹ]', 'y', s)
    s = re.sub(r'[đ]', 'd', s)
    return s

def search_law(keyword):
    # Tim file ultra neu co, khong thi dung file enriched
    file_to_open = 'nghidinh168_knowledge_graph_ultra.json'
    if not os.path.exists(file_to_open):
        file_to_open = 'nghidinh168_knowledge_graph_enriched.json'
    
    try:
        with open(file_to_open, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Khong tim thay file du lieu. Vui long kiem tra lai.")
        return

    # Chuan hoa tu khoa (bo dau, viet thuong)
    query_normalized = remove_accents(keyword.lower())
    search_words = [w.strip() for w in query_normalized.split() if len(w) > 2]
    results = []

    for item in data:
        summary = item['behavior'].get('summary', '')
        raw_text = item['behavior'].get('raw_legal_text', '')
        slangs = item['behavior']['semantic_expansion'].get('slang', [])
        questions = item['behavior']['semantic_expansion'].get('common_questions', [])
        context = item['behavior'].get('real_world_context', '')
        
        # Gop tat ca vao 1 vung de tim kiem
        search_area = remove_accents(f"{summary} {raw_text} {' '.join(slangs)} {' '.join(questions)} {context}".lower())
        
        match_score = 0
        for word in search_words:
            if word in search_area:
                match_score += 1
        
        if match_score > 0:
            item['_score'] = match_score
            results.append(item)

    results.sort(key=lambda x: x.get('_score', 0), reverse=True)

    if not results:
        print(f"\n[!] Khong tim thay ket qua cho tu khoa: '{keyword}'")
        return

    print(f"\n🔍 Tim thay {len(results)} ket qua cho '{keyword}':")
    print("=" * 80)
    
    for i, res in enumerate(results[:3]):
        m = res['metadata']
        b = res['behavior']
        c = res['consequences']
        
        print(f"[{i+1}] Dieu {m['article']} - Khoan {m['clause']} {('- Diem ' + str(m['point'])) if m['point'] else ''}")
        print(f"📌 Noi dung: {b['summary']}")
        
        if c['fine_range'] and c['fine_range']['min']:
            print(f"💰 Muc phat: {c['fine_range']['min']:,} - {c['fine_range']['max']:,} VNĐ")
        else:
            print("💰 Muc phat: Khong co phat tien")
            
        if b['semantic_expansion']['slang']:
            print(f"🗣️ Tieng long: {', '.join(b['semantic_expansion']['slang'][:10])}...")
        
        if b['semantic_expansion'].get('common_questions'):
            print(f"❓ Cau hoi thuong gap: {b['semantic_expansion']['common_questions'][0]}")
            
        print("-" * 80)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        search_law(query)
    else:
        while True:
            query = input("\nNhap tu khoa muon tim (go 'exit' de thoat): ")
            if query.lower() == 'exit': break
            search_law(query)
