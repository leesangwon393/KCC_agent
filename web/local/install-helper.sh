#!/bin/zsh
set -euo pipefail
umask 077
archive="$1"
source_hash="$2"
bundle_path="$3"
cloud_origin="$4"
moa_support="$HOME/Library/Application Support/Moa"
moa_tools="$moa_support/tools"
moa_release="$moa_support/releases/$source_hash"
[[ ${#source_hash} -eq 64 && "$source_hash" != *[^0-9a-f]* ]] || exit 2
actual_hash=$(/usr/bin/shasum -a 256 "$archive")
[[ "${actual_hash%% *}" == "$source_hash" ]] || { print 'Source archive checksum mismatch'; exit 2; }
mkdir -p "$moa_tools" "$moa_release" "$HOME/Applications"
installed_app="$HOME/Applications/Moa Helper.app"
if [[ "$bundle_path" != "$installed_app" ]]; then
  if [[ -e "$installed_app/Contents/Info.plist" ]]; then
    installed_id=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$installed_app/Contents/Info.plist")
    [[ "$installed_id" == 'com.moa.helper' ]] || { print 'Another application exists at the install path'; exit 2; }
  fi
  /usr/bin/ditto "$bundle_path" "$installed_app"
fi
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$installed_app"
if [[ ! -x "$moa_tools/bin/uv" ]]; then
  /usr/bin/curl --fail --location --proto '=https' --tlsv1.2 https://astral.sh/uv/0.13.7/install.sh -o "$moa_tools/install-uv.sh"
  env UV_INSTALL_DIR="$moa_tools/bin" UV_NO_MODIFY_PATH=1 /bin/sh "$moa_tools/install-uv.sh"
fi
"$moa_tools/bin/uv" python install 3.12
if [[ ! -f "$moa_release/.ready" ]]; then
  /usr/bin/tar -xzf "$archive" -C "$moa_release"
  "$moa_tools/bin/uv" venv --allow-existing --python 3.12 "$moa_release/.venv-moa"
  "$moa_tools/bin/uv" pip install --python "$moa_release/.venv-moa/bin/python" -r "$moa_release/web/backend/requirements.txt" -r "$moa_release/file-lifecycle-agent/requirements.txt"
  touch "$moa_release/.ready"
fi
MOA_CLOUD_ORIGIN="$cloud_origin" "$moa_release/.venv-moa/bin/python" "$moa_release/web/local/install.py" --helper-only
