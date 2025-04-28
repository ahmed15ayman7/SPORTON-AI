import streamlit as st
import requests
import json

st.set_page_config(
    page_title="نظام تحليل أداء لاعبي كرة القدم",
    page_icon="⚽",
    layout="wide"
)

st.title("نظام تحليل أداء لاعبي كرة القدم 🎯")

st.write("""
### مرحباً بك في نظام التحليل الذكي للاعبي كرة القدم
قم برفع فيديو المباراة للحصول على تحليل شامل للأداء
""")

uploaded_file = st.file_uploader("اختر فيديو المباراة", type=['mp4', 'avi', 'mov'])

if uploaded_file is not None:
    with st.spinner('جاري تحليل الفيديو...'):
        # إرسال الفيديو إلى الـ API
        files = {'video': uploaded_file}
        response = requests.post('http://localhost:8000/analyze/', files=files)
        
        if response.status_code == 200:
            results = response.json()
            
            # عرض النتائج في تبويبات منفصلة
            tab1, tab2, tab3, tab4 = st.tabs([
                "التحليل الفني", 
                "التحليل البدني", 
                "التحليل التكتيكي",
                "التحليل النفسي"
            ])
            
            with tab1:
                st.header("التحليل الفني")
                st.json(results['technical_analysis'])
                
            with tab2:
                st.header("التحليل البدني")
                st.json(results['physical_analysis'])
                
            with tab3:
                st.header("التحليل التكتيكي")
                st.json(results['tactical_analysis'])
                
            with tab4:
                st.header("التحليل النفسي")
                st.json(results['psychological_analysis'])
        else:
            st.error('حدث خطأ أثناء تحليل الفيديو')

st.sidebar.markdown("""
### معلومات عن النظام
- يدعم تحليل مباريات كرة القدم
- يستخدم تقنيات الذكاء الاصطناعي
- يوفر تحليلاً شاملاً للأداء
""") 