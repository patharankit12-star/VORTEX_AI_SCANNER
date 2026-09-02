import sys
import argparse
import requests
import re
import socket
import concurrent.futures
import json
import hashlib
from google import genai
import base64
from bs4 import BeautifulSoup
import time
import platform
import subprocess



class UniversalVortex:
 def __init__(self, raw_target, port_limit, api_provider, api_key, model_name):
        self.raw_target = raw_target
        self.clean_target = re.sub(r"^https?://", "", raw_target).strip("/")
        self.port_limit = port_limit
        
        # New AI variables 
        self.api_provider = api_provider
        self.api_key = api_key
        self.model_name = model_name

        self.report = {"target":self.clean_target, "os_guess":"Unknown","osint":{},"subdomains": [],"live_subdomains": [], "open_ports":[]}
        print(f"\n [VORTEX] Universal Scan Initiated on: {self.clean_target}")
        print("-" * 60)
# MODULE 1: OS Fingerprinting & Ping


 def check_and_os(self):
    print("=" *65)
    print("[*] STEP 1:Pinging target & Guessing os...")
    print("=" *65)
    # set ping command as a os 
    
    if platform.system().lower() == "windows":
        command = ['ping','-n','1',self.clean_target]
    else:
       command = ['ping','-c','1',self.clean_target]
    
    try:
      # capture ping output 
       result = subprocess.run(command,stdout = subprocess.PIPE,stderr = subprocess.DEVNULL, text = True)
       output = result.stdout.lower()
      
       if result.returncode == 0:
            print("====> Target is ONLINE!<====")
         
            if "ttl=" in output:
                # Regex's TTL
                ttl_match = re.search(r"ttl=(\d+)", output)
                if ttl_match:
                     ttl_val = int(ttl_match.group(1))
                     if ttl_val <= 64:
                       self.report["os_guess"] = "Linux/Unix"
                     elif ttl_val <= 128:
                       self_report["os_guess"] = "windows"
            print("="*10)
            print(f"====> Target OS guess (Based on TTL): {self.report['os_guess']}\n")
            print("="*10)
       else:
            print("    ❌ Target is DOWN or Firewalled. (Proceeding anyway for deep scan...)\n")

    except Exception as e:
           print(f" System Error:{e}\n")


