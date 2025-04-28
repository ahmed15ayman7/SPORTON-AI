from setuptools import setup, find_packages

setup(
    name="sporton-ai",
    version="0.1.0",
    packages=find_packages(include=['app', 'app.*']),
    python_requires=">=3.8",
    install_requires=[
        "streamlit>=1.24.0",
        "opencv-python>=4.8.0",
        "numpy>=1.24.0",
        "ultralytics>=8.0.0",
        "mediapipe>=0.10.0",
        "torch>=2.0.0",
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0"
    ],
    description="نظام تحليل أداء لاعبي كرة القدم باستخدام الذكاء الاصطناعي",
    author="Ahmed Ayman",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
) 