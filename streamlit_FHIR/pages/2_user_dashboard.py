import streamlit as st
import sys
import os
from datetime import datetime, timedelta
import pandas as pd

# 加入父目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fhir_manager import FHIRManager

# 檢查登入狀態
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ 請先登入")
    st.stop()

# 初始化 FHIR Manager
if 'fhir_manager' not in st.session_state:
    st.session_state.fhir_manager = FHIRManager()

st.set_page_config(
    page_title="我的健康數據",
    page_icon="📊",
    layout="wide"
)

st.title("📊 我的健康數據")
st.markdown(f"### 👤 {st.session_state.user['full_name']}")
st.markdown("---")

# 取得使用者資訊
user_id = st.session_state.user['id']
user_info = st.session_state.fhir_manager.get_user_by_id(user_id)

# 側邊欄 - 顯示個人資訊
with st.sidebar:
    st.header("👤 個人資訊")
    
    if user_info:
        st.write(f"**姓名:** {user_info['full_name']}")
        st.write(f"**帳號:** {user_info['username']}")
        if user_info.get('gender'):
            gender_display = {
                'male': '男性',
                'female': '女性',
                'other': '其他'
            }
            st.write(f"**性別:** {gender_display.get(user_info['gender'], user_info['gender'])}")
        if user_info.get('birth_date'):
            st.write(f"**生日:** {user_info['birth_date']}")
            
            # 計算年齡
            from datetime import datetime
            birth = datetime.strptime(user_info['birth_date'], '%Y-%m-%d')
            today = datetime.now()
            age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
            st.write(f"**年齡:** {age} 歲")
        
        # FHIR Patient ID
        if user_info.get('fhir_patient_id'):
            st.markdown("---")
            st.write(f"**FHIR Patient ID:**")
            st.code(user_info['fhir_patient_id'], language=None)
        else:
            st.warning("⚠️ 尚未同步到 FHIR Server")
    
    st.markdown("---")
    
    # 快速統計
    st.header("📈 快速統計")
    
    with st.spinner("載入統計資料..."):
        ecg_records = st.session_state.fhir_manager.get_user_ecg_measurements(user_id, limit=1000)
        vital_records = st.session_state.fhir_manager.get_user_vital_signs(user_id, limit=1000)
    
    st.metric("ECG 測量次數", len(ecg_records))
    st.metric("生理數據筆數", len(vital_records))
    
    st.markdown("---")
    
    # FHIR Server 狀態
    st.header("🌐 FHIR Server")
    if st.session_state.fhir_manager.test_fhir_connection():
        st.success("✅ 連線正常")
    else:
        st.error("❌ 連線失敗")

# Tab 選單
tab1, tab2, tab3 = st.tabs(["💓 ECG 心電圖", "📊 生理數據", "📅 時間軸"])

# ==================== Tab 1: ECG 心電圖 ====================
with tab1:
    st.header("💓 ECG 心電圖記錄")
    
    # 時間範圍選擇
    col1, col2 = st.columns(2)
    
    with col1:
        limit = st.number_input(
            "顯示筆數",
            min_value=5,
            max_value=100,
            value=20,
            step=5,
            key="ecg_limit"
        )
    
    with col2:
        if st.button("🔄 重新載入 ECG 資料", use_container_width=True):
            st.rerun()
    
    # 從 FHIR Server 取得 ECG 記錄
    with st.spinner("正在從 FHIR Server 載入 ECG 資料..."):
        ecg_records = st.session_state.fhir_manager.get_user_ecg_measurements(
            user_id, limit=int(limit)
        )
    
    if ecg_records:
        # 統計資訊
        st.subheader("📊 統計摘要")
        
        col1, col2, col3, col4 = st.columns(4)
        
        heart_rates = [r['heart_rate'] for r in ecg_records if r['heart_rate']]
        
        with col1:
            st.metric("總測量次數", len(ecg_records))
        
        with col2:
            if heart_rates:
                st.metric("平均心率", f"{sum(heart_rates) / len(heart_rates):.1f} bpm")
        
        with col3:
            if heart_rates:
                st.metric("最高心率", f"{max(heart_rates)} bpm")
        
        with col4:
            if heart_rates:
                st.metric("最低心率", f"{min(heart_rates)} bpm")
        
        st.markdown("---")
        
        # 心率趨勢圖
        st.subheader("📈 心率趨勢圖")
        
        if len(heart_rates) > 0:
            chart_data = pd.DataFrame({
                '時間': [r['measurement_time'][:19] for r in ecg_records if r['heart_rate']],
                '心率 (bpm)': heart_rates
            })
            
            st.line_chart(chart_data.set_index('時間'))
        else:
            st.info("📌 暫無心率數據可顯示")
        
        st.markdown("---")
        
        # 詳細記錄表格
        st.subheader("📋 詳細記錄")
        
        df_ecg = pd.DataFrame(ecg_records)
        df_ecg = df_ecg[['measurement_time', 'heart_rate', 'notes', 'id']]
        df_ecg.columns = ['測量時間', '心率 (bpm)', '備註', 'FHIR Observation ID']
        
        # 格式化時間
        df_ecg['測量時間'] = df_ecg['測量時間'].apply(
            lambda x: x[:19] if x else ""
        )
        
        # 簡化 FHIR ID 顯示
        df_ecg['FHIR Observation ID'] = df_ecg['FHIR Observation ID'].apply(
            lambda x: f"{x[:12]}..." if x else ""
        )
        
        st.dataframe(df_ecg, use_container_width=True, hide_index=True)
        
        # 下載按鈕
        csv = df_ecg.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 下載 CSV",
            data=csv,
            file_name=f"ecg_records_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("📌 目前沒有 ECG 測量記錄")
        st.markdown("""
        ### 💡 如何開始？
        
        您可以：
        1. 使用 ESP32 設備進行測量，數據會自動上傳到 FHIR Server
        2. 聯繫管理員手動新增記錄
        
        所有測量後的資料會自動同步並顯示在這裡。
        """)

