import json
import os
import re
from datetime import datetime, timezone
import requests


def read_trackers():
    with open('trackers.json', 'r', encoding='utf8') as file:
        trackers = json.load(file)
    return trackers

def read_exceptions():
    with open('exceptions.json', 'r', encoding='utf8') as file:
        exceptions = json.load(file)
    return exceptions

def read_existing_domains(file_path):
    existing_domains = []
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf8') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    existing_domains.append(line.split()[1])
    return set(existing_domains)

def read_domains(file_content, regex_exceptions, host_exceptions):
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

        if domain_exceptions(domain, regex_exceptions, host_exceptions):
            continue

        if re.search(r'^(((?!-))(xn--|_)?[a-z0-9-]{0,61}[a-z0-9]{1,1}\.)*(xn--)?([a-z0-9][a-z0-9\-]{0,60}|[a-z0-9-]{1,30}\.[a-z]{2,})$', domain):
            domains.append(domain)

    return domains

def domain_exceptions(domain, regex_exceptions, host_exceptions):
    for exception in host_exceptions:
        if domain == exception:
            return True

    for exception in regex_exceptions:
        if re.search(exception, domain):
            return True

    return False

def fetch_and_process_trackers(trackers, exceptions):
    priority = ['malicious', 'tracker', 'ads', 'other']

    regex_exceptions = []
    host_exceptions = []
    for exception in exceptions:
        if exception['type'] == 'host':
            host_exceptions.append(exception['domain'])
        elif exception['type'] == 'regex':
            regex_exceptions.append(exception['domain'])

    all_domains_by_type = {}
    for tracker in trackers:
        tracker_type = tracker['type']
        domain_url = tracker['domain']

        print(f'Fetching domains from {domain_url}')

        response = requests.get(domain_url)
        if response.status_code == 200:
            file_content = response.text
            domains = read_domains(file_content, regex_exceptions, host_exceptions)
            if tracker_type not in all_domains_by_type:
                all_domains_by_type[tracker_type] = []

            all_domains_by_type[tracker_type].extend(domains)
        else:
            print(f'Failed to fetch {domain_url}: {response.status_code}')

    prioritized_domains = {}
    domain_tracker_map = {}

    for domain_type in priority:
        if domain_type in all_domains_by_type:
            for domain in all_domains_by_type[domain_type]:
                if domain not in domain_tracker_map:
                    domain_tracker_map[domain] = domain_type
                    if domain_type not in prioritized_domains:
                        prioritized_domains[domain_type] = []
                    prioritized_domains[domain_type].append(domain)

    for tracker_type, domains in prioritized_domains.items():
        prioritized_domains[tracker_type] = set(domains)

    return prioritized_domains

def save_domains_to_files(domains_by_type):
    for tracker_type, domains in domains_by_type.items():
        file_path = os.path.join('lists', f'{tracker_type}-list.txt')
        existing_domains = read_existing_domains(file_path)
        new_domains = list(domains - existing_domains)
        removed_domains = list(existing_domains - domains)
        domains = sorted(list(domains))
        if removed_domains or new_domains:
            with open(file_path, 'w', encoding='utf8') as file:
                file.write(f'# Blocklist for {tracker_type} hosts\n')
                file.write(f'# ----\n')
                file.write(f'# last updated on {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")} UTC\n')
                file.write(f'# entries: {len(domains)}\n')
                file.write(f'# additions: {len(new_domains)}\n')
                file.write(f'# removals: {len(removed_domains)}\n')
                file.write(f'#\n')
                for domain in domains:
                    file.write(f'0.0.0.0 {domain}\n')

            print(f'saved domains to files: {file_path}')

def update_lists():
    trackers = read_trackers()
    exceptions = read_exceptions()
    all_domains_by_type = fetch_and_process_trackers(trackers, exceptions)
    save_domains_to_files(all_domains_by_type)

if __name__ == '__main__':
    update_lists()
