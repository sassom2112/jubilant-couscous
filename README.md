# CyberNotify: Real-time Cybersecurity Intelligence Monitor

CyberNotifyRSS is a Python-based real-time cybersecurity intelligence monitor designed to aggregate critical threat information from various RSS feeds and deliver concise, AI-summarized alerts directly to your terminal. Built with a focus on efficiency and minimizing distraction, it helps cybersecurity professionals, particularly those in Managed Security Service Providers (MSPs), stay abreast of the latest threats without constant interruptions.

---

## Features

* **Customizable RSS Feed Monitoring:** Tracks multiple cybersecurity news sources, blogs, and advisories, including general threat intelligence and MSP-focused content.

* **AI-Powered Insights (Google Gemini <span style="color:red;">work in progress</span>):** Leverages Google Gemini to provide a concise, MSP-centric analysis of critical alerts, focusing on:
    * Impact and urgency for SMB/mid-market clients.
    * Red team perspectives on attack vectors.
    * Immediate defensive actions for MSPs.
    * Technical "nerdy details" like MITRE ATT&CK tactics, malware families, and exploit types.

* **Command-Line Interface (CLI):** Delivers alerts directly to your terminal, offering a focused and less distracting way to consume threat intelligence.

* **Critical Keyword Detection:** Automatically flags and prioritizes alerts containing high-impact keywords (e.g., "ransomware", "zero-day", "RCE", "privilege escalation").

* **Desktop Notifications (Optional):** Integrates with `notify-send` for desktop notifications (primarily for critical alerts), offering compatibility with Windows environments via WSL2 (though this feature's utility is subject to user preference).

* **Persistent Seen Entries:** Keeps track of previously seen articles using a JSON file, ensuring you only receive notifications for new content.

---

## Motivation

As a cybersecurity professional, the need for a non-distracting yet comprehensive threat intelligence feed became apparent. Traditional notification systems often lead to information overload. CyberNotify was born from the desire to create a lean, command-line-centric solution that provided relevant information without constant interruptions, while also exploring the integration of AI for smarter insights and cross-platform notification capabilities within a WSL2 environment.

---

## Installation and Setup

### Prerequisites

* Python 3.8+
* `pip` (Python package installer)
* **Google Gemini API Key:** Obtain one from [Google AI Studio](https://aistudio.google.com/).
* **For Desktop Notifications (Windows/WSL2):**
    * Windows Subsystem for Linux 2 (WSL2) enabled.
    * A `notify-send` equivalent or symlink/alias configured in your WSL2 environment to push notifications to Windows (e.g., using `wsl-notify-send.exe`).