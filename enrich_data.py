import google.generativeai as genai
import json
import time
import os
import re

# ==========================================
# DANH SÁCH 4 KEY CỦA BẠN
# ==========================================
KEYS = [
    "AIzaSyDcN9LLYR04McNF-veS3UVsHV-IH6nzV9I",
    "AIzaSyDr4dDJCmEXQiDql2k_Pjzd78SFsO_1TvM",
    "AIzaSyCFdmBvwwiuqa7LDoQsmYIw79RSIFCL4gs",
    "AIzaSyBd_YVbTpTrGTx-NopN_V8mXiji_S59rjo"
]
current_key_idx = 0

def configure_next_key():
    global current_key_idx, model
    key = KEYS[current_key_idx]
    genai.configure(api_key=key)
    # Dung gemini-flash-latest (1.5) de co quota 1500/day
    model = genai.GenerativeModel('gemini-flash-latest', generation_config={
        "response_mime_type": "application/json",
        "temperature": 0.7
    })
    print(f"--- Su dung Key {current_key_idx + 1}/{len(KEYS)} ---")
    current_key_idx = (current_key_idx + 1) % len(KEYS)

# Khoi tao key dau tien
configure_next_key()

INPUT_FILE = "nghidinh168_knowledge_graph_final_v2.json"
OUTPUT_FILE = "nghidinh168_knowledge_graph_enriched.json"

ENRICH_PROMPT = """
Bạn là một chuyên gia về đời sống giao thông tại Việt Nam. 
Dựa vào nội dung tóm tắt hành vi vi phạm pháp luật sau đây, hãy cung cấp dữ liệu bổ sung theo định dạng JSON:

NỘI DUNG: {summary}

YÊU CẦU JSON TRẢ VỀ:
{{
  "slang": ["3-5 từ lóng hoặc cách gọi bình dân của người dân về lỗi này"],
  "synonyms": ["2-3 từ đồng nghĩa chuyên môn khác"],
  "tools": ["Các thiết bị hoặc công cụ thực tế CSGT dùng để phát hiện/xử lý lỗi này"]
}}

LƯU Ý: 
- Nếu hành vi quá chung chung hoặc không có tiếng lóng phù hợp, hãy để mảng rỗng [].
- Tiếng lóng phải gần gũi với đời sống (ví dụ: "quá tốc độ" -> "mát ga", "bắn tốc độ", "rụng gậy"...).
"""

def main():
    if not os.path.exists(INPUT_FILE):
        print("Khong tim thay file nguon!")
        return

    # Load data (neu da co file enriched thi load de tiep tuc - Resume)
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

    print(f"[*] Bat dau lam giau du lieu cho {len(data)} nodes...")
    
    count = 0
    for item in data:
        art_num = item.get("metadata", {}).get("article", 0)
        
        # Chi lam giau cho cac Dieu vi pham (6-40) va nhung node CHUA co slang
        slangs = item["behavior"]["semantic_expansion"].get("slang", [])
        if 6 <= art_num <= 40 and not slangs:
            summary = item["behavior"]["summary"]
            count += 1
            print(f"[{count}] Enriching Art {art_num}...")
            
            success = False
            attempts_for_node = 0
            while not success and attempts_for_node < len(KEYS):
                try:
                    response = model.generate_content(ENRICH_PROMPT.format(summary=summary))
                    enriched_info = json.loads(response.text)
                    
                    item["behavior"]["semantic_expansion"]["slang"] = enriched_info.get("slang", [])
                    item["behavior"]["semantic_expansion"]["synonyms"].extend(enriched_info.get("synonyms", []))
                    item["legal_procedure"]["evidence_requirements"]["tools"] = enriched_info.get("tools", [])
                    item["behavior"]["semantic_expansion"]["synonyms"] = list(set(item["behavior"]["semantic_expansion"]["synonyms"]))
                    
                    success = True
                    # Luu sau moi node de chac chan
                    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    time.sleep(4) # Tang len 4s de tranh RPM (15 req/min)
                except Exception as e:
                    attempts_for_node += 1
                    err_msg = str(e)
                    if "429" in err_msg:
                        print(f"   [!] Key het han muc. Dang doi sang Key tiep theo...")
                        configure_next_key()
                    else:
                        print(f"   [!] Error at node {item['node_id']}: {e}")
                        break

    print(f"\n[DONE] Enriched {count} nodes. Final file: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
