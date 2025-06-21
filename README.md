CyberNotify: Real-time Cybersecurity Intelligence Monitor

🚀 Overview
CyberNotify is a powerful Python-based application designed to keep cybersecurity professionals, Managed Security Service Providers (MSSPs), and security-conscious individuals perpetually informed about the latest threats, vulnerabilities, and industry news. By aggregating critical information from leading cybersecurity RSS feeds, CyberNotify ensures you're always abreast of developments that matter, providing both terminal and critical desktop notifications.

Its core purpose is to filter the noise and highlight urgent intelligence, allowing for proactive response to emerging threats like zero-days, ransomware campaigns, and critical exploits.

✨ Features
Real-time Feed Monitoring: Continuously pulls updates from a curated list of top-tier cybersecurity RSS feeds.

Intelligent Keyword Detection: Identifies critical alerts based on a configurable list of keywords (e.g., "ransomware", "zero-day", "exploit").

Dual Notification System:

Terminal Output: All new and relevant updates are displayed directly in your terminal with clear, color-coded formatting.

Critical Desktop Alerts: Urgent, keyword-matched threats trigger prominent desktop notifications (leveraging notify-send for Linux/WSL environments).

Persistent State Management: Utilizes a JSON file (seen_cyber_entries.json) to track previously seen entries, preventing redundant notifications across sessions.

Comprehensive Logging: Detailed logs are maintained in cyber_notifications.log for review and auditing.

Extensible Feed Configuration: Easily add or remove RSS feeds to tailor the information stream to your specific needs.

Designed for Proactive Security: Aims to minimize reaction time to critical incidents by providing immediate, actionable intelligence.

⚙️ Installation & Setup
Clone the Repository (if applicable):

git clone https://github.com/your-username/cyberstuff.git
cd cyberstuff

(If this is your existing directory, you can skip cloning and just ensure you're in ~/cyberstuff)

Create a Virtual Environment (Recommended):
It's good practice to use a virtual environment to manage dependencies.

python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

Install Dependencies:
Install the required Python libraries using pip:

pip install requests feedparser beautifulsoup4

Desktop Notification Setup (Linux / WSL - Windows Subsystem for Linux):
CyberNotify uses notify-send for desktop notifications.

Linux: notify-send is usually pre-installed or can be installed via your package manager (e.g., sudo apt-get install libnotify-bin).

WSL (Windows): You'll need to configure wsl-notify-send.exe to enable desktop notifications from WSL.

Download: Get wsl-notify-send.exe from this GitHub repository or a similar source.

Place it: Put wsl-notify-send.exe somewhere accessible, e.g., C:\Users\YourUser\Bin.

Create a Symlink/Alias in WSL: In your WSL terminal, create a symlink to wsl-notify-send.exe in a directory included in your WSL's PATH. A common choice is /usr/local/bin/.

sudo ln -s /mnt/c/Users/YourUser/Bin/wsl-notify-send.exe /usr/local/bin/notify-send

(Adjust C:\Users\YourUser\Bin to your actual path).

Test: You can test your setup by running: notify-send "Hello" "Test from WSL"

Icon (Optional): If you want a custom icon for your desktop notifications, update the "--icon" path in the send_desktop_notification function in the script. Ensure the path is correct for your WSL environment (e.g., /mnt/c/Users/mikeg/Bin/cyber_icon.png). If you don't have an icon or the path is incorrect, simply comment out that line in the script to avoid errors.

🚀 Usage
To run the CyberNotify service, simply execute the Python script:

python3 cyber_notify.py

The script will start monitoring the configured RSS feeds. New and critical updates will appear in your terminal, and critical alerts will also trigger desktop notifications.

To stop the service, press Ctrl+C.

⚙️ Configuration
You can customize CyberNotify by modifying the following variables at the top of the cyber_notify.py script:

FEEDS: A dictionary where keys are friendly names for the feeds and values are their RSS feed URLs. Feel free to add, remove, or modify these URLs to suit your information sources.

SEEN_ENTRIES_FILE: The name of the JSON file used to store seen entries. Default is seen_cyber_entries.json.

CHECK_INTERVAL_SECONDS: The time (in seconds) between each feed check. Default is 300 seconds (5 minutes). Adjust this based on how frequently you want to receive updates and to avoid overwhelming the RSS feed servers.

CRITICAL_KEYWORDS: A list of keywords (case-insensitive) that, if found in an entry's title or summary, will flag the entry as a critical alert, triggering a desktop notification.

📂 Project Structure
cyberstuff/
├── cyber_notify.py             # The main Python script
├── seen_cyber_entries.json     # Stores IDs of already seen entries (created on first run)
└── cyber_notifications.log     # Logs all activities, warnings, and errors (created on first run)

⚠️ Important Notes
Internet Connection: An active internet connection is required for the script to fetch RSS feeds.

Rate Limiting: Be mindful of the CHECK_INTERVAL_SECONDS. Setting it too low might lead to IP blocking by some RSS feed providers due to excessive requests.

Feed Parser Robustness: The script attempts to handle various RSS feed formats and fallbacks for unique entry IDs, but some malformed feeds might cause minor parsing warnings.

notify-send: Ensure notify-send is correctly configured and accessible in your environment for critical desktop alerts to function.

🤝 Contributing
Contributions are welcome! If you have suggestions for new features, bug fixes, or improvements, please feel free to:

Fork the repository.

Create a new branch (git checkout -b feature/your-feature).

Make your changes.

Commit your changes (git commit -m 'feat: Add new feature').

Push to the branch (git push origin feature/your-feature).

Open a Pull Request.