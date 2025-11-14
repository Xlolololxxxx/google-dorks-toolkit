from googlesearch import search
from enum import Enum
import argparse
import pyfiglet
import re
import subprocess
import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from urllib.parse import urlparse
from datetime import datetime

# Print the name in cool way
result = pyfiglet.figlet_format("GoogleDorks Toolkit")
print(result)

x = '\033[0m'
u = '\033[4m'
R = '\033[1;91m'
r = '\033[0;91m'
g = '\033[0;92m'
y = '\033[0;33m'
w = '\033[0;37m'

def print_dotted_text_with_developers(text, developers):
    border = f'{R}+' + '.' * (len(text) + 2) + f'{R}+'
    content = f'{R}| {text} |'
    developer_info = f'{R}| Developers: {", ".join(developers)} |'

    print(border)
    print(content)
    print(border)
    print(developer_info)
    print(border)

text_to_display = "Seiyun University - seiyunu.edu.ye"
developers_list = ["Saleh Lardhi", "Zaid Frarah", "Mohammed Mahros"]
print_dotted_text_with_developers(text_to_display, developers_list)
print('\033[0;37m \033[0m')

# URL Normalizer
def normalize_url(domain):
    """
    Normalize URL by adding https:// if missing and handling www for main domains.
    www is only added for main domains, not subdomains like api.domain.com
    """
    domain = domain.strip()

    # Remove trailing slash
    domain = domain.rstrip('/')

    # If already has protocol, just return it
    if domain.startswith('http://') or domain.startswith('https://'):
        return domain

    # Check if it's a subdomain (has more than 2 parts before TLD)
    # Count dots to determine if it's a subdomain
    parts = domain.split('.')

    # If no protocol, add https://
    # Only add www if it's a main domain (2 parts like example.com)
    # Don't add www if it's already there or if it's a subdomain
    if len(parts) == 2 and not domain.startswith('www.'):
        # Main domain without www, add both https:// and www
        return f'https://www.{domain}'
    else:
        # Subdomain or already has www, just add https://
        return f'https://{domain}'

def extract_base_name(domain):
    """
    Extract base name from domain for file naming.
    Example: https://www.example.com -> example
    Example: api.example.com -> api.example
    """
    # Remove protocol if present
    domain = re.sub(r'https?://', '', domain)
    # Remove www. if present
    domain = re.sub(r'^www\.', '', domain)
    # Remove trailing slash
    domain = domain.rstrip('/')
    # Remove TLD extensions
    domain = re.sub(r'\.(com|org|net|edu|gov|io|co|uk|de|fr|jp|cn|in|au|br|ru|it|es|nl|se|no|dk|fi|pl|be|ch|at|gr|cz|pt|ie|nz|za|mx|ar|cl|pe|ve|co\.uk|co\.in|co\.za|com\.au|com\.br)$', '', domain)
    # Replace dots with underscores for file naming
    domain = domain.replace('.', '_')
    return domain

class RateLimiter:
    """
    Auto rate limiter with adaptive backoff
    """
    def __init__(self, initial_delay=2.0, max_delay=60.0, backoff_factor=1.5):
        self.delay = initial_delay
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.lock = Lock()
        self.last_request_time = 0
        self.success_count = 0
        self.error_count = 0

    def wait(self):
        """Wait before making next request"""
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time

            if time_since_last < self.delay:
                sleep_time = self.delay - time_since_last
                time.sleep(sleep_time)

            self.last_request_time = time.time()

    def report_success(self):
        """Report successful request to potentially decrease delay"""
        with self.lock:
            self.success_count += 1
            self.error_count = 0

            # After 5 successful requests, reduce delay slightly
            if self.success_count >= 5:
                self.delay = max(self.initial_delay, self.delay * 0.9)
                self.success_count = 0

    def report_error(self):
        """Report failed request to increase delay"""
        with self.lock:
            self.error_count += 1
            self.success_count = 0

            # Increase delay with backoff
            self.delay = min(self.max_delay, self.delay * self.backoff_factor)
            print(f'{y}Rate limit detected, increasing delay to {self.delay:.2f}s{x}')

