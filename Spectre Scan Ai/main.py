import requests
import socket
import threading
import os
import time

# ---------------- Colors ----------------
RED = "\033[91m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# ---------------- Banner ----------------
def banner():
    os.system("cls" if os.name == "nt" else "clear")
    logo = """
                                          $$\\                                $$$$$$\\
                                          $$ |                              $$  __$$\\
 $$$$$$$\\  $$$$$$\\   $$$$$$\\   $$$$$$$\\ $$$$$$\\    $$$$$$\\   $$$$$$\\        $$ /  \\__| $$$$$$$\\ $$$$$$\\  $$$$$$$\\
$$  _____|$$  __$$\\ $$  __$$\\ $$  _____|\\_$$  _|  $$  __$$\\ $$  __$$\\       \\$$$$$$\\  $$  _____|\\____$$\\ $$  __$$\\
\\$$$$$$\\  $$ /  $$ |$$$$$$$$ |$$ /        $$ |    $$ |  \\__|$$$$$$$$ |       \\____$$\\ $$ /      $$$$$$$ |$$ |  $$ |
 \\____$$\\ $$ |  $$ |$$   ____|$$ |        $$ |$$\\ $$ |      $$   ____|      $$\\   $$ |$$ |     $$  __$$ |$$ |  $$ |
$$$$$$$  |$$$$$$$  |\\$$$$$$$\\ \\$$$$$$$\\   \\$$$$  |$$ |      \\$$$$$$$\\       \\$$$$$$  |\\$$$$$$$\\\\$$$$$$$ |$$ |  $$ |
\\_______/ $$  ____/  \\_______| \\_______|   \\____/ \\__|       \\_______|       \\______/  \\_______|\\_______|\\__|  \\__|
          $$ |
          $$ |
          \\__|

SpectreScan AI - Ghost Your Network
    """
    print(CYAN + logo + RESET)
    print(CYAN + "-"*70 + RESET)

# ---------------- OpenRouter AI (optional) ----------------
OPENROUTER_API_KEY = "Add Your OpenRouter API Key This Program Uses GPT 3.5 Turbo"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def ai_predict_subnets(active_ips):
    prompt = f"""
    I have detected the following IPs on my local network: {', '.join(active_ips)}.
    Suggest other nearby subnets or IPs that might also be active.
    Return only a comma-separated list of subnets in the format 192.168.X.0.
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 60
    }
    try:
        r = requests.post(OPENROUTER_URL, headers=headers, json=data, timeout=10)
        r.raise_for_status()
        text = r.json()['choices'][0]['message']['content']
        return [s.strip() for s in text.split(',') if s.strip()]
    except Exception as e:
        print(f"{RED}AI subnet prediction failed: {e}{RESET}")
        return []

def ai_identify_device(ip, ports, banners):
    prompt = f"""
    Device detected at IP {ip} with open ports: {', '.join(str(p) for p in ports)}.
    Banners collected: {banners}.
    Identify the likely device type, OS, and manufacturer.
    Return in format: DeviceType (OS) - Manufacturer
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 60
    }
    try:
        r = requests.post(OPENROUTER_URL, headers=headers, json=data, timeout=10)
        r.raise_for_status()
        return r.json()['choices'][0]['message']['content']
    except:
        return "Unknown"

# ---------------- Banner Grabbing ----------------
def grab_banner(ip, port):
    try:
        s = socket.socket()
        s.settimeout(0.5)
        s.connect((ip, port))
        s.send(b'HEAD / HTTP/1.0\r\n\r\n')
        banner = s.recv(1024).decode(errors='ignore')
        s.close()
        return banner.strip()
    except:
        return ""

# ---------------- Risk Assessment ----------------
def calculate_risk(ports):
    score = 0
    reasons = []
    critical_ports = [22, 23, 139, 445, 3389]
    for port in ports:
        if port in critical_ports:
            score += 3
            reasons.append(f"Port {port} is critical")
        elif port > 8000:
            score += 1
            reasons.append(f"Port {port} is high-numbered")
    score = min(score, 10)
    if score <= 3:
        reason_text = "Low risk: only essential or secure ports open."
    elif score <= 7:
        reason_text = "Medium risk: some commonly exploited ports open."
    else:
        reason_text = "High risk: several vulnerable ports open."
    reason_text += " " + "; ".join(reasons)
    return score, reason_text

