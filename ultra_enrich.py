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
    model = genai.GenerativeModel('gemini-flash-latest', generation_config={
        "response_mime_type": "application/json",
        "temperature": 0.9 # Tang temperature len de cuc ky sang tao
    })
    print(f"--- Su dung Key {current_key_idx + 1}/{len(KEYS)} ---")
    current_key_idx = (current_key_idx + 1) % len(KEYS)

configure_next_key()

INPUT_FILE = "nghidinh168_knowledge_graph_enriched.json"
OUTPUT_FILE = "nghidinh168_knowledge_graph_ultra.json"

# PROMPT SIEU CAP: Đắp da thịt cực dày
ULTRA_PROMPT = """
Bạn là một chuyên gia thực thụ về luật giao thông và văn hóa vỉa hè tại Việt Nam.
Nhiệm vụ: Chuyển đổi nội dung luật khô khan thành bộ tri thức sống động, gần gũi với người dân.

NỘI DUNG LUẬT: {summary}

YÊU CẦU DỮ LIỆU (PHẢI THẬT CHI TIẾT):
1. slang: Ít nhất 10-15 từ. Bao gồm tiếng lóng vùng miền (Bắc/Trung/Nam), từ ngữ của giới trẻ, dân xế lâu năm.
2. common_questions: 5-7 câu hỏi thực tế nhất. Phải thể hiện đúng tâm lý người dân khi bị bắt (lo sợ, tìm cách giải thích, hỏi về thủ tục, hỏi về mức phạt...).
3. real_world_context: Viết 1 đoạn văn 3-4 câu mô tả một tình huống "oái oăm" ngoài đời dẫn đến lỗi này.

TRẢ VỀ JSON:
{{
  "slang": [],
  "common_questions": [],
  "real_world_context": ""
}}
"""

def main():
    if not os.path.exists(INPUT_FILE):
        print("Khong tim thay file nguon!")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"[*] BAT DAU CHIEN DICH ULTRA-ENRICHMENT CHO {len(data)} NODES...")
    
    count = 0
    for item in data:
        art_num = item.get("metadata", {}).get("article", 0)
        
        # Chi lam giau cho cac Dieu vi pham (6-40)
        if 6 <= art_num <= 40:
            summary = item["behavior"]["summary"]
            count += 1
            print(f"[{count}] Ultra-Enriching Art {art_num}...")
            
            try:
                response = model.generate_content(ULTRA_PROMPT.format(summary=summary))
                info = json.loads(response.text)
                
                # Gap doi slang
                existing_slang = item["behavior"]["semantic_expansion"].get("slang", [])
                new_slang = info.get("slang", [])
                item["behavior"]["semantic_expansion"]["slang"] = list(set(existing_slang + new_slang))
                
                # Them cac truong thong tin moi
                item["behavior"]["semantic_expansion"]["common_questions"] = info.get("common_questions", [])
                item["behavior"]["real_world_context"] = info.get("real_world_context", "")
                
                if count % 5 == 0:
                    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                
                time.sleep(3) 
            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg:
                    configure_next_key()
                else:
                    print(f"   [!] Error: {e}")
                    time.sleep(2)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n[DONE] Ultra-Enriched. Final file: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
