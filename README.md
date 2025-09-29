# ngDomainBot

A Python-based toolkit for checking and finding available Nigerian (.ng) domain names using the Domainr API, can be modified to search for other TLDs.

## Overview

ngDomainBot helps you discover available .ng domain names through various strategies:

- Check availability of domain names using the Domainr API
- Generate domain candidates from curated wordlists
- Track API usage to stay within rate limits
- Save results to CSV files for further analysis

## Features

- **Asynchronous Domain Checking**: Check multiple domains in parallel
- **Smart Word Selection**: Uses common English words, Nigerian terms, and industry-specific vocabularies
- **Domain Generation**: Creates domain candidates by combining words strategically
- **Specialized Modules**:
  - `domain_checker.py`: Main domain availability checker
  - `finance.py`: Finance-specific domain finder
  - `maternity.py`: Maternity/parenting domain finder
  - `blooket.py`: Educational domain checker
  - `clean.py`: Data cleaning utilities
  - `pronounce.py`: Pronunciation analysis

## Requirements

- Python 3.7+
- Required packages:
  - aiohttp
  - asyncio
  - wordfreq
  - certifi

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Configure your API key:
   ```
   cp config_local.py.template config_local.py
   ```
4. Edit `config_local.py` and add your RapidAPI key

## Usage

### Basic Domain Checking

```python
python domain_checker.py
```

### Finance-Specific Domains

```python
python finance.py
```

### Maternity/Parenting Domains

```python
python maternity.py
```

### Data Files

- `checked_domains.csv`: All checked domains with their status
- `available_domains.csv`: Only available domains
- `api_usage.json`: Tracks API call usage
- Various input/output CSV files for specific domain categories

## API Usage

This project uses the [Domainr API](https://rapidapi.com/domainr/api/domainr) through RapidAPI. You'll need to:

1. Sign up for a RapidAPI account
2. Subscribe to the Domainr API
3. Replace the `RAPIDAPI_KEY` in the scripts with your own key

## Project Structure

### Core Files
- `domain_checker.py`: Main domain availability checker
- `finance.py`: Finance-specific domain finder
- `maternity.py`: Maternity/parenting domain finder
- `blooket.py`: Educational domain checker
- `pronounce.py`: Pronunciation analysis tool
- `config.py`: Configuration settings
- `config_local.py.template`: Template for local configuration

### Data Files
These files are generated during runtime and are excluded from version control:
- `checked_domains.csv`: All checked domains with their status
- `available_domains.csv`: Only available domains
- `api_usage.json`: Tracks API call usage
- Various CSV files for specific domain categories

## License

MIT

## Author

Victor
