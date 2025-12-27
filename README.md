# 🏥 FHIR ECG Health Management System

基於 FHIR 標準的 ESP32 ECG 健康監測與管理系統

## 📋 目錄

- [系統概述](#系統概述)
- [系統架構](#系統架構)
- [功能特點](#功能特點)
- [技術棧](#技術棧)
- [系統需求](#系統需求)
- [安裝部署](#安裝部署)
- [使用指南](#使用指南)
- [配置說明](#配置說明)
- [故障排除](#故障排除)
- [開發指南](#開發指南)
- [License](#license)

---

## 🎯 系統概述

這是一個完整的健康監測系統，整合了：
- **ESP32 硬體**：實時心電圖（ECG）信號採集與心率檢測
- **FHIR Server**：符合 FHIR（Fast Healthcare Interoperability Resources）標準的醫療數據存儲
- **Streamlit 前端**：直觀的 Web 界面，用於數據管理與可視化

### 主要特色

✅ **符合醫療標準**：完全遵循 FHIR R4 標準  
✅ **實時監測**：ESP32 實時採集心電信號並計算心率  
✅ **雲端同步**：所有數據自動同步到 FHIR Server  
✅ **多用戶管理**：支持管理員和普通用戶角色  
✅ **數據可視化**：豐富的圖表展示健康趨勢  

---

## 🏗️ 系統架構

```
┌─────────────────┐
│   ESP32 硬體    │
│  - ECG 感測器   │
│  - WiFi 模組    │
│  - 心率計算     │
└────────┬────────┘
         │ HTTP/FHIR
         ↓
┌─────────────────┐
│  HAPI FHIR      │
│  Server         │
│  (Docker)       │
│  - Patient      │
│  - Observation  │
└────────┬────────┘
         │ REST API
         ↓
┌─────────────────┐
│  Streamlit      │
│  Web Interface  │
│  - 用戶管理     │
│  - 數據可視化   │
│  - 趨勢分析     │
└─────────────────┘
```

### 數據流程

1. **ESP32 採集** → ECG 信號 + 心率計算
2. **FHIR 上傳** → 創建 FHIR Observation 資源
3. **數據存儲** → HAPI FHIR Server 持久化
4. **前端展示** → Streamlit 讀取並可視化

---

## ✨ 功能特點

### ESP32 硬體端

- ✅ **實時 ECG 採集**（10ms 採樣率）
- ✅ **DC 偏移去除**（IIR 濾波器）
- ✅ **心率檢測**（基於局部峰值檢測）
- ✅ **30 秒測量週期**
- ✅ **WiFi 自動連接**
- ✅ **FHIR 數據上傳**
- ✅ **LED反饋**

### FHIR Server

- ✅ **Patient 資源管理**
- ✅ **Observation 資源存儲**
- ✅ **標準 LOINC 編碼**
- ✅ **RESTful API**
- ✅ **數據持久化**（支援 Docker volume）

### Streamlit 前端

#### 管理員功能
- ✅ **用戶管理**（新增、編輯、刪除）
- ✅ **FHIR 同步**（自動創建 Patient 資源）
- ✅ **所有用戶數據查看**
- ✅ **系統統計儀表板**

#### 用戶功能
- ✅ **個人健康數據查看**
- ✅ **心率趨勢圖**
- ✅ **ECG 測量歷史**
- ✅ **測量詳情查看**

---

## 🛠️ 技術棧

### 硬體
- **ESP32** (MicroPython)
- **ECG 感測器**（AD8232 或類似）
- **LED 指示燈**
- **蜂鳴器**

### 後端
- **HAPI FHIR Server** (Docker)
- **FHIR R4 標準**
- **Python FHIR Client**

### 前端
- **Streamlit** (Python)
- **Plotly** (數據可視化)
- **Pandas** (數據處理)

### 開發工具
- **mpremote** (ESP32 燒錄)
- **Docker** (FHIR Server 部署)
- **VS Code** (推薦開發環境)

---

## 💻 系統需求

### 硬體需求

| 組件 | 規格 |
|------|------|
| ESP32 開發板 | ESP32-WROOM-32 或類似 |
| ECG 感測器 | AD8232 模組 |
| LED | 藍色 LED × 1 |
| 蜂鳴器 | 有源或無源蜂鳴器 × 1 |
| 電源 | USB 供電（5V） |

### 軟體需求

| 項目 | 版本 |
|------|------|
| Python | 3.8+ |
| Docker | 20.10+ |
| MicroPython | ESP32 firmware |
| Node.js | 14+ (可選，用於開發) |

### 網路需求

- WiFi 網路（ESP32 和電腦需在同一網段）
- 開放端口：8080（FHIR Server）、8501（Streamlit）

---

## 📦 安裝部署

### 1. 部署 FHIR Server

#### 使用 Docker（推薦）

```bash
# 停止並刪除舊容器
docker stop hapi-fhir
docker rm hapi-fhir

# 創建數據目錄（持久化）
mkdir %USERPROFILE%\hapi-fhir-data  # Windows
mkdir ~/hapi-fhir-data              # Linux/macOS

# 啟動 HAPI FHIR Server（持久化模式）
docker run -d \
  --name hapi-fhir \
  -p 8080:8080 \
  -v ~/hapi-fhir-data:/data/hapi \
  -e spring.datasource.url="jdbc:h2:file:/data/hapi/db;DB_CLOSE_DELAY=-1" \
  hapiproject/hapi:latest

# 等待服務器啟動（約 30 秒）
# 測試連接
curl http://localhost:8080/fhir/metadata
```

**測試 FHIR Server：**
瀏覽器訪問 http://localhost:8080/fhir

---

### 2. 部署 Streamlit 前端

```bash
# Clone 或下載專案
cd streamlit_FHIR

# 安裝 Python 依賴
pip install -r requirements.txt

# 啟動 Streamlit
streamlit run app.py

# 瀏覽器會自動打開 http://localhost:8501
```

**requirements.txt 內容：**
```
streamlit>=1.28.0
requests>=2.31.0
pandas>=2.0.0
plotly>=5.17.0
```

**預設帳號：**
- 管理員：`admin` / `admin123`
- 用戶：`user1` / `pass123`

---

### 3. 燒錄 ESP32 程式

#### 準備工作

```bash
# 安裝 mpremote
pip install mpremote

# 查看 COM 端口（Windows）
mode  # 或使用設備管理器

# 查看設備（Linux/macOS）
ls /dev/tty*
```

#### 上傳程式

```bash
cd ESP32

# 上傳 FHIR Client
mpremote connect COM6 cp fhir_client_enhanced.py :fhir_client_enhanced.py

# 上傳主程式
mpremote connect COM6 cp main.py :main.py

# 重啟 ESP32
mpremote connect COM6 reset

# 監控輸出（可選）
python -m serial.tools.miniterm COM6 115200
```

---

## 📖 使用指南

### ESP32 操作流程

#### 1. **配置 ESP32**

編輯 `ESP32/main.py`，修改以下配置：

```python
# WiFi 設定
WIFI_SSID = "你的WiFi名稱"
WIFI_PASSWORD = "你的WiFi密碼"

# FHIR Server 設定
FHIR_BASE_URL = "http://192.168.0.9:8080/fhir"  # 改成你電腦的 IP
PATIENT_ID = "1139"  # 從 Streamlit 獲取的 Patient ID
```

**如何獲取電腦 IP：**
```bash
# Windows
ipconfig

# Linux/macOS
ifconfig
```

#### 2. **硬體連接**

| ESP32 Pin | 連接 |
|-----------|------|
| GPIO 36 (VP) | ECG 信號輸出 |
| GPIO 5 | 藍色 LED（正極） |
| GPIO 2 | 蜂鳴器（正極） |
| GND | 所有地線 |

#### 3. **測量流程**

1. **上傳程式**並重啟 ESP32
2. **等待 WiFi 連接**（LED 開始閃爍）
3. **聽到長嗶聲**表示測量開始
4. **保持靜止 30 秒**
5. **測量結束**會聽到長嗶聲
6. **查看 Streamlit** 確認數據已上傳

**ESP32 輸出示例：**
```
==================================================
ESP32 HR 30s | DC remover + nodc local peak
==================================================
Connecting to WiFi: tungman142...
[OK] WiFi connected, IP: 192.168.0.12
[OK] FHIR reachable: http://192.168.0.9:8080/fhir

[TEST] Start 30s measurement
[HR] 75.2 bpm | rr= 800 ms | nodc= 125 | lvl= 45 | trig= 47
[HR] 76.5 bpm | rr= 785 ms | nodc= 130 | lvl= 46 | trig= 48
[HR] 74.8 bpm | rr= 805 ms | nodc= 128 | lvl= 45 | trig= 47

[TEST] Done. LED OFF. Samples: 10
[FHIR] ✓ Session summary uploaded: 5678
```

---

### Streamlit 使用指南

#### 管理員操作

1. **登入系統**
   - 使用 `admin` / `admin123` 登入
   - 自動進入首頁

2. **創建新用戶**
   - 前往「後台管理 → 使用者管理」
   - 點擊「新增使用者」
   - 填寫資料並儲存
   - **記下 FHIR Patient ID**（給 ESP32 使用）

3. **查看用戶數據**
   - 在「用戶列表」中選擇用戶
   - 查看該用戶的所有測量記錄
   - 查看心率趨勢圖

4. **系統統計**
   - 首頁顯示系統統計資訊
   - 包括用戶數、FHIR 同步狀態等

#### 用戶操作

1. **登入系統**
   - 使用個人帳號密碼登入

2. **查看健康數據**
   - 前往「我的健康數據」
   - 查看最近的測量記錄
   - 查看心率趨勢圖

3. **查看測量詳情**
   - 點擊任一記錄展開詳情
   - 查看完整的測量資訊

---

## ⚙️ 配置說明

### ESP32 配置選項

```python
# main.py 配置說明

# === WiFi 設定 ===
WIFI_SSID = "tungman142"        # WiFi 名稱
WIFI_PASSWORD = "tungman212142"  # WiFi 密碼

# === FHIR Server 設定 ===
FHIR_BASE_URL = "http://192.168.0.9:8080/fhir"  # FHIR Server URL
PATIENT_ID = "1139"  # Patient ID（從 Streamlit 獲取）

# === 硬體設定 ===
ADC_PIN = 36              # ECG 信號輸入（GPIO 36 / VP）
BLUE_LED_PIN = 5          # LED 指示燈（GPIO 5）
BUZZER_PIN = 2            # 蜂鳴器（GPIO 2）
BUZZER_ACTIVE_HIGH = True # 蜂鳴器邏輯（True=高電平觸發）

# === 測量設定 ===
TEST_DURATION_MS = 30000  # 測量時長（30 秒）
SAMPLE_MS = 10            # 採樣間隔（10ms = 100Hz）
PRINT_EVERY_MS = 3000     # 打印間隔（3 秒）

# === 心率檢測設定 ===
DC_ALPHA = 0.995          # DC 濾波器係數
LEVEL_ALPHA = 0.95        # 背景水平濾波係數
NODC_OFFSET = 2           # 觸發閾值偏移
REFRACTORY_MS = 250       # 不應期（防止重複檢測）
RR_MIN_MS = 270           # 最小 RR 間隔（222 bpm）
RR_MAX_MS = 2000          # 最大 RR 間隔（30 bpm）
TARGET_N_BEATS = 3        # 計算心率用的心跳數

# === 反饋設定 ===
BEEP_ON_BEAT = True       # 心跳時發出嗶聲
BEEP_MS = 60              # 嗶聲時長（60ms）
LED_BLINK_MS = 200        # LED 閃爍間隔（200ms）
START_END_BEEP_MS = 500   # 開始/結束嗶聲時長（500ms）
```

### Streamlit 配置

```python
# app.py 配置

# FHIR Server URL（Streamlit 在同一台電腦用 localhost）
FHIR_SERVER_URL = "http://localhost:8080/fhir"

# 如果 Streamlit 在不同電腦，改成：
# FHIR_SERVER_URL = "http://192.168.0.9:8080/fhir"
```

### 網路配置注意事項

**所有設備必須在同一網段！**

✅ **正確配置：**
- ESP32 IP: `192.168.0.12`
- 電腦 IP: `192.168.0.9`
- FHIR Server: `192.168.0.9:8080`

❌ **錯誤配置：**
- ESP32 IP: `192.168.0.12`
- 電腦 IP: `172.20.10.6`（不同網段）

**解決方法：**
1. 所有設備連接同一個 WiFi
2. 或使用手機熱點讓所有設備連接

---

## 🐛 故障排除

### 常見問題

#### 1. ESP32 無法連接 WiFi

**症狀：**
```
[X] WiFi failed -> local only
```

**解決：**
- 檢查 WiFi SSID 和密碼是否正確
- 確認 ESP32 支援該 WiFi 頻段（僅支援 2.4GHz）
- 檢查 WiFi 信號強度

---

#### 2. ESP32 無法連接 FHIR Server

**症狀：**
```
[X] FHIR unreachable -> local only
```

**解決：**
1. **檢查網路連通性**
   ```bash
   # 在電腦上測試
   curl http://192.168.0.9:8080/fhir/metadata
   ```

2. **確認 IP 正確**
   - ESP32 的 `FHIR_BASE_URL` 要用電腦的實際 IP
   - 不能用 `localhost`（ESP32 無法解析）

3. **檢查防火牆**
   ```bash
   # Windows 防火牆允許 8080 端口
   netsh advfirewall firewall add rule name="HAPI FHIR" dir=in action=allow protocol=TCP localport=8080
   ```

4. **確認 FHIR Server 運行**
   ```bash
   docker ps | findstr hapi-fhir
   ```

---

#### 3. Patient ID 錯誤

**症狀：**
```
[FHIR] ✗ HR upload failed: HTTP 400
```

**解決：**
1. 確認 Patient 已在 Streamlit 創建
2. 從 Streamlit「使用者管理」獲取正確的 FHIR Patient ID
3. 更新 ESP32 的 `PATIENT_ID`

**驗證 Patient 存在：**
```bash
# 在瀏覽器訪問
http://localhost:8080/fhir/Patient/1139
```

---

#### 4. Streamlit 無法連接 FHIR Server

**症狀：**
```
❌ FHIR Server 連線失敗
```

**解決：**
1. 確認 FHIR Server 正在運行
   ```bash
   docker ps
   ```

2. 確認 `app.py` 的 URL 正確
   ```python
   # Streamlit 在同一台電腦用 localhost
   FHIR_SERVER_URL = "http://localhost:8080/fhir"
   ```

3. 測試連接
   ```bash
   curl http://localhost:8080/fhir/metadata
   ```

---

#### 5. 心率檢測不準確

**症狀：**
- 心率顯示為 0
- 心率波動過大
- 沒有檢測到心跳

**解決：**
1. **檢查 ECG 信號質量**
   - 查看 `nodc` 值（應該有明顯波動）
   - 查看 `lvl` 和 `trig` 值

2. **調整檢測參數**
   ```python
   # 增加觸發閾值（如果誤檢測太多）
   NODC_OFFSET = 5  # 原本是 2
   
   # 增加不應期（如果重複檢測）
   REFRACTORY_MS = 350  # 原本是 250
   
   # 調整 DC 濾波器（如果基線漂移）
   DC_ALPHA = 0.998  # 原本是 0.995
   ```

3. **改善硬體連接**
   - 確認電極片貼緊皮膚
   - 減少干擾源（遠離電源線）
   - 保持靜止不動

---

#### 6. 數據沒有顯示在 Streamlit

**檢查清單：**
- [ ] ESP32 成功上傳（看到 `✓` 符號）
- [ ] Patient ID 正確
- [ ] FHIR Server 正常運行
- [ ] Streamlit 刷新頁面

**查看 FHIR Server 原始數據：**
```bash
# 查看某個 Patient 的所有 Observation
http://localhost:8080/fhir/Observation?subject=Patient/1139
```

---

### 調試技巧

#### ESP32 調試

**查看詳細輸出：**
```bash
python -m serial.tools.miniterm COM6 115200
```

**測試網路連接：**
```python
# 在 ESP32 REPL 中測試
import urequests
response = urequests.get("http://192.168.0.9:8080/fhir/metadata")
print(response.status_code)
response.close()
```

#### FHIR Server 調試

**查看 Docker 日誌：**
```bash
docker logs hapi-fhir
```

**測試 API：**
```bash
# 獲取所有 Patient
curl http://localhost:8080/fhir/Patient

# 創建測試 Patient
curl -X POST http://localhost:8080/fhir/Patient \
  -H "Content-Type: application/fhir+json" \
  -d '{"resourceType":"Patient","name":[{"text":"Test User"}]}'
```

#### Streamlit 調試

**啟用調試模式：**
```bash
streamlit run app.py --logger.level=debug
```

**查看 Python 錯誤：**
- Streamlit 會在界面顯示完整錯誤訊息
- 或查看終端輸出

---

## 👨‍💻 開發指南

### 專案結構

```
project/
├── ESP32/
│   ├── main.py                      # ESP32 主程式
│   ├── fhir_client_enhanced.py      # FHIR Client 庫
│   ├── circular_buffer.py           # 循環緩衝區（備用）
│   └── max30102.py                  # MAX30102 驅動（備用）
│
├── streamlit_FHIR/
│   ├── app.py                       # Streamlit 主程式
│   ├── fhir_manager.py              # FHIR 管理器
│   ├── fhir_client_enhanced.py      # FHIR Client（共用）
│   ├── users.json                   # 用戶數據庫
│   ├── requirements.txt             # Python 依賴
│   └── pages/
│       ├── 1_admin_dashboard.py     # 管理員頁面
│       └── 2_user_dashboard.py      # 用戶頁面
│
├── hapi-fhir-jpaserver-starter/     # FHIR Server 源碼（可選）
└── README.md                         # 本文件
```

### 核心組件說明

#### 1. fhir_client_enhanced.py

**功能：**
- FHIR 資源的創建、讀取、更新、刪除（CRUD）
- 支援 MicroPython（ESP32）和標準 Python（Streamlit）
- 自動處理 HTTP 請求和 JSON 序列化

**主要方法：**
```python
# Patient 管理
create_patient(identifier, full_name, gender, birth_date)
get_patient(patient_id)
search_patients(identifier, name)

# Observation 管理
create_heart_rate_observation(patient_id, heart_rate)
create_vital_sign_observation(patient_id, type, value, unit)
get_patient_observations(patient_id, limit)

# 連接測試
test_connection()
```

#### 2. fhir_manager.py

**功能：**
- Streamlit 專用的 FHIR 管理層
- 用戶認證與授權
- 本地用戶數據庫（users.json）與 FHIR 同步

**主要方法：**
```python
# 用戶管理
verify_user(username, password)
create_user(username, password, full_name, ...)
update_user(user_id, ...)
delete_user(user_id)

# FHIR 同步
sync_user_to_fhir(user_data)
get_user_ecg_measurements(user_id, limit)
get_user_vital_signs(user_id, limit)
```

#### 3. main.py (ESP32)

**核心流程：**
1. WiFi 連接
2. FHIR Client 初始化
3. 30 秒測量循環
   - 10ms 採樣
   - DC 去除
   - 心跳檢測
   - 心率計算
4. 每 3 秒上傳心率到 FHIR
5. 測量結束上傳完整會話摘要

**關鍵算法：**
```python
# DC 去除（IIR 濾波）
dc_val = dc_remover.step(ecg)
nodc = ecg - dc_val

# 背景水平估計
nodc_level = level_filter.step(abs(nodc))
trigger_level = nodc_level + NODC_OFFSET

# 局部峰值檢測
if (n1 > n2) and (n1 > n0) and (n1 > trigger_level):
    # 檢測到心跳
    calculate_heart_rate()
```

### 擴展開發

#### 添加新的生理參數

**1. 修改 ESP32 程式：**
```python
# 添加新參數測量
spo2 = measure_spo2()  # 假設函數

# 使用 FHIR Client 上傳
success, res = fhir_client.create_vital_sign_observation(
    PATIENT_ID,
    measurement_type="SpO2",
    value=spo2,
    unit="%",
    notes="Peripheral oxygen saturation"
)
```

**2. FHIR Client 無需修改**（通用方法）

**3. 修改 Streamlit 前端：**
```python
# 在 fhir_manager.py 添加獲取方法
def get_user_spo2(self, user_id, limit=100):
    observations = self.get_user_vital_signs(user_id, limit)
    return [obs for obs in observations if obs['measurement_type'] == 'SpO2']
```

#### 添加新的感測器

**1. 創建驅動文件**（例如 `spo2_sensor.py`）：
```python
class SpO2Sensor:
    def __init__(self, i2c):
        self.i2c = i2c
    
    def read(self):
        # 讀取感測器數據
        return spo2_value
```

**2. 整合到 main.py：**
```python
from spo2_sensor import SpO2Sensor

spo2_sensor = SpO2Sensor(i2c)

# 在測量循環中
spo2 = spo2_sensor.read()
fhir_client.create_vital_sign_observation(...)
```

### API 參考

#### FHIR Server RESTful API

**基礎 URL：** `http://localhost:8080/fhir`

**常用端點：**

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/metadata` | 獲取 Server 能力聲明 |
| GET | `/Patient` | 列出所有 Patient |
| GET | `/Patient/{id}` | 獲取特定 Patient |
| POST | `/Patient` | 創建新 Patient |
| GET | `/Observation?subject=Patient/{id}` | 獲取 Patient 的所有 Observation |
| POST | `/Observation` | 創建新 Observation |

**示例：創建 Patient**
```bash
curl -X POST http://localhost:8080/fhir/Patient \
  -H "Content-Type: application/fhir+json" \
  -d '{
    "resourceType": "Patient",
    "identifier": [{
      "system": "http://ditto-healthcare.org/patient-id",
      "value": "user123"
    }],
    "name": [{
      "text": "張小明"
    }],
    "gender": "male",
    "birthDate": "1990-01-01"
  }'
```

**示例：創建 Observation（心率）**
```bash
curl -X POST http://localhost:8080/fhir/Observation \
  -H "Content-Type: application/fhir+json" \
  -d '{
    "resourceType": "Observation",
    "status": "final",
    "code": {
      "coding": [{
        "system": "http://loinc.org",
        "code": "8867-4",
        "display": "Heart rate"
      }]
    },
    "subject": {
      "reference": "Patient/1139"
    },
    "effectiveDateTime": "2025-12-27T22:30:00Z",
    "valueQuantity": {
      "value": 75.2,
      "unit": "beats/minute",
      "system": "http://unitsofmeasure.org",
      "code": "/min"
    }
  }'
```

### 測試

#### 單元測試（Python）

```python
# test_fhir_client.py
import unittest
from fhir_client_enhanced import FHIRClient

class TestFHIRClient(unittest.TestCase):
    def setUp(self):
        self.client = FHIRClient("http://localhost:8080/fhir")
    
    def test_connection(self):
        self.assertTrue(self.client.test_connection())
    
    def test_create_patient(self):
        success, patient_id = self.client.create_patient(
            "test123", "Test User", "male", "2000-01-01"
        )
        self.assertTrue(success)
        self.assertIsNotNone(patient_id)

if __name__ == '__main__':
    unittest.main()
```

#### 集成測試（端到端）

```python
# test_end_to_end.py
# 測試完整流程：創建 Patient → 上傳 Observation → 驗證數據

def test_full_workflow():
    # 1. 創建 Patient
    client = FHIRClient("http://localhost:8080/fhir")
    success, patient_id = client.create_patient(...)
    assert success
    
    # 2. 上傳心率數據
    success, obs_id = client.create_heart_rate_observation(patient_id, 75.0)
    assert success
    
    # 3. 讀取並驗證
    success, observations = client.get_patient_observations(patient_id)
    assert success
    assert len(observations) > 0
    assert observations[0]['value'] == 75.0
```

---

## 📊 性能優化

### ESP32 優化

1. **減少上傳頻率**
   ```python
   PRINT_EVERY_MS = 5000  # 從 3 秒改為 5 秒
   ```

2. **批量上傳**（減少 HTTP 請求）
   ```python
   # 累積多筆數據後一次上傳
   batch_data = []
   # ... 收集數據 ...
   # 一次上傳所有數據
   ```

3. **降低採樣率**（如果不需要高精度）
   ```python
   SAMPLE_MS = 20  # 從 10ms 改為 20ms (50Hz)
   ```

### FHIR Server 優化

1. **使用更高效的數據庫**
   ```bash
   # 從 H2 改為 PostgreSQL
   docker run -d \
     --name hapi-fhir \
     -e spring.datasource.url="jdbc:postgresql://db:5432/hapi" \
     ...
   ```

2. **增加 JVM 記憶體**
   ```bash
   docker run -d \
     --name hapi-fhir \
     -e JAVA_OPTS="-Xmx2g -Xms1g" \
     ...
   ```

### Streamlit 優化

1. **緩存數據**
   ```python
   @st.cache_data(ttl=60)  # 緩存 60 秒
   def get_user_data(user_id):
       return fhir_manager.get_user_ecg_measurements(user_id)
   ```

2. **分頁加載**
   ```python
   # 一次只加載 20 筆記錄
   measurements = fhir_manager.get_user_ecg_measurements(user_id, limit=20)
   ```

---

## 🔒 安全性考量

### 生產環境部署建議

1. **啟用 HTTPS**
   ```bash
   # 使用 Nginx 反向代理
   # 配置 SSL 證書
   ```

2. **用戶認證加強**
   ```python
   # 使用更安全的密碼哈希（如 bcrypt）
   import bcrypt
   hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
   ```

3. **API 訪問控制**
   ```python
   # 添加 JWT Token 認證
   # 限制 API 訪問頻率
   ```

4. **數據加密**
   ```python
   # 敏感數據加密存儲
   # 傳輸層使用 TLS
   ```

5. **FHIR Server 安全**
   ```bash
   # 啟用認證
   # 限制外部訪問
   # 定期備份數據
   ```

---

## 📝 FHIR 標準參考

本系統使用 **FHIR R4** 標準，主要資源類型：

### Patient Resource

用於存儲患者基本資訊：
- 識別碼（Identifier）
- 姓名（Name）
- 性別（Gender）
- 出生日期（Birth Date）

**規範：** https://www.hl7.org/fhir/patient.html

### Observation Resource

用於存儲測量數據：
- 心率（Heart Rate）- LOINC Code: `8867-4`
- 血氧（SpO2）- LOINC Code: `59408-5`
- 體溫（Temperature）- LOINC Code: `8310-5`

**規範：** https://www.hl7.org/fhir/observation.html

### LOINC Codes

系統使用標準 LOINC 編碼：
- `8867-4`: Heart rate
- `131328`: ECG study
- `8310-5`: Body temperature
- `59408-5`: Oxygen saturation

**查詢：** https://loinc.org/

---

## 📄 License

本專案採用 MIT License。

```
MIT License

Copyright (c) 2024 FHIR ECG Health Management System

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📞 聯繫與支持

如有問題或建議，歡迎通過以下方式聯繫：

- **GitHub Issues**: [專案頁面](https://github.com/your-repo)
- **Email**: your-email@example.com
- **Documentation**: [完整文檔](https://your-docs-site.com)

---

## 🙏 致謝

本專案使用了以下開源項目：

- **HAPI FHIR** - FHIR Server 實現
- **Streamlit** - Web 應用框架
- **MicroPython** - ESP32 Python 運行環境
- **Plotly** - 數據可視化庫

特別感謝所有貢獻者和社群支持！

---

## 📅 更新日誌

### v1.0.0 (2025-12-27)

**初始發布**

✨ **新功能：**
- ESP32 實時 ECG 採集與心率檢測
- FHIR R4 標準數據存儲
- Streamlit Web 管理界面
- 多用戶管理系統
- 數據可視化與趨勢分析

🐛 **修復：**
- MicroPython urequests params 參數問題
- NTP 時間同步
- FHIR Patient 驗證問題

📚 **文檔：**
- 完整的 README
- 配置指南
- 故障排除文檔
- API 參考

---

**最後更新：** 2025-12-27  
**版本：** 1.0.0  
**狀態：** ✅ 穩定版本