class ResultsWriter:
    """
    Thread-safe JSON writer for real-time output
    """
    def __init__(self, output_file):
        self.output_file = output_file
        self.lock = Lock()
        self.results = {
            'scan_info': {
                'start_time': datetime.now().isoformat(),
                'domain': '',
                'total_dorks': 0,
                'total_urls_found': 0
            },
            'results': []
        }

        # Initialize the file
        self._write_to_file()

    def set_scan_info(self, domain, total_dorks):
        """Set scan information"""
        with self.lock:
            self.results['scan_info']['domain'] = domain
            self.results['scan_info']['total_dorks'] = total_dorks
            self._write_to_file()

    def add_result(self, dork_info, urls):
        """Add a result and immediately write to file"""
        with self.lock:
            if urls:
                result_entry = {
                    'dork': dork_info['dork'],
                    'author': dork_info['author'],
                    'reference': dork_info['reference'],
                    'severity': dork_info['severity'],
                    'urls': urls,
                    'url_count': len(urls),
                    'timestamp': datetime.now().isoformat()
                }
                self.results['results'].append(result_entry)
                self.results['scan_info']['total_urls_found'] += len(urls)
                self._write_to_file()

    def finalize(self):
        """Finalize the results file"""
        with self.lock:
            self.results['scan_info']['end_time'] = datetime.now().isoformat()
            self._write_to_file()

    def _write_to_file(self):
        """Write results to file"""
        try:
            with open(self.output_file, 'w') as f:
                json.dump(self.results, f, indent=2)
        except Exception as e:
            print(f'{R}Error writing to file: {e}{x}')

def process_single_dork(dork_line, domain, num_of_pages, rate_limiter, search_in_vdp, results_writer):
    """
    Process a single dork query with error handling
    """
    try:
        # Parse dork line
        parts = list(map(str.strip, dork_line.split('<>')))
        if len(parts) < 4:
            print(f'{R}Invalid dork format: {dork_line}{x}')
            return None

        dork, author, reference, severity = parts[:4]
        query = f'{dork} site:{domain}'

        dork_info = {
            'dork': dork,
            'author': author,
            'reference': reference,
            'severity': severity
        }

        print(f'\n{g}Checking Dork: {query}{x}')
        print(f'{y}Author: {author} | Reference: {reference} | Severity: {severity}{x}')

        urls = []
        counter = 0

        try:
            # Wait for rate limiter
            rate_limiter.wait()

            for url in search(query, tld='com', num=num_of_pages, stop=num_of_pages, pause=2):
                urls.append(url)
                counter += 1
                print(f'{g}{counter}) {url}{x}')

                # Extract the domain from the URL
                try:
                    extracted_domain = re.search(r'https?://([^/]+)', url).group(1)

                    # Check if --search option is specified
                    if search_in_vdp and search_in_vdp.lower() in ["yes", "y"]:
                        grep_command = f"grep -q {extracted_domain} OpenForReport.txt"
                        grep_process = subprocess.run(grep_command, shell=True, capture_output=True)

                        if grep_process.returncode == 0:
                            print(f'{R}Note:{x} {g}This Website ( {extracted_domain} ) is vulnerable and has VDP/bbp so, you can report them legally!{x}')
                except Exception as e:
                    print(f'{y}Warning: Could not extract domain from {url}: {e}{x}')

                if counter >= num_of_pages:
                    break

            # Report success to rate limiter
            rate_limiter.report_success()

        except Exception as e:
            print(f'{R}Error searching dork "{dork}": {e}{x}')
            rate_limiter.report_error()

        # Save results immediately
        if urls:
            results_writer.add_result(dork_info, urls)
            print(f'{g}Found {len(urls)} URLs for this dork{x}')
        else:
            print(f'{y}No URLs found for this dork{x}')

        return {
            'dork_info': dork_info,
            'urls': urls
        }

    except Exception as e:
        print(f'{R}Error processing dork: {e}{x}')
        return None

