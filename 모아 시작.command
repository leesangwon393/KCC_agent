#!/bin/zsh
set -eu
cd "${0:A:h}"
MOA_TOOLS="$HOME/Library/Application Support/Moa/tools"
if [[ ! -x "$MOA_TOOLS/bin/uv" ]]; then
  mkdir -p "$MOA_TOOLS"
  /usr/bin/curl -LsSf https://astral.sh/uv/0.13.7/install.sh -o "$MOA_TOOLS/install-uv.sh"
  env UV_INSTALL_DIR="$MOA_TOOLS/bin" UV_NO_MODIFY_PATH=1 /bin/sh "$MOA_TOOLS/install-uv.sh"
fi
"$MOA_TOOLS/bin/uv" python install 3.12
if [[ ! -x .venv-moa/bin/python ]]; then
  "$MOA_TOOLS/bin/uv" venv --python 3.12 .venv-moa
fi
"$MOA_TOOLS/bin/uv" pip install --python .venv-moa/bin/python -r web/backend/requirements.txt
.venv-moa/bin/python web/local/install.py --helper-only
