import cv2
import numpy as np

class FaceDetectionService:
    """
    Face detection service implementing OpenCV Haar Cascades and DNN face detector
    to locate faces, bounding boxes, and verify face presence.
    """
    def __init__(self):
        self.face_cascade = None
        try:
            if hasattr(cv2, 'CascadeClassifier') and hasattr(cv2, 'data') and hasattr(cv2.data, 'haarcascades'):
                cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                self.face_cascade = cv2.CascadeClassifier(cascade_path)
                if self.face_cascade.empty():
                    self.face_cascade = None
        except Exception:
            self.face_cascade = None

    def detect_faces(self, image_bgr):
        """
        Detects faces in a BGR image.
        
        Returns:
        - face_detected: bool
        - faces: list of bounding boxes [(x, y, w, h)]
        - face_crops: list of BGR image numpy arrays
        """
        if image_bgr is None or image_bgr.size == 0:
            return False, [], []

        if self.face_cascade is None:
            # Fallback if CascadeClassifier is unavailable: process full frame
            return False, [], [image_bgr]

        try:
            gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
            
            # Multiscale detection
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=4,
                minSize=(30, 30)
            )
            
            if len(faces) == 0:
                return False, [], [image_bgr]

            face_crops = []
            faces_list = []
            for (x, y, w, h) in faces:
                # Add small padding margin around face crop
                margin_w = int(w * 0.15)
                margin_h = int(h * 0.15)
                
                img_h, img_w = image_bgr.shape[:2]
                x1 = max(0, x - margin_w)
                y1 = max(0, y - margin_h)
                x2 = min(img_w, x + w + margin_w)
                y2 = min(img_h, y + h + margin_h)
                
                crop = image_bgr[y1:y2, x1:x2]
                face_crops.append(crop)
                faces_list.append((int(x1), int(y1), int(x2 - x1), int(y2 - y1)))

            return True, faces_list, face_crops
        except Exception:
            return False, [], [image_bgr]
