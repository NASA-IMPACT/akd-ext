#!/usr/bin/env bash
# Launch a long-lived Chromium with remote-debugging enabled, then run
# the GeoUI Worldview chat notebook against it. The Playwright MCP
# attaches to this Chromium per turn via CDP, so the map's URL / pan /
# zoom / layer state survives across chat turns even though the MCP
# itself doesn't.
#
# Browser: Playwright's bundled Chromium (from
# ~/Library/Caches/ms-playwright/...) is used by default. It gets
# auto-installed via `npx playwright install chromium` on first run
# (~150 MB, one-time). To use a different browser instead, set
# CHROME_BIN to its executable.
#
# Re-running the script reattaches to the same Chromium instead of
# spawning a second one. Kill the browser manually when you're done:
#
#     pkill -f "remote-debugging-port=9222"
#
# Overrides via env vars:
#   CHROME_BIN                  path to a Chrome/Chromium binary
#                               (skips Playwright auto-resolve)
#   PLAYWRIGHT_BROWSERS_PATH    Playwright cache root (default
#                               ~/Library/Caches/ms-playwright)
#   CDP_PORT                    remote-debugging port (default 9222)
#   WORLDVIEW_CHROMIUM_PROFILE  user-data-dir (default /tmp/worldview-chromium)
#   MARIMO_MODE                 "run" (default) or "edit"
#
# Platform support:
#   - Bash + POSIX userspace (curl, ls, npx, uv). Does NOT run natively
#     on Windows cmd/PowerShell.
#   - Tested on macOS (Apple Silicon).
#   - Linux: the launch / CDP / marimo plumbing is portable, but the
#     Playwright Chromium auto-resolver below currently globs the
#     macOS-specific cache layout
#     (chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium).
#     On Linux you'll need to either:
#       (a) extend `find_playwright_chromium` to also match
#           chromium-*/chrome-linux/chrome under ~/.cache/ms-playwright, or
#       (b) set CHROME_BIN explicitly to a Chromium / Chrome binary.
#   - Windows: not supported natively. Workaround via WSL:
#       1. Install WSL (PowerShell, admin):  wsl --install
#       2. From the WSL shell, clone the repo and run start.sh from
#          inside WSL - it executes as Linux, so the Linux notes
#          above apply (cache at ~/.cache/ms-playwright, binary at
#          chrome-linux/chrome; either extend the resolver or set
#          CHROME_BIN). `npx playwright install chromium` inside WSL
#          will fetch the Linux Chromium build.
#       3. Open http://localhost:<marimo-port> in your Windows browser
#          - WSL2 forwards localhost transparently.

set -euo pipefail

CDP_PORT="${CDP_PORT:-9222}"
USER_DATA_DIR="${WORLDVIEW_CHROMIUM_PROFILE:-/tmp/worldview-chromium}"
MARIMO_MODE="${MARIMO_MODE:-run}"
PW_CACHE="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/Library/Caches/ms-playwright}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

is_cdp_up() {
    curl -fs -o /dev/null "http://localhost:${CDP_PORT}/json/version"
}

# Print the newest cached Playwright Chromium binary path on stdout,
# or return non-zero if none is installed.
#
# NOTE: macOS-only layout. Linux Chromium lives at
# chromium-*/chrome-linux/chrome under ~/.cache/ms-playwright; extend
# the glob below to add Linux support, or set CHROME_BIN explicitly.
find_playwright_chromium() {
    local d
    # `ls -td` orders by mtime newest-first; first executable hit wins.
    for d in $(ls -td "$PW_CACHE"/chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium 2>/dev/null); do
        if [[ -x "$d" ]]; then
            echo "$d"
            return 0
        fi
    done
    return 1
}

# Resolve a usable browser binary, installing Playwright Chromium on
# the fly if neither CHROME_BIN nor a cached install is present.
ensure_browser() {
    if [[ -n "${CHROME_BIN:-}" ]]; then
        if [[ -x "$CHROME_BIN" ]]; then
            echo "$CHROME_BIN"
            return 0
        fi
        echo "Error: CHROME_BIN='$CHROME_BIN' is not an executable file" >&2
        return 1
    fi

    local binary
    if binary=$(find_playwright_chromium); then
        echo "$binary"
        return 0
    fi

    echo "Playwright Chromium not found in $PW_CACHE - installing (one-time, ~150 MB)..." >&2
    if ! command -v npx >/dev/null 2>&1; then
        echo "Error: 'npx' is required to install Playwright Chromium and is not on PATH" >&2
        return 1
    fi
    if ! npx -y playwright install chromium >&2; then
        echo "Error: 'npx playwright install chromium' failed" >&2
        return 1
    fi

    if binary=$(find_playwright_chromium); then
        echo "$binary"
        return 0
    fi
    echo "Error: Playwright Chromium still not found after install (looked in $PW_CACHE)" >&2
    return 1
}

if is_cdp_up; then
    echo "Chromium CDP already up on port ${CDP_PORT} - reusing."
else
    CHROME="$(ensure_browser)" || exit 1
    echo "Browser: $CHROME"

    echo "Launching Chromium on port ${CDP_PORT}..."
    "$CHROME" \
        --remote-debugging-port="$CDP_PORT" \
        --user-data-dir="$USER_DATA_DIR" \
        --no-first-run \
        --no-default-browser-check \
        >/dev/null 2>&1 &
    CHROME_PID=$!
    echo "Chromium PID: $CHROME_PID  (kill with: kill $CHROME_PID)"

    # Wait up to 10s for the CDP endpoint to accept connections.
    for _ in {1..20}; do
        if is_cdp_up; then
            break
        fi
        sleep 0.5
    done

    if ! is_cdp_up; then
        echo "Error: Chromium CDP did not come up within 10s on port ${CDP_PORT}" >&2
        exit 1
    fi
    echo "Chromium CDP ready."
fi

export PLAYWRIGHT_CDP_ENDPOINT="http://localhost:${CDP_PORT}"
echo "PLAYWRIGHT_CDP_ENDPOINT=${PLAYWRIGHT_CDP_ENDPOINT}"
echo

# Run marimo from the worktree root (one level up from this script).
# Running inside ieso_w_geoui/ would shadow the package and break the
# notebook's `from ieso_w_geoui import …` import.
cd "$SCRIPT_DIR/.."
exec uv run marimo "$MARIMO_MODE" ieso_w_geoui/notebooks/chat.py
