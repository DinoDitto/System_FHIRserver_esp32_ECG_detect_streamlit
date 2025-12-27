# fhir_manager.py - FHIR 為中心的數據管理器
# 替代 database.py，所有健康數據存儲在 FHIR Server

import json
import hashlib
from pathlib import Path
from datetime import datetime
from fhir_client_enhanced import FHIRClient


class FHIRManager:
    """
    FHIR 為中心的數據管理器
    
    - 用戶認證：本地 JSON 文件
    - 健康數據：FHIR Server
    """
    
    def __init__(self, fhir_server_url="http://localhost:8080/fhir", 
                 users_file="users.json"):
        """
        初始化 FHIR Manager
        
        Args:
            fhir_server_url: FHIR Server URL (默認：本機 HTTP)
            users_file: 用戶認證資料檔案
        """
        self.fhir_client = FHIRClient(fhir_server_url)
        self.users_file = Path(users_file)
        self._init_users_file()
    
    # ==================== 用戶認證管理（本地 JSON） ====================
    
    def _init_users_file(self):
        """初始化用戶資料檔案"""
        if not self.users_file.exists():
            # 創建預設管理員帳號
            default_users = {
                "users": [
                    {
                        "id": 1,
                        "username": "admin",
                        "password": self.hash_password("admin123"),
                        "full_name": "系統管理員",
                        "role": "admin",
                        "gender": "other",
                        "birth_date": "1990-01-01",
                        "fhir_patient_id": None,
                        "created_at": datetime.now().isoformat()
                    }
                ],
                "next_id": 2
            }
            
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(default_users, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 用戶資料檔案已創建: {self.users_file}")
    
    def _load_users(self):
        """載入用戶資料"""
        with open(self.users_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_users(self, data):
        """儲存用戶資料"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def hash_password(self, password):
        """密碼雜湊"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_user(self, username, password):
        """
        驗證使用者
        
        Returns:
            (success, user_data or None)
        """
        data = self._load_users()
        hashed_password = self.hash_password(password)
        
        for user in data['users']:
            if user['username'] == username and user['password'] == hashed_password:
                return True, {
                    'id': user['id'],
                    'username': user['username'],
                    'full_name': user['full_name'],
                    'role': user['role'],
                    'fhir_patient_id': user.get('fhir_patient_id')
                }
        
        return False, None
    
    def add_user(self, username, password, full_name, role='user', 
                 birth_date=None, gender=None):
        """
        新增使用者（同時在 FHIR Server 創建 Patient）
        
        Returns:
            (success, user_id or error_message)
        """
        data = self._load_users()
        
        # 檢查用戶名是否已存在
        if any(u['username'] == username for u in data['users']):
            return False, "使用者名稱已存在"
        
        # 為一般使用者在 FHIR Server 創建 Patient
        fhir_patient_id = None
        if role == 'user':
            success, result = self.fhir_client.create_patient(
                identifier=username,
                full_name=full_name,
                gender=gender,
                birth_date=birth_date
            )
            
            if success:
                fhir_patient_id = result
                print(f"✓ FHIR Patient created: {fhir_patient_id}")
            else:
                print(f"✗ FHIR Patient creation failed: {result}")
                # 繼續創建本地用戶，稍後可以同步
        
        # 創建本地用戶記錄
        user_id = data['next_id']
        new_user = {
            "id": user_id,
            "username": username,
            "password": self.hash_password(password),
            "full_name": full_name,
            "role": role,
            "gender": gender,
            "birth_date": birth_date,
            "fhir_patient_id": fhir_patient_id,
            "created_at": datetime.now().isoformat()
        }
        
        data['users'].append(new_user)
        data['next_id'] += 1
        self._save_users(data)
        
        return True, user_id
    
    def get_all_users(self):
        """取得所有使用者"""
        data = self._load_users()
        return [
            {
                'id': u['id'],
                'username': u['username'],
                'full_name': u['full_name'],
                'role': u['role'],
                'gender': u.get('gender'),
                'birth_date': u.get('birth_date'),
                'fhir_patient_id': u.get('fhir_patient_id'),
                'created_at': u['created_at']
            }
            for u in data['users']
        ]
    
    def get_user_by_id(self, user_id):
        """根據 ID 取得使用者"""
        data = self._load_users()
        
        for user in data['users']:
            if user['id'] == user_id:
                return {
                    'id': user['id'],
                    'username': user['username'],
                    'full_name': user['full_name'],
                    'role': user['role'],
                    'gender': user.get('gender'),
                    'birth_date': user.get('birth_date'),
                    'fhir_patient_id': user.get('fhir_patient_id'),
                    'created_at': user['created_at']
                }
        
        return None
    
    def delete_user(self, user_id):
        """刪除使用者（僅刪除本地記錄，不刪除 FHIR 資源）"""
        data = self._load_users()
        
        # 不允許刪除管理員
        user = next((u for u in data['users'] if u['id'] == user_id), None)
        if user and user['role'] == 'admin':
            return False
        
        data['users'] = [u for u in data['users'] if u['id'] != user_id]
        self._save_users(data)
        return True
    
    def update_user_fhir_id(self, user_id, fhir_patient_id):
        """更新使用者的 FHIR Patient ID"""
        data = self._load_users()
        
        for user in data['users']:
            if user['id'] == user_id:
                user['fhir_patient_id'] = fhir_patient_id
                self._save_users(data)
                return True
        
        return False
    
    # ==================== 健康數據管理（FHIR Server） ====================
    
    def add_ecg_measurement(self, user_id, measurement_time, ecg_data=None,
                           heart_rate=None, notes=None):
        """
        新增 ECG 測量記錄（直接存到 FHIR Server）
        
        Args:
            user_id: 用戶 ID
            measurement_time: 測量時間（ISO格式字串）
            ecg_data: ECG 原始數據（可選）
            heart_rate: 心率 (bpm)
            notes: 備註
        
        Returns:
            observation_id or None
        """
        user = self.get_user_by_id(user_id)
        if not user or not user.get('fhir_patient_id'):
            print(f"✗ User {user_id} has no FHIR Patient ID")
            return None
        
        patient_id = user['fhir_patient_id']
        
        # 創建心率 Observation
        if heart_rate:
            success, obs_id = self.fhir_client.create_heart_rate_observation(
                patient_id=patient_id,
                heart_rate=heart_rate,
                measurement_time=measurement_time,
                notes=notes
            )
            
            if success:
                return obs_id
        
        return None
    
    def add_vital_sign(self, user_id, measurement_time, measurement_type,
                      value, unit=None, notes=None):
        """
        新增生理數據記錄（直接存到 FHIR Server）
        
        Args:
            user_id: 用戶 ID
            measurement_time: 測量時間（ISO格式字串）
            measurement_type: 測量類型
            value: 數值
            unit: 單位
            notes: 備註
        
        Returns:
            observation_id or None
        """
        user = self.get_user_by_id(user_id)
        if not user or not user.get('fhir_patient_id'):
            print(f"✗ User {user_id} has no FHIR Patient ID")
            return None
        
        patient_id = user['fhir_patient_id']
        
        success, obs_id = self.fhir_client.create_vital_sign_observation(
            patient_id=patient_id,
            measurement_type=measurement_type,
            value=value,
            unit=unit,
            measurement_time=measurement_time,
            notes=notes
        )
        
        if success:
            return obs_id
        
        return None
    
    def get_user_ecg_measurements(self, user_id, limit=20):
        """
        取得使用者的 ECG 測量記錄（從 FHIR Server）
        
        Returns:
            list of measurement dicts
        """
        user = self.get_user_by_id(user_id)
        if not user or not user.get('fhir_patient_id'):
            return []
        
        patient_id = user['fhir_patient_id']
        
        # 取得心率觀察記錄
        success, observations = self.fhir_client.get_patient_heart_rates(
            patient_id, limit=limit
        )
        
        if not success:
            return []
        
        # 轉換為應用程式格式
        measurements = []
        for obs in observations:
            parsed = self.fhir_client.parse_observation(obs)
            measurements.append({
                'id': parsed['id'],
                'measurement_time': parsed['time'],
                'heart_rate': int(parsed['value']) if parsed['value'] else None,
                'notes': parsed['notes'],
                'created_at': parsed['time']
            })
        
        return measurements
    
    def get_user_vital_signs(self, user_id, measurement_type=None, limit=20):
        """
        取得使用者的生理數據記錄（從 FHIR Server）
        
        Returns:
            list of vital sign dicts
        """
        user = self.get_user_by_id(user_id)
        if not user or not user.get('fhir_patient_id'):
            return []
        
        patient_id = user['fhir_patient_id']
        
        # 取得生理數據觀察記錄
        success, observations = self.fhir_client.get_patient_vital_signs(
            patient_id, 
            measurement_type=measurement_type,
            limit=limit
        )
        
        if not success:
            return []
        
        # 轉換為應用程式格式
        vital_signs = []
        for obs in observations:
            parsed = self.fhir_client.parse_observation(obs)
            
            # 跳過心率記錄（已在 ECG 中處理）
            if 'Heart rate' in parsed['type']:
                continue
            
            vital_signs.append({
                'id': parsed['id'],
                'measurement_time': parsed['time'],
                'measurement_type': parsed['type'],
                'value': parsed['value'],
                'unit': parsed['unit'],
                'notes': parsed['notes']
            })
        
        return vital_signs
    
    # ==================== FHIR 同步與管理 ====================
    
    def test_fhir_connection(self):
        """測試 FHIR Server 連線"""
        return self.fhir_client.test_connection()
    
    def sync_user_to_fhir(self, user_id):
        """
        同步使用者到 FHIR Server（如果還沒有 Patient ID）
        
        Returns:
            (success, patient_id or error_message)
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return False, "使用者不存在"
        
        # 如果已經有 FHIR ID，直接返回
        if user.get('fhir_patient_id'):
            return True, user['fhir_patient_id']
        
        # 創建 FHIR Patient
        success, result = self.fhir_client.create_patient(
            identifier=user['username'],
            full_name=user['full_name'],
            gender=user.get('gender'),
            birth_date=user.get('birth_date')
        )
        
        if success:
            # 更新本地記錄
            self.update_user_fhir_id(user_id, result)
            return True, result
        else:
            return False, result
    
    def get_fhir_sync_status(self, user_id):
        """
        取得使用者的 FHIR 同步狀態
        
        Returns:
            status dict
        """
        user = self.get_user_by_id(user_id)
        
        status = {
            'user_fhir_id': user.get('fhir_patient_id') if user else None,
            'ecg_total': 0,
            'ecg_synced': 0,
            'vital_total': 0,
            'vital_synced': 0
        }
        
        if user and user.get('fhir_patient_id'):
            # 從 FHIR Server 取得記錄數量
            ecg_records = self.get_user_ecg_measurements(user_id, limit=1000)
            vital_records = self.get_user_vital_signs(user_id, limit=1000)
            
            status['ecg_total'] = len(ecg_records)
            status['ecg_synced'] = len(ecg_records)  # 全部都已同步
            status['vital_total'] = len(vital_records)
            status['vital_synced'] = len(vital_records)  # 全部都已同步
        
        return status
    
    # ==================== 初始化示範數據 ====================
    
    def init_demo_data(self):
        """初始化示範數據（可選）"""
        print("\n初始化示範數據...")
        
        # 新增示範使用者
        success, user_id = self.add_user(
            username="user1",
            password="pass123",
            full_name="王小明",
            role="user",
            gender="male",
            birth_date="1995-03-15"
        )
        
        if success:
            print(f"✓ 示範使用者已創建: user1 (ID: {user_id})")
            
            # 新增示範 ECG 記錄
            for i in range(5):
                obs_id = self.add_ecg_measurement(
                    user_id=user_id,
                    measurement_time=datetime.now().isoformat(),
                    heart_rate=70 + i * 2,
                    notes=f"測試記錄 {i+1}"
                )
                if obs_id:
                    print(f"  ✓ ECG 記錄 {i+1} 已創建")
            
            # 新增示範生理數據
            vital_types = [
                ("血壓收縮壓", 120, "mmHg"),
                ("血壓舒張壓", 80, "mmHg"),
                ("體溫", 36.5, "°C"),
                ("血氧飽和度", 98, "%")
            ]
            
            for vtype, value, unit in vital_types:
                obs_id = self.add_vital_sign(
                    user_id=user_id,
                    measurement_time=datetime.now().isoformat(),
                    measurement_type=vtype,
                    value=value,
                    unit=unit,
                    notes="示範數據"
                )
                if obs_id:
                    print(f"  ✓ {vtype} 記錄已創建")
        
        print("\n✅ 示範數據初始化完成")


# ==================== 測試代碼 ====================
if __name__ == '__main__':
    print("=" * 50)
    print("FHIR Manager 測試")
    print("=" * 50)
    
    # 初始化管理器
    manager = FHIRManager(fhir_server_url="https://hapi.fhir.org/baseR4")
    
    # 測試連接
    print("\n1. 測試 FHIR Server 連接...")
    if manager.test_fhir_connection():
        print("   ✓ 連接成功")
    else:
        print("   ✗ 連接失敗")
    
    # 測試登入
    print("\n2. 測試管理員登入...")
    success, user_data = manager.verify_user("admin", "admin123")
    if success:
        print(f"   ✓ 登入成功: {user_data['full_name']}")
    else:
        print("   ✗ 登入失敗")
    
    # 列出所有使用者
    print("\n3. 列出所有使用者...")
    users = manager.get_all_users()
    for user in users:
        print(f"   - {user['full_name']} ({user['username']}) - FHIR ID: {user.get('fhir_patient_id')}")
    
    # 詢問是否初始化示範數據
    print("\n要初始化示範數據嗎？(y/n): ", end="")
    choice = input().strip().lower()
    if choice == 'y':
        manager.init_demo_data()
    
    print("\n" + "=" * 50)
    print("測試完成")
    print("=" * 50)