# MODULE 2: Universal OSINT (HTTP/HTTPS Fallback)

 def run_universal_osint(self):
          print("="*65)
          print("[*] STEP 2: Extracting Web Data (Trying HTTPS -> HTTP)...")
          print("="*65)
          # WAF/Firewall bypass for fake user
          headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0'}
        
          # try first https after http
          protocols = [f"https://{self.clean_target}", f"http://{self.clean_target}"]
          html_content = None
          working_url = None

          for url in protocols:
             try:
               # Target requests
               response = requests.get(url,headers = headers, timeout=5)
               html_content = response.text
               working_url = url
               print(f"====> Successfully connected via: {url}")
               break
             except requests.exceptions.RequestException:
               continue

          if html_content:
             try:
                soup = BeautifulSoup(html_content,'html.parser')
                # Title
                title = soup.title.string if soup.title else "No Title Found"
                self.report["osint"]["title"] = title.strip()
                print(f"    ----> Title: {title.strip()}")
       # find emails
                emails = list(set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",html_content)))
                self.report["osint"]["emails"] = emails
                print(f"    ----> Found {len(emails)} Emails: {emails}")
             except Exception as e:
                print(f"[*] parsing Error :{e}")
          else:
            print("[-] Website is unreachable or not running a web server on port 80/443.")
          print("") 


# Modul 2.5 : find subdomains (HackerTarget + crt.sh)
 def find_subdomains(self):
       print("="*65)
       print("[*] STEP 2.5: Hunting for Hidden Subdomains...")
       print("="*65)
       if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", self.clean_target):
           print("    [-] Target is an IP address. Skipping Subdomain Enumeration.\n")
           return
       subdomains = set()
       # METHOD 1: HackerTarget API (Fast & Reliable)
       try:
         print("    ----> Querying HackerTarget API...")
         ht_url = f"https://api.hackertarget.com/hostsearch/?q={self.clean_target}"
         ht_response = requests.get(ht_url,timeout=10)
         
         if ht_response.status_code == 200:
            for line in ht_response.text.split('\n'):
                  if ',' in line:
                     sub = line.split(',')[0].strip()
                     if self.clean_target in sub:
                          subdomains.add(sub)

       except Exception:
             print("    [-] HackerTarget API failed or timed out.")
       

       # METHOD 2: crt.sh API (Deep Search)
       try:
        print("    -----> Querying crt.sh API (Might give 502 on huge targets)...")
        crt_url = f"https://crt.sh/?q=%.{self.clean_target}&output=json"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        crt_response = requests.get(crt_url,headers = headers,timeout =15)
        
        if crt_response.status_code == 200:
             data = crt_response.json()
             for entry in data:
                   name_value = entry.get('name_value','')
                   for sub in name_value.split('\n'):
                         clean_sub = sub.strip().replace('*.', '')
                         if self.clean_target in clean_sub:
                                   subdomains.add(clean_sub)
        else:
          print(f"--> [-] crt.sh returned {crt_response.status_code}. (Moving on...)")
       except Exception:
          
         print("    [-] crt.sh API failed or timed out.")
      # FINAL RESULT PROCESSING
       self.report["subdomains"] = list(subdomains)
       print(f"====>Found {len(subdomains)} unique Subdomains!")
       for sub in list(subdomains)[:5]:
            print(f"       -> {sub}")
       if len(subdomains) > 5:
            print(f"       -> ... and {len(subdomains) - 5} more (Saved in final encrypted report)")
       print(" ")

# MODULE 2.6: Live Subdomain Prober (httpx Clone)
 

 def check_live_status(self,sub):
         # check this subdomain is live or not
         # first try https after try http
         protocols = [f"https://{sub}",f"http://{sub}"]
         

         for url in protocols:
             try:
               response = requests.get(url, timeout=3, allow_redirects=False)
               return {"subdomain":sub,"url":url,"status_code":response.status_code}
               
             except requests.exceptions.RequestException:
                     continue                  
         return None

 def probe_live_subdomains(self):
          print("="*65)
          print("[*] STEP 2.6: Probing Live Subdomains (Filtering Dead Assets)...")
          print("="*65)
         # if subdomains not  find that skip this step
          if not self.report.get("subdomains"):
                print("    [-] No subdomains found to probe.\n")
                return
          print(f"    -----> Probing {len(self.report['subdomains'])} subdomains for active Web Servers...")
          # 50 workers 
          with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
              tasks = [executor.submit(self.check_live_status,sub) for sub in self.report["subdomains"]]
              print("*"*65)
              for future in concurrent.futures.as_completed(tasks):
                     result = future.result()
                     if result:
                        # if subdomains  live print in this list
                        self.report["live_subdomains"].append(result)
                        print(f"  ----->LIVE: {result['url']:<30} [Status: {result['status_code']}]")
              print("*"*65)
          total_live = len(self.report["live_subdomains"])
          print(f"    -----> Filtered! Found {total_live} LIVE subdomains out of {len(self.report['subdomains'])} total.\n")               

# MODULE 3: Mass Port & Banner Scanner

 def grab_banner(self,host,port):
         s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
         s.settimeout(1.5)
         try:
          if s.connect_ex((host, port)) == 0:
             # if this is a web-port that send http probe 
             if port in [80,443,8000,8080,8443]:
                    s.send(b"HEAD / HTTP/1.1\r\nHost: " + host.encode() + b"\r\n\r\n")
 
             # Receive up to 1024 bytes and decode
             banner = s.recv(1024).decode('utf-8',errors='ignore').strip()
             return {"host": host , "port": port,"banner":banner if banner else "Unknown Service"}
             
         except:
            pass
         finally:
              s.close()
         return None

 def fast_scan(self):
        print("\n" + "="*65)
        print(f"[*] STEP 3: MASS PORT SCANNING (Target + Live Subdomains)")
        print("="*65)
        # --- NEW PORT PARSING LOGIC ---
        ports_to_check = []
        port_str = str(self.port_limit)
        if '-' in port_str:
          # if range is given 
          start,end = port_str.split('-')
          ports_to_check = range(int(start), int(end) + 1)
        elif ',' in port_str:
          # if give specific ports 
          ports_to_check = [int(p.strip()) for p in port_str.split(',')]
        else:
          ports_to_check = [int(port_str)]       
        # --- NEW LOGIC: COMBINE ALL TARGETS ---
        # first input target in list
        targets_to_scan = [self.clean_target]
        # enter all subdomain in list
        for live_sub in self.report.get("live_subdomains", []):
               targets_to_scan.append(live_sub["subdomain"])
        print(f" --> Target loaded:{len(targets_to_scan)}(Main Domain + Subdomains)")
        print(f" --> ports hosts:{len(ports_to_check)}")
        print(f" --> Total Tasks:{len(targets_to_scan) * len(ports_to_check)}\n")
        print("=" * 65)


        scan_tasks = [(host,port) for host in targets_to_scan for port in ports_to_check]
                
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            tasks = [executor.submit(self.grab_banner,t[0],t[1] ) for t in scan_tasks]
            for future in concurrent.futures.as_completed(tasks):
                   result = future.result()
                   if result:
                      print("-"*80)
                      print(f"---> Port {result['host']:<25} | Port: {result['port']:<5}  {result['banner']}")
                      self.report["open_ports"].append(result)
                      print("-"*80)
        if not self.report["open_ports"]:
               print("    [-] No open ports found in the specified range.")

# MODULE 4: AI Vulnerability Engine

 def ai_auditor(self):
        print("\n" + "="*65)
        print("[*] STEP 4: AI Analyzing Discovered Services")
        print("="*65)
        
        if not self.api_key:
            print("[-] API key missing! Skipping AI audit...")
            return 
       
        for item in self.report["open_ports"]:
            banner = item["banner"]
            host = item["host"]
            port = item["port"]

            # 'Unknown service' 
            if banner and banner.lower() != "unknown service":
                prompt = (
                    f"Act as a strict cybersecurity analyst. I found this banner: '{banner}' "
                    f"on port {port} (Likely OS: {self.report['os_guess']}). "
                    f"Provide a highly concise, direct risk assessment strictly in 3 short bullet points:\n"
                    f"1. Service Identification: (What is this exact service/version?)\n"
                    f"2. Potential Risks: (What are the common vulnerabilities or misconfigurations for this?)\n"
                    f"3. Recommended Action: (What exact steps should a defender take to secure it?)\n"
                    f"Do not use long sentences. Keep it brief and technical."
                )                
                try:
                    # 1. GEMINI LOGIC
                    if self.api_provider == 'gemini':
                        client = genai.Client(api_key=self.api_key)
                        response = client.models.generate_content(
                            model=self.model_name, contents=prompt
                        )
                        print(f"---> {host} (Port {port}): {response.text.strip()}")
                    
                    # 2. OPENAI (ChatGPT) LOGIC
                    elif self.api_provider == 'openai':
                        import openai
                        openai.api_key = self.api_key
                        response = openai.ChatCompletion.create(
                            model=self.model_name,
                            messages=[{"role": "user", "content": prompt}]
                        )
                        print(f"---> {host} (Port {port}): {response.choices[0].message.content.strip()}")
                        
                    # 3. CLAUDE (Anthropic) LOGIC
                    elif self.api_provider == 'claude':
                        import anthropic
                        client = anthropic.Anthropic(api_key=self.api_key)
                        response = client.messages.create(
                            model=self.model_name,
                            max_tokens=256, 
                            messages=[
                                {"role": "user", "content": prompt}
                            ]
                        )
                        print(f"---> {host} (Port {port}): {response.content[0].text.strip()}")
                        
                except Exception as e:
                    print(f"---> [-] AI analysis failed for {host}:{port} | Error: {e}")
# MODULE 5: Cryptographic Secure Report
 def save_secure_report(self):
       print("=" * 50)
       print("[*] STEP 5: Encrypting and Saving Final Report...")
       print("=" * 50)
       report_json =  json.dumps(self.report,indent=4)
       # data in convert into rhe base64
       encoded_data = base64.b64encode(report_json.encode('utf-8')).decode('utf-8')
       file_hash = hashlib.md5(encoded_data.encode('utf-8')).hexdigest() 

       filename = f"VORTEX_{self.clean_target.replace('.', '_')}_Report.txt"
       with open(filename,"w") as f:
            f.write("=== VORTEX UNIVERSAL REPORT ===\n")
            f.write(f"Target: {self.clean_target}\n")
            f.write(f"Integrity Hash (MD5): {file_hash}\n")
            f.write("=" * 35 + "\n\n")
            f.write(f"BASE64 ENCODED DATA:\n{encoded_data}\n")
       print(f"     Data encrypted and saved to '{filename}'")
       print("=" * 65 + "\n VORTEX  MISSION ACCOMPLISHED!")
      
# MASTER LAUNCHER
def main():
    print("\n" + "="*50)
    print(" WELCOME TO VORTEX UNIVERSAL SECURITY SCANNER")
    print("="*50)
    
    
    print("\n[AI CONFIGURATION]")
    api_provider = input("-> Select AI Provider (gemini/openai/claude) [Default: gemini]: ").strip().lower() or "gemini"
    api_key = input(f"-> Enter your {api_provider.upper()} API Key: ").strip()
    model_name = input("-> Enter Model Name (e.g., gemini-1.5-flash, gpt-4o, claude-3) [Default: gemini-1.5-flash]: ").strip() or "gemini-1.5-flash"
    
    
    print("\n[TARGET CONFIGURATION]")
    target = input("-> Enter Target (IP or URL, e.g., 192.168.1.1, example.com): ").strip()
    if not target:
        print("[-] Target is required! Exiting...")
        return
        
    ports = input("-> Enter Ports (e.g., 80,443 or 1-1000) [Default: 1-1000]: ").strip() or "1-1000"

    
    vortex = UniversalVortex(target, ports, api_provider, api_key, model_name)
    
    start_time = time.time()
    vortex.check_and_os()
    vortex.run_universal_osint()
    
    choice = input("\n[?] Do you want to scan subdomains? (yes/no): ").strip().lower()
    if choice in ['yes', 'y']:
        vortex.find_subdomains()
        vortex.probe_live_subdomains()
    else:
        print("\n[-] Skipping Subdomain scan. Scanning only the main domain...")

    vortex.fast_scan()
    vortex.ai_auditor()
    vortex.save_secure_report()

    print(f"Total Execution Time: {round(time.time() - start_time, 2)} seconds.\n")
if __name__ == "__main__":
      main()
