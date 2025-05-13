from flask import Flask, jsonify, render_template
import requests
import threading
import time
import logging
from waitress import serve
from dotenv import load_dotenv
import os
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="assets", static_url_path="/assets")
load_dotenv()

class Service:
    def __init__(self, name, url, description, icon, icon_dark=None, export=True, host=None):
        self.name = name
        self.host = host
        self.url = url
        self.description = description
        self.icon = icon
        self.icon_dark = icon_dark
        self.export = export
        self.status = "up"
        self.previous_status = "up"
        self.last_checked = time.time()
        self.response_code = 200
        self.response_time = 0
        self.error = None

    def __str__(self):
        if self.host:
            return f"{self.name}@{self.host}"
        else:
            return self.name
        
    def check_service_health(self):
        self.previous_status = self.status
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            # First try a HEAD request which is faster
            start_time = time.time()
            response = requests.head(self.url, timeout=5, headers=headers, allow_redirects=True)
            status_code = response.status_code
            
            # If the HEAD request fails or returns non-2xx, try a GET request
            if status_code >= 400:
                start_time = time.time()
                response = requests.get(self.url, timeout=5, headers=headers, allow_redirects=True)
                status_code = response.status_code
            
            # Calculate response time
            response_time = (time.time() - start_time) * 1000
            self.response_time = int(response_time)
            
            if status_code < 400 or (status_code in [401, 403]):
                if response_time > SLOW_THRESHOLD:
                    self.status = "slow"
                else:
                    self.status = "up"
                self.response_code = status_code
            else:
                self.response_time = None
                self.status = "down"
                self.response_code = status_code
                self.error = response.text
        except requests.RequestException as e:
            self.status = "down"
            self.response_code = None
            self.response_time = None
            self.error = str(e)
        
        self.last_checked = time.time()
        logger.info(f"Health check for {self.name}: {self.status} (Code: {self.response_code}, Time: {self.response_time}s)")
    
    def is_newly_down(self):
        return self.status == "down" and self.previous_status != "down"

    def is_recovered(self):
        return self.status != "down" and self.previous_status == "down"

# Load services from YAML file
def load_services():
    try:
        with open("services.yaml", "r") as file:
            data = yaml.safe_load(file)
            services_list = []
            
            # Convert each service dict to a Service object
            for svc in data.get("services", []):
                service = Service(
                    name=svc.get("name"),
                    host=svc.get("host"),
                    url=svc.get("url"),
                    description=svc.get("description"),
                    icon=svc.get("icon"),
                    icon_dark=svc.get("icon_dark"),
                    export=svc.get("export")
                )
                services_list.append(service)
                
            return services_list
    except Exception as e:
        logger.error(f"Error loading services: {e}")
        return []

# Services to monitor
services = load_services()

# Response time threshold for slow status (in milliseconds)
SLOW_THRESHOLD = float(os.getenv("SLOW_THRESHOLD", 1000))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health-status')
def health_status():
    services_data = []
    for service in services:
        services_data.append({
            "name": service.name,
            "host": service.host,
            "url": service.url,
            "description": service.description,
            "icon": service.icon,
            "icon_dark": service.icon_dark,
            "status": service.status,
            "previous_status": service.previous_status,
            "last_checked": service.last_checked,
            "response_code": service.response_code,
            "response_time": service.response_time,
            "error": service.error,
            "export": service.export
        })
    return jsonify(services_data)

def send_notification(title, message, priority=5):
    data = {
        "title": title,
        "priority": priority,
        "message": message
    }
    response = requests.post(f'{os.getenv("NOTIFY_URL")}?token={os.getenv("NOTIFY_TOKEN")}', json=data)

    return response.json()

def health_check_worker():
    while True:
        newly_down_services = []
        recovered_services = []
        
        for service in services:
            service.check_service_health()
            
            # Check for state transitions
            if service.is_newly_down():
                newly_down_services.append(service)
            elif service.is_recovered():
                recovered_services.append(service)

        if newly_down_services:
            message = f"⚠️ Services down: {', '.join([str(s) for s in newly_down_services])}"
            notify_resp = send_notification("Service Down Alert", message, priority=9)
            logger.info(f"Down notification sent: {notify_resp}")
        
        if recovered_services:
            message = f"✅ Services recovered: {', '.join([str(s) for s in recovered_services])}"
            notify_resp = send_notification("Service Recovery", message, priority=2)
            logger.info(f"Recovery notification sent: {notify_resp}")
        
        # Sleep for 5 minutes before next check
        time.sleep(int(os.getenv("CHECK_INTERVAL", 300)))


is_preproduction = os.getenv("PREPRODUCTION", "false").lower() == "true"

if not is_preproduction:
    health_thread = threading.Thread(target=health_check_worker, daemon=True)
    health_thread.start()

if __name__ == '__main__':
    if is_preproduction:
        app.run(host='0.0.0.0', port=8100, debug=True)
    else:
        serve(app, host='0.0.0.0', port=8100, threads=16) 