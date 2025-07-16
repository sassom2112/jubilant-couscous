import requests
import feedparser
import time
import json
import os
import logging
import subprocess
from bs4 import BeautifulSoup
import google.generativeai as genai # New: Import the Google Generative AI library

# --- ANSI Escape Codes for Colors ---
# Because who doesn't love a bit of terminal bling? Makes the cyber alerts pop!
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m" # For those "oh crap" moments
GREEN = "\033[92m" # For fresh, delightful new insights
BLUE = "\033[94m" # Just a nice general info color
CYAN = "\033[96m" # For mundane info that still needs to be seen
MAGENTA = "\033[95m" # Unused, but available for future disco alerts
YELLOW = "\033[93m" # Also unused, maybe for warnings that aren't quite red?
ORANGE = "\033[33m" # AI insights color, because AI is the new orange (or black, depends on the day)

# --- Logging Configuration ---
# Keeping a paper trail, because "it worked on my machine" isn't an excuse in cybersecurity.
LOG_FILE = "cyber_notifications.log"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # We want to know what's happening, but not *everything*.

# Clear existing handlers to prevent duplicate log entries, a common Python gotcha.
# Otherwise, you get that awkward moment where every log line prints twice.
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# --- Gemini API Client Initialization ---
# This is where the magic (or the "oops, forgot my API key") happens.
try:
    # IMPORTANT: Set your GOOGLE_API_KEY environment variable.
    # Seriously, don't hardcode your API key. That's a rookie mistake.
    # For example, in your terminal: export GOOGLE_API_KEY="YOUR_API_KEY"
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    # If the key isn't there, we log it and move on. AI insights are a luxury, not a necessity (yet).
    logger.error("GOOGLE_API_KEY environment variable not set. AI insights will not work.")
except Exception as e:
    # General catch-all for any other weirdness during API setup.
    logger.error(f"Error configuring Gemini API: {e}")

