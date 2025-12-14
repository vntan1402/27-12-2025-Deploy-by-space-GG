"""
Manual trace of certificate abbreviation logic
Input: "CARGO SHIP SAFETY EQUIPMENT CERTIFICATE"
Expected: "CSSE"
Actual: "CSEC"
"""
import re

cert_name = "CARGO SHIP SAFETY EQUIPMENT CERTIFICATE"

print("=" * 80)
print("TRACE: Certificate Abbreviation Generation")
print("=" * 80)
print(f"Input: '{cert_name}'")
print()

# Step 1: Check if DOC certificate
print("STEP 1: Check if DOC certificate")
print("-" * 80)
cert_name_upper = cert_name.upper().strip()
print(f"cert_name_upper = '{cert_name_upper}'")
is_doc = 'DOCUMENT OF COMPLIANCE' in cert_name_upper or cert_name_upper == 'DOC'
print(f"Is DOC? {is_doc}")
print()

# Step 2: Clean certificate name
print("STEP 2: Clean certificate name")
print("-" * 80)
cert_name_cleaned = cert_name.upper()
print(f"After .upper(): '{cert_name_cleaned}'")

phrases_to_remove = [
    'STATEMENT OF COMPLIANCE',
    'STATEMENT OF COMPIANCE',
    'SOC',
]
print(f"Phrases to remove: {phrases_to_remove}")
for phrase in phrases_to_remove:
    before = cert_name_cleaned
    cert_name_cleaned = cert_name_cleaned.replace(phrase, '')
    if before != cert_name_cleaned:
        print(f"  Removed '{phrase}': '{cert_name_cleaned}'")

cert_name_cleaned = ' '.join(cert_name_cleaned.split())
print(f"After cleanup: '{cert_name_cleaned}'")
print()

# Step 3: Extract words
print("STEP 3: Extract words using regex")
print("-" * 80)
words = re.findall(r'\b[A-Za-z]+\b', cert_name_cleaned)
print(f"Extracted words: {words}")
print(f"Total words: {len(words)}")
print()

# Step 4: Filter common words
print("STEP 4: Filter common words")
print("-" * 80)
common_words = {'the', 'and', 'a', 'an', 'for', 'in', 'on', 'at', 'to', 'is', 'are', 'was', 'were'}
print(f"Common words to filter: {common_words}")
print()

significant_words = []
for i, word in enumerate(words):
    is_common = word.lower() in common_words
    print(f"  Word {i+1}: '{word}' -> {'FILTERED' if is_common else 'KEPT'}")
    if not is_common:
        significant_words.append(word)

print(f"\nSignificant words: {significant_words}")
print(f"Total significant words: {len(significant_words)}")
print()

# Step 5: Generate abbreviation (first letter of each word, max 6)
print("STEP 5: Generate abbreviation (max 6 letters)")
print("-" * 80)
print(f"Taking first {min(6, len(significant_words))} words")
selected_words = significant_words[:6]
print(f"Selected words: {selected_words}")
print()

letters = []
for i, word in enumerate(selected_words):
    letter = word[0]
    letters.append(letter)
    print(f"  Word {i+1}: '{word}' -> '{letter}'")

abbreviation = ''.join(letters)
print(f"\nAbbreviation after joining: '{abbreviation}'")
print(f"Length: {len(abbreviation)}")
print()

# Step 6: Remove trailing 'C' if last word is "CERTIFICATE"
print("STEP 6: Remove trailing 'C' if last word is 'CERTIFICATE'")
print("-" * 80)
print(f"Current abbreviation: '{abbreviation}'")
print(f"Ends with 'C'? {abbreviation.endswith('C')}")
print(f"Length > 1? {len(abbreviation) > 1}")
print(f"Has significant words? {len(significant_words) > 0}")
if len(significant_words) > 0:
    print(f"Last significant word: '{significant_words[-1]}'")
    print(f"Last word == 'CERTIFICATE'? {significant_words[-1].upper() == 'CERTIFICATE'}")

if (abbreviation.endswith('C') and len(abbreviation) > 1 and 
    len(significant_words) > 0 and significant_words[-1].upper() == 'CERTIFICATE'):
    print(f"✅ Condition MET: Removing trailing 'C'")
    abbreviation = abbreviation[:-1]
    print(f"After removal: '{abbreviation}'")
else:
    print(f"❌ Condition NOT MET: Keeping abbreviation as is")
print()

# Final result
print("=" * 80)
print(f"FINAL RESULT: '{abbreviation}'")
print(f"Expected: 'CSSE'")
print(f"Match? {abbreviation == 'CSSE'}")
print("=" * 80)