# ==================== Tab 2: 生理數據 ====================
with tab2:
    st.header("📊 生理數據記錄")
    
    # 時間範圍選擇
    col1, col2 = st.columns(2)
    
    with col1:
        limit_vital = st.number_input(
            "顯示筆數 ",
            min_value=5,
            max_value=100,
            value=20,
            step=5,
            key="vital_limit"
        )
    
    with col2:
        if st.button("🔄 重新載入生理數據", use_container_width=True):
            st.rerun()
    
    # 從 FHIR Server 取得生理數據
    with st.spinner("正在從 FHIR Server 載入生理數據..."):
        vital_records = st.session_state.fhir_manager.get_user_vital_signs(
            user_id, limit=int(limit_vital)
        )
    
    if vital_records:
        # 按測量類型分組
        measurement_types = list(set([r['measurement_type'] for r in vital_records]))
        
        st.subheader("📋 測量類型")
        
        selected_type = st.selectbox(
            "選擇要查看的測量類型",
            ["全部"] + measurement_types,
            key="vital_type_filter"
        )
        
        # 篩選資料
        if selected_type != "全部":
            filtered_records = [r for r in vital_records if r['measurement_type'] == selected_type]
        else:
            filtered_records = vital_records
        
        if filtered_records:
            # 統計資訊
            st.subheader("📊 統計摘要")
            
            col1, col2, col3, col4 = st.columns(4)
            
            values = [r['value'] for r in filtered_records]
            
            with col1:
                st.metric("總測量次數", len(filtered_records))
            
            with col2:
                st.metric("平均值", f"{sum(values) / len(values):.2f}")
            
            with col3:
                st.metric("最大值", f"{max(values):.2f}")
            
            with col4:
                st.metric("最小值", f"{min(values):.2f}")
            
            st.markdown("---")
            
            # 趨勢圖
            st.subheader("📈 數據趨勢")
            
            chart_data = pd.DataFrame({
                '時間': [r['measurement_time'][:19] for r in filtered_records],
                '數值': values
            })
            
            st.line_chart(chart_data.set_index('時間'))
            
            st.markdown("---")
            
            # 詳細記錄表格
            st.subheader("📋 詳細記錄")
            
            df_vital = pd.DataFrame(filtered_records)
            df_vital = df_vital[['measurement_time', 'measurement_type', 'value', 'unit', 'notes', 'id']]
            df_vital.columns = ['測量時間', '測量類型', '數值', '單位', '備註', 'FHIR Observation ID']
            
            # 格式化時間
            df_vital['測量時間'] = df_vital['測量時間'].apply(
                lambda x: x[:19] if x else ""
            )
            
            # 簡化 FHIR ID 顯示
            df_vital['FHIR Observation ID'] = df_vital['FHIR Observation ID'].apply(
                lambda x: f"{x[:12]}..." if x else ""
            )
            
            st.dataframe(df_vital, use_container_width=True, hide_index=True)
            
            # 下載按鈕
            csv = df_vital.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 下載 CSV",
                data=csv,
                file_name=f"vital_signs_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("📌 該類型暫無測量記錄")
    else:
        st.info("📌 目前沒有生理數據記錄")
        st.markdown("""
        ### 💡 如何開始？
        
        請聯繫管理員為您新增生理數據測量記錄。
        
        可記錄的數據包括：
        - 血壓（收縮壓/舒張壓）
        - 血糖
        - 體溫
        - 血氧飽和度
        - 體重
        - 身高
        
        所有數據都會自動存儲在 FHIR Server。
        """)

# ==================== Tab 3: 時間軸 ====================
with tab3:
    st.header("📅 測量時間軸")
    
    # 合併所有測量記錄並排序
    all_records = []
    
    # 加入 ECG 記錄
    for ecg in ecg_records:
        all_records.append({
            'time': ecg['measurement_time'],
            'type': 'ECG',
            'value': f"{ecg['heart_rate']} bpm" if ecg['heart_rate'] else 'N/A',
            'notes': ecg['notes'] or '',
            'fhir_id': ecg['id']
        })
    
    # 加入生理數據記錄
    for vital in vital_records:
        all_records.append({
            'time': vital['measurement_time'],
            'type': vital['measurement_type'],
            'value': f"{vital['value']} {vital['unit']}",
            'notes': vital['notes'] or '',
            'fhir_id': vital['id']
        })
    
    # 按時間排序
    all_records.sort(key=lambda x: x['time'], reverse=True)
    
    if all_records:
        st.info(f"📊 總共 {len(all_records)} 筆測量記錄（從 FHIR Server 載入）")
        
        # 以時間軸方式呈現
        for idx, record in enumerate(all_records[:50]):  # 限制顯示前50筆
            col1, col2, col3, col4 = st.columns([2, 2, 2, 3])
            
            with col1:
                st.write(f"**{record['time'][:19]}**")
            
            with col2:
                # 根據類型顯示不同的圖標
                icon = "💓" if record['type'] == 'ECG' else "📊"
                st.write(f"{icon} {record['type']}")
            
            with col3:
                st.write(record['value'])
            
            with col4:
                if record['notes']:
                    st.write(f"📝 {record['notes']}")
                st.caption(f"FHIR ID: {record['fhir_id'][:12]}...")
            
            if idx < len(all_records) - 1:
                st.markdown("---")
    else:
        st.info("📌 目前沒有測量記錄")

st.markdown("---")
st.caption("📊 我的健康數據 | FHIR Health Management | 所有數據存儲在 FHIR Server")
