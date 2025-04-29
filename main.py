# main.py
print("Webhook 1 loaded:", bool(WEBHOOK_URL_1))
print("Webhook 2 loaded:", bool(WEBHOOK_URL_2))

import os
import requests
from datetime import datetime
from bs4 import BeautifulSoup

# Setup webhooks
WEBHOOK_URL_1 = os.getenv('DISCORD_WEBHOOK_URL_1')
WEBHOOK_URL_2 = os.getenv('DISCORD_WEBHOOK_URL_2')
WEBHOOK_URLS = [WEBHOOK_URL_1, WEBHOOK_URL_2]

POSTED_FILE = 'posted_jams.txt'


def load_posted_jams():
    if not os.path.exists(POSTED_FILE):
        return set()
    with open(POSTED_FILE, 'r') as f:
        return set(line.strip() for line in f.readlines())


def save_posted_jam(jam_url):
    with open(POSTED_FILE, 'a') as f:
        f.write(jam_url + '\n')


def fetch_featured_ongoing_jams():
    url = 'https://itch.io/jams'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    jams = []
    now = datetime.utcnow()

    featured = soup.select_one('.featured_jams')
    if not featured:
        print("❌ Couldn't find featured jams section.")
        return jams

    for jam in featured.select('.jam'):
        link_tag = jam.select_one('a.title')
        date_range_tag = jam.select_one('.date_range')

        if not link_tag or not date_range_tag:
            continue

        jam_link = link_tag['href']
        full_url = f"https://itch.io{jam_link}" if jam_link.startswith(
            '/') else jam_link
        date_range = date_range_tag.get('title') or date_range_tag.text.strip()

        try:
            parts = date_range.split('–')
            if len(parts) != 2:
                continue

            start_str, end_str = parts
            start_time = datetime.strptime(start_str.strip(),
                                           '%B %d, %Y %I:%M %p UTC')
            end_time = datetime.strptime(end_str.strip(),
                                         '%B %d, %Y %I:%M %p UTC')

            if start_time <= now <= end_time:
                jams.append(full_url)
        except Exception as e:
            print(f"❌ Date parse error for {jam_link}: {e}")

    return jams


def post_to_discord(jams, posted_jams):
    for jam in jams:
        if jam in posted_jams:
            continue  # Skip already posted
        data = {"content": f"🌟 **Ongoing Featured Jam!** 🎮\n{jam}"}
        for webhook in WEBHOOK_URLS:
            if webhook:
                try:
                    res = requests.post(webhook, json=data)
                    if res.status_code == 204:
                        print(f"✅ Posted: {jam}")
                        posted_jams.add(jam)
                        save_posted_jam(jam)
                    else:
                        print(f"❌ Post failed ({res.status_code}): {res.text}")
                except Exception as e:
                    print(f"❌ Discord error: {e}")


def main():
    posted_jams = load_posted_jams()
    print("🚀 Checking for featured jams...")

    # Fetch the featured ongoing jams
    jams = fetch_featured_ongoing_jams()

    # If no jams were found, print a message
    if not jams:
        print("❌ No new featured jams found.")
    else:
        # If jams were found, post them to Discord
        post_to_discord(jams, posted_jams)

    print(f"✅ Checked at {datetime.utcnow()} UTC")


if __name__ == '__main__':
    main()
