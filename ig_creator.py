import requests
import uuid
import random
import time
import sys

# ─── CONFIG ───────────────────────────────────────────────────────────────────
EMAIL_FILE   = "email.txt"
PASSWORD_FILE= "password.txt"
OUTPUT_FILE  = "ig_accounts.txt"
IG_APP_ID    = "567067343352427"
IG_VERSION   = "370.0.0.42.96"
IG_BASE      = "https://i.instagram.com"
# ──────────────────────────────────────────────────────────────────────────────

FIRST_NAMES = [
    "Zara","Nova","Lyra","Cass","Remy","Sable","Orion","Vega","Zion",
    "Atlas","Sage","Riven","Nyx","Soleil","Kira","Dax","Zeph","Aria",
    "Cleo","Lux","Mira","Enzo","Blaze","Indigo","Sienna","Ember","Rune",
    "Onyx","Lior","Noa","Kai","Zuri","Coda","Soren","Zola","Kael",
    "Thea","Wren","Arlo","Clio","Elio","Fenn","Gael","Hale","Juno",
    "Kova","Leif","Mael","Nero","Orin","Pell","Raen","Skye","Tael",
]
LAST_NAMES = [
    "Voss","Rael","Drex","Zane","Kohl","Frey","Holt","Cade","Vane",
    "Rook","Zell","Thane","Sire","Renn","Pax","Mael","Lux","Kael",
    "Jove","Haze","Grim","Fell","Dusk","Crow","Bane","Ash","Vex",
    "Wulf","Xol","Zest","Aeon","Bael","Crux","Dorn","Flint","Gale",
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
    return str(random.randint(1993,2001)), str(random.randint(1,12)), str(random.randint(1,28))

def calc_jazoest(phone_id):
    return "2" + str(sum(ord(c) for c in phone_id))


# ─── DEVICE ───────────────────────────────────────────────────────────────────
DEVICES = [
    ("samsung", "SM-G991B", "o1s",        "exynos2100"),
    ("samsung", "SM-A515F", "a51",        "exynos9611"),
    ("samsung", "SM-S908B", "b0q",        "exynos2200"),
    ("OnePlus", "IN2023",   "OnePlus8T",  "kona"),
    ("Xiaomi",  "M2102J20SG","alioth",    "lahaina"),
]

def gen_device():
    mfr, model, codename, cpu = random.choice(DEVICES)
    return {
        "phone_id":    str(uuid.uuid4()),
        "device_id":   "android-" + uuid.uuid4().hex[:16],
        "uuid":        str(uuid.uuid4()),
        "waterfall_id":str(uuid.uuid4()),
        "manufacturer":mfr, "model":model,
        "codename":codename, "cpu":cpu,
        "resolution":  random.choice(["1080x2220","1080x2340","1080x2400"]),
        "dpi":         random.choice(["420","480","560"]),
    }

def build_headers(device):
    ua = (
        f"Instagram {IG_VERSION} Android "
        f"(33/13; {device['dpi']}dpi; {device['resolution']}; "
        f"{device['manufacturer']}; {device['model']}; {device['codename']}; "
        f"{device['cpu']}; en_US; 655896867)"
    )
    return {
        "User-Agent":             ua,
        "X-IG-App-ID":            IG_APP_ID,
        "X-IG-Capabilities":      "3brTvwE=",
        "X-IG-Connection-Type":   "WIFI",
        "X-IG-Bandwidth-Speed-KBPS":   "-1.000",
        "X-IG-Bandwidth-TotalBytes-B": "0",
        "X-IG-Bandwidth-TotalTime-MS": "0",
        "X-IG-Extended-CDN-Thumbnail-Cache-Busting-Value": "1000",
        "X-IG-App-Locale":        "en_US",
        "X-IG-Device-Locale":     "en_US",
        "X-IG-Mapped-Locale":     "en_US",
        "X-IG-Device-ID":         device["uuid"],
        "X-IG-Android-ID":        device["device_id"],
        "X-Pigeon-Session-Id":    str(uuid.uuid4()),
        "X-Pigeon-Rawclienttime": f"{time.time():.3f}",
        "X-Bloks-Version-Id":     "ce9b4eb3f7fc0b57b4e4af765b66b3bfe9e3a5bbd58e50feac0e6ed8a6834bc5",
        "X-Bloks-Is-Layout-RTL":  "false",
        "Accept-Language":        "en-US",
        "Accept-Encoding":        "gzip, deflate",
        "Content-Type":           "application/x-www-form-urlencoded; charset=UTF-8",
        "Connection":             "close",
    }


# ─── IG API ───────────────────────────────────────────────────────────────────
def step_fetch_headers(session, headers, device):
    r = session.get(
        f"{IG_BASE}/api/v1/si/fetch_headers/",
        params={"challenge_type": "signup", "guid": device["uuid"].replace("-","")},
        headers=headers,
    )
    print(f"  [fetch_headers] {r.status_code}")
    return r.status_code == 200

def step_check_email(session, headers, device, email):
    """Wajib sebelum send OTP — cek ketersediaan email."""
    data = {
        "android_device_id": device["device_id"],
        "email":             email,
        "qe_id":             str(uuid.uuid4()),
        "waterfall_id":      device["waterfall_id"],
    }
    r = session.post(f"{IG_BASE}/api/v1/accounts/check_email/", data=data, headers=headers)
    print(f"  [check_email] {r.status_code} → {r.text[:150]}")
    if r.status_code != 200:
        return False
    body = r.json()
    # valid=true → bisa dipakai; existing_user=true → sudah terdaftar
    if body.get("existing_user"):
        print("  [!] Email sudah terdaftar di IG.")
        return False
    return body.get("valid", False)

def step_send_otp(session, headers, device, email):
    data = {
        "phone_id":    device["phone_id"],
        "device_id":   device["device_id"],
        "email":       email,
        "waterfall_id":device["waterfall_id"],
        "tos_version": "row",
    }
    r = session.post(f"{IG_BASE}/api/v1/accounts/send_verify_email/", data=data, headers=headers)
    print(f"  [send_verify_email] {r.status_code} → {r.text[:150]}")
    return r.status_code == 200

def step_verify_otp(session, headers, device, email, otp):
    data = {
        "code":        otp,
        "device_id":   device["device_id"],
        "email":       email,
        "waterfall_id":device["waterfall_id"],
    }
    r = session.post(f"{IG_BASE}/api/v1/accounts/check_confirmation_code/", data=data, headers=headers)
    print(f"  [check_confirmation_code] {r.status_code} → {r.text[:150]}")
    if r.status_code == 200:
        body = r.json()
        return body.get("signup_code") or body.get("code")
    return None

def step_create(session, headers, device, email, password, username, name, signup_code):
    year, month, day = gen_birthday()
    data = {
        "jazoest":           calc_jazoest(device["phone_id"]),
        "country_codes":     '[{"country_code":"1","source":["default"]}]',
        "phone_id":          device["phone_id"],
        "enc_password":      f"#PWD_INSTAGRAM:0:{int(time.time())}:{password}",
        "username":          username,
        "first_name":        name,
        "day":               day,
        "month":             month,
        "year":              year,
        "registrationMethod":"email",
        "email":             email,
        "signup_code":       signup_code,
        "seamlesssignup_used":"0",
        "tos_version":       "row",
        "suggestedUsername": "",
        "sn_result":         "GOOGLE_PLAY_UNAVAILABLE",
        "do_not_auto_login_if_credentials_match":"false",
        "device_id":         device["device_id"],
        "uuid":              device["uuid"],
        "waterfall_id":      device["waterfall_id"],
        "_uuid":             device["uuid"],
    }
    r = session.post(f"{IG_BASE}/api/v1/accounts/create/", data=data, headers=headers)
    print(f"  [create] {r.status_code} → {r.text[:200]}")
    return r.json() if r.status_code == 200 else None


# ─── RUNNER ───────────────────────────────────────────────────────────────────
def save_result(email, username, password, user_id=""):
    with open(OUTPUT_FILE, "a") as f:
        f.write(f"email={email} | username={username} | password={password} | uid={user_id}\n")

def run(email, password):
    print(f"\n{'─'*55}")
    device  = gen_device()
    headers = build_headers(device)
    session = requests.Session()

    name     = gen_name()
    username = gen_username(name)
    print(f"[*] Email    : {email}")
    print(f"[*] Name     : {name}")
    print(f"[*] Username : @{username}")

    print("[1/5] Fetch headers...")
    if not step_fetch_headers(session, headers, device):
        print("[!] Gagal."); return
    time.sleep(random.uniform(1.5, 3))

    print("[2/5] Check email...")
    if not step_check_email(session, headers, device, email):
        print("[!] Email tidak valid / sudah terdaftar."); return
    time.sleep(random.uniform(1.5, 3))

    print("[3/5] Kirim OTP...")
    if not step_send_otp(session, headers, device, email):
        print("[!] Gagal kirim OTP."); return

    otp = input(f"[4/5] OTP dari {email} : ").strip()
    if not otp:
        print("[!] OTP kosong, skip."); return

    signup_code = step_verify_otp(session, headers, device, email, otp)
    if not signup_code:
        print("[!] OTP salah / expired."); return

    print("[5/5] Buat akun...")
    result = step_create(session, headers, device, email, password, username, name, signup_code)
    if not result:
        return

    user_id = result.get("created_user", {}).get("pk", "")
    print(f"\n[✓] Sukses! @{username} | uid={user_id}")
    save_result(email, username, password, user_id)
    print(f"[*] Disimpan ke {OUTPUT_FILE}")


# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        password = open(PASSWORD_FILE).read().strip().splitlines()[0]
    except FileNotFoundError:
        print(f"[!] {PASSWORD_FILE} tidak ditemukan."); sys.exit(1)

    try:
        emails = [l.strip() for l in open(EMAIL_FILE) if l.strip()]
    except FileNotFoundError:
        print(f"[!] {EMAIL_FILE} tidak ditemukan."); sys.exit(1)

    print(f"=== IG Creator | {len(emails)} akun ===")

    for i, email in enumerate(emails):
        print(f"\n[Akun {i+1}/{len(emails)}]")
        run(email, password)
        if i < len(emails) - 1:
            delay = random.randint(10, 20)
            print(f"[*] Jeda {delay}s...")
            time.sleep(delay)

    print(f"\n=== Selesai. Hasil di {OUTPUT_FILE} ===")
