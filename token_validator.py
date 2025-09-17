import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# 📥 Input file
input_file = input("📄 Enter filename (e.g., tokens.txt): ").strip()
if not os.path.exists(input_file):
    print(f"❌ File '{input_file}' not found.")
    exit()

# 🔃 Read and deduplicate
with open(input_file, "r") as f:
    entries = list(set(line.strip() for line in f if "|" in line.strip()))

valid = []
invalid = []

# 🛡️ User-Agent header
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36"
}

# ✅ Improved validator
def validate_token(entry):
    try:
        uid, token = entry.split("|", 1)
        url = "https://graph.facebook.com/me"
        params = {"access_token": token, "fields": "id,name"}

        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        res = r.json()

        if r.status_code == 200 and "id" in res:
            return (entry, True)

        elif r.status_code == 400 and "error" in res:
            error_msg = res["error"].get("message", "").lower()

            if "checkpoint" in error_msg or "session" in error_msg:
                print(f"⚠️  CHECKPOINTED: {uid}")
            elif "invalid" in error_msg or "expired" in error_msg:
                print(f"🔒 EXPIRED or INVALID: {uid}")
            else:
                print(f"❌ ERROR ({uid}): {res['error'].get('message')}")
            return (entry, False)

        else:
            print(f"❓ UNKNOWN ERROR ({uid}): {res}")
            return (entry, False)

    except Exception as e:
        print(f"🔥 EXCEPTION ({entry}): {str(e)}")
        return (entry, False)

print(f"\n🔍 Validating {len(entries)} tokens...\n")

# 🚀 Multithreaded validation
with ThreadPoolExecutor(max_workers=30) as executor:
    futures = [executor.submit(validate_token, entry) for entry in entries]
    for i, future in enumerate(as_completed(futures), 1):
        entry, status = future.result()
        if status:
            print(f"[{i}] ✅ VALID: {entry}")
            valid.append(entry)
        else:
            print(f"[{i}] ❌ REJECTED: {entry}")
            invalid.append(entry)

# 💾 Output
with open("USABLE.txt", "w") as f:
    f.writelines(v + "\n" for v in valid)

with open("REJECT.txt", "w") as f:
    f.writelines(r + "\n" for r in invalid)

# 📊 Summary
print(f"\n✅ USABLE: {len(valid)} saved to USABLE.txt")
print(f"❌ REJECTED: {len(invalid)} saved to REJECT.txt")
print("📁 Original input file not modified.")
