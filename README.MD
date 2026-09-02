🌀 VORTEX: Universal Security Scanner

VORTEX is an automated, AI-powered reconnaissance and vulnerability auditing tool. It is designed for cybersecurity engineers, penetration testers, and bug bounty hunters to rapidly scan targets, enumerate subdomains, analyze open ports, and use advanced AI models (Gemini, OpenAI, Claude) to identify potential vulnerabilities.

🔥 Features

Smart OSINT & Subdomain Hunting: Automatically extracts emails, titles, and hidden subdomains using HackerTarget and crt.sh APIs.

Mass Port & Banner Scanning: High-speed multithreaded port scanning for both the main target and discovered live subdomains.

BYOK AI Integration: Bring Your Own Key! Supports Google Gemini, OpenAI, and Anthropic Claude for intelligent vulnerability analysis of discovered services.

Cryptographic Secure Reporting: Generates an MD5-hashed, Base64 encrypted final report to ensure data integrity.

Interactive CLI Interface: User-friendly terminal experience—no complex command-line arguments required to run the main logic.

⚙️ Installation & Setup
Prerequisites: You need Python 3.x installed on your system (Works perfectly on Linux/Kali Linux).

Step 1: Clone the Repository

Bash
git clone https://github.com//UniversalVortex.git
cd UniversalVortex
Step 2: Install Dependencies

Bash
pip install -r requirements.txt
🚀 How to Use (Usage)
Run the script. VORTEX operates in a fully interactive mode.

Bash
python vortex.py
The Interactive Workflow:
AI Setup: The tool will ask you to choose your preferred AI provider (gemini, openai, or claude) and ask for your API Key. (Default is set to Gemini for fast, free testing).

Target Details: Enter the target IP or Domain (e.g., example.com or 192.168.1.1).

Port Range: Define the ports you want to scan (e.g., 80,443 or 1-1000).

Execution: The scanner will ping the target, attempt OS fingerprinting, fetch subdomains, filter dead assets, and initiate a mass banner grab.

AI Audit & Report: The chosen AI will analyze the banners for vulnerabilities, and the final encrypted report will be saved locally.

⚠️ Disclaimer
This tool is built strictly for Educational Purposes and Ethical Hacking. The creator is not responsible for any misuse or illegal activities performed with this script. Always ensure you have explicit permission before scanning any target.

🤝 Contributing
Feel free to fork this project, submit pull requests, or open an issue if you find a bug or have a feature request!