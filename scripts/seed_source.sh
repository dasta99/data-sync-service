#!/bin/bash
# seed_source.sh — Insert new records into tdp-source for testing CDC
# Usage: ./scripts/seed_source.sh [count]

set -e

COUNT=${1:-20}
USER="sync_user"
PASS="sync_pass"
DB="mytdp"

echo "=== Seeding $COUNT new booth_voter records into tdp-source ==="

# Get current max numeric ID
MAX_ID=$(docker exec tdp-source mysql -u $USER -p$PASS $DB -N -e \
  "SELECT IFNULL(MAX(CAST(SUBSTRING(id,3) AS UNSIGNED)),0) FROM booth_voter;" 2>/dev/null)
echo "Current max: BV$(printf '%05d' $MAX_ID)"

# Wait 2 seconds so new records get a newer timestamp than watermark
echo "Waiting 2s for fresh timestamps..."
sleep 2

# Build VALUES list
VALUES=""
for i in $(seq 1 $COUNT); do
  N=$((MAX_ID + i))
  ID=$(printf 'BV%05d' $N)
  VID=$(printf 'V%05d' $N)
  KSS=$(printf 'KSS%05d' $N)
  BID=$(printf 'B%04d' $(( (i % 60) + 1 )))
  AID=$((1001 + (i % 20)))
  PID=$((101 + (i % 20)))
  STATUS=$(echo "available temporary_shift permanent_shift death duplicate double_vote" | tr ' ' '\n' | sed -n "$(( (i % 6) + 1 ))p")
  CASTE=$(echo "SC ST BC General" | tr ' ' '\n' | sed -n "$(( (i % 4) + 1 ))p")

  [ -n "$VALUES" ] && VALUES="$VALUES,"
  VALUES="$VALUES('$ID','$BID',$AID,$PID,'$VID',$N,'$KSS',1,'User$(( (i % 10) + 1 ))','BLO','$CASTE','P$(printf '%02d' $(( (i % 5) + 1 )))','C$(printf '%02d' $(( (i % 8) + 1 )))','9$(printf '%09d' $(( RANDOM % 1000000000 )))','16.$(printf '%04d' $(( RANDOM % 5000 )))','80.$(printf '%04d' $(( RANDOM % 5000 )))','$STATUS',NOW(),NOW())"
done

docker exec tdp-source mysql -u $USER -p$PASS $DB -e \
  "INSERT INTO booth_voter (id,booth_id,assembly_id,parliament_id,voter_id,serial_no,kss_id,sir_verified,sir_verified_by,sir_verified_role,sir_caste_category,sir_political_party_id,sir_caste_id,sir_mobile_number,sir_latitude,sir_longitude,sir_status,created_at,updated_at) VALUES $VALUES;" \
  2>/dev/null

# Verify
TOTAL=$(docker exec tdp-source mysql -u $USER -p$PASS $DB -N -e "SELECT COUNT(*) FROM booth_voter;" 2>/dev/null)
NEW_MAX=$(docker exec tdp-source mysql -u $USER -p$PASS $DB -N -e "SELECT MAX(id) FROM booth_voter;" 2>/dev/null)
echo "Inserted: $COUNT records"
echo "Total booth_voter: $TOTAL rows (max id: $NEW_MAX)"
echo ""
echo "Run: python3 main.py --local"
