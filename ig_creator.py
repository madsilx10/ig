import requests
import uuid
import random
import re
import time
import sys
import json

# ─── CONFIG ───────────────────────────────────────────────────────────────────
EMAIL_FILE   = "email.txt"
PASSWORD_FILE= "password.txt"
OUTPUT_FILE  = "ig_accounts.txt"
IG_APP_ID    = "567067343352427"
IG_VERSION   = "370.0.0.42.96"
# ──────────────────────────────────────────────────────────────────────────────

# ─── NAME POOLS ───────────────────────────────────────────────────────────────
FIRST_NAMES = [
    "Zara","Nova","Lyra","Cass","Remy","Sable","Orion","Vega","Zion",
    "Atlas","Sage","Riven","Nyx","Soleil","Kira","Dax","Zeph","Aria",
    "Cleo","Lux","Mira","Enzo","Blaze","Indigo","Sienna","Ember","Rune",
    "Onyx","Lior","Noa","Kai","Zuri","Coda","Soren","Zola","Kael",
    "Thea","Wren","Arlo","Clio","Elio","Fenn","Gael","Hale","Juno",
    "Kova","Leif","Mael","Nero","Orin","Pell","Quill","Raen","Skye",
    "Tael","Ulric","Vael","Xen","Yael","Zael","Brix","Cael","Dael",
]
LAST_NAMES = [
    "Voss","Rael","Drex","Zane","Kohl","Frey","Holt","Cade","Vane",
    "Rook","Zell","Thane","Sire","Renn","Pax","Mael","Lux","Kael",
    "Jove","Irix","Haze","Grim","Fell","Dusk","Crow","Bane","Ash",
    "Vex","Wulf","Xol","Yore","Zest","Aeon","Bael","Crux","Dorn",
]

def gen_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def gen_username(full_name):
    first = full_name.split()[0].lower()
    last  = full_name.split()[1].lower()
    style = random.randint(0, 4)
    if   style == 0: return f"{first}.{last}{random.randint(10,99)}"
    elif style == 1: return f"{first}_{last[:3]}{random.randint(10,99)}"
    elif style == 2: return f"{first}{last}{random.randint(100,999)}"
    elif style == 3: return f"_{first}{random.randint(10,99)}{last[:2]}"
    else:            return f"{first[:3]}{last}{random.randint(10,99)}"

def gen_birthday():
    return {
        "day":   str(random.randint(1, 28)),
        "month": str(random.randint(1, 12)),
        "year":  str(random.randint(1993, 2001)),
    }

def calc_jazoest(phone_id):
    return "2" + str(sum(ord(c) for c in phone_id))


# ─── DEVICE & HEADERS ─────────────────────────────────────────────────────────
DEVICES = [
    ("samsung", "SM-G991B", "o1s",       "exynos2100"),
    ("samsung", "SM-A515F", "a51",       "exynos9611"),
    ("samsung", "SM-S908B", "b0q",       "exynos2200"),
    ("OnePlus", "IN2023",   "OnePlus8T", "kona"),
    ("Xiaomi",  "M2102J20SG","alioth",   "lahaina"),
]
RESOLUTIONS = ["1080x2220","1080x2340","1080x2400","1440x3200"]
DPIS        = ["420","480","560"]

def gen_device():
    mfr, model, codename, cpu = random.choice(DEVICES)
    return {
        "phone_id":    str(uuid.uuid4()),
        "device_id":   "android-" + uuid.uuid4().hex[:16],
        "uuid":        str(uuid.uuid4()),
        "waterfall_id":str(uuid.uuid4()),
        "manufacturer":mfr,
        "model":       model,
        "codename":    codename,
        "cpu":         cpu,
        "resolution":  random.choice(RESOLUTIONS),
        "dpi":         random.choice(DPIS),
    }

def build_headers(device):
    ua = (
        f"Instagram {IG_VERSION} Android "
        f"(33/13; {device['dpi']}dpi; {device['resolution']}; "
        f"{device['manufacturer']}; {device['model']}; {device['codename']}; "
        f"{device['cpu']}; en_US; 655896867)"
    )
    return {
        "User-Agent":                    ua,
        "X-IG-App-ID":                   IG_APP_ID,
        "X-IG-Capabilities":             "3brTvwE=",
        "X-IG-Connection-Type":          "WIFI",
        "X-IG-Bandwidth-Speed-KBPS":     "-1.000",
        "X-IG-Bandwidth-TotalBytes-B":   "0",
        "X-IG-Bandwidth-TotalTime-MS":   "0",
        "X-IG-Extended-CDN-Thumbnail-Cache-Busting-Value": "1000",
        "Accept-Language":               "en-US",
        "Accept-Encoding":               "gzip, deflate",
        "Content-Type":                  "application/x-www-form-urlencoded; charset=UTF-8",
        "Connection":                    "close",
    }


# ─── IG API STEPS ─────────────────────────────────────────────────────────────
IG_BASE = "https://i.instagram.com"

def fetch_headers(session, headers):
    """Step 1: ambil CSRF token & mid cookie."""
    r = session.get(
        f"{IG_BASE}/api/v1/si/fetch_headers/",
        params={"challenge_type": "signup", "guid": str(uuid.uuid4()).replace("-","")},
        headers=headers,
    )
    print(f"  [fetch_headers] {r.status_code}")
    return r.status_code == 200

