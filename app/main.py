from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from .services.video.video_processor import VideoProcessor
from .services.technical.technical_analyzer import TechnicalAnalyzer
from .services.physical.physical_analyzer import PhysicalAnalyzer
from .services.tactical.tactical_analyzer import TacticalAnalyzer
from .services.psychological.psychological_analyzer import PsychologicalAnalyzer
import tempfile
import os

app = FastAPI(
    title="نظام تحليل أداء لاعبي كرة القدم",
    description="API لتحليل أداء لاعبي كرة القدم باستخدام الذكاء الاصطناعي",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze/")
async def analyze_video(video: UploadFile = File(...)):
    """
    تحليل فيديو مباراة كرة القدم وإرجاع البيانات التحليلية
    """
    # حفظ الفيديو مؤقتاً
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    try:
        contents = await video.read()
        with open(temp_file.name, 'wb') as f:
            f.write(contents)
        
        # إنشاء كائنات المحللات
        video_processor = VideoProcessor()
        technical_analyzer = TechnicalAnalyzer()
        physical_analyzer = PhysicalAnalyzer()
        tactical_analyzer = TacticalAnalyzer()
        psychological_analyzer = PsychologicalAnalyzer()
        
        # معالجة الفيديو واستخراج البيانات
        frames = video_processor.process_video(temp_file.name)
        
        # تحليل الأداء
        technical_data = technical_analyzer.analyze(frames)
        physical_data = physical_analyzer.analyze(frames)
        tactical_data = tactical_analyzer.analyze(frames)
        psychological_data = psychological_analyzer.analyze(frames)
        
        return {
            "technical_analysis": technical_data,
            "physical_analysis": physical_data,
            "tactical_analysis": tactical_data,
            "psychological_analysis": psychological_data
        }
        
    finally:
        temp_file.close()
        os.unlink(temp_file.name)

@app.get("/")
async def root():
    return {"message": "مرحباً بك في نظام تحليل أداء لاعبي كرة القدم"} 