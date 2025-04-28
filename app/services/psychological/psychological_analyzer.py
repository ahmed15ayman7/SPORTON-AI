import numpy as np
from typing import List, Dict
import cv2

class PsychologicalAnalyzer:
    def __init__(self):
        """
        تهيئة محلل الأداء النفسي
        """
        self.reaction_window = 30  # نافذة تحليل ردة الفعل (عدد الإطارات)
        self.error_threshold = 0.7  # عتبة اعتبار الحدث خطأً
        self.pressure_threshold = 0.8  # عتبة اعتبار اللاعب تحت الضغط
        
    def analyze(self, frames_data: List[Dict]) -> Dict:
        """
        تحليل الأداء النفسي من بيانات الإطارات
        """
        psychological_stats = {
            'concentration': self._analyze_concentration(frames_data),
            'pressure_handling': self._analyze_pressure_handling(frames_data),
            'error_reaction': self._analyze_error_reaction(frames_data),
            'emotional_state': self._analyze_emotional_state(frames_data),
            'decision_making': self._analyze_decision_making(frames_data)
        }
        
        return psychological_stats
    
    def _analyze_concentration(self, frames_data: List[Dict]) -> Dict:
        """
        تحليل مستوى التركيز
        """
        concentration_data = {
            'focus_score': 0.0,
            'attention_lapses': 0,
            'recovery_time': 0.0,
            'consistency': 0.0
        }
        
        focus_scores = []
        attention_windows = []
        
        for i in range(len(frames_data) - 1):
            current_frame = frames_data[i]
            next_frame = frames_data[i + 1]
            
            for player in current_frame['players']:
                # تحليل تركيز اللاعب بناءً على موقعه وحركته
                focus_score = self._calculate_focus_score(
                    player,
                    current_frame,
                    next_frame
                )
                focus_scores.append(focus_score)
                
                # تحديد فترات تشتت الانتباه
                if focus_score < 0.5:  # عتبة التركيز المنخفض
                    attention_windows.append(i)
        
        # حساب مؤشرات التركيز
        if focus_scores:
            concentration_data['focus_score'] = np.mean(focus_scores)
            concentration_data['consistency'] = 1 - np.std(focus_scores)
            
        concentration_data['attention_lapses'] = len(attention_windows)
        
        if attention_windows:
            # حساب متوسط وقت التعافي بين فترات تشتت الانتباه
            recovery_times = np.diff(attention_windows)
            concentration_data['recovery_time'] = np.mean(recovery_times) / 30  # تحويل إلى ثواني
            
        return concentration_data
    
    def _analyze_pressure_handling(self, frames_data: List[Dict]) -> Dict:
        """
        تحليل التعامل مع الضغط
        """
        pressure_data = {
            'pressure_resistance': 0.0,
            'errors_under_pressure': 0,
            'pressure_adaptation': 0.0,
            'composure_score': 0.0
        }
        
        pressure_scores = []
        errors_under_pressure = 0
        total_pressure_situations = 0
        
        for i in range(len(frames_data) - 1):
            current_frame = frames_data[i]
            next_frame = frames_data[i + 1]
            
            for player in current_frame['players']:
                # تحديد ما إذا كان اللاعب تحت الضغط
                pressure_level = self._calculate_pressure_level(
                    player,
                    current_frame
                )
                
                if pressure_level > self.pressure_threshold:
                    total_pressure_situations += 1
                    
                    # تحليل الأداء تحت الضغط
                    performance_score = self._evaluate_pressure_performance(
                        player,
                        current_frame,
                        next_frame
                    )
                    pressure_scores.append(performance_score)
                    
                    # تحديد الأخطاء تحت الضغط
                    if self._is_error_made(player, current_frame, next_frame):
                        errors_under_pressure += 1
        
        if total_pressure_situations > 0:
            pressure_data['pressure_resistance'] = 1 - (
                errors_under_pressure / total_pressure_situations
            )
            
        pressure_data['errors_under_pressure'] = errors_under_pressure
        
        if pressure_scores:
            pressure_data['pressure_adaptation'] = np.mean(pressure_scores)
            pressure_data['composure_score'] = 1 - np.std(pressure_scores)
            
        return pressure_data
    
    def _analyze_error_reaction(self, frames_data: List[Dict]) -> Dict:
        """
        تحليل ردة الفعل بعد الأخطاء
        """
        reaction_data = {
            'recovery_speed': 0.0,
            'emotional_control': 0.0,
            'error_learning': 0.0,
            'resilience_score': 0.0
        }
        
        error_reactions = []
        recovery_times = []
        
        for i in range(len(frames_data) - self.reaction_window):
            current_frame = frames_data[i]
            
            for player in current_frame['players']:
                # تحديد ما إذا حدث خطأ
                if self._is_error_made(
                    player,
                    current_frame,
                    frames_data[i + 1]
                ):
                    # تحليل ردة الفعل في النافذة الزمنية التالية
                    reaction_score, recovery_time = self._analyze_reaction_window(
                        player,
                        frames_data[i:i + self.reaction_window]
                    )
                    error_reactions.append(reaction_score)
                    recovery_times.append(recovery_time)
        
        if error_reactions:
            reaction_data['emotional_control'] = np.mean(error_reactions)
            reaction_data['resilience_score'] = 1 - np.std(error_reactions)
            
        if recovery_times:
            reaction_data['recovery_speed'] = np.mean(recovery_times)
            
        # تقدير قدرة التعلم من الأخطاء
        if len(error_reactions) > 1:
            reaction_data['error_learning'] = (
                error_reactions[-1] - error_reactions[0]
            ) / len(error_reactions)
            
        return reaction_data
    
    def _analyze_emotional_state(self, frames_data: List[Dict]) -> Dict:
        """
        تحليل الحالة النفسية
        """
        emotional_data = {
            'emotional_stability': 0.0,
            'confidence_level': 0.0,
            'frustration_index': 0.0,
            'motivation_score': 0.0
        }
        
        emotional_scores = []
        confidence_indicators = []
        frustration_events = 0
        
        for i in range(len(frames_data) - 1):
            current_frame = frames_data[i]
            next_frame = frames_data[i + 1]
            
            for player in current_frame['players']:
                # تحليل المؤشرات العاطفية
                emotional_score = self._evaluate_emotional_indicators(
                    player,
                    current_frame,
                    next_frame
                )
                emotional_scores.append(emotional_score)
                
                # تقييم مستوى الثقة
                confidence_score = self._evaluate_confidence(
                    player,
                    current_frame
                )
                confidence_indicators.append(confidence_score)
                
                # تحديد أحداث الإحباط
                if self._is_frustrated(player, current_frame, next_frame):
                    frustration_events += 1
        
        if emotional_scores:
            emotional_data['emotional_stability'] = 1 - np.std(emotional_scores)
            emotional_data['motivation_score'] = np.mean(emotional_scores)
            
        if confidence_indicators:
            emotional_data['confidence_level'] = np.mean(confidence_indicators)
            
        total_situations = len(frames_data)
        if total_situations > 0:
            emotional_data['frustration_index'] = (
                frustration_events / total_situations
            )
            
        return emotional_data
    
    def _analyze_decision_making(self, frames_data: List[Dict]) -> Dict:
        """
        تحليل اتخاذ القرارات
        """
        decision_data = {
            'decision_speed': 0.0,
            'decision_quality': 0.0,
            'adaptability': 0.0,
            'risk_taking': 0.0
        }
        
        decision_times = []
        decision_outcomes = []
        adaptation_scores = []
        risk_scores = []
        
        for i in range(len(frames_data) - 1):
            current_frame = frames_data[i]
            next_frame = frames_data[i + 1]
            
            for player in current_frame['players']:
                # تحليل سرعة اتخاذ القرار
                decision_time = self._calculate_decision_time(
                    player,
                    current_frame,
                    next_frame
                )
                decision_times.append(decision_time)
                
                # تقييم جودة القرار
                decision_outcome = self._evaluate_decision_outcome(
                    player,
                    current_frame,
                    next_frame
                )
                decision_outcomes.append(decision_outcome)
                
                # تقييم القدرة على التكيف
                adaptation_score = self._evaluate_adaptation(
                    player,
                    current_frame,
                    next_frame
                )
                adaptation_scores.append(adaptation_score)
                
                # تحليل المخاطرة
                risk_score = self._calculate_risk_level(
                    player,
                    current_frame
                )
                risk_scores.append(risk_score)
        
        if decision_times:
            decision_data['decision_speed'] = 1 / np.mean(decision_times)
            
        if decision_outcomes:
            decision_data['decision_quality'] = np.mean(decision_outcomes)
            
        if adaptation_scores:
            decision_data['adaptability'] = np.mean(adaptation_scores)
            
        if risk_scores:
            decision_data['risk_taking'] = np.mean(risk_scores)
            
        return decision_data
    
    def _calculate_focus_score(self, player: Dict, current_frame: Dict, next_frame: Dict) -> float:
        """
        حساب درجة تركيز اللاعب
        """
        # يمكن تحسين هذه الدالة بإضافة منطق أكثر تعقيداً
        return 0.8
    
    def _calculate_pressure_level(self, player: Dict, frame: Dict) -> float:
        """
        حساب مستوى الضغط على اللاعب
        """
        # يمكن تحسين هذه الدالة بإضافة منطق أكثر تعقيداً
        return 0.5
    
    def _evaluate_pressure_performance(self, player: Dict, current_frame: Dict, next_frame: Dict) -> float:
        """
        تقييم أداء اللاعب تحت الضغط
        """
        # يمكن تحسين هذه الدالة بإضافة منطق أكثر تعقيداً
        return 0.7
    
    def _is_error_made(self, player: Dict, current_frame: Dict, next_frame: Dict) -> bool:
        """
        تحديد ما إذا ارتكب اللاعب خطأً
        """
        # يمكن تحسين هذه الدالة بإضافة منطق أكثر تعقيداً
        return False
    
    def _analyze_reaction_window(self, player: Dict, frames: List[Dict]) -> tuple:
        """
        تحليل ردة فعل اللاعب في نافذة زمنية
        """
        # يمكن تحسين هذه الدالة بإضافة منطق أكثر تعقيداً
        return 0.6, 2.0
    
    def _evaluate_emotional_indicators(self, player: Dict, current_frame: Dict, next_frame: Dict) -> float:
        """
        تقييم المؤشرات العاطفية للاعب
        """
        # يمكن تحسين هذه الدالة بإضافة منطق أكثر تعقيداً
        return 0.7
    
    def _evaluate_confidence(self, player: Dict, frame: Dict) -> float:
        """
        تقييم مستوى ثقة اللاعب
        """
        # يمكن تحسين هذه الدالة بإضافة منطق أكثر تعقيداً
        return 0.8
    
    def _is_frustrated(self, player: Dict, current_frame: Dict, next_frame: Dict) -> bool:
        """
        تحديد ما إذا كان اللاعب محبطاً
        """
        # يمكن تحسين هذه الدالة بإضافة منطق أكثر تعقيداً
        return False
    
    def _calculate_decision_time(self, player: Dict, current_frame: Dict, next_frame: Dict) -> float:
        """
        حساب وقت اتخاذ القرار
        """
        # يمكن تحسين هذه الدالة بإضافة منطق أكثر تعقيداً
        return 0.5
    
    def _evaluate_decision_outcome(self, player: Dict, current_frame: Dict, next_frame: Dict) -> float:
        """
        تقييم نتيجة القرار
        """
        # يمكن تحسين هذه الدالة بإضافة منطق أكثر تعقيداً
        return 0.7
    
    def _evaluate_adaptation(self, player: Dict, current_frame: Dict, next_frame: Dict) -> float:
        """
        تقييم قدرة اللاعب على التكيف
        """
        # يمكن تحسين هذه الدالة بإضافة منطق أكثر تعقيداً
        return 0.6
    
    def _calculate_risk_level(self, player: Dict, frame: Dict) -> float:
        """
        حساب مستوى المخاطرة في قرارات اللاعب
        """
        # يمكن تحسين هذه الدالة بإضافة منطق أكثر تعقيداً
        return 0.4 