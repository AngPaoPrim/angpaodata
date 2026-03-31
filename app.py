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

# 🌉 🔥 GOOGLE BRIDGE URL (ใส่ลิงก์ /exec ที่คุณทำเสร็จแล้วตรงนี้)
GAS_BRIDGE_URL = "https://script.google.com/macros/s/AKfycbzm8e6S2arlK800mTnr7fXbFcZH9odCAKZF5d_QxSG-0G02cxDZtsbTon-xxXM_GCtQ/exec"

def is_thai(text):
    return bool(re.search('[ก-๙]', text))

# 🔥 HEADERS กัน block
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.tiktok.com/",
    "Origin": "https://www.tiktok.com",
    "Connection": "keep-alive"
}

# 🔥 REQUEST ผ่าน Google Bridge กันพัง + bypass 403
def safe_request(url, params):
    # เตรียม params สำหรับส่งให้ Google Bridge
    bridge_params = params.copy()
    bridge_params['url'] = url  # บอก Google ว่าจะให้ยิงไปที่ไหน
    
    for i in range(3):
        try:
            # 💡 เปลี่ยนจากยิงตรง เป็นยิงผ่านสะพาน Google
            res = requests.get(GAS_BRIDGE_URL, params=bridge_params, headers=headers, timeout=30)

            print(f">>> Bridge Status: {res.status_code} (Try: {i+1})")

            if res.status_code == 200 and res.text.strip():
                try:
                    return res.json()
                except:
                    print("❌ ไม่ใช่ JSON:", res.text[:100])
            else:
                print(f"❌ Bridge Error หรือ Response ว่าง")

        except Exception as e:
            print("❌ Request Error:", e)
        
        time.sleep(1) # รอ 1 วินาทีก่อนลองใหม่

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

            # 🟢 ลอง user/posts ผ่าน Bridge
            params = {"unique_id": target, "count": 15, "key": TIKWM_KEY}
            data = safe_request(TIKWM_USER_POSTS, params)

            video_list = []

            # 🔴 ถ้าโดน block → fallback search ผ่าน Bridge
            if not data or data.get('code') != 0:
                print("⚠️ FALLBACK → feed/search via Bridge")

                search_params = {
                    "keywords": f"@{target}",
                    "count": 30,
                    "key": TIKWM_KEY
                }

                search_data = safe_request(TIKWM_SEARCH_URL, search_params)

                if not search_data or search_data.get('code') != 0:
                    return jsonify({"status": "Error", "message": "API ล้มทั้งคู่ (Bridge Blocked?)", "products": []})

                raw_videos = search_data.get('data', {}).get('videos', [])

                for v in raw_videos:
                    author = v.get('author', {}).get('unique_id', '').lower()
                    if author == target.lower():
                        video_list.append(v)
                    if len(video_list) >= 10:
                        break
            else:
                raw_data = data.get('data')
                if isinstance(raw_data, list):
                    video_list = raw_data
                elif isinstance(raw_data, dict):
                    video_list = raw_data.get('videos', [])
                else:
                    video_list = []

            for i, v in enumerate(video_list):
                play_count = v.get('play_count', 0)
                revenue = (play_count / 1000) * 150
                img_url = v.get('origin_cover') or v.get('cover') or v.get('ai_dynamic_cover')

                products.append({
                    "rank": i + 1,
                    "image": img_url,
                    "name": v.get('title', 'No Title')[:65] + "...",
                    "video_url": f"https://www.tiktok.com/@{target}/video/{v.get('video_id')}",
                    "price": f"❤️ {v.get('digg_count', 0):,}",
                    "revenue": f"{revenue:,.0f}",
                    "sales": f"{play_count:,} views",
                    "growth": f"SCORE: {random.randint(85, 99)}"
                })

            return jsonify({
                "status": "Success",
                "products": products,
                "name": f"Insights: @{target}",
                "bio": f"สแกนวิดีโอผ่าน Google Bridge",
                "trend": "🛡️ SECURE MODE"
            })

        # ==============================
        # 🔥 MODE: TRENDING
        # ==============================
        else:
            params = {
                "keywords": "review tiktokshop thailand",
                "region": "TH",
                "count": 30,
                "key": TIKWM_KEY
            }

            data = safe_request(TIKWM_SEARCH_URL, params)

            if not data:
                return jsonify({"status": "Error", "message": "Bridge ไม่ตอบกลับ", "products": []})

            if data.get('code') == 0:
                video_list = data.get('data', {}).get('videos', [])

                for v in video_list:
                    title = v.get('title', '')
                    if not is_thai(title):
                        continue

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

                    if len(products) >= 12:
                        break

                return jsonify({
                    "status": "Success",
                    "products": products,
                    "name": "Thailand Top Trends",
                    "bio": "คัดวิดีโอผ่าน Google Bridge",
                    "trend": "🛍️ SHOP TREND"
                })

    except Exception as e:
        print(f"❌ X99 Error: {e}")
        return jsonify({"status": "Error", "message": str(e), "products": []})

if __name__ == '__main__':
    # สำหรับรันบน Render หรือ Local
    port = int(os.environ.get("PORT", 1010))
    app.run(host='0.0.0.0', port=port, debug=True)
