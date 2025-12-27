# fhir_client_enhanced.py - 完整的 FHIR API 客戶端
# 支援 ESP32 和 Streamlit 共用

try:
    import urequests as requests
    import ujson as json
    from utime import localtime
    IS_MICROPYTHON = True
except ImportError:
    import requests
    import json
    from datetime import datetime
    IS_MICROPYTHON = False


class FHIRClient:
    """完整的 FHIR API 客戶端，支援創建、讀取、搜索功能"""
    
    def __init__(self, fhir_base_url="http://192.168.0.9:8080/fhir"):
        """
        初始化 FHIR 客戶端
        
        Args:
            fhir_base_url: FHIR 服務器的基礎 URL
        """
        self.base_url = fhir_base_url.rstrip('/')
        self.headers = {
            'Content-Type': 'application/fhir+json',
            'Accept': 'application/fhir+json'
        }
    
    # ==================== 工具函數 ====================
    
    def _get_timestamp(self):
        """生成 ISO 8601 格式的時間戳"""
        if IS_MICROPYTHON:
            # 注意：你的 ESP32 RTC 多半已設為台灣時間(UTC+8)
            # 所以這裡不要硬加 Z(UTC)，避免時間被誤標
            t = localtime()
            return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(
                t[0], t[1], t[2], t[3], t[4], t[5]
            )
        else:
            return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    
    def _make_request(self, method, url, data=None, params=None):
        """
        統一的 HTTP 請求處理
        
        Args:
            method: HTTP 方法 (GET, POST, PUT, DELETE)
            url: 完整的 URL
            data: 請求體數據
            params: URL 參數
        
        Returns:
            (success, response_data or error_message)
        """
        try:
            # 處理 URL 參數（MicroPython 的 urequests 不支持 params）
            if params:
                param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
                url = f"{url}?{param_str}"
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers)
            elif method.upper() == 'POST':
                json_data = json.dumps(data) if data else None
                response = requests.post(url, data=json_data, headers=self.headers)
            elif method.upper() == 'PUT':
                json_data = json.dumps(data) if data else None
                response = requests.put(url, data=json_data, headers=self.headers)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            else:
                return False, f"Unsupported method: {method}"
            
            # 詳細日誌
            if IS_MICROPYTHON:
                print(f"  DEBUG: Response status={response.status_code}")
            
            success = response.status_code in [200, 201]
            
            if success:
                try:
                    data = response.json()
                    response.close()
                    
                    # 詳細日誌
                    if IS_MICROPYTHON:
                        print(f"  DEBUG: JSON parsed successfully")
                    
                    return True, data
                except Exception as e:
                    # 詳細日誌
                    if IS_MICROPYTHON:
                        print(f"  DEBUG: JSON parse failed: {e}")
                    
                    response.close()
                    return True, None
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.text
                    error_msg += f": {error_data[:400]}"  # 取前400字符，較容易看到關鍵錯誤
                except:
                    pass
                
                # 詳細日誌
                if IS_MICROPYTHON:
                    print(f"  DEBUG: Request failed: {error_msg}")
                
                response.close()
                return False, error_msg
                
        except Exception as e:
            # 詳細日誌
            if IS_MICROPYTHON:
                print(f"  DEBUG: Exception: {e}")
            
            return False, str(e)
    
    # ==================== Patient 資源管理 ====================
    
    def create_patient(self, identifier, full_name, gender=None, birth_date=None):
        """
        創建 Patient 資源
        
        Args:
            identifier: 病患識別碼（例如：username）
            full_name: 姓名
            gender: 性別 (male/female/other)
            birth_date: 生日 (YYYY-MM-DD)
        
        Returns:
            (success, patient_id or error_message)
        """
        # 拆分姓名為 family 和 given
        name_parts = full_name.split(' ', 1)
        family_name = name_parts[0]
        given_name = name_parts[1] if len(name_parts) > 1 else ""
        
        patient = {
            "resourceType": "Patient",
            "identifier": [{
                "system": "http://192.168.0.9:8080/patient-id",
                "value": identifier
            }],
            "name": [{
                "family": family_name,
                "given": [given_name] if given_name else []
            }],
            "active": True
        }
        
        if gender:
            patient["gender"] = gender
        
        if birth_date:
            patient["birthDate"] = birth_date
        
        url = f"{self.base_url}/Patient"
        success, result = self._make_request('POST', url, patient)
        
        if success and result:
            patient_id = result.get('id')
            print(f"✓ Patient created: {patient_id}")
            return True, patient_id
        else:
            print(f"✗ Patient creation failed: {result}")
            return False, result
    
    def get_patient(self, patient_id):
        """
        取得 Patient 資源
        
        Args:
            patient_id: Patient 的 FHIR ID
        
        Returns:
            (success, patient_resource or error_message)
        """
        url = f"{self.base_url}/Patient/{patient_id}"
        
        # 詳細日誌（調試用）
        if IS_MICROPYTHON:
            print(f"  DEBUG: GET {url}")
        
        success, result = self._make_request('GET', url)
        
        # 詳細日誌（調試用）
        if IS_MICROPYTHON:
            print(f"  DEBUG: success={success}, result type={type(result)}")
            if success and result:
                print(f"  DEBUG: result keys={list(result.keys()) if isinstance(result, dict) else 'not dict'}")
        
        return success, result
    
    def search_patients(self, identifier=None, name=None):
        """
        搜索 Patient 資源
        
        Args:
            identifier: 病患識別碼
            name: 姓名（部分匹配）
        
        Returns:
            (success, list of patients or error_message)
        """
        url = f"{self.base_url}/Patient"
        params = {}
        
        if identifier:
            params['identifier'] = identifier
        if name:
            params['name'] = name
        
        success, result = self._make_request('GET', url, params=params)
        
        if success and result:
            entries = result.get('entry', [])
            patients = [entry['resource'] for entry in entries]
            return True, patients
        else:
            return False, result
    
    def get_patient_by_identifier(self, identifier):
        """
        根據 identifier 取得 Patient
        
        Args:
            identifier: 病患識別碼（例如 username）
        
        Returns:
            (success, patient_resource or None)
        """
        success, patients = self.search_patients(identifier=identifier)
        
        if success and patients:
            # 返回第一個匹配的患者
            return True, patients[0]
        else:
            return False, None
    
    # ==================== Observation 資源管理 ====================
    
    def create_heart_rate_observation(self, patient_id, heart_rate, 
                                      measurement_time=None, notes=None):
        """
        創建心率 Observation
        
        Args:
            patient_id: Patient 的 FHIR ID
            heart_rate: 心率值 (bpm)
            measurement_time: 測量時間（ISO格式），默認為當前時間
            notes: 備註
        
        Returns:
            (success, observation_id or error_message)
        """
        observation = {
            "resourceType": "Observation",
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs"
                }]
            }],
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "8867-4",
                    "display": "Heart rate"
                }],
                "text": "Heart Rate"
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "effectiveDateTime": measurement_time or self._get_timestamp(),
            "valueQuantity": {
                "value": heart_rate,
                "unit": "beats/minute",
                "system": "http://unitsofmeasure.org",
                "code": "/min"
            }
        }
        
        if notes:
            observation["note"] = [{"text": notes}]
        
        url = f"{self.base_url}/Observation"
        success, result = self._make_request('POST', url, observation)
        
        if success and result:
            obs_id = result.get('id')
            print(f"✓ Heart rate observation created: {obs_id}")
            return True, obs_id
        else:
            print(f"✗ Heart rate observation failed: {result}")
            return False, result
    
    def create_ecg_observation(self, patient_id, ecg_value, 
                               measurement_time=None, notes=None):
        """
        創建 ECG Observation
        
        Args:
            patient_id: Patient 的 FHIR ID
            ecg_value: ECG 數值
            measurement_time: 測量時間（ISO格式），默認為當前時間
            notes: 備註
        
        Returns:
            (success, observation_id or error_message)
        """
        observation = {
            "resourceType": "Observation",
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs"
                }]
            }],
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "131328",
                    "display": "MDC ECG"
                }],
                "text": "ECG Signal"
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "effectiveDateTime": measurement_time or self._get_timestamp(),
            "valueQuantity": {
                "value": ecg_value,
                "unit": "mV",
                "system": "http://unitsofmeasure.org",
                "code": "mV"
            }
        }
        
        if notes:
            observation["note"] = [{"text": notes}]
        
        url = f"{self.base_url}/Observation"
        success, result = self._make_request('POST', url, observation)
        
        if success and result:
            obs_id = result.get('id')
            print(f"✓ ECG observation created: {obs_id}")
            return True, obs_id
        else:
            print(f"✗ ECG observation failed: {result}")
            return False, result
    
    def create_vital_sign_observation(self, patient_id, measurement_type, 
                                      value, unit, measurement_time=None, notes=None):
        """
        創建通用的生理數據 Observation
        
        Args:
            patient_id: Patient 的 FHIR ID
            measurement_type: 測量類型（如：血壓、血糖等）
            value: 數值
            unit: 單位
            measurement_time: 測量時間（ISO格式），默認為當前時間
            notes: 備註
        
        Returns:
            (success, observation_id or error_message)
        """
        # LOINC 代碼映射
        loinc_codes = {
            "血壓收縮壓": ("8480-6", "Systolic blood pressure"),
            "血壓舒張壓": ("8462-4", "Diastolic blood pressure"),
            "血糖": ("2339-0", "Glucose"),
            "體溫": ("8310-5", "Body temperature"),
            "血氧飽和度": ("59408-5", "Oxygen saturation"),
            "體重": ("29463-7", "Body weight"),
            "身高": ("8302-2", "Body height")
        }
        
        loinc_code, display = loinc_codes.get(measurement_type, ("unknown", measurement_type))
        
        observation = {
            "resourceType": "Observation",
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs"
                }]
            }],
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": loinc_code,
                    "display": display
                }],
                "text": measurement_type
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "effectiveDateTime": measurement_time or self._get_timestamp(),
            "valueQuantity": {
                "value": value,
                "unit": unit,
                "system": "http://unitsofmeasure.org",
                "code": unit
            }
        }
        
        if notes:
            observation["note"] = [{"text": notes}]
        
        url = f"{self.base_url}/Observation"
        success, result = self._make_request('POST', url, observation)
        
        if success and result:
            obs_id = result.get('id')
            print(f"✓ Vital sign observation created: {obs_id}")
            return True, obs_id
        else:
            print(f"✗ Vital sign observation failed: {result}")
            return False, result
    
    def get_observation(self, observation_id):
        """
        取得 Observation 資源
        
        Args:
            observation_id: Observation 的 FHIR ID
        
        Returns:
            (success, observation_resource or error_message)
        """
        url = f"{self.base_url}/Observation/{observation_id}"
        return self._make_request('GET', url)
    
    def get_patient_observations(self, patient_id, code=None, limit=20):
        """
        取得病患的所有 Observation
        
        Args:
            patient_id: Patient 的 FHIR ID
            code: LOINC 代碼篩選（可選）
            limit: 返回數量限制
        
        Returns:
            (success, list of observations or error_message)
        """
        url = f"{self.base_url}/Observation"
        params = {
            'patient': patient_id,
            '_count': limit,
            '_sort': '-date'  # 按日期降序
        }
        
        if code:
            params['code'] = code
        
        success, result = self._make_request('GET', url, params=params)
        
        if success and result:
            entries = result.get('entry', [])
            observations = [entry['resource'] for entry in entries]
            return True, observations
        else:
            return False, result
    
    def get_patient_heart_rates(self, patient_id, limit=20):
        """取得病患的心率記錄"""
        return self.get_patient_observations(patient_id, code="8867-4", limit=limit)
    
    def get_patient_vital_signs(self, patient_id, measurement_type=None, limit=20):
        """
        取得病患的生理數據
        
        Args:
            patient_id: Patient 的 FHIR ID
            measurement_type: 測量類型（可選）
            limit: 返回數量限制
        """
        loinc_codes = {
            "血壓收縮壓": "8480-6",
            "血壓舒張壓": "8462-4",
            "血糖": "2339-0",
            "體溫": "8310-5",
            "血氧飽和度": "59408-5",
            "體重": "29463-7",
            "身高": "8302-2"
        }
        
        code = loinc_codes.get(measurement_type) if measurement_type else None
        return self.get_patient_observations(patient_id, code=code, limit=limit)
    
    # ==================== ESP32 兼容方法 ====================
    
    def send_heart_rate(self, heart_rate, patient_id="patient-001"):
        """
        ESP32 用：發送心率數據（兼容舊版 API）
        
        Args:
            heart_rate: 心率值 (bpm)
            patient_id: Patient ID（默認為 patient-001）
        
        Returns:
            bool: 成功返回 True
        """
        if heart_rate <= 0:
            return False
        
        success, result = self.create_heart_rate_observation(patient_id, heart_rate)
        return success
    
    def send_ecg(self, ecg_value, patient_id="patient-001"):
        """
        ESP32 用：發送 ECG 數據（兼容舊版 API）
        
        Args:
            ecg_value: ECG 原始值
            patient_id: Patient ID（默認為 patient-001）
        
        Returns:
            bool: 成功返回 True
        """
        success, result = self.create_ecg_observation(patient_id, ecg_value)
        return success
    
    def test_connection(self):
        """測試與 FHIR 服務器的連接"""
        try:
            url = f"{self.base_url}/metadata"
            response = requests.get(url, headers={'Accept': 'application/fhir+json'})
            success = response.status_code == 200
            response.close()
            
            if success:
                print("✓ FHIR 服務器連接成功")
            else:
                print(f"✗ FHIR 服務器連接失敗: {response.status_code}")
            
            return success
        except Exception as e:
            print(f"✗ FHIR 服務器連接錯誤: {e}")
            return False
    
    # ==================== 數據解析工具 ====================
    
    def parse_observation(self, observation):
        """
        解析 Observation 資源，提取關鍵信息
        
        Args:
            observation: FHIR Observation 資源
        
        Returns:
            dict: 解析後的數據
        """
        result = {
            'id': observation.get('id'),
            'type': observation.get('code', {}).get('text', 'Unknown'),
            'value': None,
            'unit': None,
            'time': observation.get('effectiveDateTime'),
            'notes': None,
            'patient_id': None
        }
        
        # 提取數值
        if 'valueQuantity' in observation:
            result['value'] = observation['valueQuantity'].get('value')
            result['unit'] = observation['valueQuantity'].get('unit')
        
        # 提取備註
        if 'note' in observation and observation['note']:
            result['notes'] = observation['note'][0].get('text')
        
        # 提取 Patient ID
        if 'subject' in observation:
            ref = observation['subject'].get('reference', '')
            if '/' in ref:
                result['patient_id'] = ref.split('/')[-1]
        
        return result


