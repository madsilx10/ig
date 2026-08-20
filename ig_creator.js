const fs  = require("fs");
const rl  = require("readline").createInterface({ input: process.stdin, output: process.stdout });
const { v4: uuidv4 } = require("uuid");

// ─── CONFIG ──────────────────────────────────────────────────────────────────
const EMAIL_FILE    = "email.txt";
const PASSWORD_FILE = "password.txt";
const OUTPUT_FILE   = "ig_accounts.txt";
const IG_APP_ID     = "567067343352427";
const IG_VERSION    = "370.0.0.42.96";
const IG_BASE       = "https://i.instagram.com";
// ─────────────────────────────────────────────────────────────────────────────

const FIRST_NAMES = [
  "Zara","Nova","Lyra","Cass","Remy","Sable","Orion","Vega","Zion",
  "Atlas","Sage","Riven","Nyx","Soleil","Kira","Dax","Zeph","Aria",
  "Cleo","Lux","Mira","Enzo","Blaze","Indigo","Sienna","Ember","Rune",
  "Onyx","Lior","Noa","Kai","Zuri","Coda","Soren","Zola","Kael",
  "Thea","Wren","Arlo","Clio","Elio","Fenn","Gael","Hale","Juno",
  "Kova","Leif","Mael","Nero","Orin","Pell","Raen","Skye","Tael",
];
const LAST_NAMES = [
  "Voss","Rael","Drex","Zane","Kohl","Frey","Holt","Cade","Vane",
  "Rook","Zell","Thane","Sire","Renn","Pax","Mael","Lux","Kael",
  "Jove","Haze","Grim","Fell","Dusk","Crow","Bane","Ash","Vex",
  "Wulf","Xol","Zest","Aeon","Bael","Crux","Dorn","Flint","Gale",
];
const DEVICES = [
  ["samsung","SM-G991B","o1s","exynos2100"],
  ["samsung","SM-A515F","a51","exynos9611"],
  ["samsung","SM-S908B","b0q","exynos2200"],
  ["OnePlus","IN2023","OnePlus8T","kona"],
  ["Xiaomi","M2102J20SG","alioth","lahaina"],
];

// ─── HELPERS ─────────────────────────────────────────────────────────────────
const pick  = arr => arr[Math.floor(Math.random() * arr.length)];
const rand  = (a, b) => Math.floor(Math.random() * (b - a + 1)) + a;
const sleep = ms => new Promise(r => setTimeout(r, ms));
const ask   = q  => new Promise(r => rl.question(q, r));

function genName()     { return `${pick(FIRST_NAMES)} ${pick(LAST_NAMES)}`; }
function genUsername(name) {
  const [first, last] = name.toLowerCase().split(" ");
  return pick([
    () => `${first}.${last}${rand(10,99)}`,
    () => `${first}_${last.slice(0,3)}${rand(10,99)}`,
    () => `${first}${last}${rand(100,999)}`,
    () => `_${first}${rand(10,99)}${last.slice(0,2)}`,
    () => `${first.slice(0,3)}${last}${rand(10,99)}`,
  ])();
}
function genDevice() {
  const [manufacturer, model, codename, cpu] = pick(DEVICES);
  return {
    phone_id: uuidv4(), device_id: "android-" + uuidv4().replace(/-/g,"").slice(0,16),
    uuid: uuidv4(), waterfall_id: uuidv4(),
    manufacturer, model, codename, cpu,
    resolution: pick(["1080x2220","1080x2340","1080x2400"]),
    dpi: pick(["420","480","560"]),
  };
}
function calcJazoest(phoneId) {
  return "2" + [...phoneId].reduce((s, c) => s + c.charCodeAt(0), 0);
}
function buildHeaders(device) {
  const ua = `Instagram ${IG_VERSION} Android (33/13; ${device.dpi}dpi; ${device.resolution}; ${device.manufacturer}; ${device.model}; ${device.codename}; ${device.cpu}; en_US; 655896867)`;
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
    "X-IG-Device-ID":         device.uuid,
    "X-IG-Android-ID":        device.device_id,
    "X-Pigeon-Session-Id":    uuidv4(),
    "X-Pigeon-Rawclienttime": (Date.now() / 1000).toFixed(3),
    "X-Bloks-Version-Id":     "ce9b4eb3f7fc0b57b4e4af765b66b3bfe9e3a5bbd58e50feac0e6ed8a6834bc5",
    "X-Bloks-Is-Layout-RTL":  "false",
    "Accept-Language":        "en-US",
    "Accept-Encoding":        "gzip, deflate",
    "Content-Type":           "application/x-www-form-urlencoded",
    "Connection":             "close",
  };
}

// ─── IG API ──────────────────────────────────────────────────────────────────
async function igGet(url, params, headers) {
  const qs = new URLSearchParams(params).toString();
  const r  = await fetch(`${url}?${qs}`, { headers });
  return { status: r.status, data: await r.text() };
}

async function igPost(url, body, headers) {
  const r = await fetch(url, {
    method: "POST",
    headers,
    body: new URLSearchParams(body).toString(),
  });
  const text = await r.text();
  let data = text;
  try { data = JSON.parse(text); } catch {}
  return { status: r.status, data };
}