# Create an argument parser
parser = argparse.ArgumentParser(
    description='Google Dorks Toolkit - Automated dorking with parallel processing and auto rate limiting',
    formatter_class=argparse.RawDescriptionHelpFormatter
)

# Add command-line arguments
parser.add_argument('-d', '--domain', required=True, help='Domain to search (auto-normalizes URLs)')
parser.add_argument('-n', '--number_of_pages', type=int, default=3, help='Number of pages to search per dork (default: 3)')
parser.add_argument('-o', '--output', help='Specify output file name (default: auto-generated from domain)')
parser.add_argument('--search', help='Search matched domains in OpenForReport.txt (yes/y)')
parser.add_argument('-l', '--list', help='Add your own dorks list (default: dorks.txt)')
parser.add_argument('-w', '--workers', type=int, default=3, help='Number of parallel workers (default: 3)')
parser.add_argument('--initial-delay', type=float, default=2.0, help='Initial delay between requests in seconds (default: 2.0)')

# Parse the command-line arguments
args = parser.parse_args()

# Normalize domain URL
domain = normalize_url(args.domain)
print(f'{g}Normalized domain: {domain}{x}')

# Extract base name for output file
base_name = extract_base_name(args.domain)

# Set default output file if not specified
if args.output:
    output_file = args.output
    # Add .json extension if not present
    if not output_file.endswith('.json'):
        output_file += '.json'
else:
    # Auto-generate filename from domain
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'{base_name}_dorks_{timestamp}.json'

print(f'{g}Output file: {output_file}{x}')

num_of_pages = args.number_of_pages
dorks_list_file = args.list or "dorks.txt"
search_in_vdp = args.search
max_workers = args.workers

# Initialize rate limiter
rate_limiter = RateLimiter(initial_delay=args.initial_delay)

# Initialize results writer
results_writer = ResultsWriter(output_file)

try:
    with open(dorks_list_file, 'r') as dorks_file:
        dorks = [line.strip() for line in dorks_file.readlines() if line.strip()]

    print(f'\n{g}Loaded {len(dorks)} dorks from {dorks_list_file}{x}')
    print(f'{g}Using {max_workers} parallel workers{x}')
    print(f'{g}Searching {num_of_pages} pages per dork{x}\n')

    # Set scan info
    results_writer.set_scan_info(domain, len(dorks))

    # Process dorks in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all dork processing tasks
        future_to_dork = {
            executor.submit(
                process_single_dork,
                dork_line,
                domain,
                num_of_pages,
                rate_limiter,
                search_in_vdp,
                results_writer
            ): dork_line for dork_line in dorks
        }

        # Process completed tasks
        completed = 0
        total = len(dorks)

        for future in as_completed(future_to_dork):
            completed += 1
            dork_line = future_to_dork[future]

            try:
                result = future.result()
                print(f'\n{g}Progress: {completed}/{total} dorks completed{x}')
            except Exception as e:
                print(f'{R}Error processing dork: {e}{x}')

    # Finalize results
    results_writer.finalize()

    print(f'\n{g}{"="*60}{x}')
    print(f'{g}Scan completed!{x}')
    print(f'{g}Total URLs found: {results_writer.results["scan_info"]["total_urls_found"]}{x}')
    print(f'{g}Results saved to: {output_file}{x}')
    print(f'{g}{"="*60}{x}')

except FileNotFoundError:
    print(f'{R}Error: Could not find dorks file: {dorks_list_file}{x}')
    print(f'{y}Please ensure the dorks file exists{x}')

except KeyboardInterrupt:
    print(f'\n{y}Exit! Saving partial results...{x}')
    results_writer.finalize()
    print(f'{g}Partial results saved to: {output_file}{x}')
    print(f'{g}Thanks for using!{x}')

except Exception as e:
    print(f'{R}An error occurred: {e}{x}')
    results_writer.finalize()
    print(f'{g}Partial results saved to: {output_file}{x}')
