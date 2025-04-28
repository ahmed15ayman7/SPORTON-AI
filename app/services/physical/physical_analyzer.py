import numpy as np
from typing import List, Dict
import cv2

class PhysicalAnalyzer:
    def __init__(self):
        """
        تهيئة محلل الأداء البدني
        """
        self.sprint_threshold = 7.0  # عتبة السرعة للانطلاق السريع (م/ث)
        self.jump_threshold = 0.3    # عتبة ارتفاع القفز (م)
        self.pixels_to_meters = 0.1  # معامل تحويل البكسل إلى متر
        
    def analyze(self, player_frames: List[Dict]) -> Dict:
        """
        تحليل الأداء البدني للاعب
        
        Args:
            player_frames: قائمة الإطارات التي يظهر فيها اللاعب
            
        Returns:
            Dict: نتائج التحليل البدني
        """
        if not player_frames:
            return self._empty_analysis()
            
        # حساب المسافات
        distances = self._calculate_distances(player_frames)
        
        # حساب السرعات
        speeds = self._calculate_speeds(player_frames)
        
        # حساب الانطلاقات السريعة
        sprints = self._analyze_sprints(player_frames)
        
        # تحليل مستوى الجهد
        effort = self._analyze_effort(player_frames)
        
        return {
            'distance': distances,
            'speed': speeds,
            'sprints': sprints,
            'effort': effort
        }
    
    def _empty_analysis(self) -> Dict:
        """
        إرجاع تحليل فارغ عندما لا تتوفر بيانات
        """
        return {
            'distance': {
                'total_distance': 0,
                'high_intensity_distance': 0,
                'sprint_distance': 0
            },
            'speed': {
                'avg_speed': 0,
                'max_speed': 0,
                'speed_zones': {
                    'walking': 0,
                    'jogging': 0,
                    'running': 0,
                    'sprinting': 0
                }
            },
            'sprints': {
                'total_sprints': 0,
                'avg_sprint_distance': 0,
                'max_sprint_distance': 0
            },
            'effort': {
                'total_effort': 0,
                'effort_zones': {
                    'low': 0,
                    'medium': 0,
                    'high': 0
                }
            }
        }
    
    def _calculate_distances(self, player_frames: List[Dict]) -> Dict:
        """
        حساب المسافات المقطوعة
        """
        total_distance = 0
        high_intensity_distance = 0
        sprint_distance = 0
        
        for i in range(1, len(player_frames)):
            prev_frame = player_frames[i-1]
            curr_frame = player_frames[i]
            
            # حساب المسافة بين الإطارين
            distance = self._calculate_frame_distance(prev_frame, curr_frame)
            total_distance += distance
            
            # تصنيف المسافة حسب الشدة
            speed = distance * 30  # تحويل المسافة/إطار إلى متر/ثانية
            if speed > 7:  # سرعة عالية
                high_intensity_distance += distance
            if speed > 8:  # سرعة انطلاق
                sprint_distance += distance
        
        return {
            'total_distance': total_distance,
            'high_intensity_distance': high_intensity_distance,
            'sprint_distance': sprint_distance
        }
    
    def _calculate_speeds(self, player_frames: List[Dict]) -> Dict:
        """
        حساب وتحليل السرعات
        """
        speeds = []
        speed_zones = {
            'walking': 0,  # 0-2 م/ث
            'jogging': 0,  # 2-4 م/ث
            'running': 0,  # 4-7 م/ث
            'sprinting': 0  # >7 م/ث
        }
        
        for i in range(1, len(player_frames)):
            prev_frame = player_frames[i-1]
            curr_frame = player_frames[i]
            
            # حساب السرعة اللحظية
            distance = self._calculate_frame_distance(prev_frame, curr_frame)
            speed = distance * 30  # تحويل إلى م/ث
            speeds.append(speed)
            
            # تصنيف السرعة
            if speed <= 2:
                speed_zones['walking'] += 1
            elif speed <= 4:
                speed_zones['jogging'] += 1
            elif speed <= 7:
                speed_zones['running'] += 1
            else:
                speed_zones['sprinting'] += 1
        
        # تحويل العدد إلى نسب مئوية
        total_frames = sum(speed_zones.values())
        if total_frames > 0:
            for zone in speed_zones:
                speed_zones[zone] = (speed_zones[zone] / total_frames) * 100
        
        return {
            'avg_speed': np.mean(speeds) if speeds else 0,
            'max_speed': max(speeds) if speeds else 0,
            'speed_zones': speed_zones
        }
    
    def _analyze_sprints(self, player_frames: List[Dict]) -> Dict:
        """
        تحليل الانطلاقات السريعة
        """
        sprint_distances = []
        current_sprint = 0
        is_sprinting = False
        
        for i in range(1, len(player_frames)):
            prev_frame = player_frames[i-1]
            curr_frame = player_frames[i]
            
            distance = self._calculate_frame_distance(prev_frame, curr_frame)
            speed = distance * 30
            
            if speed > 8:  # بداية انطلاقة
                if not is_sprinting:
                    is_sprinting = True
                current_sprint += distance
            elif is_sprinting:  # نهاية انطلاقة
                if current_sprint > 0:
                    sprint_distances.append(current_sprint)
                current_sprint = 0
                is_sprinting = False
        
        # إضافة آخر انطلاقة إذا كانت مستمرة
        if current_sprint > 0:
            sprint_distances.append(current_sprint)
        
        return {
            'total_sprints': len(sprint_distances),
            'avg_sprint_distance': np.mean(sprint_distances) if sprint_distances else 0,
            'max_sprint_distance': max(sprint_distances) if sprint_distances else 0
        }
    
    def _analyze_effort(self, player_frames: List[Dict]) -> Dict:
        """
        تحليل مستوى الجهد
        """
        total_effort = 0
        effort_zones = {
            'low': 0,    # 0-50%
            'medium': 0, # 50-80%
            'high': 0    # 80-100%
        }
        
        for i in range(1, len(player_frames)):
            prev_frame = player_frames[i-1]
            curr_frame = player_frames[i]
            
            # حساب الجهد بناءً على السرعة والمسافة
            distance = self._calculate_frame_distance(prev_frame, curr_frame)
            speed = distance * 30
            
            # حساب نسبة الجهد (0-100)
            effort = min(100, (speed / 9) * 100)  # 9 م/ث كحد أقصى
            total_effort += effort
            
            # تصنيف الجهد
            if effort < 50:
                effort_zones['low'] += 1
            elif effort < 80:
                effort_zones['medium'] += 1
            else:
                effort_zones['high'] += 1
        
        # تحويل العدد إلى نسب مئوية
        total_frames = sum(effort_zones.values())
        if total_frames > 0:
            for zone in effort_zones:
                effort_zones[zone] = (effort_zones[zone] / total_frames) * 100
        
        # حساب متوسط الجهد الكلي
        avg_effort = total_effort / len(player_frames) if player_frames else 0
        
        return {
            'total_effort': avg_effort,
            'effort_zones': effort_zones
        }
    
    def _calculate_frame_distance(self, prev_frame: Dict, curr_frame: Dict) -> float:
        """
        حساب المسافة المقطوعة بين إطارين
        """
        if not prev_frame['players'] or not curr_frame['players']:
            return 0
            
        prev_pos = prev_frame['players'][0]['position']
        curr_pos = curr_frame['players'][0]['position']
        
        return np.sqrt(
            (curr_pos[0] - prev_pos[0])**2 +
            (curr_pos[1] - prev_pos[1])**2
        )
    
    def _calculate_distance(self, frames_data: List[Dict]) -> Dict:
        """
        حساب المسافة المقطوعة
        """
        distance_data = {
            'total_distance': 0.0,  # بالأمتار
            'high_intensity_distance': 0.0,
            'medium_intensity_distance': 0.0,
            'low_intensity_distance': 0.0
        }
        
        for i in range(len(frames_data) - 1):
            for player in frames_data[i]['players']:
                if i + 1 < len(frames_data):
                    next_frame_players = frames_data[i + 1]['players']
                    
                    # البحث عن نفس اللاعب في الإطار التالي
                    for next_player in next_frame_players:
                        if self._is_same_player(player, next_player):
                            distance = self._calculate_player_movement(
                                player['position'],
                                next_player['position']
                            )
                            
                            distance_meters = distance * self.pixels_to_meters
                            distance_data['total_distance'] += distance_meters
                            
                            # تصنيف المسافة حسب الشدة
                            speed = distance_meters * 30  # افتراض 30 إطار/ثانية
                            if speed > 5.5:  # عالية الشدة
                                distance_data['high_intensity_distance'] += distance_meters
                            elif speed > 3.5:  # متوسطة الشدة
                                distance_data['medium_intensity_distance'] += distance_meters
                            else:  # منخفضة الشدة
                                distance_data['low_intensity_distance'] += distance_meters
        
        return distance_data
    
    def _analyze_jumps(self, frames_data: List[Dict]) -> Dict:
        """
        تحليل القفزات
        """
        jump_data = {
            'total_jumps': 0,
            'average_jump_height': 0.0,
            'max_jump_height': 0.0
        }
        
        jump_heights = []
        for frame in frames_data:
            for player in frame['players']:
                if 'poses' in frame:
                    for pose in frame['poses']:
                        if pose['player_bbox'] == player['bbox']:
                            # تحليل ارتفاع مركز الجسم من نقاط MediaPipe
                            height = self._calculate_jump_height(pose['landmarks'])
                            if height > self.jump_threshold:
                                jump_data['total_jumps'] += 1
                                jump_heights.append(height)
                                jump_data['max_jump_height'] = max(
                                    jump_data['max_jump_height'],
                                    height
                                )
        
        if jump_heights:
            jump_data['average_jump_height'] = np.mean(jump_heights)
            
        return jump_data
    
    def _calculate_player_movement(self, pos1: List[float], pos2: List[float]) -> float:
        """
        حساب مسافة حركة اللاعب
        """
        return np.sqrt(
            (pos2[0] - pos1[0])**2 + (pos2[1] - pos1[1])**2
        )
    
    def _calculate_player_speed(self, pos1: List[float], pos2: List[float]) -> float:
        """
        حساب سرعة اللاعب
        """
        distance = self._calculate_player_movement(pos1, pos2)
        return distance * self.pixels_to_meters * 30  # م/ث
    
    def _calculate_jump_height(self, landmarks: List[List[float]]) -> float:
        """
        حساب ارتفاع القفزة من نقاط الجسم
        """
        # استخدام نقاط الورك والكتف لتقدير ارتفاع القفزة
        hip_point = np.mean([landmarks[23], landmarks[24]], axis=0)
        shoulder_point = np.mean([landmarks[11], landmarks[12]], axis=0)
        return abs(shoulder_point[1] - hip_point[1]) * self.pixels_to_meters
    
    def _calculate_player_effort(self, player1: Dict, player2: Dict, poses: List[Dict]) -> float:
        """
        حساب الجهد البدني للاعب
        """
        speed = self._calculate_player_speed(
            player1['position'],
            player2['position']
        )
        
        # حساب معامل الجهد بناءً على السرعة
        effort = min(100, speed * 10)  # تحويل السرعة إلى نسبة مئوية
        
        return effort
    
    def _is_same_player(self, player1: Dict, player2: Dict) -> bool:
        """
        تحديد ما إذا كان اللاعبان هما نفس اللاعب
        """
        # يمكن تحسين هذه الدالة باستخدام خوارزميات تتبع أكثر تقدماً
        pos1 = np.array(player1['position'])
        pos2 = np.array(player2['position'])
        return np.linalg.norm(pos1 - pos2) < 0.2  # عتبة المسافة للتطابق 