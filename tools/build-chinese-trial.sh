#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."
archive="${1:-$PWD/dist/Orbit-Chinese-Intel.zip}"
[[ "$archive" = /* ]] || archive="$PWD/$archive"
work=$(mktemp -d "${TMPDIR%/}/orbit-chinese.XXXXXX")
trap 'rm -rf "$work"' EXIT

built_app="${ORBIT_BUILT_APP:-}"
if [[ -z "$built_app" ]]; then
    python3 tools/i18n.py
    xcodebuild -project Orbit.xcodeproj -scheme Orbit -configuration Debug \
        -destination 'generic/platform=macOS' -derivedDataPath "$work/build" \
        ONLY_ACTIVE_ARCH=NO ARCHS=x86_64 ENABLE_DEBUG_DYLIB=NO CODE_SIGNING_ALLOWED=NO build
    built_app="$work/build/Build/Products/Debug/Orbit.app"
fi

trial_app="$work/Orbit 简体中文.app"
ditto "$built_app" "$trial_app"
contents="$trial_app/Contents"
plist="$contents/Info.plist"
plist_editor=/usr/libexec/PlistBuddy
"$plist_editor" -c 'Set :CFBundleIdentifier io.github.mrltr-cmd.orbit.zh' "$plist"
"$plist_editor" -c 'Set :CFBundleDisplayName Orbit 简体中文' "$plist"
for key in NSServices CFBundleDocumentTypes; do
    if "$plist_editor" -c "Print :$key" "$plist" >/dev/null 2>&1; then
        "$plist_editor" -c "Delete :$key" "$plist"
    fi
done

# These integrations share registrations with the official app and require its signing identity.
rm -rf "$contents/Library/LaunchDaemons" "$contents/PlugIns" "$contents/Helpers" "$contents/MacOS/OrbitFanHelper"
codesign --force --sign - --timestamp=none "$contents/Frameworks/OrbitMediaRemote.dylib"
codesign --force --sign - --timestamp=none --entitlements Orbit/Orbit.entitlements "$trial_app"
codesign --verify --deep --strict "$trial_app"
lipo -verify_arch x86_64 "$contents/MacOS/Orbit"
test -s "$contents/Resources/zh-Hans.lproj/Localizable.strings"
test -s "$contents/Resources/zh-Hans.lproj/InfoPlist.strings"

mkdir -p "$(dirname "$archive")"
ditto -c -k --sequesterRsrc --keepParent "$trial_app" "$work/trial.zip"
mv -f "$work/trial.zip" "$archive"
shasum -a 256 "$archive"
