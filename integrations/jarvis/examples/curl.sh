#!/usr/bin/env bash
# Call every endpoint with curl. Start the server first: integrations/jarvis/serve.sh
URL="${1:-http://localhost:8080}"
call() { printf '%-10s %-45s → ' "$1" "$2"
         curl -s -X POST "$URL/$1" -H 'Content-Type: application/json' -d "$2"; echo; }
call Hello     '{"name":"Ann"}'
call Sum       '[1,2,3,4]'
call Sort      '["pear","apple","fig"]'
call Primes    '30'
call Stats     '[2,4,4,4,5,5,7,9]'
call WordCount '{"text":"the cat and the hat and the bat","top":3}'
call Primes    '1'          # bad input → 400 with an error message
