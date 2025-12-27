import streamlit as st
from fhir_manager import FHIRManager

# 設定頁面配置
st.set_page_config(
    page_title="FHIR 健康管理系統",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 初始化 FHIR Manager
if 'fhir_manager' not in st.session_state:
    # 本機 HAPI FHIR Server（將 IP 改成你電腦的實際 IP）
    FHIR_SERVER_URL = "http://localhost:8080/fhir"  # Streamlit 在同一台電腦，用 localhost
    
    st.session_state.fhir_manager = FHIRManager(
        fhir_server_url=FHIR_SERVER_URL
    )

# 初始化 session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None

def login(username, password):
    """登入功能"""
    success, user_data = st.session_state.fhir_manager.verify_user(username, password)
    if success:
        st.session_state.logged_in = True
        st.session_state.user = user_data
        return True
    return False

def logout():
    """登出功能"""
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()

# 主頁面
if not st.session_state.logged_in:
    # 登入頁面
    st.markdown("""
        <h1 style='text-align: center; color: #1f77b4;'>🏥 FHIR 健康管理系統</h1>
        <p style='text-align: center; font-size: 18px;'>基於 FHIR 標準的健康數據管理平台</p>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 置中的登入表單
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 使用者登入")
        
        with st.form("login_form"):
            username = st.text_input("帳號", placeholder="請輸入帳號")
            password = st.text_input("密碼", type="password", placeholder="請輸入密碼")
            submit = st.form_submit_button("登入", use_container_width=True)
            
            if submit:
                if username and password:
                    if login(username, password):
                        st.success(f"✅ 歡迎回來，{st.session_state.user['full_name']}！")
                        st.rerun()
                    else:
                        st.error("❌ 帳號或密碼錯誤")
                else:
                    st.warning("⚠️ 請輸入帳號和密碼")
        
        st.markdown("---")
        
        # 示範帳號資訊
        with st.expander("📌 示範帳號資訊"):
            st.markdown("""
            **管理員帳號：**
            - 帳號: `admin`
            - 密碼: `admin123`
            
            **一般使用者：**
            - 帳號: `user1`
            - 密碼: `pass123`
            
            ---
            **首次使用提示：**
            系統會自動在 FHIR Server 創建 Patient 資源
            
            所有健康數據都存儲在 FHIR Server：
            - 🌐 ESP32 → FHIR Server
            - 🌐 Streamlit → FHIR Server
            - ✅ 數據自動同步，無需手動操作
            """)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
        <div style='text-align: center; color: gray; padding-top: 50px;'>
            <p>💡 提示：本系統使用 FHIR 標準，所有數據存儲在雲端 FHIR Server</p>
            <p style='font-size: 12px;'>© 2024 FHIR Health Management System | Powered by HAPI FHIR</p>
        </div>
    """, unsafe_allow_html=True)

else:
    # 已登入，顯示側邊欄資訊
    st.sidebar.title(f"👤 {st.session_state.user['full_name']}")
    st.sidebar.write(f"**角色:** {st.session_state.user['role']}")
    
    # 顯示 FHIR Patient ID
    if st.session_state.user.get('fhir_patient_id'):
        st.sidebar.write(f"**FHIR ID:** `{st.session_state.user['fhir_patient_id'][:8]}...`")
    
    st.sidebar.markdown("---")
    
    # Streamlit 會自動生成頁面導航
    # 不需要手動添加 page_link
    
    # 登出按鈕
    if st.sidebar.button("🚪 登出", use_container_width=True):
        logout()
    
    # 首頁內容
    st.title("🏥 FHIR 健康管理系統")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 👋 歡迎使用
        
        您已成功登入系統！
        
        **系統功能：**
        """)
        
        if st.session_state.user['role'] == 'admin':
            st.markdown("""
            - ⚙️ **後台管理**: 管理所有使用者及其健康數據
            - 📊 **個人數據**: 查看您自己的健康記錄
            - 💓 **ECG 測量**: 上傳和管理 ECG 資料
            - 📈 **數據分析**: 查看使用者的健康趨勢
            - 🌐 **FHIR 整合**: 所有數據存儲在 FHIR Server
            """)
        else:
            st.markdown("""
            - 📊 **我的健康數據**: 查看您的所有健康記錄
            - 💓 **ECG 記錄**: 查看您的心電圖測量歷史
            - 📈 **趨勢分析**: 了解您的健康狀況變化
            - 📝 **測量記錄**: 記錄每次的測量數據
            - 🌐 **雲端同步**: 數據自動同步到 FHIR Server
            """)
    
    with col2:
        st.markdown("### 📋 快速資訊")
        
        # 取得使用者的最近測量記錄
        recent_ecg = st.session_state.fhir_manager.get_user_ecg_measurements(
            st.session_state.user['id'], 
            limit=1
        )
        
        recent_vitals = st.session_state.fhir_manager.get_user_vital_signs(
            st.session_state.user['id'],
            limit=1
        )
        
        if recent_ecg:
            st.info(f"📌 最近 ECG 測量：{recent_ecg[0]['measurement_time'][:19]}")
            if recent_ecg[0]['heart_rate']:
                st.metric("最新心率", f"{recent_ecg[0]['heart_rate']} bpm")
        else:
            st.warning("📌 尚無 ECG 測量記錄")
        
        if recent_vitals:
            vital = recent_vitals[0]
            st.info(f"📌 最近測量：{vital['measurement_type']} - {vital['value']} {vital['unit']}")
        else:
            st.warning("📌 尚無生理數據記錄")
        
        st.markdown("---")
        
        # FHIR Server 狀態
        st.markdown("### 🌐 FHIR Server 狀態")
        if st.session_state.fhir_manager.test_fhir_connection():
            st.success("✅ FHIR Server 連線正常")
        else:
            st.error("❌ FHIR Server 連線失敗")
        
        st.markdown("---")
        
        # 快速連結
        st.markdown("### 🔗 快速連結")
        
        if st.session_state.user['role'] == 'admin':
            if st.button("前往後台管理 ⚙️", use_container_width=True):
                st.switch_page("pages/1_admin_dashboard.py")
        
        if st.button("查看我的數據 📊", use_container_width=True):
            st.switch_page("pages/2_user_dashboard.py")
    
    st.markdown("---")
    
    # 系統統計（僅管理員可見）
    if st.session_state.user['role'] == 'admin':
        st.markdown("### 📊 系統統計")
        
        all_users = st.session_state.fhir_manager.get_all_users()
        total_users = len([u for u in all_users if u['role'] == 'user'])
        users_with_fhir = len([u for u in all_users if u.get('fhir_patient_id')])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("總使用者數", total_users)
        
        with col2:
            st.metric("管理員數", len([u for u in all_users if u['role'] == 'admin']))
        
        with col3:
            st.metric("FHIR 同步", f"{users_with_fhir}/{total_users}")
        
        with col4:
            st.metric("FHIR Server", "連線中 ✅")