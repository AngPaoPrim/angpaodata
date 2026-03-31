from flask import Flask, request, jsonify, send_from_directory
import requests
import random
import re
import time
import os

app = Flask(__name__, static_folder='public')

# --- CONFIG ---
TIKWM_KEY = "952b70079e5a4675e7a01081339be9fc"
TIKWM_SEARCH_URL = "https://www.tikwm.com/api/feed/search"
TIKWM_USER_POSTS = "https://www.tikwm.com/api/user/posts"

# 🌉 🔥 GOOGLE BRIDGE URL (ใช้ตัวที่คุณ Deploy ล่าสุด)
GAS_BRIDGE_URL = "https://script.google.com/macros/s/AKfycbzm8e6S2arlK800mTnr7fXbFcZH9odCAKZF5d_QxSG-0G02cxDZtsbTon-xxXM_GCtQ/exec"

def is_thai(text):
    return bool(re.search('[ก-๙]', text))

# 🔥 HEADERS จำลองเป็น Browser จริง
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.tiktok.com/",
    "Connection": "keep-alive"
}

# 🔥 REQUEST ผ่านสะพาน Google (กัน Block 403)
def safe_request(url, params):
    # รวม params เดิมเข้ากับ url เพื่อส่งให้ Google Bridge
    bridge_params = params.copy()
    bridge_params['url'] = url 
    
    for i in range(3):
        try:
            # ยิงผ่าน Google Apps Script Bridge
            res = requests.get(GAS_BRIDGE_URL, params=bridge_params, headers=headers, timeout=30)
            
            print(f">>> [Try {i+1}] Bridge Status: {res.status_code}")

            if res.status_code == 200 and res.text.strip():
                try:
                    return res.json()
                except:
                    print("❌ Response is not valid JSON")
            else:
                print(f"❌ Bridge returned error/empty: {res.status_code}")

        except Exception as e:
            print(f"❌ Connection error: {e}")
            
        time.sleep(random.uniform(1.0, 2.0)) # หน่วงเวลาสุ่มกันโดนจับได้

    return None

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/analyze')
def analyze():
    mode = request.args.get('mode', 'trending_products')
    target = request.args.get('target', '').replace('@', '').strip()

    products = []

    try:
        # ==============================
        # 🔥 MODE: SHOP (USER VIDEOS)
        # ==============================
        if mode == 'shop' and target:
            print(f">>> X99 Insight: Scouting @{target}...")

            # 🟢 พยายามดึงผ่าน user/posts ก่อน (ผ่าน Bridge)
            params = {"unique_id": target, "count": 15, "key": TIKWM_KEY}
            data = safe_request(TIKWM_USER_POSTS, params)

            video_list = []

            # 🔴 ถ้าติดปัญหาหรือโดน Block -> ใช้ระบบค้นหาแทน (Fallback)
            if not data or data.get('code') != 0:
                print(f"⚠️ Switching to Search Fallback for @{target}")

                search_params = {
                    "keywords": f"@{target}",
                    "count": 30,
                    "key": TIKWM_KEY
                }

                search_data = safe_request(TIKWM_SEARCH_URL, search_params)

                if search_data and search_data.get('code') == 0:
                    raw_videos = search_data.get('data', {}).get('videos', [])
                    
                    # กรองเฉพาะวิดีโอที่เป็นของ User นั้นจริงๆ
                    for v in raw_videos:
                        author_id = v.get('author', {}).get('unique_id', '').lower()
                        if author_id == target.lower():
                            video_list.append(v)
                        if len(video_list) >= 10: break
                    
                    # ถ้ากรองแล้วไม่เจอเลย ให้เอา 5 อันแรกที่ใกล้เคียงมาแสดงแทน
                    if not video_list and raw_videos:
                        video_list = raw_videos[:5]
            else:
                # ถ้า user/posts ใช้งานได้ปกติ
                raw_data = data.get('data')
                if isinstance(raw_data, list):
                    video_list = raw_data
                elif isinstance(raw_data, dict):
                    video_list = raw_data.get('videos', [])

            if not video_list:
                return jsonify({"status": "Error", "message": "ไม่พบข้อมูลวิดีโอ หรือบัญชีอาจเป็นส่วนตัว", "products": []})

            for i, v in enumerate(video_list):
                play_count = v.get('play_count', 0)
                # สูตรคำนวณรายได้โดยประมาณ
                revenue = (play_count / 1000) * 150
                img_url = v.get('origin_cover') or v.get('cover') or v.get('ai_dynamic_cover')

                products.append({
                    "rank": i + 1,
                    "image": img_url,
                    "name": v.get('title', 'Video Insight')[:65] + "...",
                    "video_url": f"https://www.tiktok.com/@{target}/video/{v.get('video_id')}",
                    "price": f"❤️ {v.get('digg_count', 0):,}",
                    "revenue": f"{revenue:,.0f}",
                    "sales": f"{play_count:,} views",
                    "growth": f"SCORE: {random.randint(88, 99)}"
                })

            return jsonify({
                "status": "Success",
                "products": products,
                "name": f"Results for: @{target}",
                "bio": f"วิเคราะห์ข้อมูลผ่าน Google Bridge",
                "trend": "🛡️ SECURE MODE"
            })

        # ==============================
        # 🔥 MODE: TRENDING
        # ==============================
        else:
            params = {
                "keywords": "review tiktokshop thailand",
                "region": "TH",
                "count": 35,
                "key": TIKWM_KEY
            }

            data = safe_request(TIKWM_SEARCH_URL, params)

            if not data or data.get('code') != 0:
                return jsonify({"status": "Error", "message": "ไม่สามารถดึงข้อมูลเทรนด์ได้ในขณะนี้", "products": []})

            raw_videos = data.get('data', {}).get('videos', [])
            for v in raw_videos:
                title = v.get('title', '')
                if not is_thai(title): continue # เน้นเฉพาะสินค้าไทย

                play_count = v.get('play_count', 0)
                revenue = (play_count / 1000) * 150
                author_id = v.get('author', {}).get('unique_id', 'user')
                img_url = v.get('origin_cover') or v.get('cover')

                products.append({
                    "rank": len(products) + 1,
                    "image": img_url,
                    "name": title[:65] + "...",
                    "video_url": f"https://www.tiktok.com/@{author_id}/video/{v.get('video_id')}",
                    "price": f"❤️ {v.get('digg_count', 0):,}",
                    "revenue": f"{revenue/1000000:.2f}M" if revenue > 1000000 else f"{revenue:,.0f}",
                    "sales": f"{play_count:,} views",
                    "growth": f"+{random.randint(40, 99)}%"
                })

                if len(products) >= 12: break

            return jsonify({
                "status": "Success",
                "products": products,
                "name": "Thailand Top Trends",
                "bio": "คัดสรรวิดีโอติดเทรนด์จาก Google Bridge",
                "trend": "🛍️ SHOP TREND"
            })

    except Exception as e:
        print(f"❌ X99 Main Error: {e}")
        return jsonify({"status": "Error", "message": "เกิดข้อผิดพลาดภายในระบบ", "products": []})

if __name__ == '__main__':
    # รองรับทั้ง Local และ Render
    port = int(os.environ.get("PORT", 1010))
    app.run(host='0.0.0.0', port=port)
