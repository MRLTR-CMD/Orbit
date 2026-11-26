#!/usr/bin/env python3
"""Builds Orbit/Resources/Localizable.xcstrings.

Keys come from two places:
  1. SwiftUI literals the compiler extracts (build with SWIFT_EMIT_LOC_STRINGS=YES first).
  2. Plain string literals in Swift sources that reach the UI through `.loc`.
Translations live in tools/i18n/<locale>*.json (English key → translation).
Run with --missing --locale zh-Hans to list untranslated keys for Simplified Chinese.
"""
import argparse, glob, json, os, re, subprocess, sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root)
catalog_path = 'Orbit/Resources/Localizable.xcstrings'
locales = ('ko', 'zh-Hans')
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--missing', action='store_true')
parser.add_argument('--locale', choices=locales, default='ko')
args = parser.parse_args()

if not args.missing:
    subprocess.run([sys.executable, 'tools/settings_index.py'], check=True)

extracted = set()
previous = {}
if os.path.isfile(catalog_path):
    with open(catalog_path, encoding='utf-8') as existing:
        previous = json.load(existing)['strings']
extraction_files = glob.glob('build/Build/Intermediates.noindex/Orbit.build/**/*.stringsdata', recursive=True)
for f in extraction_files:
    data = json.load(open(f))
    for entry in data.get('tables', {}).get('Localizable', []):
        extracted.add(entry['key'])
if not extraction_files:
    # Keep compiler-generated keys when updating translations without a local Xcode build.
    extracted.update(key for key, entry in previous.items() if entry.get('extractionState') != 'manual')

literal = re.compile(r'"((?:[^"\\\n]|\\.)*)"')
def looks_like_ui(s):
    if not re.search(r'[A-Za-z]', s) or '\\(' in s: return False
    if re.fullmatch(r'[a-z0-9_.\-]+', s): return False          # SF Symbols, identifiers
    if re.fullmatch(r'[a-zA-Z]+[A-Z][a-zA-Z]*', s) and s[0].islower(): return False  # camelCase ids
    if s.startswith(('com.', '/', 'http', 'public.', 'NS', 'AX', 'kAX')) or '.app' in s: return False
    return True

sources = set()
for f in glob.glob('Orbit/**/*.swift', recursive=True):
    if f.startswith('Orbit/App/Generated/'): continue  # the search index: keywords, not UI
    for m in literal.finditer(open(f).read()):
        s = m.group(1).replace('\\n', '\n').replace('\\"', '"')
        if looks_like_ui(s): sources.add(s)

translations = {locale: {} for locale in locales}
for locale, dictionary in translations.items():
    for f in sorted(glob.glob(f'tools/i18n/{locale}*.json')):
        with open(f, encoding='utf-8') as data:
            dictionary.update(json.load(data))
keys = sorted(extracted | sources | set().union(*translations.values()))
keys = sorted(set(keys) | {key for key, entry in previous.items()
                           if any(locale != 'zh-Hans' for locale in entry.get('localizations', {}))})

if args.missing:
    for k in keys:
        if not translations[args.locale].get(k): print(json.dumps(k, ensure_ascii=False))
    sys.exit(0)

strings = {}
for k in keys:
    entry = {}
    # Upstream also has catalog-only translations. Keep them when merging source dictionaries.
    localizations = {locale: value for locale, value in previous.get(k, {}).get('localizations', {}).items()
                     if locale != 'zh-Hans'}
    for locale, dictionary in translations.items():
        if k in dictionary and dictionary[k] is not None:
            localizations[locale] = {'stringUnit': {'state': 'translated', 'value': dictionary[k]}}
    if localizations:
        entry['localizations'] = localizations
    if k not in extracted:
        entry['extractionState'] = 'manual'
    strings[k] = entry

catalog = {'sourceLanguage': 'en', 'strings': strings, 'version': '1.0'}
with open(catalog_path, 'w', encoding='utf-8') as output:
    json.dump(catalog, output, ensure_ascii=False, indent=2, sort_keys=True)
summary = ', '.join(f'{sum(locale in entry.get("localizations", {}) for entry in strings.values())} {locale}'
                    for locale in locales)
print(f'{len(keys)} keys, translations: {summary}')
