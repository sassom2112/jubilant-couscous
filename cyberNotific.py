import requests
import feedparser
import time
import json
import os
import logging
import subprocess
from bs4 import BeautifulSoup

# --- ANSI Escape Codes for Colors ---
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
BLUE = "\033[94m"  # Brighter blue for titles
CYAN = "\033[96m"
MAGENTA = "\033[95m"
YELLOW = "\033[93m" # Added for warnings

# --- Logging Configuration ---
LOG_FILE = "cyber_notifications.log"

# Set up a logger for the application
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # Set the logger to capture INFO and above

# Remove any existing handlers to prevent duplicate output if script is re-run in same session
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# File handler for saving logs to a file (no colors here, just plain text)
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# --- Configuration ---
# --- Configuration ---
FEEDS = {
    "The Hacker News": "https://thehackernews.com/feed/",
    "Krebs on Security": "https://krebsonsecurity.com/feed/",
    "CISA Alerts": "https://www.cisa.gov/news-events/alerts.xml",
    "Exploit-DB": "https://www.exploit-db.com/rss.xml",
    "BleepingComputer": "https://www.bleepingcomputer.com/feed/",
    # --- New Feeds for MSPs ---
    "SANS ISC Diary": "https://isc.sans.edu/rssfeed_full.xml",
    "Palo Alto Networks Unit 42": "https://unit42.paloaltonetworks.com/feed/",
    "Microsoft Security Response Center": "https://msrc.microsoft.com/update-guide/rss",
    "Google Cloud Security Blog": "https://cloud.google.com/blog/products/identity-security/feed",
    "AWS Security Blog": "https://aws.amazon.com/blogs/security/feed/",
    "Azure Security Blog": "https://azure.microsoft.com/en-us/blog/tag/security/feed/",
    "Data Breach Today": "https://www.databreachtoday.com/rss",
    # --------------------------
}

SEEN_ENTRIES_FILE = "seen_cyber_entries.json"
CHECK_INTERVAL_SECONDS = 300 # Every 5 minutes
CRITICAL_KEYWORDS = ["ransomware", "zero-day", "rce", "privilege escalation", "authentication bypass", "exploit", "critical vulnerability", "malware", "ddos", "phishing", "supply chain"]

# --- Notification Functions ---

