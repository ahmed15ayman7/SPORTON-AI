import cv2
import numpy as np
from ultralytics import YOLO
import torch
import mediapipe as mp
import math
from typing import Dict, List, Optional, Tuple
from deep_sort_realtime.deepsort_tracker import DeepSort
from scipy.spatial import distance
from collections import deque

class Player:
    def __init__(self, id: int, initial_position: Tuple[float, float]):
        self.id = id
        self.positions = deque(maxlen=30)  # تخزين آخر 30 موضع
        self.positions.append(initial_position)
        self.bbox_history = deque(maxlen=30)
        self.pose_history = deque(maxlen=30)
        self.last_seen = 0
        self.total_distance = 0.0
        self.avg_speed = 0.0
        self.max_speed = 0.0
        self.possession_frames = 0
        self.zone_presence = {}
        self.confidence_history = deque(maxlen=30)
        self.appearance_features = deque(maxlen=30)  # تخزين ميزات المظهر
        self.motion_features = deque(maxlen=30)  # تخزين ميزات الحركة
        self.pose_features = deque(maxlen=30)  # تخزين ميزات الوضعية

class VideoProcessor:
    def __init__(self):
        """
        تهيئة معالج الفيديو مع نماذج YOLO و DeepSORT
        """
        try:
            self.yolo_model = YOLO('yolov8n.pt')
            self.tracker = DeepSort(
                max_age=30,  # زيادة عدد الإطارات قبل حذف التتبع
                n_init=3,    # تقليل عدد الإطارات المطلوبة لتأكيد التتبع
                nms_max_overlap=0.7,  # زيادة تداخل الحد الأقصى للكائنات
                max_cosine_distance=0.3,  # زيادة مسافة جيب التمام القصوى للمطابقة
                nn_budget=100,  # تحديد عدد الميزات المخزنة لكل كائن
                override_track_class=None,
                embedder="mobilenet",  # نوع نموذج استخراج الميزات
                half=True,  # استخدام نصف الدقة
                bgr=True,  # تنسيق الصورة BGR
                embedder_gpu=True  # استخدام GPU لاستخراج الميزات
            )
        except Exception as e:
            print(f"خطأ في تحميل النماذج: {str(e)}")
            raise
        
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,  # زيادة تعقيد النموذج
            enable_segmentation=True,  # تفعيل التجزئة
            min_detection_confidence=0.5,  # زيادة عتبة الكشف
            min_tracking_confidence=0.5  # إضافة عتبة التتبع
        )
        
        self.players: Dict[int, Player] = {}
        self.next_player_id = 1
        self.frame_count = 0
        self.ball_positions = []
        self.yolo_boxes = {}
        self.track_history = {}
        self.occlusion_history = {}  # تتبع حالات التداخل
        self.feature_history = {}  # تخزين ميزات المظهر

    def _calculate_distance(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """حساب المسافة بين نقطتين"""
        return np.sqrt((pos2[0] - pos1[0])**2 + (pos2[1] - pos1[1])**2)

    def _calculate_iou(self, box1, box2):
        """حساب نسبة التداخل بين boxين"""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        if x2 < x1 or y2 < y1:
            return 0.0
            
        intersection = (x2 - x1) * (y2 - y1)
        box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
        box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
        
        return intersection / float(box1_area + box2_area - intersection)

    def _extract_appearance_features(self, frame, bbox):
        """استخراج ميزات المظهر من الصورة"""
        try:
            x1, y1, x2, y2 = [int(coord) for coord in bbox]
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(frame.shape[1], x2)
            y2 = min(frame.shape[0], y2)
            
            if x2 <= x1 or y2 <= y1:
                return None
                
            roi = frame[y1:y2, x1:x2]
            if roi.size == 0:
                return None
                
            # تحويل الصورة إلى تنسيق مناسب
            roi = cv2.resize(roi, (64, 128))
            roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # تطبيق HOG
            hog = cv2.HOGDescriptor()
            features = hog.compute(roi)
            
            return features.flatten()
        except Exception as e:
            print(f"خطأ في استخراج ميزات المظهر: {str(e)}")
            return None

    def _extract_motion_features(self, positions):
        """استخراج ميزات الحركة من المواقع السابقة"""
        if len(positions) < 2:
            return None
            
        # حساب السرعة والاتجاه
        velocities = []
        directions = []
        
        for i in range(1, len(positions)):
            dx = positions[i][0] - positions[i-1][0]
            dy = positions[i][1] - positions[i-1][1]
            velocity = np.sqrt(dx**2 + dy**2)
            direction = np.arctan2(dy, dx)
            
            velocities.append(velocity)
            directions.append(direction)
            
        return np.array([np.mean(velocities), np.std(velocities), 
                        np.mean(directions), np.std(directions)])

    def _extract_pose_features(self, landmarks):
        """استخراج ميزات الوضعية من نقاط الجسم"""
        if landmarks is None:
            return None
            
        # حساب زوايا المفاصل
        angles = []
        for i in range(len(landmarks)-2):
            p1 = np.array(landmarks[i])
            p2 = np.array(landmarks[i+1])
            p3 = np.array(landmarks[i+2])
            
            v1 = p1 - p2
            v2 = p3 - p2
            
            angle = np.arccos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
            angles.append(angle)
            
        return np.array(angles)

    def _predict_next_position(self, positions, velocities):
        """توقع الموقع التالي بناءً على الحركة السابقة"""
        if len(positions) < 2 or len(velocities) < 1:
            return None
            
        last_pos = positions[-1]
        avg_velocity = np.mean(velocities, axis=0)
        
        return (last_pos[0] + avg_velocity[0], 
                last_pos[1] + avg_velocity[1])

    def _handle_occlusion(self, track_id, current_box, other_boxes):
        """معالجة حالات التداخل بين اللاعبين"""
        if track_id not in self.occlusion_history:
            self.occlusion_history[track_id] = []
            
        # البحث عن تداخل مع اللاعبين الآخرين
        for other_id, other_box in other_boxes.items():
            iou = self._calculate_iou(current_box, other_box)
            if iou > 0.3:  # عتبة التداخل
                self.occlusion_history[track_id].append((other_id, iou))
                
        # إذا كان هناك تداخل، استخدام الموقع المتوقع
        if len(self.occlusion_history[track_id]) > 0:
            if track_id in self.players:
                player = self.players[track_id]
                if len(player.positions) > 1:
                    velocities = []
                    for i in range(1, len(player.positions)):
                        dx = player.positions[i][0] - player.positions[i-1][0]
                        dy = player.positions[i][1] - player.positions[i-1][1]
                        velocities.append((dx, dy))
                        
                    predicted_pos = self._predict_next_position(
                        list(player.positions), velocities)
                    if predicted_pos is not None:
                        return predicted_pos
                        
        return None

    def process_video(self, video_path, progress_callback=None, frame_callback=None):
        """
        معالجة الفيديو وإرجاع البيانات المستخرجة
        """
        cap = cv2.VideoCapture(video_path)
        frames_data = []
        self.frame_count = 0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            self.frame_count += 1
            if self.frame_count % 3 != 0:
                continue
                
            try:
                if progress_callback:
                    progress = min(self.frame_count / total_frames, 1.0)
                    progress_callback(progress)
                
                frame = cv2.resize(frame, (640, 480))
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # الكشف عن الكائنات باستخدام YOLO
                with torch.no_grad():
                    results = self.yolo_model(frame)
                
                # تحويل نتائج YOLO إلى تنسيق DeepSORT
                detections = []
                yolo_boxes_current = {}
                other_boxes = {}  # تخزين boxes اللاعبين الآخرين
                
                for result in results:
                    if not hasattr(result, 'boxes'):
                        continue
                        
                    boxes = result.boxes
                    for box in boxes:
                        if not hasattr(box, 'xyxy') or not hasattr(box, 'conf') or not hasattr(box, 'cls'):
                            continue
                            
                        try:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            conf = float(box.conf[0].cpu().numpy())
                            cls = int(box.cls[0].cpu().numpy())
                            
                            if cls in [0, 32]:  # 0: شخص، 32: كرة
                                detections.append(([x1, y1, x2, y2], conf, cls))
                                yolo_boxes_current[(x1, y1, x2, y2)] = (x1, y1, x2, y2, conf, cls)
                                
                                # استخراج ميزات المظهر
                                features = self._extract_appearance_features(frame, [x1, y1, x2, y2])
                                if features is not None:
                                    yolo_boxes_current[(x1, y1, x2, y2)] = (x1, y1, x2, y2, conf, cls, features)
                        except Exception as e:
                            print(f"خطأ في معالجة box: {str(e)}")
                            continue
                
                # تتبع الكائنات باستخدام DeepSORT
                tracks = self.tracker.update_tracks(detections, frame=frame)
                
                annotated_frame = frame_rgb.copy()
                frame_players_data = []
                ball_data = None
                
                # معالجة المسارات المتبعة
                for track in tracks:
                    if not track.is_confirmed():
                        continue
                        
                    try:
                        ltrb = track.to_ltrb()
                        track_id = track.track_id
                        class_id = track.get_det_class()
                        
                        # البحث عن أفضل box من YOLO باستخدام IoU والميزات
                        best_box = None
                        max_score = 0.3  # عتبة المطابقة
                        
                        for box_coords, box_data in yolo_boxes_current.items():
                            iou = self._calculate_iou(ltrb, box_coords)
                            
                            # إذا كان لدينا ميزات مظهر
                            if len(box_data) > 6:
                                features = box_data[6]
                                if track_id in self.feature_history:
                                    # حساب التشابه بين الميزات
                                    similarity = 1 - distance.cosine(
                                        features, self.feature_history[track_id])
                                    score = 0.7 * iou + 0.3 * similarity
                                else:
                                    score = iou
                            else:
                                score = iou
                                
                            if score > max_score:
                                max_score = score
                                best_box = box_data
                        
                        if best_box is not None:
                            x1, y1, x2, y2, conf, cls = best_box[:6]
                            center = (int((x1 + x2) / 2), int((y1 + y2) / 2))
                            
                            # معالجة التداخل
                            predicted_pos = self._handle_occlusion(
                                track_id, [x1, y1, x2, y2], other_boxes)
                            if predicted_pos is not None:
                                center = predicted_pos
                            
                            # تحديث تاريخ التتبع والميزات
                            if track_id not in self.track_history:
                                self.track_history[track_id] = []
                            self.track_history[track_id].append((center, conf))
                            
                            if len(best_box) > 6:
                                self.feature_history[track_id] = best_box[6]
                            
                            # تقليل الضوضاء في التتبع
                            if len(self.track_history[track_id]) > 5:
                                positions = [p[0] for p in self.track_history[track_id][-5:]]
                                confidences = [p[1] for p in self.track_history[track_id][-5:]]
                                
                                # استخدام متوسط المواقع مع وزن الثقة
                                center = (
                                    int(sum(x * c for (x, y), c in zip(positions, confidences)) / sum(confidences)),
                                    int(sum(y * c for (x, y), c in zip(positions, confidences)) / sum(confidences))
                                )
                            
                            if class_id == 0:  # شخص
                                # تحديث بيانات اللاعب
                                if track_id not in self.players:
                                    self.players[track_id] = Player(track_id, center)
                                
                                player = self.players[track_id]
                                self._update_player_stats(player, center)
                                
                                # استخراج ميزات الحركة
                                motion_features = self._extract_motion_features(
                                    list(player.positions))
                                if motion_features is not None:
                                    player.motion_features.append(motion_features)
                                
                                # إضافة بيانات اللاعب للإطار الحالي
                                player_data = {
                                    'id': track_id,
                                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                                    'position': [float(center[0]) / 640, float(center[1]) / 480],
                                    'confidence': conf,
                                    'stats': {
                                        'total_distance': player.total_distance,
                                        'avg_speed': player.avg_speed,
                                        'max_speed': player.max_speed,
                                        'possession_time': player.possession_frames,
                                        'time_in_frame': len(player.positions)
                                    }
                                }
                                frame_players_data.append(player_data)
                                
                                # تخزين box اللاعب للتحقق من التداخل
                                other_boxes[track_id] = [x1, y1, x2, y2]
                                
                                # رسم معلومات اللاعب
                                color = (0, 255, 0)
                                cv2.rectangle(annotated_frame, 
                                            (int(x1), int(y1)), 
                                            (int(x2), int(y2)), 
                                            color, 2)
                                cv2.putText(annotated_frame, 
                                          f"Player #{track_id}", 
                                          (int(x1), int(y1) - 10),
                                          cv2.FONT_HERSHEY_SIMPLEX, 
                                          0.5, 
                                          color, 
                                          2)
                                
                                # رسم مسار اللاعب
                                if len(player.positions) > 1:
                                    points = list(player.positions)
                                    for i in range(1, len(points)):
                                        cv2.line(annotated_frame,
                                               points[i-1],
                                               points[i],
                                               color,
                                               1)
                            
                            elif class_id == 32:  # كرة
                                ball_data = {
                                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                                    'position': [float(center[0]) / 640, float(center[1]) / 480],
                                    'confidence': conf
                                }
                                self.ball_positions.append(center)
                                
                                # رسم الكرة ومسارها
                                color = (255, 0, 0)
                                cv2.rectangle(annotated_frame, 
                                            (int(x1), int(y1)), 
                                            (int(x2), int(y2)), 
                                            color, 2)
                                cv2.putText(annotated_frame, 
                                          f"Ball", 
                                          (int(x1), int(y1) - 10),
                                          cv2.FONT_HERSHEY_SIMPLEX, 
                                          0.5, 
                                          color, 
                                          2)
                                
                                if len(self.ball_positions) > 1:
                                    points = self.ball_positions[-30:]
                                    for i in range(1, len(points)):
                                        cv2.line(annotated_frame,
                                               points[i-1],
                                               points[i],
                                               color,
                                               1)
                    except Exception as e:
                        print(f"خطأ في معالجة track: {str(e)}")
                        continue
                
                # تحليل وضعيات الجسم
                pose_data = self._analyze_poses(frame, frame_players_data)
                
                # إضافة بيانات الإطار
                frame_data = {
                    'frame_number': self.frame_count,
                    'players': frame_players_data,
                    'ball': ball_data,
                    'poses': pose_data
                }
                frames_data.append(frame_data)
                
                if frame_callback:
                    frame_callback(annotated_frame)
                    
            except Exception as e:
                print(f"خطأ في معالجة الإطار: {str(e)}")
                continue
            
        cap.release()
        
        # إضافة إحصائيات اللاعبين النهائية
        player_stats = {
            player_id: {
                'total_frames': len(player.positions),
                'total_distance': player.total_distance,
                'avg_speed': player.avg_speed,
                'max_speed': player.max_speed,
                'possession_percentage': (player.possession_frames / (self.frame_count / 3)) * 100 if self.frame_count > 0 else 0,
                'zone_presence': player.zone_presence
            }
            for player_id, player in self.players.items()
        }
        
        return {
            'frames': frames_data,
            'player_stats': player_stats,
            'total_frames': self.frame_count
        }
    
    def _update_player_stats(self, player: Player, new_position: Tuple[float, float]):
        """تحديث إحصائيات اللاعب"""
        if len(player.positions) > 0:
            distance = self._calculate_distance(player.positions[-1], new_position)
            player.total_distance += distance
            
            # حساب السرعة (وحدات البكسل/إطار)
            speed = distance / 3  # نقسم على 3 لأننا نعالج كل 3 إطارات
            player.avg_speed = (player.avg_speed * len(player.positions) + speed) / (len(player.positions) + 1)
            player.max_speed = max(player.max_speed, speed)
        
        player.positions.append(new_position)
        player.last_seen = self.frame_count

    def _analyze_poses(self, frame, players_data):
        """تحليل وضعيات الجسم للاعبين"""
        pose_data = []
        
        for player in players_data:
            try:
                bbox = player['bbox']
                x1, y1, x2, y2 = [max(0, int(coord)) for coord in bbox]
                x2 = min(x2, frame.shape[1])
                y2 = min(y2, frame.shape[0])
                
                player_img = frame[y1:y2, x1:x2]
                
                if player_img.size > 0 and player_img.shape[0] > 0 and player_img.shape[1] > 0:
                    results = self.pose.process(cv2.cvtColor(player_img, cv2.COLOR_BGR2RGB))
                    if results.pose_landmarks:
                        landmarks = [[float(lm.x), float(lm.y), float(lm.z)] 
                                  for lm in results.pose_landmarks.landmark]
                        
                        # استخراج ميزات الوضعية
                        pose_features = self._extract_pose_features(landmarks)
                        if pose_features is not None:
                            player_id = player['id']
                            if player_id in self.players:
                                self.players[player_id].pose_features.append(pose_features)
                        
                        pose_data.append({
                            'player_bbox': bbox,
                            'landmarks': landmarks
                        })
            except Exception as e:
                print(f"خطأ في تحليل وضعية اللاعب: {str(e)}")
                continue
        
        return pose_data
    
    def _calculate_field_position(self, bbox, frame_shape):
        """
        حساب موقع اللاعب/الكرة على أرض الملعب
        """
        try:
            center_x = (bbox[0] + bbox[2]) / 2
            center_y = (bbox[1] + bbox[3]) / 2
            
            # تحويل الإحداثيات إلى نسب مئوية من حجم الإطار
            relative_x = center_x / frame_shape[1]
            relative_y = center_y / frame_shape[0]
            
            return [self._validate_float(relative_x), self._validate_float(relative_y)]
        except Exception as e:
            print(f"خطأ في حساب الموقع: {str(e)}")
            return [0.0, 0.0] 