# --- Configuration ---
# The buffet of cybersecurity feeds. Choose wisely.
FEEDS = {
    # --- General Cybersecurity Feeds (Existing & Corrected) ---
    # Hacker News: Because sometimes, the news hacks you.
    "The Hacker News": "https://thehackernews.com/feeds/posts/default", # Corrected feed URL, RSS feeds love to move.
    # Krebs: The OG. If Brian says it, it's probably true.
    "Krebs on Security": "https://krebsonsecurity.com/feed/",
    # CISA Alerts: Uncle Sam wants you... to patch your systems.
    "CISA Alerts": "https://www.cisa.gov/uscert/ncas/alerts.xml", # Corrected feed URL, they moved the cheese.
    "CISA Blogs": "https://www.cisa.gov/blog.xml",
    "CISA Advisories": "https://www.cisa.gov/cybersecurity-advisories/all.xml",
    # Exploit-DB: For when you need to know exactly how bad it can get.
    "Exploit-DB": "https://www.exploit-db.com/rss.xml",
    # BleepingComputer: More like "BeepingComputer" when a new threat drops.
    "BleepingComputer": "https://www.bleepingcomputer.com/feed/",

    # --- MSP-focused Feeds (Existing & Corrected) ---
    # SANS ISC Diary: Daily dose of infosec wisdom, often from folks in the trenches.
    "SANS ISC Diary Full": "https://isc.sans.edu/rssfeed_full.xml",
    "SANS ISC Podcast": "https://isc.sans.edu/podcast.xml", # Because reading is hard, and podcasts are easy.
    # Palo Alto Unit 42: Fancy threat intel from the folks who make firewalls.
    "Palo Alto Networks Unit 42": "https://unit42.paloaltonetworks.com/feed/",
    # MSRC: Microsoft's way of saying "we fixed it... probably."
    "Microsoft Security Response Center": "https://techcommunity.microsoft.com/t5/microsoft-security-response-center/bg-p/MSRCblog/rss", # Corrected to a working blog feed (the old one was a bit moody).
    # Google Cloud Security: Keeping the cloud a *little* less cloudy.
    "Google Cloud Security Blog": "https://cloud.google.com/blog/products/identity-security/rss.xml", # Corrected feed URL.
    # AWS Security: Don't mess with S3 buckets. Just don't.
    "AWS Security Blog": "https://aws.amazon.com/blogs/security/feed/",
    # Azure Security: Blue team's favorite shade of cloud.
    "Azure Security Blog": "https://azure.microsoft.com/en-us/blog/tag/security/feed/",
    # Data Breach Today: For when you need to feel validated about your job security.
    "Data Breach Today": "https://www.databreachtoday.com/rss",

    # --- NEW: Incident Response & Management Feeds ---
    # The cavalry is coming... or at least, the blogs about them are.
    "Intezer Blog": "https://www.intezer.com/feed",
    "CrowdStrike Cybersecurity Blog": "https://www.crowdstrike.com/blog/feed/",
    "Windows Incident Response Blog": "https://windowsir.blogspot.com/feeds/posts/default",
    "My DFIR Blog": "https://dfir.ru/feed",
    "DFIR Diva": "https://dfirdiva.com/feed", # Because DFIR needs more divas.
    "Cisco Blog Incident Response": "https://blogs.cisco.com/tag/incident-response/feed/",
    "CIRCL": "https://www.circl.lu/rss.xml", # Computer Incident Response Center Luxembourg - sounds fancy.
    "Exigence Blog": "https://blog.exigence.io/feed",
    "Squadcast Blog": "https://squadcast.com/blog/rss.xml", # On-call for incidents, but also for blogs.
    "PagerTree Blog": "https://pagertree.com/blog/feed/", # More on-call, less sleep.
    "Rootly Blog": "https://rootly.com/blog/rss.xml", # Incident management, probably means less panic.
    "RadarFirst Incident Response": "https://radarfirst.com/blog/category/incident-response-management/feed/",
    "Arete Cybersecurity": "https://arete.com/feed/",
    "Infocyte Blog": "https://www.infocyte.com/feed/",
    "Exabeam Incident Response": "https://www.exabeam.com/blog/category/incident-response/feed/",
    # -------------------------------------------------
}

SEEN_ENTRIES_FILE = "seen_cyber_entries.json" # Where we keep track of what we've already nagged you about.
CHECK_INTERVAL_SECONDS = 300 # How often we bother the internet (5 minutes). Don't set this too low or you'll get blocked!
CRITICAL_KEYWORDS = ["ransomware", "zero-day", "rce", "privilege escalation", "authentication bypass", "exploit", "critical vulnerability", "malware", "ddos", "phishing", "supply chain"] # The words that make us go "uh oh".

# --- AI Insight Function (Updated for Gemini) ---
# This is where the magic eight-ball of AI gets its answers.
def get_ai_insights(title, message, link):
    """
    Sends article content to Gemini API for insights.
    Essentially, asks an AI: "So, what's the big deal here?"
    """
    prompt_parts = [
        # The AI's persona: a super-smart, slightly sarcastic cybersecurity expert.
        "As a highly skilled cybersecurity expert and red teamer analyzing threat intelligence for a Managed Security Service Provider (MSP), provide a concise analysis of the following article. Focus on the impact for an MSP's clients (typically SMBs to mid-market), potential attack vectors, immediate defensive actions, and relevant \"nerdy\" cybersecurity details (e.g., MITRE ATT&CK tactics, specific malware families, or exploit types).",
        "", # A little breathing room for the prompt.
        f"Article Title: {title}",
        f"Article Summary: {message}",
        f"Article Link: {link}", # Just in case the AI wants to do its own research (it won't, but good practice).
        "",
        "Provide your analysis in bullet points under the following headings:",
        "- **MSP Impact & Urgency:** (High/Medium/Low, why)", # How much should an MSP sweat?
        "- **Red Team Perspective:** (How attackers would leverage this)", # Thinking like the enemy.
        "- **Immediate Defenses for MSPs:** (Actionable steps)", # "Just patch it" usually isn't enough.
        "- **Nerdy Details:** (Technical insights, attack types, relevant frameworks like MITRE ATT&CK if applicable)" # The stuff we actually care about.
    ]

    try:
        logger.info(f"Requesting AI insights for: {title[:50]}...") # Just logging the first 50 chars, saves log space.
        # Ensure 'gemini-pro' is the correct model name for your region/API version.
        # Don't try 'gemini-ultra' unless you've got the beta access or a fat wallet.
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt_parts)
        ai_response = response.text
        logger.info("Received AI insights.")
        return ai_response
    except Exception as e:
        # If the AI breaks, we just tell you it broke. Can't fix everything.
        logger.error(f"An error occurred while getting AI insights from Gemini: {e}")
        return f"AI Insight Error: {e}" # Returns an error message instead of crashing.

