from utime import ticks_ms, ticks_diff, sleep_ms
from machine import Pin, ADC
import network
import ujson

from fhir_client_enhanced import FHIRClient

# =========================
# IIR Filter
# =========================
class IIR_filter:
    def __init__(self, alpha):
        self.old_value = 0.0
        self.alpha = alpha

    def step(self, value):
        value = (self.old_value * self.alpha + value * (1 - self.alpha))
        self.old_value = value
        return value

# =========================
# Config
# =========================
WIFI_SSID = "tungman142"
WIFI_PASSWORD = "tungman212142"

FHIR_BASE_URL = "http://192.168.0.9:8080/fhir"
PATIENT_ID = "1139"

ADC_PIN = 36
BLUE_LED_PIN = 5
BUZZER_PIN = 2
BUZZER_ACTIVE_HIGH = True   # 蜂鳴器不叫就改 False

TEST_DURATION_MS = 30000
LED_BLINK_MS = 200
START_END_BEEP_MS = 500
PRINT_EVERY_MS = 3000

BEEP_ON_BEAT = True
BEEP_MS = 60

# DC remover + nodc peak detection
DC_ALPHA = 0.995
LEVEL_ALPHA = 0.95
NODC_OFFSET = 2
REFRACTORY_MS = 250

RR_MIN_MS = 270
RR_MAX_MS = 2000
TARGET_N_BEATS = 3

SAMPLE_MS = 10

# =========================
# Helpers (no HTTP here)
# =========================
def buzzer_on(buzzer: Pin):
    buzzer.value(1 if BUZZER_ACTIVE_HIGH else 0)

def buzzer_off(buzzer: Pin):
    buzzer.value(0 if BUZZER_ACTIVE_HIGH else 1)

def beep(buzzer: Pin, ms: int):
    # 非阻塞：只開啟蜂鳴器，關閉交給主迴圈用 beep_until 控制
    buzzer_on(buzzer)
    return ticks_ms() + ms

def blink_led_step(led: Pin, now, next_toggle_ts, interval_ms):
    if ticks_diff(now, next_toggle_ts) >= 0:
        led.value(0 if led.value() else 1)
        next_toggle_ts = now + interval_ms
    return next_toggle_ts

# =========================
# Hardware init
# =========================
blue_led = Pin(BLUE_LED_PIN, Pin.OUT)
blue_led.value(0)

buzzer = Pin(BUZZER_PIN, Pin.OUT)
buzzer_off(buzzer)

adc = ADC(Pin(ADC_PIN))
adc.width(ADC.WIDTH_10BIT)
adc.atten(ADC.ATTN_11DB)

dc_remover = IIR_filter(DC_ALPHA)
nodc_level_filter = IIR_filter(LEVEL_ALPHA)

# =========================
# WiFi + FHIR
# =========================
print("=" * 50)
print("ESP32 HR 30s | DC remover + nodc local peak (NO AC_extractor)")
print("=" * 50)

sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect(WIFI_SSID, WIFI_PASSWORD)

timeout = 30
while (not sta.isconnected()) and timeout > 0:
    sleep_ms(1000)
    timeout -= 1
    print(".", end="")

fhir_ok = False
fhir_client = None

if not sta.isconnected():
    print("\n[X] WiFi failed -> local only")
else:
    ip = sta.ifconfig()[0]
    print("\n[OK] WiFi connected, IP:", ip)

    fhir_client = FHIRClient(FHIR_BASE_URL)
    if fhir_client.test_connection():
        print("[OK] FHIR reachable:", FHIR_BASE_URL)
        fhir_ok = True
    else:
        print("[X] FHIR unreachable -> local only")

# =========================
# Test Start
# =========================
print("\n[TEST] Start 30s measurement")
beep_until = beep(buzzer, START_END_BEEP_MS)


test_start = ticks_ms()
test_end = test_start + TEST_DURATION_MS

next_led_toggle = ticks_ms()
next_print = ticks_ms()
next_sample = ticks_ms()

# init with first sample
raw_val = adc.read()
ecg = raw_val
dc_remover.old_value = float(ecg)

dc_val = float(ecg)
nodc = 0.0
nodc_level = 0.0
trigger_level = 0.0

# local peak buffers
n2 = 0.0
n1 = 0.0
n0 = 0.0

lockout_until = 0
beep_until = 0

beat_time_mark = ticks_ms()
last_rr = -1
num_beats = 0
tot_intval = 0
heart_rate = 0.0
last_hr_update_ts = ticks_ms()

# store samples (for session summary / debugging)
session_samples = []

# (optional) avoid uploading same HR too frequently
last_uploaded_hr = None

