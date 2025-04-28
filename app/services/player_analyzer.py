from typing import Dict, List, Optional, Union
from .physical.physical_analyzer import PhysicalAnalyzer
from .tactical.tactical_analyzer import TacticalAnalyzer
from .psychological.psychological_analyzer import PsychologicalAnalyzer

class PlayerAnalyzer:
    def __init__(self):
        """
        تهيئة محلل اللاعبين
        """
        self.physical_analyzer = PhysicalAnalyzer()
        self.tactical_analyzer = TacticalAnalyzer()
        self.psychological_analyzer = PsychologicalAnalyzer()
    
    def analyze_players(self, video_data: Dict, player_ids: Optional[List[int]] = None) -> Dict:
        """
        تحليل أداء اللاعبين المحددين أو جميع اللاعبين
        
        Args:
            video_data: بيانات الفيديو المعالجة
            player_ids: قائمة معرفات اللاعبين المراد تحليلهم (اختياري)
        
        Returns:
            Dict: نتائج التحليل لكل لاعب
        """
        frames_data = video_data['frames']
        all_player_stats = video_data['player_stats']
        
        # تحديد اللاعبين المراد تحليلهم
        if player_ids is None:
            player_ids = list(all_player_stats.keys())
        
        # تجميع بيانات كل لاعب
        players_analysis = {}
        for player_id in player_ids:
            if str(player_id) not in all_player_stats:
                continue
                
            # استخراج بيانات اللاعب من الإطارات
            player_frames = self._extract_player_frames(frames_data, player_id)
            
            # تحليل الأداء البدني
            physical_stats = self.physical_analyzer.analyze(player_frames)
            
            # تحليل الأداء التكتيكي
            tactical_stats = self.tactical_analyzer.analyze(player_frames)
            
            # تحليل الأداء النفسي
            psychological_stats = self.psychological_analyzer.analyze(player_frames)
            
            # تجميع الإحصائيات الأساسية
            base_stats = all_player_stats[str(player_id)]
            
            # تجميع جميع التحليلات
            players_analysis[player_id] = {
                'base_stats': base_stats,
                'physical_analysis': physical_stats,
                'tactical_analysis': tactical_stats,
                'psychological_analysis': psychological_stats,
                'summary': self._generate_player_summary(
                    base_stats,
                    physical_stats,
                    tactical_stats,
                    psychological_stats
                )
            }
        
        return players_analysis
    
    def _extract_player_frames(self, frames_data: List[Dict], player_id: int) -> List[Dict]:
        """
        استخراج الإطارات التي يظهر فيها اللاعب المحدد
        """
        player_frames = []
        
        for frame in frames_data:
            # نسخ بيانات الإطار مع تصفية اللاعبين
            frame_copy = frame.copy()
            frame_copy['players'] = [
                player for player in frame['players']
                if player['id'] == player_id
            ]
            
            if frame_copy['players']:
                player_frames.append(frame_copy)
        
        return player_frames
    
    def _generate_player_summary(
        self,
        base_stats: Dict,
        physical_stats: Dict,
        tactical_stats: Dict,
        psychological_stats: Dict
    ) -> Dict:
        """
        إنشاء ملخص لأداء اللاعب
        """
        summary = {
            'total_play_time': base_stats['total_frames'] / 30,  # بالثواني
            'distance_covered': base_stats['total_distance'],
            'average_speed': base_stats['avg_speed'],
            'possession_percentage': base_stats['possession_percentage'],
            
            'physical_performance': {
                'endurance': self._calculate_endurance_score(physical_stats),
                'speed': self._calculate_speed_score(physical_stats),
                'intensity': self._calculate_intensity_score(physical_stats)
            },
            
            'tactical_performance': {
                'positioning': self._calculate_positioning_score(tactical_stats),
                'team_play': self._calculate_team_play_score(tactical_stats),
                'decision_making': tactical_stats['decision_making']['decision_quality']
            },
            
            'psychological_performance': {
                'concentration': psychological_stats['concentration']['focus_score'],
                'pressure_handling': psychological_stats['pressure_handling']['pressure_resistance'],
                'emotional_control': psychological_stats['emotional_state']['emotional_stability']
            }
        }
        
        # حساب التقييم الإجمالي
        summary['overall_rating'] = self._calculate_overall_rating(summary)
        
        return summary
    
    def _calculate_endurance_score(self, physical_stats: Dict) -> float:
        """
        حساب درجة التحمل
        """
        distance_score = min(1.0, physical_stats['distance']['total_distance'] / 10000)  # افتراض 10 كم كحد أقصى
        high_intensity_score = physical_stats['distance']['high_intensity_distance'] / physical_stats['distance']['total_distance']
        return (distance_score * 0.7 + high_intensity_score * 0.3) * 100
    
    def _calculate_speed_score(self, physical_stats: Dict) -> float:
        """
        حساب درجة السرعة
        """
        sprint_score = min(1.0, physical_stats['sprints']['total_sprints'] / 20)  # افتراض 20 انطلاقة كحد أقصى
        max_speed_score = min(1.0, physical_stats['speed']['max_speed'] / 9)  # افتراض 9 م/ث كحد أقصى
        return (sprint_score * 0.5 + max_speed_score * 0.5) * 100
    
    def _calculate_intensity_score(self, physical_stats: Dict) -> float:
        """
        حساب درجة شدة الأداء
        """
        effort_score = physical_stats['effort']['total_effort'] / 100
        high_intensity_ratio = (
            physical_stats['effort']['effort_zones']['high'] /
            sum(physical_stats['effort']['effort_zones'].values())
        )
        return (effort_score * 0.6 + high_intensity_ratio * 0.4) * 100
    
    def _calculate_positioning_score(self, tactical_stats: Dict) -> float:
        """
        حساب درجة التموضع
        """
        formation_score = tactical_stats['positioning']['formation_adherence']
        coverage_score = (
            tactical_stats['coverage']['defensive_coverage'] +
            tactical_stats['coverage']['offensive_coverage']
        ) / 2
        return (formation_score * 0.4 + coverage_score * 0.6) * 100
    
    def _calculate_team_play_score(self, tactical_stats: Dict) -> float:
        """
        حساب درجة اللعب الجماعي
        """
        pressure_score = tactical_stats['pressure']['pressure_index']
        shape_score = tactical_stats['team_shape']['average_shape']['average_compactness']
        return (pressure_score * 0.5 + shape_score * 0.5) * 100
    
    def _calculate_overall_rating(self, summary: Dict) -> float:
        """
        حساب التقييم الإجمالي للاعب
        """
        # حساب متوسط الأداء في كل جانب
        physical_avg = sum(summary['physical_performance'].values()) / 3
        tactical_avg = sum(summary['tactical_performance'].values()) / 3
        psychological_avg = sum(summary['psychological_performance'].values()) / 3
        
        # الأوزان النسبية لكل جانب
        weights = {
            'physical': 0.35,
            'tactical': 0.35,
            'psychological': 0.30
        }
        
        # حساب التقييم النهائي
        overall_rating = (
            physical_avg * weights['physical'] +
            tactical_avg * weights['tactical'] +
            psychological_avg * weights['psychological']
        )
        
        return round(overall_rating, 2) 