def send_desktop_notification(title, message, url=None, is_critical=False):
    """
    Sends a desktop notification using the 'notify-send' command,
    which should be symlinked to wsl-notify-send.exe for Windows.
    """
    # NOTE: This function is now ONLY called if is_critical is True
    # so we can assume it's always a critical notification for logging purposes here.
    full_message_body = f"{message}\nLink: {url}" if url else message

    try:
        # Arguments for wsl-notify-send (via notify-send)
        # The main message is the first non-flag argument.
        command = [
            "notify-send",
            full_message_body, # This will be the main text of the notification
            "--appId", "Cyber Notify (Critical)", # Add "Critical" to AppId for distinction
            "--category", "Security Alert",
            # Add --icon if you have one. Make sure path is correct for WSL.
            # Example: "/mnt/c/Users/mikeg/Bin/cyber_icon.png"
            # If you don't have this icon or path is wrong, comment out the line below.
            # "--icon", "/mnt/c/Users/mikeg/Bin/cyber_icon.png",
        ]

        # Execute the command and capture output for debugging
        result = subprocess.run(command, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            logger.info(f"[DESKTOP NOTIFICATION SENT - CRITICAL] Title: {title}, Message: {full_message_body[:70]}...")
        else:
            logger.error(f"Failed to send critical desktop notification. Return code: {result.returncode}")
            logger.error(f"STDOUT from notify-send: {result.stdout.strip()}")
            logger.error(f"STDERR from notify-send: {result.stderr.strip()}")

    except FileNotFoundError:
        logger.error("Error: 'notify-send' command not found. Ensure wsl-notify-send is correctly symlinked/aliased for critical alerts.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during critical desktop notification: {e}")


def print_to_terminal(title, message, url, is_new=False, is_critical=False):
    """Prints the notification details directly to the terminal with colors."""
    if is_critical:
        status_tag = f"{RED}{BOLD}!!! CRITICAL ALERT !!!{RESET}"
        title_color = RED
    elif is_new:
        status_tag = f"{GREEN}{BOLD}[NEW]{RESET}"
        title_color = BLUE
    else:
        status_tag = f"{CYAN}[INFO]{RESET}" # For general status updates, not new items
        title_color = CYAN # Or choose another subtle color

    # Calculate dynamic dash length based on the visible characters of status_tag and title
    clean_status_tag = status_tag.replace(RESET, '').replace(BOLD, '').replace(RED, '').replace(GREEN, '').replace(YELLOW, '').replace(BLUE, '').replace(CYAN, '').replace(MAGENTA, '')
    clean_title = title # Assuming title doesn't have ANSI codes

    dash_length = len(clean_status_tag) + len(clean_title) + 8 # Adjusted for better visual flow

    print(f"\n{status_tag} {title_color}{BOLD}{title}{RESET}")
    print(f"{CYAN}{'-' * dash_length}{RESET}")
    print(f"  {BOLD}Message:{RESET} {message}")
    if url:
        print(f"  {BOLD}Link:{RESET} {url}")
    print(f"{CYAN}{'-' * 30}{RESET}") # Consistent dash length for footer

def load_seen_entries():
    """Loads the last seen entry IDs from a JSON file."""
    if os.path.exists(SEEN_ENTRIES_FILE):
        try:
            with open(SEEN_ENTRIES_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding {SEEN_ENTRIES_FILE}: {e}. Starting with empty seen entries.")
            return {}
    return {}

def save_seen_entries(seen_entries):
    """Saves the last seen entry IDs to a JSON file."""
    try:
        with open(SEEN_ENTRIES_FILE, 'w') as f:
            json.dump(seen_entries, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving {SEEN_ENTRIES_FILE}: {e}")

def check_for_new_entries(seen_entries):
    """Checks each feed for new entries and sends notifications."""
    new_seen_entries = seen_entries.copy()
    items_to_save_as_seen = {} # Track all new items to save, regardless of criticality
    total_new_items = 0

    for feed_name, feed_url in FEEDS.items():
        logger.info(f"Checking feed: {feed_name}")
        try:
            response = requests.get(feed_url, timeout=15)
            response.raise_for_status()

            feed = feedparser.parse(response.content)

            if feed.bozo:
                logger.warning(f"Feed '{feed_name}' has parsing errors (Bozo bit set): {feed.bozo_exception}. Proceeding cautiously.")

            if not feed.entries:
                logger.info(f"No entries found for {feed_name}.")
                continue

            latest_id_from_feed = None
            if feed.entries:
                if feed.entries[0].get('id'):
                    latest_id_from_feed = feed.entries[0].id
                elif feed.entries[0].get('link'):
                    latest_id_from_feed = feed.entries[0].link
                elif feed.entries[0].get('guid'):
                    latest_id_from_feed = feed.entries[0].guid
                else:
                    latest_id_from_feed = feed.entries[0].title + (feed.entries[0].published if hasattr(feed.entries[0], 'published') else '')
                    logger.warning(f"Using less reliable ID fallback for '{feed_name}': {latest_id_from_feed}")

            if latest_id_from_feed and str(latest_id_from_feed) == str(seen_entries.get(feed_name)):
                logger.info(f"No new entries for {feed_name}.")
                # Since no new items, ensure we don't accidentally clear the seen_entries for this feed
                items_to_save_as_seen[feed_name] = seen_entries.get(feed_name)
                continue

            # This list will hold IDs of new entries found in the current feed
            new_entries_ids_in_current_feed = []

            for entry in reversed(feed.entries):
                entry_id = None
                if entry.get('id'):
                    entry_id = entry.id
                elif entry.get('link'):
                    entry_id = entry.link
                elif entry.get('guid'):
                    entry_id = entry.guid
                else:
                    entry_id = entry.title + (entry.published if hasattr(entry, 'published') else '')

                if not entry_id:
                    logger.warning(f"Could not get a unique ID for an entry in {feed_name}. Skipping this entry.")
                    continue

                if str(entry_id) == str(seen_entries.get(feed_name)):
                    # We've reached the last item we already know about, stop processing this feed
                    break

                # --- New item found ---
                total_new_items += 1
                new_entries_ids_in_current_feed.append(entry_id) # Add to list to mark as seen later

                title = entry.title if hasattr(entry, 'title') else "No Title"
                link = entry.link if hasattr(entry, 'link') else "No Link"
                message = entry.summary if hasattr(entry, 'summary') else (
                          entry.description if hasattr(entry, 'description') else "No description available.")

                message_soup = BeautifulSoup(message, 'html.parser')
                clean_message = message_soup.get_text(separator=' ', strip=True)

                # --- Critical Keyword Check ---
                is_critical = False
                for keyword in CRITICAL_KEYWORDS:
                    if keyword in title.lower() or keyword in clean_message.lower():
                        is_critical = True
                        break

                # --- Send Notifications (Conditional Logic) ---

                # Always print to terminal if it's a new item (critical or not)
                print_to_terminal(f"{feed_name}: {title}", clean_message, link, is_new=True, is_critical=is_critical)

                # ONLY send desktop notification if it's a critical alert
                if is_critical:
                    send_desktop_notification(f"{feed_name}: {title}", clean_message, link, is_critical=True)

            # Update the seen_entries for this feed with the latest ID found
            # This ensures ALL new items (critical or not) are marked as seen
            if latest_id_from_feed:
                items_to_save_as_seen[feed_name] = latest_id_from_feed

        except requests.exceptions.Timeout:
            logger.error(f"Timeout occurred while fetching {feed_name}. Skipping this check.")
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Network error fetching {feed_name}: {req_err}. Skipping this check.")
        except Exception as e:
            logger.error(f"An unexpected error occurred processing {feed_name}: {e}")

    # Update global seen_entries after checking all feeds
    if total_new_items > 0:
        # Merge new_seen_entries for feeds that had new items, and keep old values for others
        seen_entries.update(items_to_save_as_seen)
        save_seen_entries(seen_entries)
        logger.info(f"Total new items processed: {total_new_items}. Seen entries updated.")
    else:
        logger.info("No new cybersecurity notifications found during this check.")

# --- Main Loop ---
if __name__ == "__main__":
    seen_entries = load_seen_entries()
    logger.info("Starting cybersecurity notification service...")
    logger.info(f"Initial check. Checking every {CHECK_INTERVAL_SECONDS} seconds. Press Ctrl+C to stop.")

    try:
        while True:
            check_for_new_entries(seen_entries)
            logger.info(f"\nWaiting {CHECK_INTERVAL_SECONDS} seconds for next check...")
            time.sleep(CHECK_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        logger.info("\nNotification service stopped gracefully.")