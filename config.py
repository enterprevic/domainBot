"""
Configuration file for ngDomainBot.
This file contains settings that should be modified by the user.
"""

# API Keys - Replace with your own keys
RAPIDAPI_KEY = "YOUR_RAPIDAPI_KEY"

# API Settings
API_HOST = "domainr.p.rapidapi.com"
API_CALL_LIMIT = 9750

# Domain Settings
DEFAULT_TLD = "ng"  # Change this to search for different TLDs

# Search Settings
MAX_WORD_LENGTH = 12
TOP_ENGLISH_WORDS = 5000
CONCURRENCY = 10
TARGET_DOMAIN_COUNT = 4000  # max domains to generate/check
