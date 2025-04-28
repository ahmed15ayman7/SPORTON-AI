import numpy as np
from typing import List, Dict
import cv2

class TechnicalAnalyzer:
    def __init__(self):
        """
        تهيئة محلل الأداء الفني
        """
        self.pass_threshold = 0.7  # عتبة اكتشاف التمريرة
        self.shot_threshold = 0.8  # عتبة اكتشاف التسديدة
        self.possession_threshold = 2  # عتبة مسافة حيازة الكرة (بالأمتار)
        
    def analyze(self, frames_data: List[Dict]) -> Dict:
        """
        تحليل الأداء الفني من بيانات الإطارات
        """
        technical_stats = {
            'passes': self._analyze_passes(frames_data),
            'shots': self._analyze_shots(frames_data),
            'ball_possession': self._analyze_possession(frames_data),
            'tackles': self._analyze_tackles(frames_data),
            'interceptions': self._analyze_interceptions(frames_data)
        }
        
        return technical_stats
    
    def _analyze_passes(self, frames_data: List[Dict]) -> Dict:
        """
        تحليل التمريرات
        """
        passes_data = {
            'total_passes': 0,
            'successful_passes': 0,
            'pass_accuracy': 0.0,
            'long_passes': 0,
            'short_passes': 0
        }
        
        for i in range(len(frames_data) - 1):
            current_frame = frames_data[i]
            next_frame = frames_data[i + 1]
            
            # تحليل حركة الكرة بين الإطارات
            if current_frame['ball'] and next_frame['ball']:
                ball_movement = self._calculate_ball_movement(
                    current_frame['ball']['position'],
                    next_frame['ball']['position']
                )
                
                if ball_movement > self.pass_threshold:
                    passes_data['total_passes'] += 1
                    
                    # تصنيف التمريرة (طويلة/قصيرة)
                    if ball_movement > 20:  # بالأمتار
                        passes_data['long_passes'] += 1
                    else:
                        passes_data['short_passes'] += 1
                    
                    # تحديد نجاح التمريرة
                    if self._is_pass_successful(current_frame, next_frame):
                        passes_data['successful_passes'] += 1
        
        # حساب دقة التمريرات
        if passes_data['total_passes'] > 0:
            passes_data['pass_accuracy'] = (
                passes_data['successful_passes'] / passes_data['total_passes']
            ) * 100
            
        return passes_data
    
    def _analyze_shots(self, frames_data: List[Dict]) -> Dict:
        """
        تحليل التسديدات
        """
        shots_data = {
            'total_shots': 0,
            'shots_on_target': 0,
            'goals': 0,
            'shot_accuracy': 0.0
        }
        
        for i in range(len(frames_data) - 1):
            current_frame = frames_data[i]
            next_frame = frames_data[i + 1]
            
            if current_frame['ball'] and next_frame['ball']:
                ball_velocity = self._calculate_ball_velocity(
                    current_frame['ball']['position'],
                    next_frame['ball']['position']
                )
                
                if ball_velocity > self.shot_threshold:
                    shots_data['total_shots'] += 1
                    
                    # تحديد ما إذا كانت التسديدة على المرمى
                    if self._is_shot_on_target(next_frame['ball']['position']):
                        shots_data['shots_on_target'] += 1
                        
                        # تحديد ما إذا كان هدفاً
                        if self._is_goal(next_frame['ball']['position']):
                            shots_data['goals'] += 1
        
        # حساب دقة التسديدات
        if shots_data['total_shots'] > 0:
            shots_data['shot_accuracy'] = (
                shots_data['shots_on_target'] / shots_data['total_shots']
            ) * 100
            
        return shots_data
    
    def _analyze_possession(self, frames_data: List[Dict]) -> Dict:
        """
        تحليل حيازة الكرة
        """
        possession_data = {
            'total_touches': 0,
            'possession_duration': 0,  # بالثواني
            'possession_percentage': 0.0
        }
        
        for frame in frames_data:
            if frame['ball']:
                for player in frame['players']:
                    if self._is_player_in_possession(
                        player['position'],
                        frame['ball']['position']
                    ):
                        possession_data['total_touches'] += 1
                        possession_data['possession_duration'] += 1/30  # افتراض 30 إطار/ثانية
        
        # حساب نسبة الاستحواذ
        total_duration = len(frames_data) / 30  # الوقت الكلي بالثواني
        if total_duration > 0:
            possession_data['possession_percentage'] = (
                possession_data['possession_duration'] / total_duration
            ) * 100
            
        return possession_data
    
    def _analyze_tackles(self, frames_data: List[Dict]) -> Dict:
        """
        تحليل التدخلات
        """
        return {
            'successful_tackles': 0,
            'failed_tackles': 0,
            'tackle_success_rate': 0.0
        }
    
    def _analyze_interceptions(self, frames_data: List[Dict]) -> Dict:
        """
        تحليل قطع الكرات
        """
        return {
            'total_interceptions': 0,
            'successful_interceptions': 0
        }
    
    def _calculate_ball_movement(self, pos1: List[float], pos2: List[float]) -> float:
        """
        حساب مسافة حركة الكرة
        """
        return np.sqrt(
            (pos2[0] - pos1[0])**2 + (pos2[1] - pos1[1])**2
        )
    
    def _calculate_ball_velocity(self, pos1: List[float], pos2: List[float]) -> float:
        """
        حساب سرعة الكرة
        """
        distance = self._calculate_ball_movement(pos1, pos2)
        return distance * 30  # افتراض 30 إطار/ثانية
    
    def _is_pass_successful(self, current_frame: Dict, next_frame: Dict) -> bool:
        """
        تحديد ما إذا كانت التمريرة ناجحة
        """
        # تنفيذ منطق تحديد نجاح التمريرة
        return True
    
    def _is_shot_on_target(self, ball_position: List[float]) -> bool:
        """
        تحديد ما إذا كانت التسديدة على المرمى
        """
        # تنفيذ منطق تحديد التسديدة على المرمى
        return True
    
    def _is_goal(self, ball_position: List[float]) -> bool:
        """
        تحديد ما إذا كان هدفاً
        """
        # تنفيذ منطق تحديد الهدف
        return True
    
    def _is_player_in_possession(self, player_pos: List[float], ball_pos: List[float]) -> bool:
        """
        تحديد ما إذا كان اللاعب في حيازة الكرة
        """
        distance = self._calculate_ball_movement(player_pos, ball_pos)
        return distance < self.possession_threshold 