async function stepFetchHeaders(device, headers) {
  const r = await igGet(`${IG_BASE}/api/v1/si/fetch_headers/`,
    { challenge_type: "signup", guid: device.uuid.replace(/-/g,"") }, headers);
  console.log(`  [fetch_headers] ${r.status}`);
  return r.status === 200;
}

async function stepSendOtp(device, email, headers) {
  const r = await igPost(`${IG_BASE}/api/v1/accounts/send_verify_email/`, {
    phone_id: device.phone_id, device_id: device.device_id,
    email, waterfall_id: device.waterfall_id, tos_version: "row",
  }, headers);
  console.log(`  [send_verify_email] ${r.status} → ${JSON.stringify(r.data).slice(0,150)}`);
  return r.status === 200;
}

async function stepVerifyOtp(device, email, otp, headers) {
  const r = await igPost(`${IG_BASE}/api/v1/accounts/check_confirmation_code/`, {
    code: otp, device_id: device.device_id,
    email, waterfall_id: device.waterfall_id,
  }, headers);
  console.log(`  [check_confirmation_code] ${r.status} → ${JSON.stringify(r.data).slice(0,150)}`);
  if (r.status === 200) return r.data?.signup_code || r.data?.code || null;
  return null;
}

async function stepCreate(device, email, password, username, name, signupCode, headers) {
  const r = await igPost(`${IG_BASE}/api/v1/accounts/create/`, {
    jazoest:            calcJazoest(device.phone_id),
    country_codes:      '[{"country_code":"1","source":["default"]}]',
    phone_id:           device.phone_id,
    enc_password:       `#PWD_INSTAGRAM:0:${Math.floor(Date.now()/1000)}:${password}`,
    username, first_name: name,
    day: rand(1,28), month: rand(1,12), year: rand(1993,2001),
    registrationMethod: "email",
    email, signup_code: signupCode,
    seamlesssignup_used:"0", tos_version: "row",
    suggestedUsername:  "", sn_result: "GOOGLE_PLAY_UNAVAILABLE",
    do_not_auto_login_if_credentials_match: "false",
    device_id: device.device_id, uuid: device.uuid,
    waterfall_id: device.waterfall_id, _uuid: device.uuid,
  }, headers);
  console.log(`  [create] ${r.status} → ${JSON.stringify(r.data).slice(0,200)}`);
  return r.status === 200 ? r.data : null;
}

// ─── RUNNER ──────────────────────────────────────────────────────────────────
function saveResult(email, username, password, uid = "") {
  fs.appendFileSync(OUTPUT_FILE, `email=${email} | username=${username} | password=${password} | uid=${uid}\n`);
}

async function run(email, password) {
  console.log("\n" + "─".repeat(55));
  const device  = genDevice();
  const headers = buildHeaders(device);
  const name     = genName();
  const username = genUsername(name);
  console.log(`[*] Email    : ${email}`);
  console.log(`[*] Name     : ${name}`);
  console.log(`[*] Username : @${username}`);

  console.log("[1/4] Fetch headers...");
  if (!await stepFetchHeaders(device, headers)) { console.log("[!] Gagal."); return; }
  await sleep(rand(2000, 4000));

  console.log("[2/4] Kirim OTP ke email...");
  if (!await stepSendOtp(device, email, headers)) { console.log("[!] Gagal kirim OTP."); return; }

  const otp = (await ask(`[3/4] OTP dari ${email} : `)).trim();
  if (!otp) { console.log("[!] OTP kosong, skip."); return; }

  const signupCode = await stepVerifyOtp(device, email, otp, headers);
  if (!signupCode) { console.log("[!] OTP salah / expired."); return; }

  console.log("[4/4] Buat akun...");
  const result = await stepCreate(device, email, password, username, name, signupCode, headers);
  if (!result) return;

  const uid = result?.created_user?.pk ?? "";
  console.log(`\n[✓] Sukses! @${username} | uid=${uid}`);
  saveResult(email, username, password, uid);
  console.log(`[*] Disimpan ke ${OUTPUT_FILE}`);
}

// ─── MAIN ────────────────────────────────────────────────────────────────────
async function main() {
  const password = fs.readFileSync(PASSWORD_FILE, "utf8").trim().split("\n")[0];
  const emails   = fs.readFileSync(EMAIL_FILE, "utf8").trim().split("\n").filter(Boolean);
  console.log(`=== IG Creator | ${emails.length} akun ===`);

  for (let i = 0; i < emails.length; i++) {
    console.log(`\n[Akun ${i+1}/${emails.length}]`);
    await run(emails[i].trim(), password);
    if (i < emails.length - 1) {
      const delay = rand(10000, 20000);
      console.log(`[*] Jeda ${delay/1000}s...`);
      await sleep(delay);
    }
  }
  console.log(`\n=== Selesai. Hasil di ${OUTPUT_FILE} ===`);
  rl.close();
}

main().catch(err => { console.error(err); rl.close(); });
