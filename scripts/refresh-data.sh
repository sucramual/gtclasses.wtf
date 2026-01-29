#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CRAWLER_DIR="$ROOT_DIR/crawler-v2"
CRAWLER_DATA_DIR="$CRAWLER_DIR/data"
DATA_DIR="$ROOT_DIR/data"

if [[ ! -d "$CRAWLER_DIR" ]]; then
  echo "Missing crawler directory: $CRAWLER_DIR" >&2
  exit 1
fi

cd "$CRAWLER_DIR"
if [[ "${SKIP_NPM_CI:-}" != "1" ]]; then
  npm ci
fi
: "${DETAILS_CONCURRENCY:=8}"
export DETAILS_CONCURRENCY
npm run start

mkdir -p "$DATA_DIR"
shopt -s nullglob
for file in "$CRAWLER_DATA_DIR"/[0-9][0-9][0-9][0-9][0-9][0-9].json; do
  cp -f "$file" "$DATA_DIR/"
done
shopt -u nullglob

cd "$ROOT_DIR"
python3 bridge.py
go run . combine

if [[ -z "${R2_BUCKET:-}" || -z "${R2_ENDPOINT:-}" ]]; then
  echo "R2_BUCKET and R2_ENDPOINT are required." >&2
  exit 1
fi

AWS_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID:-${AWS_ACCESS_KEY_ID:-}}"
AWS_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY:-${AWS_SECRET_ACCESS_KEY:-}}"
if [[ -z "${AWS_ACCESS_KEY_ID:-}" || -z "${AWS_SECRET_ACCESS_KEY:-}" ]]; then
  echo "R2_ACCESS_KEY_ID/R2_SECRET_ACCESS_KEY (or AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY) are required." >&2
  exit 1
fi

export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY
export AWS_REGION="${AWS_REGION:-auto}"
export AWS_EC2_METADATA_DISABLED=true

R2_OBJECT="${R2_OBJECT:-courses.json}"
aws s3 cp "$DATA_DIR/courses.json" "s3://$R2_BUCKET/$R2_OBJECT" \
  --endpoint-url "$R2_ENDPOINT"

if [[ -n "${FLY_APP_NAME:-}" ]]; then
  fly apps restart "$FLY_APP_NAME"
else
  echo "FLY_APP_NAME not set; skipping Fly restart." >&2
fi
