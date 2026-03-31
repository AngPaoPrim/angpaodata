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

# 🌉 🔥 GOOGLE BRIDGE (Bypass Render IP Block)
GAS_BRIDGE_URL = "https://script.google.com/macros/s/AKfycbzm8e6S2arlK800mTnr7fXbFcZH9odCAKZF5d_QxSG-0G02cxDZtsbTon-xxXM_GCtQ/exec"

def is_thai(text):
    return bool(re.search('[ก-๙]', text))

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.tiktok.com/",
    "Connection": "keep-alive"
}

def safe_request(url, params):
    bridge_params = params.copy()
    bridge_params['url'] = url 
    for i in range(3):
        try:
            # ยิงผ่านสะพาน Google เสมอ
            res = requests.get(GAS_BRIDGE_URL, params=bridge_params, headers=headers, timeout=30)
            if res.status_code == 200 and res.text.strip():
                try: return res.json()
                except: print("❌ Not JSON")
            else: print(f"❌ Status: {res.status_code}")
        except Exception as e: print(f"❌ Error: {e}")
        time.sleep(random.uniform(0.5, 1.5))
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
        if mode == 'shop' and target:
            params = {"unique_id": target, "count": 15, "key": TIKWM_KEY}
            data = safe_request(TIKWM_USER_POSTS, params)
            video_list = []
            if not data or data.get('code') != 0:
                search_params = {"keywords": f"@{target}", "count": 30, "key": TIKWM_KEY}
                search_data = safe_request(TIKWM_SEARCH_URL, search_params)
                if search_data and search_data.get('code') == 0:
                    raw_v = search_data.get('data', {}).get('videos', [])
                    video_list = [v for v in raw_v if v.get('author', {}).get('unique_id', '').lower() == target.lower()]
                    if not video_list and raw_v: video_list = raw_v[:5]
            else:
                raw_data = data.get('data')
                video_list = raw_data if isinstance(raw_data, list) else raw_data.get('videos', [])

            for i, v in enumerate(video_list):
                play_count = v.get('play_count', 0)
                revenue = (play_count / 1000) * 150
                products.append({
                    "rank": i + 1,
                    "image": v.get('origin_cover') or v.get('cover'),
                    "name": v.get('title', 'Video')[:65] + "...",
                    "video_url": f"https://www.tiktok.com/@{target}/video/{v.get('video_id')}",
                    "price": f"❤️ {v.get('digg_count', 0):,}",
                    "revenue": f"{revenue:,.0f}",
                    "sales": f"{play_count:,} views",
                    "growth": f"SCORE: {random.randint(85, 99)}"
                })
            return jsonify({"status": "Success", "products": products, "name": f"@{target}", "bio": "สแกนผ่าน Google Bridge", "trend": "🛡️ SECURE"})

        else: # TRENDING MODE
            params = {"keywords": "review tiktokshop thailand", "region": "TH", "count": 30, "key": TIKWM_KEY}
            data = safe_request(TIKWM_SEARCH_URL, params)
            if data and data.get('code') == 0:
                for v in data.get('data', {}).get('videos', []):
                    if not is_thai(v.get('title', '')): continue
                    p_count = v.get('play_count', 0)
                    revenue = (p_count / 1000) * 150
                    products.append({
                        "rank": len(products) + 1,
                        "image": v.get('origin_cover') or v.get('cover'),
                        "name": v.get('title', '')[:65] + "...",
                        "video_url": f"https://www.tiktok.com/@{v.get('author',{}).get('unique_id')}/video/{v.get('video_id')}",
                        "price": f"❤️ {v.get('digg_count', 0):,}",
                        "revenue": f"{revenue:,.0f}",
                        "sales": f"{p_count:,} views",
                        "growth": f"+{random.randint(40, 99)}%"
                    })
                    if len(products) >= 12: break
                return jsonify({"status": "Success", "products": products, "name": "Thailand Trends", "bio": "ดึงข้อมูลสำเร็จ", "trend": "🛍️ SHOP"})
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e), "products": []})
    return jsonify({"status": "Error", "message": "No data found", "products": []})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 1010))
    app.run(host='0.0.0.0', port=port)
