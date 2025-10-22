#!/usr/bin/env bash
set -euo pipefail

# 用法： ALLOW_HOSTS="pypi.mycorp.local deb.mycorp.local" bin/scan_logs_sources.sh build.log runtime.log
# 功能：提取日志中的所有 http(s) 主机名，输出不在允许列表中的来源

if [ "$#" -lt 1 ]; then
  echo "Usage: ALLOW_HOSTS=\"host1 host2\" $0 <log1> [<log2> ...]" >&2
  exit 2
fi

allowed_set=" ${ALLOW_HOSTS:-} "
tmp_hosts=$(mktemp)
trap 'rm -f "$tmp_hosts"' EXIT

for f in "$@"; do
  [ -f "$f" ] || { echo "[warn] log not found: $f" >&2; continue; }
  # 提取 URL 主机名
  grep -Eo 'https?://[^/ ]+' "$f" | sed -E 's#^https?://##' | sed -E 's/:.*$//' >> "$tmp_hosts" || true
done

if [ ! -s "$tmp_hosts" ]; then
  echo "[info] no http(s) hosts found in logs"
  exit 0
fi

echo "[info] unique hosts found:"
sort -u "$tmp_hosts" | sed 's/^/  - /'

echo "[check] unexpected hosts (not in ALLOW_HOSTS):"
rc=0
while read -r h; do
  if [[ " $allowed_set " != *" $h "* ]]; then
    echo "  ! $h"
    rc=1
  fi
done < <(sort -u "$tmp_hosts")

exit $rc