while True:
    now = ticks_ms()

    next_led_toggle = blink_led_step(blue_led, now, next_led_toggle, LED_BLINK_MS)

    if ticks_diff(now, test_end) >= 0:
        break

    if beep_until != 0 and ticks_diff(now, beep_until) > 0:
        buzzer_off(buzzer)
        beep_until = 0

    # sample every SAMPLE_MS
    if ticks_diff(now, next_sample) >= 0:
        next_sample = now + SAMPLE_MS

        raw_val = adc.read()
        ecg = raw_val

        # DC remove
        dc_val = dc_remover.step(ecg)
        nodc = ecg - dc_val

        # background level
        nodc_level = nodc_level_filter.step(abs(nodc))
        trigger_level = nodc_level + NODC_OFFSET

        # update local peak buffers
        n2, n1, n0 = n1, n0, nodc

        # local peak detect
        if (ticks_diff(now, lockout_until) >= 0) and (n1 > n2) and (n1 > n0) and (n1 > trigger_level):
            lockout_until = now + REFRACTORY_MS

            rr = ticks_diff(now, beat_time_mark)
            last_rr = rr
            beat_time_mark = now

            if RR_MAX_MS > rr > RR_MIN_MS:
                tot_intval += rr
                num_beats += 1
                if num_beats == TARGET_N_BEATS:
                    seconds = tot_intval / 1000.0
                    heart_rate = round(TARGET_N_BEATS / (seconds / 60.0), 1)
                    last_hr_update_ts = now
                    tot_intval = 0
                    num_beats = 0
            else:
                tot_intval = 0
                num_beats = 0

            if BEEP_ON_BEAT:
                beep_until = beep(buzzer, BEEP_MS)

    # every 3 seconds: print + store sample + upload HR (via fhir_client)
    if ticks_diff(now, next_print) >= 0:
        next_print = now + PRINT_EVERY_MS
        t_ms = ticks_diff(now, test_start)
        age_ms = ticks_diff(now, last_hr_update_ts)

        # store sample
        session_samples.append({"t_ms": int(t_ms), "hr": float(heart_rate)})

        # print status
        if heart_rate > 0 and age_ms < 8000:
            print("[HR]", heart_rate, "bpm",
                  "| rr=", last_rr, "ms",
                  "| nodc=", int(nodc),
                  "| lvl=", int(nodc_level),
                  "| trig=", int(trigger_level))
        else:
            print("[NO_HR] t=", int(t_ms), "ms",
                  "| raw=", int(raw_val),
                  "| ecg=", int(ecg),
                  "| dc=", int(dc_val),
                  "| nodc=", int(nodc),
                  "| lvl=", int(nodc_level),
                  "| trig=", int(trigger_level),
                  "| last_rr=", last_rr)

        # upload this HR sample as a standard Heart Rate Observation
        if fhir_ok and fhir_client is not None:
            if heart_rate > 0 and age_ms < 8000:
                # avoid spamming identical HR (optional)
                if (last_uploaded_hr is None) or (abs(heart_rate - last_uploaded_hr) >= 0.1):
                    success, res = fhir_client.create_heart_rate_observation(PATIENT_ID, heart_rate)
                    if success:
                        last_uploaded_hr = heart_rate
                    else:
                        print("[FHIR] ✗ HR upload failed:", res)
            else:
                # 沒 HR 也留個記錄（可選：不想上傳就把這段刪掉）
                # success, res = fhir_client.create_heart_rate_observation(PATIENT_ID, 0)  # 不建議
                pass

# =========================
# End
# =========================
blue_led.value(0)
buzzer_off(buzzer)
beep_until = beep(buzzer, START_END_BEEP_MS)
# 讓它真的叫完再結束（只在結束時等，不影響量測）
while beep_until != 0 and ticks_diff(ticks_ms(), beep_until) > 0:
    sleep_ms(10)
buzzer_off(buzzer)
beep_until = 0
print("[TEST] Done. LED OFF. Samples:", len(session_samples))

# =========================
# Upload one session summary (optional, via fhir_client function)
# =========================
if fhir_ok and fhir_client is not None:
    # 把整包 JSON 放到 notes 裡，不自建 HTTP function
    summary_notes = ujson.dumps({
        "duration_ms": TEST_DURATION_MS,
        "print_every_ms": PRINT_EVERY_MS,
        "samples": session_samples
    })

    # 用 client 的 generic API 上傳一筆「Session Summary」
    # 這筆不一定會被你的 UI 算進「生理數據」，但會出現在 timeline 當作紀錄
    success, res = fhir_client.create_vital_sign_observation(
        PATIENT_ID,
        measurement_type="HR Session Summary",
        value=0,
        unit="session",
        notes=summary_notes
    )
    if success:
        print("[FHIR] ✓ Session summary uploaded:", res)
    else:
        print("[FHIR] ✗ Session summary upload failed:", res)