# --- Notification Functions ---
# How we tell you the world is (or isn't) burning.

def send_desktop_notification(title, message, url=None, is_critical=False):
    """
    Sends a desktop notification using the 'notify-send' command,
    which should be symlinked to wsl-notify-send.exe for Windows.
    This is the part I eventually came to despise. Notifications are the worst.
    """
    full_message_body = f"{message}\nLink: {url}" if url else message

    try:
        command = [
            "notify-send",
            full_message_body,
            "--appId", "Cyber Notify (Critical)", # Gives it a nice app ID for grouping
            "--category", "Security Alert", # For proper OS classification
            # "--icon", "/mnt/c/Users/mikeg/Bin/cyber_icon.png", # Uncomment if you have a cool icon!
        ]

        # Using check=False because we want to log the error, not crash the script
        result = subprocess.run(command, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            logger.info(f"[DESKTOP NOTIFICATION SENT - CRITICAL] Title: {title}, Message: {full_message_body[:70]}...")
        else:
            # If notify-send fails, we'll know why. Probably because WSL is being finicky.
            logger.error(f"Failed to send critical desktop notification. Return code: {result.returncode}")
            logger.error(f"STDOUT from notify-send: {result.stdout.strip()}")
            logger.error(f"STDERR from notify-send: {result.stderr.strip()}")

    except FileNotFoundError:
        # This means notify-send isn't where it should be. Check your symlinks!
        logger.error("Error: 'notify-send' command not found. Ensure wsl-notify-send is correctly symlinked/aliased.")
    except Exception as e:
        # Unexpected errors are the worst kind of errors.
        logger.error(f"An unexpected error occurred during critical desktop notification: {e}")


def print_to_terminal(title, message, url, is_new=False, is_critical=False, ai_insights=None):
    """
    Prints the notification details directly to the terminal with colors, including AI insights.
    This is the main event. No annoying pop-ups, just good old command line goodness.
    """
    if is_critical:
        status_tag = f"{RED}{BOLD}!!! CRITICAL ALERT !!!{RESET}" # Red means danger!
        title_color = RED
    elif is_new:
        status_tag = f"{GREEN}{BOLD}[NEW]{RESET}" # Green for fresh content.
        title_color = BLUE # A nice blue for the title.
    else:
        status_tag = f"{CYAN}[INFO]{RESET}" # Cyan for just general info (less common as we filter for new).
        title_color = CYAN

    # Calculate dash length for pretty formatting, stripping ANSI codes first.
    # Because nobody wants a header that's too short or too long.
    clean_status_tag = status_tag.replace(RESET, '').replace(BOLD, '').replace(RED, '').replace(GREEN, '').replace(YELLOW, '').replace(BLUE, '').replace(CYAN, '').replace(MAGENTA, '')
    clean_title = title # Assuming title doesn't have ANSI, if it did, we'd clean it too.
    dash_length = len(clean_status_tag) + len(clean_title) + 8 # Just a nice heuristic.

    print(f"\n{status_tag} {title_color}{BOLD}{title}{RESET}")
    print(f"{CYAN}{'-' * dash_length}{RESET}") # A nice separator for readability.
    print(f"   {BOLD}Message:{RESET} {message}")
    if url:
        print(f"   {BOLD}Link:{RESET} {url}")

    if ai_insights:
        print(f"\n{ORANGE}{BOLD}--- AI Insights ---{RESET}") # AI section header.
        print(f"{ORANGE}{ai_insights}{RESET}") # The actual AI wisdom.
        print(f"{ORANGE}{'-------------------'}{RESET}") # End of AI section.

    print(f"{CYAN}{'-' * 30}{RESET}") # A smaller separator at the end of each entry.


def load_seen_entries():
    """
    Loads the last seen entry IDs from a JSON file.
    Prevents us from spamming you with the same old news.
    """
    if os.path.exists(SEEN_ENTRIES_FILE):
        try:
            with open(SEEN_ENTRIES_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            # If the JSON is corrupted, we start fresh. Better than crashing.
            logger.error(f"Error decoding {SEEN_ENTRIES_FILE}: {e}. Starting with empty seen entries.")
            return {}
    return {} # If the file doesn't exist, it's a new day!

def save_seen_entries(seen_entries):
    """
    Saves the last seen entry IDs to a JSON file.
    Remembering what we've seen, like a digital elephant.
    """
    try:
        with open(SEEN_ENTRIES_FILE, 'w') as f:
            json.dump(seen_entries, f, indent=4) # Pretty print the JSON, because we're civilized.
    except Exception as e:
        # If we can't save, that's a problem. We need our memory!
        logger.error(f"Error saving {SEEN_ENTRIES_FILE}: {e}")

def check_for_new_entries(seen_entries):
    """
    Checks each feed for new entries and sends notifications.
    The heart of the operation: go fetch!
    """
    items_to_save_as_seen = {} # Temporarily store new seen items before saving.
    total_new_items = 0

    for feed_name, feed_url in FEEDS.items():
        logger.info(f"Checking feed: {feed_name}")
        try:
            # Timeout is crucial! We don't want to hang forever on a dead feed.
            response = requests.get(feed_url, timeout=15)
            response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)

            feed = feedparser.parse(response.content)

            if feed.bozo:
                # "Bozo bit" means the feed is a bit goofy, but we'll try anyway.
                logger.warning(f"Feed '{feed_name}' has parsing errors (Bozo bit set): {feed.bozo_exception}. Proceeding cautiously.")

            if not feed.entries:
                logger.info(f"No entries found for {feed_name}.")
                # If no entries, we keep the previous seen ID for this feed.
                items_to_save_as_seen[feed_name] = seen_entries.get(feed_name)
                continue # Move to the next feed.

            latest_id_from_feed = None
            if feed.entries:
                # Try to get a unique ID. Order of preference: 'id', 'link', 'guid', then a desperate fallback.
                # RSS feed IDs can be a chaotic mess, bless their hearts.
                if feed.entries[0].get('id'):
                    latest_id_from_feed = feed.entries[0].id
                elif feed.entries[0].get('link'):
                    latest_id_from_feed = feed.entries[0].link
                elif feed.entries[0].get('guid'):
                    latest_id_from_feed = feed.entries[0].guid
                else:
                    # The "oh well, let's just combine title and published date" strategy.
                    logger.warning(f"Using less reliable ID fallback for '{feed_name}': {latest_id_from_feed}")
                    latest_id_from_feed = feed.entries[0].title + (feed.entries[0].published if hasattr(feed.entries[0], 'published') else '')


            # If the latest entry in the feed is what we last saw, nothing new here. Move along.
            if latest_id_from_feed and str(latest_id_from_feed) == str(seen_entries.get(feed_name)):
                logger.info(f"No new entries for {feed_name}.")
                items_to_save_as_seen[feed_name] = seen_entries.get(feed_name)
                continue

            # Iterate through entries in reverse chronological order (oldest new first).
            # This makes sure you see the news as it "arrived" since last check.
            for entry in reversed(feed.entries):
                entry_id = None
                if entry.get('id'):
                    entry_id = entry.id
                elif entry.get('link'):
                    entry_id = entry.link
                elif entry.get('guid'):
                    entry_id = entry.guid
                else:
                    # Again, the fallback for poorly behaved feeds.
                    entry_id = entry.title + (entry.published if hasattr(entry, 'published') else '')

                if not entry_id:
                    logger.warning(f"Could not get a unique ID for an entry in {feed_name}. Skipping this entry.")
                    continue # Can't track it if we can't identify it.

                # Stop processing once we hit an entry we've already seen.
                if str(entry_id) == str(seen_entries.get(feed_name)):
                    break

                total_new_items += 1 # A new item! Increment the counter.

                # Extract title, link, and message (summary/description)
                # Being robust here because RSS feeds are like snowflakes, no two are exactly alike.
                title = entry.title if hasattr(entry, 'title') else "No Title"
                link = entry.link if hasattr(entry, 'link') else "No Link"
                message = entry.summary if hasattr(entry, 'summary') else (
                                entry.description if hasattr(entry, 'description') else "No description available.")

                # Clean HTML tags from the message for cleaner terminal output.
                # Nobody wants raw HTML in their threat intel.
                message_soup = BeautifulSoup(message, 'html.parser')
                clean_message = message_soup.get_text(separator=' ', strip=True)

                is_critical = False
                # Check for "oh crap" keywords in title or message.
                for keyword in CRITICAL_KEYWORDS:
                    if keyword in title.lower() or keyword in clean_message.lower():
                        is_critical = True
                        break

                ai_insights_text = None
                if is_critical:
                    # If it's critical, ask the AI for its two cents (or more).
                    ai_insights_text = get_ai_insights(title, clean_message, link)

                # Send it to the terminal. This is what we came for!
                print_to_terminal(f"{feed_name}: {title}", clean_message, link, is_new=True, is_critical=is_critical, ai_insights=ai_insights_text)

                if is_critical:
                    # If it's super important, try the desktop notification (if you haven't disabled it yet).
                    send_desktop_notification(f"{feed_name}: {title}", clean_message, link, is_critical=True)

            # After processing all new entries for this feed, update its latest seen ID.
            if latest_id_from_feed:
                items_to_save_as_seen[feed_name] = latest_id_from_feed

        except requests.exceptions.Timeout:
            logger.error(f"Timeout occurred while fetching {feed_name}. Skipping this check.")
        except requests.exceptions.RequestException as req_err:
            # For network issues, 404s, 503s, etc. Internet can be a fickle beast.
            logger.error(f"Network error fetching {feed_name}: {req_err}. Skipping this check.")
        except Exception as e:
            # The ultimate fallback for anything else that goes wrong.
            logger.error(f"An unexpected error occurred processing {feed_name}: {e}")

    if total_new_items > 0:
        # Only save if there were actual new items. No need to rewrite the file for no reason.
        seen_entries.update(items_to_save_as_seen)
        save_seen_entries(seen_entries)
        logger.info(f"Total new items processed: {total_new_items}. Seen entries updated.")
    else:
        logger.info("No new cybersecurity notifications found during this check. Time for a coffee break!")

# --- Main Loop ---
# The endless cycle of checking for doom and gloom.
if __name__ == "__main__":
    seen_entries = load_seen_entries() # Load our memory bank.
    logger.info("Starting cybersecurity notification service...")
    logger.info(f"Initial check. Checking every {CHECK_INTERVAL_SECONDS} seconds. Press Ctrl+C to stop. (Or just close the terminal, I won't judge.)")

    try:
        while True:
            check_for_new_entries(seen_entries) # Do the deed.
            logger.info(f"\nWaiting {CHECK_INTERVAL_SECONDS} seconds for next check... (Tick-tock, threat actors are probably not waiting.)")
            time.sleep(CHECK_INTERVAL_SECONDS) # Take a nap.
    except KeyboardInterrupt:
        logger.info("\nNotification service stopped gracefully. You survived another day! (Go get some actual sleep.)") # A polite farewell.