import json
import os

INPUT_FILE = "nghidinh168_violations_final.json"
OUTPUT_FILE = "nghidinh168_violations_labeled.json"

def get_vehicle_category(art_num):
    # Mapping chi tiet theo toan bo chuong hoi cua Nghi dinh 168
    if art_num == 6: return "xe_mo_to_xe_gan_may"
    if art_num == 7: return "xe_o_to"
    if art_num == 8: return "may_keo_xe_chuyen_dung"
    if art_num == 9: return "xe_tho_so_xe_dap"
    if 11 <= art_num <= 14: return "van_tai_hanh_khach_hang_hoa"
    if 15 <= art_num <= 20: return "duong_sat"
    if 24 <= art_num <= 31: return "chu_phuong_tien"
    if 32 <= art_num <= 33: return "dang_kiem"
    if 34 <= art_num <= 38: return "dao_tao_sat_hach"
    if 39 <= art_num <= 40: return "nhan_vien_duong_sat"
    return "doi_tuong_khac"

def get_violation_group(summary, raw_text, slangs):
    # Phan loai nhom loi dua tren tu khoa (Logic Ontological)
    text = (summary + " " + raw_text + " " + " ".join(slangs)).lower()
    
    groups = []
    if any(k in text for k in ["tốc độ", "mát ga", "chạy nhanh"]): groups.append("toc_do")
    if any(k in text for k in ["nồng độ cồn", "rượu bia", "thổi kèn", "nhậu"]): groups.append("nong_do_con")
    if any(k in text for k in ["ma túy", "chất kích thích"]): groups.append("ma_tuy")
    if any(k in text for k in ["làn đường", "vạch kẻ", "ngược chiều", "đường cấm"]): groups.append("quy_tac_duong_bo")
    if any(k in text for k in ["giấy phép", "bằng lái", "đăng ký", "đăng kiểm"]): groups.append("giay_to_phap_ly")
    if any(k in text for k in ["đèn tín hiệu", "đèn đỏ"]): groups.append("tin_hieu_giao_thong")
    if any(k in text for k in ["thiết bị", "còi", "đèn", "gương", "kết cấu"]): groups.append("thiet_bi_ky_thuat")
    
    return groups if groups else ["nhom_khac"]

def get_severity(fine_max):
    if fine_max is None: return "khong_xac_dinh"
    if fine_max <= 1000000: return "thap"
    if fine_max <= 5000000: return "trung_binh"
    if fine_max <= 15000000: return "cao"
    return "rat_cao"

def main():
    if not os.path.exists(INPUT_FILE):
        print("Khong tim thay file nguon!")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"[*] Dang tien hanh gan nhan (Labeling) cho {len(data)} nodes...")

    for item in data:
        art_num = item["metadata"]["article"]
        
        # Check an toan fine_range
        fine_max = None
        if item.get("consequences") and item["consequences"].get("fine_range"):
            fine_max = item["consequences"]["fine_range"].get("max")
        
        # 1. Gan nhan phuong tien
        item["labels"] = {
            "vehicle_category": get_vehicle_category(art_num),
            "violation_groups": get_violation_group(
                item["behavior"]["summary"], 
                item["behavior"]["raw_legal_text"],
                item["behavior"]["semantic_expansion"].get("slang", [])
            ),
            "severity_level": get_severity(fine_max)
        }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"--- DA GAN NHAN XONG ---")
    print(f"File moi: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
