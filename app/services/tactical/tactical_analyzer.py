from typing import Dict, List, Tuple
import numpy as np

class TacticalAnalyzer:
    def __init__(self):
        """
        تهيئة محلل الأداء التكتيكي
        """
        self.field_dimensions = (105, 68)  # أبعاد الملعب بالمتر
        self.zones = self._create_field_zones()
        
    def analyze(self, player_frames: List[Dict], team_frames: List[Dict]) -> Dict:
        """
        تحليل الأداء التكتيكي للاعب
        
        Args:
            player_frames: قائمة الإطارات التي يظهر فيها اللاعب
            team_frames: قائمة الإطارات التي تظهر فيها الفريق كامل
            
        Returns:
            Dict: نتائج التحليل التكتيكي
        """
        if not player_frames or not team_frames:
            return self._empty_analysis()
            
        # تحليل التموضع
        positioning = self._analyze_positioning(player_frames)
        
        # تحليل التمريرات
        passing = self._analyze_passing(player_frames, team_frames)
        
        # تحليل التحركات بدون كرة
        off_ball = self._analyze_off_ball_movement(player_frames, team_frames)
        
        # تحليل المساحات
        space = self._analyze_space_utilization(player_frames, team_frames)
        
        return {
            'positioning': positioning,
            'passing': passing,
            'off_ball_movement': off_ball,
            'space_utilization': space
        }
    
    def _empty_analysis(self) -> Dict:
        """
        إرجاع تحليل فارغ عندما لا تتوفر بيانات
        """
        return {
            'positioning': {
                'heat_map': [],
                'zone_coverage': {},
                'average_position': (0, 0)
            },
            'passing': {
                'total_passes': 0,
                'successful_passes': 0,
                'pass_types': {
                    'short': 0,
                    'medium': 0,
                    'long': 0
                },
                'pass_directions': {
                    'forward': 0,
                    'backward': 0,
                    'lateral': 0
                }
            },
            'off_ball_movement': {
                'movement_score': 0,
                'space_creation': 0,
                'support_runs': 0
            },
            'space_utilization': {
                'space_score': 0,
                'space_created': 0,
                'space_occupied': 0
            }
        }
    
    def _create_field_zones(self) -> Dict[str, Tuple[float, float, float, float]]:
        """
        إنشاء مناطق الملعب
        """
        width, height = self.field_dimensions
        zones = {
            'defensive_third': (0, 0, width/3, height),
            'middle_third': (width/3, 0, 2*width/3, height),
            'attacking_third': (2*width/3, 0, width, height),
            'left_wing': (0, 0, width, height/3),
            'center': (0, height/3, width, 2*height/3),
            'right_wing': (0, 2*height/3, width, height)
        }
        return zones
    
    def _analyze_positioning(self, player_frames: List[Dict]) -> Dict:
        """
        تحليل تموضع اللاعب
        """
        positions = []
        zone_counts = {zone: 0 for zone in self.zones}
        
        for frame in player_frames:
            if frame['players']:
                pos = frame['players'][0]['position']
                positions.append(pos)
                
                # تحديد المنطقة
                for zone_name, zone_bounds in self.zones.items():
                    if self._is_in_zone(pos, zone_bounds):
                        zone_counts[zone_name] += 1
        
        # حساب متوسط التموضع
        avg_pos = np.mean(positions, axis=0) if positions else (0, 0)
        
        # تحويل عدد التواجد في المناطق إلى نسب مئوية
        total_frames = len(player_frames)
        zone_coverage = {
            zone: (count/total_frames)*100 if total_frames > 0 else 0
            for zone, count in zone_counts.items()
        }
        
        # إنشاء خريطة حرارية مبسطة
        heat_map = self._create_heat_map(positions)
        
        return {
            'heat_map': heat_map,
            'zone_coverage': zone_coverage,
            'average_position': tuple(avg_pos)
        }
    
    def _analyze_passing(self, player_frames: List[Dict], team_frames: List[Dict]) -> Dict:
        """
        تحليل التمريرات
        """
        passes = []
        successful_passes = 0
        pass_types = {'short': 0, 'medium': 0, 'long': 0}
        pass_directions = {'forward': 0, 'backward': 0, 'lateral': 0}
        
        for i in range(len(player_frames)-1):
            if self._has_ball(player_frames[i]) and not self._has_ball(player_frames[i+1]):
                # تحديد إذا كانت تمريرة ناجحة
                if self._is_successful_pass(player_frames[i], team_frames[i+1]):
                    successful_passes += 1
                    
                    # تحليل نوع التمريرة
                    pass_distance = self._calculate_pass_distance(
                        player_frames[i],
                        team_frames[i+1]
                    )
                    if pass_distance < 15:
                        pass_types['short'] += 1
                    elif pass_distance < 30:
                        pass_types['medium'] += 1
                    else:
                        pass_types['long'] += 1
                    
                    # تحليل اتجاه التمريرة
                    direction = self._calculate_pass_direction(
                        player_frames[i],
                        team_frames[i+1]
                    )
                    pass_directions[direction] += 1
                    
                    passes.append({
                        'distance': pass_distance,
                        'direction': direction,
                        'successful': True
                    })
        
        total_passes = len(passes)
        return {
            'total_passes': total_passes,
            'successful_passes': successful_passes,
            'pass_types': pass_types,
            'pass_directions': pass_directions
        }
    
    def _analyze_off_ball_movement(self, player_frames: List[Dict], team_frames: List[Dict]) -> Dict:
        """
        تحليل التحركات بدون كرة
        """
        movement_score = 0
        space_creation = 0
        support_runs = 0
        
        for i in range(len(player_frames)-1):
            if not self._has_ball(player_frames[i]):
                # تقييم جودة التحرك
                movement_quality = self._evaluate_movement_quality(
                    player_frames[i],
                    player_frames[i+1],
                    team_frames[i]
                )
                movement_score += movement_quality
                
                # تحليل خلق المساحات
                space_created = self._calculate_space_creation(
                    player_frames[i],
                    player_frames[i+1],
                    team_frames[i]
                )
                space_creation += space_created
                
                # تحليل الجري المساند
                if self._is_support_run(
                    player_frames[i],
                    player_frames[i+1],
                    team_frames[i]
                ):
                    support_runs += 1
        
        total_frames = len(player_frames)
        if total_frames > 0:
            movement_score /= total_frames
            space_creation /= total_frames
        
        return {
            'movement_score': movement_score,
            'space_creation': space_creation,
            'support_runs': support_runs
        }
    
    def _analyze_space_utilization(self, player_frames: List[Dict], team_frames: List[Dict]) -> Dict:
        """
        تحليل استغلال المساحات
        """
        space_score = 0
        space_created = 0
        space_occupied = 0
        
        for i in range(len(player_frames)):
            # حساب المساحة المستغلة
            current_space = self._calculate_occupied_space(
                player_frames[i],
                team_frames[i]
            )
            space_occupied += current_space
            
            # حساب المساحة المخلوقة للزملاء
            created_space = self._calculate_created_space(
                player_frames[i],
                team_frames[i]
            )
            space_created += created_space
            
            # تقييم جودة استغلال المساحة
            space_score += self._evaluate_space_usage(
                player_frames[i],
                team_frames[i]
            )
        
        total_frames = len(player_frames)
        if total_frames > 0:
            space_score /= total_frames
            space_created /= total_frames
            space_occupied /= total_frames
        
        return {
            'space_score': space_score,
            'space_created': space_created,
            'space_occupied': space_occupied
        }
    
    def _is_in_zone(self, position: Tuple[float, float], zone_bounds: Tuple[float, float, float, float]) -> bool:
        """
        التحقق من وجود اللاعب في منطقة معينة
        """
        x, y = position
        x1, y1, x2, y2 = zone_bounds
        return x1 <= x <= x2 and y1 <= y <= y2
    
    def _create_heat_map(self, positions: List[Tuple[float, float]]) -> List[List[float]]:
        """
        إنشاء خريطة حرارية مبسطة
        """
        if not positions:
            return []
            
        # تقسيم الملعب إلى شبكة 10x10
        grid_size = (10, 10)
        heat_map = np.zeros(grid_size)
        
        width, height = self.field_dimensions
        for pos in positions:
            x, y = pos
            grid_x = int((x/width) * grid_size[0])
            grid_y = int((y/height) * grid_size[1])
            grid_x = min(grid_x, grid_size[0]-1)
            grid_y = min(grid_y, grid_size[1]-1)
            heat_map[grid_y][grid_x] += 1
        
        # تطبيع القيم
        if np.max(heat_map) > 0:
            heat_map = heat_map / np.max(heat_map)
        
        return heat_map.tolist()
    
    def _has_ball(self, frame: Dict) -> bool:
        """
        التحقق من حيازة اللاعب للكرة
        """
        if not frame['players']:
            return False
        return frame['players'][0].get('has_ball', False)
    
    def _is_successful_pass(self, start_frame: Dict, end_frame: Dict) -> bool:
        """
        التحقق من نجاح التمريرة
        """
        if not start_frame['players'] or not end_frame['players']:
            return False
            
        # التحقق من وصول الكرة لزميل في الفريق
        for player in end_frame['players']:
            if player.get('team_id') == start_frame['players'][0].get('team_id'):
                if player.get('has_ball', False):
                    return True
        return False
    
    def _calculate_pass_distance(self, start_frame: Dict, end_frame: Dict) -> float:
        """
        حساب مسافة التمريرة
        """
        if not start_frame['players'] or not end_frame['players']:
            return 0
            
        start_pos = start_frame['players'][0]['position']
        end_pos = None
        
        # البحث عن اللاعب المستلم
        for player in end_frame['players']:
            if player.get('has_ball', False):
                end_pos = player['position']
                break
                
        if end_pos is None:
            return 0
            
        return np.sqrt(
            (end_pos[0] - start_pos[0])**2 +
            (end_pos[1] - start_pos[1])**2
        )
    
    def _calculate_pass_direction(self, start_frame: Dict, end_frame: Dict) -> str:
        """
        تحديد اتجاه التمريرة
        """
        if not start_frame['players'] or not end_frame['players']:
            return 'lateral'
            
        start_pos = start_frame['players'][0]['position']
        end_pos = None
        
        for player in end_frame['players']:
            if player.get('has_ball', False):
                end_pos = player['position']
                break
                
        if end_pos is None:
            return 'lateral'
            
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        
        if abs(dx) > abs(dy):
            return 'forward' if dx > 0 else 'backward'
        return 'lateral'
    
    def _evaluate_movement_quality(self, prev_frame: Dict, curr_frame: Dict, team_frame: Dict) -> float:
        """
        تقييم جودة التحرك بدون كرة
        """
        if not prev_frame['players'] or not curr_frame['players']:
            return 0
            
        # حساب المسافة المقطوعة
        prev_pos = prev_frame['players'][0]['position']
        curr_pos = curr_frame['players'][0]['position']
        distance = np.sqrt(
            (curr_pos[0] - prev_pos[0])**2 +
            (curr_pos[1] - prev_pos[1])**2
        )
        
        # تقييم الموقع الجديد بالنسبة للفريق
        team_positions = [p['position'] for p in team_frame['players']]
        positioning_score = self._evaluate_team_positioning(curr_pos, team_positions)
        
        # الجمع بين المعايير
        movement_score = (distance * 0.4) + (positioning_score * 0.6)
        return min(1.0, movement_score)  # تطبيع النتيجة
    
    def _calculate_space_creation(self, prev_frame: Dict, curr_frame: Dict, team_frame: Dict) -> float:
        """
        حساب المساحة المخلوقة للزملاء
        """
        if not prev_frame['players'] or not curr_frame['players']:
            return 0
            
        prev_pos = prev_frame['players'][0]['position']
        curr_pos = curr_frame['players'][0]['position']
        
        # حساب المساحة المخلوقة بناءً على تحرك اللاعب
        space_created = 0
        for player in team_frame['players']:
            if player['id'] != prev_frame['players'][0]['id']:
                prev_distance = np.sqrt(
                    (player['position'][0] - prev_pos[0])**2 +
                    (player['position'][1] - prev_pos[1])**2
                )
                curr_distance = np.sqrt(
                    (player['position'][0] - curr_pos[0])**2 +
                    (player['position'][1] - curr_pos[1])**2
                )
                space_created += max(0, prev_distance - curr_distance)
        
        return space_created
    
    def _is_support_run(self, prev_frame: Dict, curr_frame: Dict, team_frame: Dict) -> bool:
        """
        تحديد إذا كان التحرك جرياً مسانداً
        """
        if not prev_frame['players'] or not curr_frame['players']:
            return False
            
        # البحث عن حامل الكرة في الفريق
        ball_carrier = None
        for player in team_frame['players']:
            if player.get('has_ball', False):
                ball_carrier = player
                break
                
        if not ball_carrier:
            return False
            
        # حساب المسافة من حامل الكرة
        curr_pos = curr_frame['players'][0]['position']
        ball_pos = ball_carrier['position']
        distance_to_ball = np.sqrt(
            (curr_pos[0] - ball_pos[0])**2 +
            (curr_pos[1] - ball_pos[1])**2
        )
        
        # التحقق من معايير الجري المساند
        is_moving_forward = curr_pos[0] > prev_frame['players'][0]['position'][0]
        is_in_support_range = 10 < distance_to_ball < 30
        
        return is_moving_forward and is_in_support_range
    
    def _calculate_occupied_space(self, frame: Dict, team_frame: Dict) -> float:
        """
        حساب المساحة المستغلة
        """
        if not frame['players']:
            return 0
            
        player_pos = frame['players'][0]['position']
        occupied_space = 0
        
        # حساب المساحة المستغلة بناءً على المسافة من الزملاء
        for player in team_frame['players']:
            if player['id'] != frame['players'][0]['id']:
                distance = np.sqrt(
                    (player['position'][0] - player_pos[0])**2 +
                    (player['position'][1] - player_pos[1])**2
                )
                # المساحة تزداد كلما كان اللاعب بعيداً عن زملائه
                occupied_space += min(100, distance)
        
        return occupied_space
    
    def _calculate_created_space(self, frame: Dict, team_frame: Dict) -> float:
        """
        حساب المساحة المخلوقة للزملاء
        """
        if not frame['players']:
            return 0
            
        player_pos = frame['players'][0]['position']
        created_space = 0
        
        # حساب المساحة المخلوقة بناءً على توزيع اللاعبين
        for player in team_frame['players']:
            if player['id'] != frame['players'][0]['id']:
                distance = np.sqrt(
                    (player['position'][0] - player_pos[0])**2 +
                    (player['position'][1] - player_pos[1])**2
                )
                # المساحة المخلوقة تزداد في المسافات المتوسطة
                if 10 < distance < 30:
                    created_space += (distance - 10)
        
        return created_space
    
    def _evaluate_space_usage(self, frame: Dict, team_frame: Dict) -> float:
        """
        تقييم جودة استغلال المساحة
        """
        if not frame['players']:
            return 0
            
        player_pos = frame['players'][0]['position']
        space_score = 0
        
        # تقييم التموضع بالنسبة للفريق
        team_positions = [p['position'] for p in team_frame['players']]
        positioning_score = self._evaluate_team_positioning(player_pos, team_positions)
        
        # تقييم المساحة المتاحة
        available_space = self._calculate_available_space(player_pos, team_positions)
        
        # الجمع بين المعايير
        space_score = (positioning_score * 0.6) + (available_space * 0.4)
        return min(1.0, space_score)  # تطبيع النتيجة
    
    def _evaluate_team_positioning(self, position: Tuple[float, float], team_positions: List[Tuple[float, float]]) -> float:
        """
        تقييم التموضع بالنسبة للفريق
        """
        if not team_positions:
            return 0
            
        # حساب متوسط موقع الفريق
        team_center = np.mean(team_positions, axis=0)
        
        # حساب المسافة من مركز الفريق
        distance_to_center = np.sqrt(
            (position[0] - team_center[0])**2 +
            (position[1] - team_center[1])**2
        )
        
        # تقييم التموضع (أفضل قيمة عندما يكون اللاعب في مسافة متوسطة من مركز الفريق)
        optimal_distance = 20  # المسافة المثالية بالمتر
        positioning_score = 1 - min(1, abs(distance_to_center - optimal_distance) / optimal_distance)
        
        return positioning_score
    
    def _calculate_available_space(self, position: Tuple[float, float], team_positions: List[Tuple[float, float]]) -> float:
        """
        حساب المساحة المتاحة حول اللاعب
        """
        if not team_positions:
            return 0
            
        # حساب متوسط المسافة من الزملاء
        distances = []
        for pos in team_positions:
            distance = np.sqrt(
                (position[0] - pos[0])**2 +
                (position[1] - pos[1])**2
            )
            distances.append(distance)
        
        avg_distance = np.mean(distances)
        
        # تقييم المساحة المتاحة (أفضل قيمة عندما تكون المسافة مناسبة)
        optimal_distance = 15  # المسافة المثالية بالمتر
        space_score = 1 - min(1, abs(avg_distance - optimal_distance) / optimal_distance)
        
        return space_score