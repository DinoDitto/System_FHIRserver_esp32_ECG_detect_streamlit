import streamlit as st
import sys
import os
from datetime import datetime
import pandas as pd

# 加入父目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fhir_manager import FHIRManager

# 檢查登入狀態
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ 請先登入")
    st.stop()

# 檢查管理員權限
if st.session_state.user['role'] != 'admin':
    st.error("❌ 您沒有權限訪問此頁面")
    st.stop()

# 初始化 FHIR Manager
if 'fhir_manager' not in st.session_state:
    st.session_state.fhir_manager = FHIRManager()

st.set_page_config(
    page_title="後台管理",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ 後台管理系統")
st.markdown("---")

# 側邊欄
st.sidebar.title(f"👤 {st.session_state.user['full_name']}")
st.sidebar.write(f"**角色:** 管理員")
st.sidebar.markdown("---")

# Tab 選單
tab1, tab2, tab3, tab4 = st.tabs(["👥 使用者管理", "📊 ECG 數據管理", "💊 生理數據管理", "➕ 新增記錄"])

# ==================== Tab 1: 使用者管理 ====================
with tab1:
    st.header("👥 使用者管理")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 所有使用者")
        
        # 取得所有使用者
        users = st.session_state.fhir_manager.get_all_users()
        
        if users:
            # 轉換成 DataFrame
            df_users = pd.DataFrame(users)
            df_users = df_users[['id', 'username', 'full_name', 'role', 'gender', 'birth_date', 'fhir_patient_id']]
            df_users.columns = ['ID', '帳號', '姓名', '角色', '性別', '生日', 'FHIR Patient ID']
            
            # 簡化 FHIR ID 顯示
            df_users['FHIR Patient ID'] = df_users['FHIR Patient ID'].apply(
                lambda x: f"{x[:8]}..." if x else "未同步"
            )
            
            st.dataframe(df_users, use_container_width=True, hide_index=True)
            
            st.info(f"📌 總共 {len(users)} 位使用者")
        else:
            st.warning("⚠️ 目前沒有使用者")
    
    with col2:
        st.subheader("➕ 新增使用者")
        
        with st.form("add_user_form"):
            new_username = st.text_input("帳號*")
            new_password = st.text_input("密碼*", type="password")
            new_full_name = st.text_input("姓名*")
            new_role = st.selectbox("角色*", ["user", "admin"])
            new_gender = st.selectbox("性別", ["male", "female", "other"])
            new_birth_date = st.date_input("生日")
            
            submit = st.form_submit_button("新增使用者", use_container_width=True)
            
            if submit:
                if new_username and new_password and new_full_name:
                    with st.spinner("正在創建使用者並同步到 FHIR Server..."):
                        success, result = st.session_state.fhir_manager.add_user(
                            new_username,
                            new_password,
                            new_full_name,
                            new_role,
                            str(new_birth_date),
                            new_gender
                        )
                        
                        if success:
                            st.success(f"✅ 成功新增使用者: {new_full_name}")
                            st.info(f"📌 User ID: {result}")
                            
                            # 顯示 FHIR Patient ID
                            user = st.session_state.fhir_manager.get_user_by_id(result)
                            if user.get('fhir_patient_id'):
                                st.success(f"✅ FHIR Patient ID: {user['fhir_patient_id']}")
                            
                            st.rerun()
                        else:
                            st.error(f"❌ 新增失敗: {result}")
                else:
                    st.warning("⚠️ 請填寫所有必填欄位")
    
    # 刪除使用者功能
    st.markdown("---")
    st.subheader("🗑️ 刪除使用者")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_to_delete = st.selectbox(
            "選擇要刪除的使用者",
            options=[u['id'] for u in users if u['role'] != 'admin'],
            format_func=lambda x: next((u['full_name'] + f" ({u['username']})" for u in users if u['id'] == x), "")
        )
    
    with col2:
        if st.button("🗑️ 刪除", type="secondary"):
            if st.session_state.fhir_manager.delete_user(user_to_delete):
                st.success("✅ 已刪除使用者（本地記錄）")
                st.info("ℹ️ FHIR Server 上的 Patient 資源不會被刪除")
                st.rerun()
            else:
                st.error("❌ 刪除失敗")

# ==================== Tab 2: ECG 數據管理 ====================
with tab2:
    st.header("📊 ECG 測量數據管理")
    
    # 選擇使用者
    users = st.session_state.fhir_manager.get_all_users()
    user_options = [u for u in users if u['role'] == 'user']
    
    if user_options:
        selected_user_id = st.selectbox(
            "選擇使用者",
            options=[u['id'] for u in user_options],
            format_func=lambda x: next((u['full_name'] + f" ({u['username']})" for u in user_options if u['id'] == x), "")
        )
        
        # 顯示該使用者的 ECG 記錄
        st.subheader(f"📈 ECG 測量記錄")
        
        # 顯示 FHIR Patient ID
        user = st.session_state.fhir_manager.get_user_by_id(selected_user_id)
        if user.get('fhir_patient_id'):
            st.info(f"🌐 FHIR Patient ID: {user['fhir_patient_id']}")
        else:
            st.warning("⚠️ 此使用者尚未同步到 FHIR Server")
        
        # 從 FHIR Server 載入資料
        with st.spinner("正在從 FHIR Server 載入資料..."):
            ecg_records = st.session_state.fhir_manager.get_user_ecg_measurements(
                selected_user_id, limit=50
            )
        
        if ecg_records:
            df_ecg = pd.DataFrame(ecg_records)
            df_ecg = df_ecg[['measurement_time', 'heart_rate', 'notes', 'id']]
            df_ecg.columns = ['測量時間', '心率 (bpm)', '備註', 'FHIR Observation ID']
            
            # 格式化時間
            df_ecg['測量時間'] = df_ecg['測量時間'].apply(
                lambda x: x[:19] if x else ""
            )
            
            # 簡化 ID 顯示
            df_ecg['FHIR Observation ID'] = df_ecg['FHIR Observation ID'].apply(
                lambda x: f"{x[:8]}..." if x else ""
            )
            
            st.dataframe(df_ecg, use_container_width=True, hide_index=True)
            
            # 簡單的心率趨勢圖
            if len(ecg_records) > 1:
                st.subheader("📈 心率趨勢")
                
                # 準備圖表資料
                chart_data = pd.DataFrame({
                    '時間': [r['measurement_time'][:19] for r in ecg_records],
                    '心率': [r['heart_rate'] if r['heart_rate'] else 0 for r in ecg_records]
                })
                
                st.line_chart(chart_data.set_index('時間'))
        else:
            st.info("📌 此使用者尚無 ECG 測量記錄")
    else:
        st.warning("⚠️ 目前沒有使用者")

# ==================== Tab 3: 生理數據管理 ====================
with tab3:
    st.header("💊 生理數據管理")
    
    if user_options:
        selected_user_id_vital = st.selectbox(
            "選擇使用者 ",
            options=[u['id'] for u in user_options],
            format_func=lambda x: next((u['full_name'] + f" ({u['username']})" for u in user_options if u['id'] == x), ""),
            key="vital_user_select"
        )
        
        # 顯示該使用者的生理數據
        st.subheader(f"📊 生理數據記錄")
        
        # 從 FHIR Server 載入資料
        with st.spinner("正在從 FHIR Server 載入資料..."):
            vital_records = st.session_state.fhir_manager.get_user_vital_signs(
                selected_user_id_vital, limit=50
            )
        
        if vital_records:
            df_vital = pd.DataFrame(vital_records)
            df_vital = df_vital[['measurement_time', 'measurement_type', 'value', 'unit', 'notes', 'id']]
            df_vital.columns = ['測量時間', '測量類型', '數值', '單位', '備註', 'FHIR Observation ID']
            
            # 格式化時間
            df_vital['測量時間'] = df_vital['測量時間'].apply(
                lambda x: x[:19] if x else ""
            )
            
            # 簡化 ID 顯示
            df_vital['FHIR Observation ID'] = df_vital['FHIR Observation ID'].apply(
                lambda x: f"{x[:8]}..." if x else ""
            )
            
            st.dataframe(df_vital, use_container_width=True, hide_index=True)
            
            # 按類型分組顯示趨勢
            measurement_types = list(set([r['measurement_type'] for r in vital_records]))
            
            if measurement_types:
                st.subheader("📈 數據趨勢")
                selected_type = st.selectbox("選擇測量類型", measurement_types)
                
                type_data = [r for r in vital_records if r['measurement_type'] == selected_type]
                
                chart_data = pd.DataFrame({
                    '時間': [r['measurement_time'][:19] for r in type_data],
                    '數值': [r['value'] for r in type_data]
                })
                
                st.line_chart(chart_data.set_index('時間'))
        else:
            st.info("📌 此使用者尚無生理數據記錄")
    else:
        st.warning("⚠️ 目前沒有使用者")

# ==================== Tab 4: 新增記錄 ====================
with tab4:
    st.header("➕ 新增測量記錄")
    
    if not user_options:
        st.warning("⚠️ 請先新增使用者")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💓 新增 ECG 測量")
            
            with st.form("add_ecg_form"):
                ecg_user_id = st.selectbox(
                    "選擇使用者",
                    options=[u['id'] for u in user_options],
                    format_func=lambda x: next((u['full_name'] for u in user_options if u['id'] == x), ""),
                    key="ecg_user"
                )

                # ecg 測量時間
                col_date, col_time = st.columns(2)
                with col_date:
                    ecg_date = st.date_input("測量日期", value=datetime.now().date())
                with col_time:
                    ecg_time = st.time_input("測量時間", value=datetime.now().time())
                ecg_measurement_time = datetime.combine(ecg_date, ecg_time)
                
                ecg_heart_rate = st.number_input(
                    "心率 (bpm)",
                    min_value=30,
                    max_value=220,
                    value=75,
                    key="ecg_hr"
                )
                
                ecg_notes = st.text_area("備註", key="ecg_notes")
                
                ecg_submit = st.form_submit_button("新增 ECG 記錄", use_container_width=True)
                
                if ecg_submit:
                    with st.spinner("正在上傳到 FHIR Server..."):
                        observation_id = st.session_state.fhir_manager.add_ecg_measurement(
                            ecg_user_id,
                            ecg_measurement_time.isoformat(),
                            None,  # ecg_data
                            ecg_heart_rate,
                            ecg_notes
                        )
                        
                        if observation_id:
                            st.success(f"✅ 成功新增 ECG 記錄")
                            st.info(f"📌 FHIR Observation ID: {observation_id}")
                        else:
                            st.error("❌ 新增失敗，請確認使用者已同步到 FHIR Server")
        
        with col2:
            st.subheader("📊 新增生理數據")
            
            with st.form("add_vital_form"):
                vital_user_id = st.selectbox(
                    "選擇使用者 ",
                    options=[u['id'] for u in user_options],
                    format_func=lambda x: next((u['full_name'] for u in user_options if u['id'] == x), ""),
                    key="vital_user"
                )

                col_date, col_time = st.columns(2)
                with col_date:
                    vital_date = st.date_input("測量日期", value=datetime.now().date())
                with col_time:
                    vital_time = st.time_input("測量時間", value=datetime.now().time())
                vital_measurement_time = datetime.combine(vital_date, vital_time)
                
                vital_type = st.selectbox(
                    "測量類型",
                    ["血壓收縮壓", "血壓舒張壓", "血糖", "體溫", "血氧飽和度", "體重", "身高"],
                    key="vital_type"
                )
                
                vital_value = st.number_input(
                    "數值",
                    min_value=0.0,
                    value=0.0,
                    step=0.1,
                    key="vital_value"
                )
                
                # 根據類型自動設定單位
                unit_map = {
                    "血壓收縮壓": "mmHg",
                    "血壓舒張壓": "mmHg",
                    "血糖": "mg/dL",
                    "體溫": "°C",
                    "血氧飽和度": "%",
                    "體重": "kg",
                    "身高": "cm"
                }
                
                vital_unit = st.text_input(
                    "單位",
                    value=unit_map.get(vital_type, ""),
                    key="vital_unit"
                )
                
                vital_notes = st.text_area("備註 ", key="vital_notes")
                
                vital_submit = st.form_submit_button("新增生理數據", use_container_width=True)
                
                if vital_submit:
                    with st.spinner("正在上傳到 FHIR Server..."):
                        observation_id = st.session_state.fhir_manager.add_vital_sign(
                            vital_user_id,
                            vital_measurement_time.isoformat(),
                            vital_type,
                            vital_value,
                            vital_unit,
                            vital_notes
                        )
                        
                        if observation_id:
                            st.success(f"✅ 成功新增生理數據")
                            st.info(f"📌 FHIR Observation ID: {observation_id}")
                        else:
                            st.error("❌ 新增失敗，請確認使用者已同步到 FHIR Server")

st.markdown("---")
st.caption("⚙️ 後台管理系統 | FHIR Health Management | 所有數據存儲在 FHIR Server")
