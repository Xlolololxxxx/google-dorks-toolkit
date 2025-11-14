# GoogleDorks Toolkit

![GoogleDorks Toolkit](https://raw.githubusercontent.com/SalehLardhi/google-dorks-toolkit/main/image.png)

GoogleDorks Toolkit is a Python script designed to help security researchers and penetration testers automate Google dorking for finding potential vulnerabilities and information about a target domain. The tool utilizes Google search queries, also known as Google hacks, to identify possible security issues and gather valuable information.

## Features

- **Parallel Processing**: Process multiple dorks concurrently for faster results with configurable worker threads.
- **Auto Rate Limiting**: Intelligent rate limiting with adaptive backoff to avoid Google blocks automatically.
- **URL Normalization**: Automatically handles missing https:// and www prefixes for domains.
- **Real-time JSON Output**: Results are saved to JSON file as they're found, with automatic data preservation.
- **Graceful Error Handling**: Continues processing even if errors occur, saving partial results.
- **Customizable Dorks**: Users can provide their own list of dorks to be used in the Google search queries with huge list of default Google Dorks list.
- **Domain Search**: The tool allows users to specify a target domain for the Google dorking process.
- **Detailed Results**: Not only the vulnerable webapps and the dork, but also the author and reference link of the dork for more information.
- **Vulnerability Disclosure and Bug Bounty Checker**: Optional detection of vulnerabilities by searching for the identified domains in existing file `OpenForReport.txt` which own VDP or BBP programs to report legally.

## Usage

## Prerequisites

- Python 3.x
- Required Python packages: `googlesearch`, `enum`, `argparse`, `pyfiglet`

## Installation



```
chmod +x setup.sh
./setup.sh
```

### Kali Linux
```
apt update; apt upgrade
git clone https://github.com/SalehLardhi/google-dorks-toolkit.git
cd google-dorks-toolkit
```
### Termux
```
pkg update; pkg upgrade
git clone https://github.com/SalehLardhi/google-dorks-toolkit.git
cd google-dorks-toolkit
```


## Command-line Arguments

    - `-d`, `--domain`: Specify the target domain for Google dorking (required). URLs are auto-normalized.
    - `-n`, `--number_of_pages`: Set the number of pages to search per dork (optional, default: 3).
    - `-o`, `--output`: (Optional) Specify the output JSON file name. If not specified, automatically generated from domain name with timestamp.
    - `-w`, `--workers`: (Optional) Number of parallel workers for concurrent processing (default: 3).
    - `--initial-delay`: (Optional) Initial delay between requests in seconds (default: 2.0). Auto-adjusts based on rate limiting.
    - `--search`: (Optional) Search matched domains in OpenForReport.txt, note that the output should be yes or y only.
    - `-l`, `--list`: (Optional) Add your own dorks list (default: dorks.txt).

## Examples

### Basic usage (minimal command):
```bash
python GoogleDorks-toolkit.py -d example.com
```
This will:
- Search example.com with 3 pages per dork (default)
- Use 3 parallel workers (default)
- Auto-generate output file: `example_dorks_YYYYMMDD_HHMMSS.json`
- Use automatic rate limiting

### Advanced usage:
```bash
python GoogleDorks-toolkit.py -d example.com -n 5 -w 5 -o custom_results.json --search yes
```

### URL normalization examples:
```bash
# All of these will be normalized to https://www.example.com
python GoogleDorks-toolkit.py -d example.com
python GoogleDorks-toolkit.py -d www.example.com
python GoogleDorks-toolkit.py -d https://example.com

# Subdomains won't get www added (correctly kept as-is):
python GoogleDorks-toolkit.py -d api.example.com  # → https://api.example.com
```

## Output Format

Results are saved in JSON format with the following structure:

```json
{
  "scan_info": {
    "start_time": "2025-11-14T10:30:00",
    "end_time": "2025-11-14T10:45:00",
    "domain": "https://www.example.com",
    "total_dorks": 47,
    "total_urls_found": 125
  },
  "results": [
    {
      "dork": "intitle:\"Index of/\"",
      "author": "Exploit-db",
      "reference": "https://www.exploit-db.com/google-hacking-database",
      "severity": "low",
      "urls": [
        "https://www.example.com/path1",
        "https://www.example.com/path2"
      ],
      "url_count": 2,
      "timestamp": "2025-11-14T10:31:00"
    }
  ]
}
```

**Features:**
- Results are written in real-time as they're found
- If interrupted (Ctrl+C), partial results are preserved
- Timestamps track when each dork was processed
- Scan info provides overview statistics

## Developers

- Saleh Lardhi
- Zaid Frarah
- Mohammed Mahros

## Note

This tool is intended for educational and ethical use only. Use it responsibly and ensure compliance with applicable laws and regulations.
## Disclaimer

The developers are not responsible for any misuse or damage caused by this script. Use it at your own risk.
