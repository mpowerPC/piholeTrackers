import json
import os
import re
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
    all_domains_by_type = {}

    for tracker in trackers:

        tracker_type = tracker['type']
        domain_url = tracker['domain']

        response = requests.get(domain_url)
        if response.status_code == 200:
            file_content = response.text
            domains = read_domains(file_content)
            print(domains)
            if tracker_type not in all_domains_by_type:
                all_domains_by_type[tracker_type] = []

            all_domains_by_type[tracker_type].extend(domains)
        else:
            print(f'Failed to fetch {domain_url}: {response.status_code}')

        break

    return all_domains_by_type

trackers = read_trackers()
all_domains = fetch_and_process_trackers(trackers)
print('All Domains:', all_domains)
