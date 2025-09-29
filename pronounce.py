import csv
from wordfreq import top_n_list
import re

# Load the most common English words
common_words = set(top_n_list('en', 5000))

def pronounceability_score(domain):
    """
    Simple estimate: domains with common words get higher score.
    Shorter syllables = easier to pronounce.
    """
    domain = re.sub(r'\.ng$', '', domain.lower())
    
    # Score by word match
    words = re.split(r'[-_]', domain)
    score = 0
    for word in words:
        if word in common_words:
            score += 2
        # Short words are easier to remember
        if len(word) <= 5:
            score += 1
        # Penalize numbers and special characters
        if re.search(r'\d', word):
            score -= 1
    return score

def length_score(domain):
    domain = re.sub(r'\.ng$', '', domain)
    if len(domain) <= 5:
        return 3
    elif len(domain) <= 8:
        return 2
    elif len(domain) <= 12:
        return 1
    else:
        return 0

def marketability_score(domain):
    """
    Combine factors
    """
    return pronounceability_score(domain) + length_score(domain)

# Load CSV
input_file = 'available_domains.csv'
output_file = 'ranked_domains.csv'

domains = []
with open(input_file, 'r', newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
        domain = row[0].strip()
        score = marketability_score(domain)
        domains.append((domain, score))

# Sort by score descending
domains.sort(key=lambda x: x[1], reverse=True)

# Save ranked CSV
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Domain', 'Score'])
    for domain, score in domains:
        writer.writerow([domain, score])

print(f"Ranked domains saved to {output_file}")