# ==================== 測試代碼 ====================
if __name__ == '__main__' and not IS_MICROPYTHON:
    print("=" * 50)
    print("FHIR Client 測試")
    print("=" * 50)
    
    # 初始化客戶端
    client = FHIRClient("http://192.168.0.9:8080/fhir")

    # 測試連接
    print("\n1. 測試連接...")
    client.test_connection()
    
    # 創建測試病患
    print("\n2. 創建測試病患...")
    success, patient_id = client.create_patient(
        identifier="test-user-001",
        full_name="張 大明",
        gender="male",
        birth_date="1990-01-01"
    )
    
    if success:
        print(f"   Patient ID: {patient_id}")
        
        # 創建心率記錄
        print("\n3. 創建心率記錄...")
        success, obs_id = client.create_heart_rate_observation(
            patient_id, 75, notes="測試記錄"
        )
        
        if success:
            print(f"   Observation ID: {obs_id}")
        
        # 查詢病患的觀察記錄
        print("\n4. 查詢病患的觀察記錄...")
        success, observations = client.get_patient_observations(patient_id, limit=5)
        
        if success:
            print(f"   找到 {len(observations)} 筆記錄")
            for obs in observations:
                parsed = client.parse_observation(obs)
                print(f"   - {parsed['type']}: {parsed['value']} {parsed['unit']}")
    
    print("\n" + "=" * 50)
    print("測試完成")
    print("=" * 50)