def send_verify_email(session, headers, device, email):
    """Step 2: kirim OTP ke email."""
    data = {
        "phone_id":    device["phone_id"],
        "device_id":   device["device_id"],
        "email":       email,
        "waterfall_id":device["waterfall_id"],
        "tos_version": "row",
    }
    r = session.post(
        f"{IG_BASE}/api/v1/accounts/send_verify_email/",
        data=data, headers=headers,
    )
    print(f"  [send_verify_email] {r.status_code} → {r.text[:120]}")
    return r.status_code == 200

def check_confirmation_code(session, headers, device, email, otp):
    """Step 3: verifikasi OTP → dapat signup_code."""
    data = {
        "code":        otp,
        "device_id":   device["device_id"],
        "email":       email,
        "waterfall_id":device["waterfall_id"],
    }
    r = session.post(
        f"{IG_BASE}/api/v1/accounts/check_confirmation_code/",
        data=data, headers=headers,
    )
    print(f"  [check_confirmation_code] {r.status_code} → {r.text[:120]}")
    if r.status_code == 200:
        body = r.json()
        return body.get("signup_code") or body.get("code")
    return None

def create_account(session, headers, device, email, password, username, name, signup_code):
    """Step 4: buat akun."""
    bday = gen_birthday()
    data = {
        "jazoest":          calc_jazoest(device["phone_id"]),
        "country_codes":    '[{"country_code":"1","source":["default"]}]',
        "phone_id":         device["phone_id"],
        "enc_password":     f"#PWD_INSTAGRAM:0:{int(time.time())}:{password}",
        "username":         username,
        "first_name":       name,
        "day":              bday["day"],
        "month":            bday["month"],
        "year":             bday["year"],
        "registrationMethod":"email",
        "email":            email,
        "signup_code":      signup_code,
        "seamlesssignup_used":"0",
        "tos_version":      "row",
        "suggestedUsername":"",
        "sn_result":        "GOOGLE_PLAY_UNAVAILABLE",
        "do_not_auto_login_if_credentials_match":"false",
        "device_id":        device["device_id"],
        "uuid":             device["uuid"],
        "waterfall_id":     device["waterfall_id"],
        "_uuid":            device["uuid"],
    }
    r = session.post(
        f"{IG_BASE}/api/v1/accounts/create/",
        data=data, headers=headers,
    )
    print(f"  [create] {r.status_code} → {r.text[:200]}")
    if r.status_code == 200:
        return r.json()
    return None


# ─── MAIN FLOW ────────────────────────────────────────────────────────────────
def save_result(email, username, password, user_id=""):
    with open(OUTPUT_FILE, "a") as f:
        f.write(f"email={email} | username={username} | password={password} | uid={user_id}\n")

def run(email, password):
    print(f"\n{'─'*55}")
    print(f"[*] Email    : {email}")

    device  = gen_device()
    headers = build_headers(device)
    session = requests.Session()
    session.headers.update(headers)

    name     = gen_name()
    username = gen_username(name)
    print(f"[*] Name     : {name}")
    print(f"[*] Username : @{username}")

    # Step 1
    print("[1/4] Fetch headers...")
    if not fetch_headers(session, headers):
        print("[!] fetch_headers gagal.")
        return

    # Step 2
    print("[2/4] Kirim OTP ke email...")
    if not send_verify_email(session, headers, device, email):
        print("[!] send_verify_email gagal.")
        return

    # Step 3 — OTP manual
    otp = input(f"[3/4] OTP dari {email} : ").strip()
    if not otp:
        print("[!] OTP kosong, skip.")
        return

    signup_code = check_confirmation_code(session, headers, device, email, otp)
    if not signup_code:
        print("[!] OTP salah atau expired.")
        return

    # Step 4
    print("[4/4] Buat akun...")
    result = create_account(session, headers, device, email, password, username, name, signup_code)
    if not result:
        return

    created = result.get("created_user", {})
    user_id = created.get("pk", "")
    print(f"\n[✓] Sukses! @{username} | uid={user_id}")
    save_result(email, username, password, user_id)
    print(f"[*] Disimpan ke {OUTPUT_FILE}")


if __name__ == "__main__":
    # Baca password
    try:
        with open(PASSWORD_FILE) as f:
            password = f.read().strip().splitlines()[0]
    except FileNotFoundError:
        print(f"[!] {PASSWORD_FILE} tidak ditemukan.")
        sys.exit(1)

    # Baca emails
    try:
        with open(EMAIL_FILE) as f:
            emails = [l.strip() for l in f if l.strip()]
    except FileNotFoundError:
        print(f"[!] {EMAIL_FILE} tidak ditemukan.")
        sys.exit(1)

    print(f"=== IG Creator | {len(emails)} akun ===")
    print(f"[*] Password  : {'*' * len(password)}")

    for i, email in enumerate(emails):
        print(f"\n[Akun {i+1}/{len(emails)}]")
        run(email, password)
        if i < len(emails) - 1:
            delay = random.randint(8, 15)
            print(f"[*] Jeda {delay}s sebelum akun berikutnya...")
            time.sleep(delay)

    print(f"\n=== Selesai. Hasil di {OUTPUT_FILE} ===")
