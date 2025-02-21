import json
import os
import re
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get environment variables
api_key = os.getenv('PI_HOLE_API')

# Print environment variables
print(f'PI_HOLE_API: {api_key}')

def read_trackers():
    with open('trackers.json', 'r', encoding='utf8') as file:
        trackers = json.load(file)
    return trackers

def read_domains(file_content):
    ip_pattern = re.compile(r'^\d{1,3}(?:\.\d{1,3}){3}\s+')
    comment_pattern = re.compile(r'\s*#.*')
    domains = []

    for line in file_content.splitlines():
        domain = line.replace('\r', '').strip().lower()
        if not domain:
            continue
        if domain.startswith('!') or domain.startswith('['):
            continue
        if re.search(r'[a-zA-Z](##|#!#|#@#|#?#)', domain):
            continue
        domain = re.sub(ip_pattern, '', domain)
        domain = re.sub(comment_pattern, '', domain).strip()
        if not domain:
            continue

        if re.search(r'^(((?!-))(xn--|_)?[a-z0-9-]{0,61}[a-z0-9]{1,1}\.)*(xn--)?([a-z0-9][a-z0-9\-]{0,60}|[a-z0-9-]{1,30}\.[a-z]{2,})$', domain):
            domains.append(domain)

        domains.append(domain)

    return domains


def fetch_and_process_trackers(trackers):
    priority = ['malicious', 'tracker', 'ads', 'other']

    all_domains_by_type = {}
    for tracker in trackers:
        tracker_type = tracker['type']
        domain_url = tracker['domain']

        print(f'Fetching domains from {domain_url}')

        response = requests.get(domain_url)
        if response.status_code == 200:
            file_content = response.text
            domains = read_domains(file_content)
            if tracker_type not in all_domains_by_type:
                all_domains_by_type[tracker_type] = []

            all_domains_by_type[tracker_type].extend(domains)
        else:
            print(f'Failed to fetch {domain_url}: {response.status_code}')

    prioritized_domains = {}
    domain_tracker_map = {}

    for domain_type in priority:
        print(f'Fetching {domain_type} trackers')
        if domain_type in all_domains_by_type:
            for domain in all_domains_by_type[domain_type]:
                if domain not in domain_tracker_map:
                    domain_tracker_map[domain] = domain_type
                    if domain_type not in prioritized_domains:
                        prioritized_domains[domain_type] = []
                    prioritized_domains[domain_type].append(domain)

    return prioritized_domains


def save_domains_to_files(domains_by_type):

    for tracker_type, domains in domains_by_type.items():
        file_path = os.path.join('lists', f'{tracker_type}-list.txt')
        with open(file_path, 'w', encoding='utf8') as file:
            file.write(f'# Blocklist for {tracker_type} hosts\n')
            file.write(f'# ----\n')
            file.write(f'# last updated on {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")} UTC\n')
            file.write(f'# entries: {len(domains)}\n')
            file.write(f'#\n')
            for domain in domains:
                file.write(f'0.0.0.0 {domain}\n')

        print(f'saved domains to files: {file_path}')

# Load trackers
trackers = read_trackers()
# Fetch and process domains by type
all_domains_by_type = fetch_and_process_trackers(trackers)
# Save domains to files
save_domains_to_files(all_domains_by_type)