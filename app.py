from flask import Flask, request, jsonify, send_from_directory
import requests
import random
import re

app = Flask(__name__, static_folder='public')

# --- [ CONFIG ] ANGPAO X99 - TIKWM LICENSED ---
TIKWM_KEY = "952b70079e5a4675e7a01081339be9fc"
TIKWM_SEARCH_URL = "https://www.tikwm.com/api/feed/search"
TIKWM_USER_POSTS = "https://www.tikwm.com/api/user/posts"

def is_thai(text):
    return bool(re.search('[ก-๙]', text))

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/analyze')
def analyze():
    mode = request.args.get('mode', 'trending_products')
    target = request.args.get('target', '').replace('@', '').strip()
    
    products = []

    try:
        # --- MODE: SHOP INSIGHTS (ส่องคู่แข่ง) ---
        if mode == 'shop' and target:
            print(f">>> X99 Insight: Scouting @{target}...")
            params = {"unique_id": target, "count": 15, "key": TIKWM_KEY}
            response = requests.get(TIKWM_USER_POSTS, params=params, timeout=30)
            data = response.json()
            
            if data.get('code') != 0:
                return jsonify({"status": "Error", "message": data.get('msg', 'API Error'), "products": []})

            # FIX: ตรวจสอบโครงสร้าง Data ให้ยืดหยุ่น
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
            
            return jsonify({"status": "Success", "products": products, "name": f"Insights: @{target}", "bio": f"สแกนวิดีโอของ @{target} สำเร็จ", "trend": "🔍 SCOUTING ACTIVE"})

        # --- MODE: TRENDING (ดึงเทรนด์สินค้าไทย) ---
        else:
            params = {"keywords": "review tiktokshop thailand", "region": "TH", "count": 30, "key": TIKWM_KEY}
            response = requests.get(TIKWM_SEARCH_URL, params=params, timeout=30)
            data = response.json()

            if data.get('code') == 0:
                video_list = data.get('data', {}).get('videos', [])
                for v in video_list:
                    title = v.get('title', '')
                    if not is_thai(title): continue
                    
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
                return jsonify({"status": "Success", "products": products, "name": "Thailand Top Trends", "bio": "คัดวิดีโอสินค้าไทยที่เป็นไวรัล", "trend": "🛍️ SHOP TREND"})

    except Exception as e:
        print(f"❌ X99 Error: {e}")
        return jsonify({"status": "Error", "message": str(e), "products": []})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1010, debug=True)