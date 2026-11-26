#!/usr/bin/env python3
"""Check settings search metadata and the ranking of real localized pages."""
import json
import plistlib
import runpy
import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[2]
entries = runpy.run_path(str(root / 'tools/settings_index.py'))['entries']


def entry(title, kind):
    return next(e for e in entries if e['page'] == 'notch' and e['title'] == title and e['kind'] == kind)


def synonyms(e):
    return set(e['keywords'] + e['related'])


for title, kind, unwanted in [
    ('AI Usage', 'group', {'디스크', '캐시', 'docker', 'cpu', 'gpu', 'ram', 'memory', 'monitor'}),
    ('Home layout', 'group', {'스냅', '분할', 'snap'}),
    ('Limit windows', 'row', {'스냅', '분할', 'snap'}),
]:
    assert not synonyms(entry(title, kind)) & unwanted, title
print('PASS: notch search excludes storage/window synonyms')

# Exercise the app's real ranking, not only the generated keyword lists.
with tempfile.TemporaryDirectory(prefix='orbit-settings-search-') as scratch:
    scratch = Path(scratch)
    main = scratch / 'main.swift'
    main.write_text(r'''import Foundation
var failures = 0
for query in ["캘린더", "음악"] {
    if !SettingsSearch.search(query).contains(where: { $0.entry?.page == "notch" && $0.entry?.kind == .row && $0.entry?.title == "Home" }) {
        print("FAIL: \(query) must find the notch Home row")
        failures += 1
    }
}
for query in ["스냅", "분할", "반쪽", "배치"] {
    let results = SettingsSearch.search(query)
    let index = results.firstIndex { $0.entry?.kind == .page && $0.entry?.page == "windows" }
    let score = index.map { results[$0].score } ?? 0
    print("Windows search \(query): rank \(index.map { $0 + 1 } ?? 0), score \(score)")
    if index != 0 || score < 900 { failures += 1 }
}
if !SettingsSearch.search("레이아웃", limit: 5).contains(where: { $0.entry?.kind == .page && $0.entry?.page == "windows" }) {
    print("FAIL: Windows must remain in the top five layout results")
    failures += 1
}
let gap = SettingsIndex.entries.first { $0.page == "windows" && $0.title == "Gap between windows" }
if !(gap?.keywords.contains("스냅") ?? false) {
    print("FAIL: window gap keeps direct window synonyms")
    failures += 1
}
for (query, page) in [("窗口管理", "windows"), ("剪贴板", "clipboard"), ("菜单栏", "menubar"), ("贴板", "clipboard")] {
    if !SettingsSearch.search(query, limit: 5).contains(where: { $0.entry?.kind == .page && $0.entry?.page == page }) {
        print("FAIL: \(query) did not find \(page)")
        failures += 1
    }
}
if SettingsSearch.marks("贴板", in: "剪贴板") != Set([1, 2]) {
    print("FAIL: Chinese search highlights matched characters")
    failures += 1
}
exit(failures == 0 ? 0 : 1)
''')
    contents = scratch / 'SettingsSearchTests.app/Contents'
    binary = contents / 'MacOS' / 'settings-search-tests'
    binary.parent.mkdir(parents=True)
    with (contents / 'Info.plist').open('wb') as info:
        plistlib.dump(dict(CFBundleIdentifier='org.orbit.settings-search-tests',
                           CFBundleExecutable=binary.name, CFBundlePackageType='APPL',
                           CFBundleDevelopmentRegion='en'), info)
    strings = contents / 'Resources/zh-Hans.lproj/Localizable.strings'
    strings.parent.mkdir(parents=True)
    with (root / 'Orbit/Resources/Localizable.xcstrings').open(encoding='utf-8') as catalog:
        chinese = {key: entry['localizations']['zh-Hans']['stringUnit']['value']
                   for key, entry in json.load(catalog)['strings'].items()
                   if 'zh-Hans' in entry.get('localizations', {})}
    with strings.open('wb') as translations:
        plistlib.dump(chinese, translations)
    subprocess.run(['xcrun', 'swiftc', '-swift-version', '5',
                    str(root / 'Orbit/App/Search/SearchMatcher.swift'),
                    str(root / 'Orbit/App/Search/SettingsSearch.swift'),
                    str(root / 'Orbit/App/Generated/SettingsIndex.swift'),
                    str(main), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
print('PASS: settings search in Simplified Chinese and Korean')
