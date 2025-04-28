# نظام تحليل أداء لاعبي كرة القدم

نظام متكامل لتحليل أداء لاعبي كرة القدم باستخدام تقنيات الرؤية الحاسوبية والذكاء الاصطناعي.

## المميزات
- تحليل الأداء الفني (التمريرات، التسديدات، الأهداف)
- تحليل الأداء البدني (المسافة، السرعة، الانطلاقات)
- تحليل الأداء التكتيكي (التموضع، الخطة)
- تحليل الفيديو (اللقطات المهمة، التتبع)
- تحليل الجانب النفسي

## المتطلبات
- Python 3.8+
- CUDA (للتسريع باستخدام GPU)

## التثبيت
1. إنشاء بيئة افتراضية:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
.\venv\Scripts\activate  # Windows
```

2. تثبيت المتطلبات:
```bash
pip install -r requirements.txt
```

3. تشغيل التطبيق:
```bash
uvicorn app.main:app --reload
```

## الاستخدام
- قم بزيارة `http://localhost:8000/docs` للوصول إلى واجهة API
- قم برفع ملف فيديو للتحليل
- انتظر النتائج في شكل JSON

## هيكل المشروع
```
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── services/
│   │   ├── technical/
│   │   ├── physical/
│   │   ├── tactical/
│   │   ├── video/
│   │   └── psychological/
│   └── utils/
├── tests/
├── venv/
├── requirements.txt
└── README.md
``` 