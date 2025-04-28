import streamlit as st
import cv2
import tempfile
import os
import numpy as np
import sys
from pathlib import Path
import torch

# إضافة المجلد الرئيسي إلى مسار Python
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from app.services.video.video_processor import VideoProcessor
    from app.services.technical.technical_analyzer import TechnicalAnalyzer
    from app.services.physical.physical_analyzer import PhysicalAnalyzer
    from app.services.tactical.tactical_analyzer import TacticalAnalyzer
    from app.services.psychological.psychological_analyzer import PsychologicalAnalyzer
except ImportError as e:
    st.error(f"""
    خطأ في استيراد الحزم: {str(e)}
    
    تأكد من تثبيت الحزمة بشكل صحيح باستخدام:
    ```
    cd {ROOT_DIR}
    pip install -e .
    ```
    """)
    st.stop()

# تهيئة المحللات
@st.cache_resource
def initialize_analyzers():
    try:
        return {
            'video_processor': VideoProcessor(),
            'technical_analyzer': TechnicalAnalyzer(),
            'physical_analyzer': PhysicalAnalyzer(),
            'tactical_analyzer': TacticalAnalyzer(),
            'psychological_analyzer': PsychologicalAnalyzer()
        }
    except Exception as e:
        st.error(f"""
        خطأ في تهيئة المحللات: {str(e)}
        
        تأكد من تثبيت جميع المكتبات المطلوبة وتوفر نموذج YOLO.
        """)
        st.stop()

def main():
    st.set_page_config(
        page_title="تحليل أداء لاعبي كرة القدم",
        page_icon="⚽",
        layout="wide"
    )

    st.title("تحليل أداء لاعبي كرة القدم 🎯")
    st.write("قم برفع فيديو المباراة للحصول على تحليل شامل للأداء")

    # تهيئة المحللات
    analyzers = initialize_analyzers()
    video_processor = analyzers['video_processor']
    technical_analyzer = analyzers['technical_analyzer']
    physical_analyzer = analyzers['physical_analyzer']
    tactical_analyzer = analyzers['tactical_analyzer']
    psychological_analyzer = analyzers['psychological_analyzer']

    uploaded_file = st.file_uploader("اختر فيديو المباراة", type=['mp4', 'avi', 'mov'])

    if uploaded_file is not None:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        temp_file.write(uploaded_file.read())

        # إنشاء عناصر العرض
        video_placeholder = st.empty()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # دوال التحديث
            def update_progress(progress):
                progress_bar.progress(progress)
                status_text.text(f"جاري التحليل... {int(progress * 100)}%")

            def update_frame(frame):
                video_placeholder.image(frame, channels="RGB", use_column_width=True)

            # معالجة الفيديو
            frames_data = video_processor.process_video(
                temp_file.name,
                progress_callback=update_progress,
                frame_callback=update_frame
            )

            # استخراج معرفات اللاعبين المتاحة
            available_player_ids = set()
            for frame in frames_data:
                for player in frame.get('players', []):
                    available_player_ids.add(player['id'])
            
            available_player_ids = sorted(list(available_player_ids))
            
            # إضافة مربع اختيار اللاعبين
            st.subheader("اختر اللاعبين للتحليل")
            selected_player_ids = st.multiselect(
                "معرفات اللاعبين",
                options=available_player_ids,
                default=available_player_ids,
                format_func=lambda x: f"اللاعب #{x}"
            )

            if not selected_player_ids:
                st.warning("الرجاء اختيار لاعب واحد على الأقل للتحليل")
                return

            # تصفية البيانات للاعبين المختارين فقط
            filtered_frames_data = []
            for frame in frames_data:
                filtered_frame = frame.copy()
                filtered_frame['players'] = [
                    player for player in frame.get('players', [])
                    if player['id'] in selected_player_ids
                ]
                filtered_frames_data.append(filtered_frame)

            # تحليل البيانات
            with st.spinner('جاري تحليل البيانات...'):
                # إنشاء أعمدة للإحصائيات
                cols = st.columns(len(selected_player_ids))
                
                for idx, player_id in enumerate(selected_player_ids):
                    with cols[idx]:
                        st.subheader(f"اللاعب #{player_id}")
                        
                        # تصفية البيانات للاعب الحالي
                        player_frames = [
                            frame for frame in filtered_frames_data
                            if any(p['id'] == player_id for p in frame.get('players', []))
                        ]
                        
                        if player_frames:
                            # تحليل البيانات
                            technical_data = technical_analyzer.analyze(player_frames)
                            physical_data = physical_analyzer.analyze(player_frames)
                            tactical_data = tactical_analyzer.analyze(player_frames)
                            psychological_data = psychological_analyzer.analyze(player_frames)
                            
                            # عرض النتائج
                            st.write("**التحليل الفني**")
                            st.json(technical_data)
                            
                            st.write("**التحليل البدني**")
                            st.json(physical_data)
                            
                            st.write("**التحليل التكتيكي**")
                            st.json(tactical_data)
                            
                            st.write("**التحليل النفسي**")
                            st.json(psychological_data)
                        else:
                            st.warning("لا توجد بيانات كافية لهذا اللاعب")

            st.success("تم الانتهاء من التحليل بنجاح! 🎉")

        except Exception as e:
            st.error(f"خطأ أثناء معالجة الفيديو: {str(e)}")
        finally:
            temp_file.close()
            os.unlink(temp_file.name)

if __name__ == "__main__":
    main() 