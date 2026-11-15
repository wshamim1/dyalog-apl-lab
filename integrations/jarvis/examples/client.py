"""Call the APL API from Python (standard library only).

    python3 integrations/jarvis/examples/client.py [http://localhost:8080]

Also works as a quick end-to-end check: exits with 1 if any answer is wrong.
"""
import json
import sys
import urllib.error
import urllib.request

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"


def call(endpoint, payload):
    """POST JSON to an APL function and return (status, decoded JSON)."""
    req = urllib.request.Request(
        f"{URL}/{endpoint}", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        body = e.read()
        try:
            return e.code, json.loads(body)
        except ValueError:
            return e.code, body.decode(errors="replace")


checks = [
    ("Hello", {"name": "Ann"}, 200, {"message": "Hello, Ann!"}),
    ("Sum", [1, 2, 3, 4], 200, 10),
    ("Sort", ["pear", "apple", "fig"], 200, ["apple", "fig", "pear"]),
    ("Primes", 30, 200, [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]),
    ("Stats", [2, 4, 4, 4, 5, 5, 7, 9], 200,
     {"count": 8, "max": 9, "mean": 5, "median": 4.5, "min": 2, "sd": 2}),
    ("WordCount", {"text": "the cat and the hat", "top": 1}, 200,
     [{"count": 2, "word": "the"}]),
    ("Primes", 1, 400, None),          # bad input: 400 + {"error": ...}
]

failed = 0
for endpoint, payload, want_status, want in checks:
    status, got = call(endpoint, payload)
    ok = status == want_status and (want is None or got == want)
    failed += not ok
    print(f"{'✅' if ok else '❌'} {endpoint:<10} {json.dumps(payload):<36} → {status} {json.dumps(got)}")
print(f"\n{len(checks) - failed}/{len(checks)} as expected")
sys.exit(1 if failed else 0)
