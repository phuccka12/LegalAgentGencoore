import google.generativeai as genai
import json
import time
import os
import re

# ==========================================
# CẤU HÌNH THÔNG SỐ
# ==========================================
# Dung Key moi nhat cua ban
API_KEY = "AIzaSyASGJBnZg3NNrCYtuUAF2EPldD05kt9gvs" 
genai.configure(api_key=API_KEY)

# Danh sách các model để rotate khi hết quota
AVAILABLE_MODELS = [
    'gemini-2.5-flash',
    'gemini-2.0-flash',
    'gemini-flash-latest',
    'gemini-pro-latest'
]
current_model_idx = 0
model = genai.GenerativeModel(AVAILABLE_MODELS[current_model_idx], generation_config={"response_mime_type": "application/json"})

INPUT_FILE = "nghidinh168.txt"
OUTPUT_FILE = "nghidinh168_knowledge_graph.json"

# Danh sách 6 Điều cuối cùng cần hoàn thiện
MISSING_ARTICLES = [1, 2, 3, 4, 5, 41]

MASTER_PROMPT = """
Bạn là một Chuyên gia Pháp lý và Kỹ sư Dữ liệu. Hãy trích xuất tri thức từ văn bản luật sang định dạng JSON Array để nạp vào Knowledge Graph.

YÊU CẦU:
1. Trả về một JSON Array, mỗi phần tử là một "Node" tri thức.
2. Cấu trúc mỗi Node PHẢI tuân thủ:
{
  "node_id": "ND168_Art[Số]_C[Số]_p[Chữ]",
  "metadata": {
    "article": [Số],
    "clause": [Số],
    "point": "[Chữ]"
  },
  "behavior": {
    "summary": "Tóm tắt ngắn gọn hành vi vi phạm hoặc quyền hạn",
    "raw_legal_text": "Toàn văn nội dung pháp lý của điểm/khoản đó",
    "semantic_expansion": {
      "synonyms": [],
      "slang": []
    }
  },
  "consequences": {
    "fine_range": {
      "min": [Số],
      "max": [Số],
      "suggested": [Số - trung bình cộng]
    },
    "point_deduction": [Số điểm bị trừ, nếu không có thì 0],
    "remedial_measures": [Danh sách các biện pháp khắc phục hậu quả hoặc hình phạt bổ sung]
  },
  "legal_procedure": {
    "evidence_requirements": {
      "mandatory": [],
      "tools": []
    }
  },
  "inference_logic": {
    "exceptions": [Các trường hợp ngoại lệ "trừ...", "ngoài..."],
    "overrides": [Các trường hợp đè lên quy định khác]
  }
}

LƯU Ý QUAN TRỌNG:
- Nếu là Điều khoản về "Thẩm quyền" (Authority) hoặc "Thủ tục" (Procedure), hãy đặt mức phạt (fine_range) là null hoặc 0, và tập trung vào phần "behavior.summary" để mô tả quyền hạn/thủ tục.
- Giữ nguyên văn phong pháp lý trong "raw_legal_text".
- Tự tính toán "suggested" fine bằng trung bình cộng của min và max.
- Nếu một khoản không có điểm (point), hãy để "point": null.
- Trích xuất ĐẦY ĐỦ các ngoại lệ vào phần "exceptions".
"""

def rotate_model():
    global current_model_idx, model
    current_model_idx = (current_model_idx + 1) % len(AVAILABLE_MODELS)
    print(f"--- Chuyen sang model: {AVAILABLE_MODELS[current_model_idx]} ---")
    model = genai.GenerativeModel(AVAILABLE_MODELS[current_model_idx], generation_config={"response_mime_type": "application/json"})

def extract_content(text, article_num, clause_num=None):
    clause_info = f" (Khoan {clause_num})" if clause_num else ""
    print(f"--- Dang xu ly Dieu {article_num}{clause_info} ---")
    
    extra_context = f"Luu y: Day la noi dung thuoc Dieu {article_num}."
    if clause_num:
        extra_context += f" Day la Khoan {clause_num}."
        
    attempt = 0
    while True:
        attempt += 1
        try:
            response = model.generate_content(f"{MASTER_PROMPT}\n\n{extra_context}\n\nNOI DUNG:\n{text}")
            return json.loads(response.text)
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg:
                match = re.search(r"retry in ([\d\.]+)s", err_msg)
                if match:
                    wait_time = int(float(match.group(1))) + 5 
                else:
                    wait_time = 60
                
                print(f"   [!] Rate Limit. Cho {wait_time}s (Luot {attempt})...")
                time.sleep(wait_time)
                
                if attempt % 3 == 0:
                    rotate_model()
            else:
                print(f"   !!! Loi nghiem trong tai Dieu {article_num}: {e}")
                return None

def main():
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            try:
                all_data = json.load(f)
            except:
                all_data = []
    else:
        all_data = []
    
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    articles_text = re.split(r'\n(?=Điều \d+\.)', content)

    for art_num in MISSING_ARTICLES:
        # Check xem Dieu nay da co chua
        exists = any(item.get("metadata", {}).get("article") == art_num for item in all_data)
        if exists:
            print(f"--- Dieu {art_num} da ton tai, bo qua. ---")
            continue
        
        print(f"\n>>> BAT DAU VA DIEU {art_num}")
        
        target_text = ""
        for text in articles_text:
            if f"Điều {art_num}." in text[:15]:
                target_text = text
                break
        
        if not target_text: continue

        # Xu ly dac biet cho cac dieu dai (neu can)
        # Dieu 1-5 va 41 khong qua dai nen co the extract ca dieu
        nodes = extract_content(target_text, art_num)
        if nodes:
            if isinstance(nodes, list): all_data.extend(nodes)
            else: all_data.append(nodes)
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
            print(f"   [DONE] Va xong Dieu {art_num}")
        
        time.sleep(10) 

    print("\n=== HOAN TAT 100%. KIEM TRA FILE: " + OUTPUT_FILE)

if __name__ == "__main__":
    main()