# ---------------- Host Scan ----------------
def scan_host(ip, results):
    open_ports = []
    banners = {}
    try:
        socket.setdefaulttimeout(0.3)
        for port in [22, 23, 80, 139, 443, 445, 5038, 8000, 8080, 8081, 8443, 8888, 9090]:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if s.connect_ex((ip, port)) == 0:
                open_ports.append(port)
                banners[port] = grab_banner(ip, port)
            s.close()
        if open_ports:
            device_info = ai_identify_device(ip, open_ports, banners)
            risk, reason = calculate_risk(open_ports)
            results.append((ip, device_info, open_ports, risk, reason))
            color = GREEN if risk < 4 else YELLOW if risk < 7 else RED
            print(f"{color}[+] {ip} - {device_info} | Open Ports: {open_ports} | Risk: {risk}/10 | {reason}{RESET}")
    except:
        pass

# ---------------- Scanning Animation ----------------
def scanning_animation(duration=5):
    chars = ['|', '/', '-', '\\']
    end_time = time.time() + duration
    i = 0
    while time.time() < end_time:
        print(f"{YELLOW}[*] Scanning network {chars[i % 4]}{RESET}", end="\r")
        i += 1
        time.sleep(0.1)
    print(" " * 50, end="\r")

# ---------------- Generate ASCII Map --------------- 
def generate_network_map(results):
    map_str = "\nNetwork Topology Map (ASCII):\n"
    for ip, data in results:
        device, ports, risk, reason = data  # unpack the inner tuple
        color = GREEN if risk < 4 else YELLOW if risk < 7 else RED
        map_str += f" - {color}{ip}{RESET}: {device} | Ports: {ports} | Risk: {risk}/10 | {reason}\n"
    return map_str


# ---------------- Main Scan ----------------
def scan_network(base_subnets=["192.168.0."]):
    banner()
    results = []

    # Initial subnet scan
    threads = []
    for base_ip in base_subnets:
        for i in range(1, 255):
            ip = base_ip + str(i)
            t = threading.Thread(target=scan_host, args=(ip, results))
            threads.append(t)
            t.start()

    anim_thread = threading.Thread(target=scanning_animation, args=(10,))
    anim_thread.start()
    for t in threads: t.join()
    anim_thread.join()

    # AI-predicted subnets
    active_ips = [ip for ip, *_ in results]
    predicted_subnets = ai_predict_subnets(active_ips)
    if predicted_subnets:
        print(f"{CYAN}[*] AI predicts additional subnets: {', '.join(predicted_subnets)}{RESET}")
        threads = []
        for base_ip in predicted_subnets:
            for i in range(1, 255):
                ip = base_ip + str(i)
                t = threading.Thread(target=scan_host, args=(ip, results))
                threads.append(t)
                t.start()
        anim_thread = threading.Thread(target=scanning_animation, args=(10,))
        anim_thread.start()
        for t in threads: t.join()
        anim_thread.join()

    # Remove duplicates
    unique_results = {}
    for ip, device, ports, risk, reason in results:
        unique_results[ip] = (device, ports, risk, reason)

    # Summary
    print(f"\n{GREEN}[✓] Scan complete! Found {len(unique_results)} active devices.{RESET}")
    for ip, (device, ports, risk, reason) in unique_results.items():
        color = GREEN if risk < 4 else YELLOW if risk < 7 else RED
        print(f"    {color}{ip}{RESET} - {device} | Open Ports: {ports} | Risk: {risk}/10 | {reason}")

    # ASCII Map
    print(generate_network_map(list(unique_results.items())))

# ---------------- Run ----------------
if __name__ == "__main__":
    scan_network(["192.168.0."])

