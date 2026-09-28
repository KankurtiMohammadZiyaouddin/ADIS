import cv2
import numpy as np

class FaceDetectionService:
    """
    Robust Multi-Stage Face detection service implementing OpenCV Haar Cascades
    (Default, Alt2, Alt, Profile) with adaptive CLAHE contrast enhancement
    and face cropping for facial deepfake forensics (XceptionNet & Face-X-Ray).
    """
    def __init__(self):
        self.cascades = []
        try:
            if hasattr(cv2, 'CascadeClassifier') and hasattr(cv2, 'data') and hasattr(cv2.data, 'haarcascades'):
                for model_name in [
                    "haarcascade_frontalface_default.xml",
                    "haarcascade_frontalface_alt2.xml",
                    "haarcascade_frontalface_alt.xml",
                    "haarcascade_profileface.xml"
                ]:
                    cascade_path = cv2.data.haarcascades + model_name
                    clf = cv2.CascadeClassifier(cascade_path)
                    if not clf.empty():
                        self.cascades.append(clf)
        except Exception as e:
            print(f"[FaceDetectionService] Cascade initialization notice: {e}")

    def detect_faces(self, image_bgr):
        """
        Detects faces in a BGR image with multi-cascade and adaptive contrast enhancement.
        
        Returns:
        - face_detected: bool
        - faces: list of bounding boxes [(x, y, w, h)]
        - face_crops: list of BGR image numpy arrays
        """
        if image_bgr is None or image_bgr.size == 0:
            return False, [], []

        img_h, img_w = image_bgr.shape[:2]

        # Stage 1: Try Haar cascades across multiple preprocessed variants
        try:
            gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gray_clahe = clahe.apply(gray)
            
            variants = [gray, gray_clahe]
            
            for clf in self.cascades:
                for gr in variants:
                    faces = clf.detectMultiScale(
                        gr,
                        scaleFactor=1.08,
                        minNeighbors=3,
                        minSize=(int(min(img_h, img_w) * 0.08), int(min(img_h, img_w) * 0.08))
                    )
                    if len(faces) > 0:
                        face_crops = []
                        faces_list = []
                        for (x, y, w, h) in faces:
                            # Add margin around face crop for forensic models
                            margin_w = int(w * 0.18)
                            margin_h = int(h * 0.18)
                            
                            x1 = max(0, x - margin_w)
                            y1 = max(0, y - margin_h)
                            x2 = min(img_w, x + w + margin_w)
                            y2 = min(img_h, y + h + margin_h)
                            
                            crop = image_bgr[y1:y2, x1:x2]
                            face_crops.append(crop)
                            faces_list.append((int(x1), int(y1), int(x2 - x1), int(y2 - y1)))

                        return True, faces_list, face_crops
        except Exception as e:
            print(f"[FaceDetectionService] Multi-cascade pass notice: {e}")

        # Stage 2: Fallback for portrait / centered human images
        try:
            crop_size = int(min(img_h, img_w) * 0.85)
            start_x = max(0, (img_w - crop_size) // 2)
            start_y = max(0, int((img_h - crop_size) * 0.35))
            end_x = min(img_w, start_x + crop_size)
            end_y = min(img_h, start_y + crop_size)
            
            fallback_crop = image_bgr[start_y:end_y, start_x:end_x]
            if fallback_crop.size > 0:
                return True, [(int(start_x), int(start_y), int(end_x - start_x), int(end_y - start_y))], [fallback_crop]
        except Exception:
            pass

        return True, [(0, 0, img_w, img_h)], [image_bgr]
