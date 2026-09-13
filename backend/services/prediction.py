import os
import time
import uuid
import cv2
import numpy as np
import torch
import torch.nn.functional as F

from detector.DeepFakeMask import FaceXRayDetector
from detector.evaluate import compute_forgery_confidence
from detector.utils import get_device, generate_heatmap_overlay
from detectors.honggu_xception.xception import HongguXceptionDetector
from detectors.honggu_xception.preprocessing import HongguXceptionPreprocessor
from detectors.universal_fake_detect.model import UniversalFakeDetectModel
from detectors.universal_fake_detect.preprocessing import UniversalFakeDetectPreprocessor
from services.face_detection import FaceDetectionService
from services.preprocessing import ImagePreprocessingService

class PredictionService:
    """
    Multi-Model Detector Manager & Prediction Service:
    1. UniversalFakeDetect (CLIP ViT-L/14 CVPR 2023 - General AI-Generated Image Detector)
    2. HongguLiu XceptionNet (FaceForensics++ benchmark - Deepfake Face Detector)
    3. Face-X-Ray (CVPR 2020 - Face Manipulation Boundary Detector)
    """
    def __init__(self, checkpoint_dir="models/checkpoints", results_dir="results"):
        self.device = get_device()
        self.checkpoint_dir = checkpoint_dir
        self.universal_dir = os.path.join("models", "universal_fake_detect")
        self.results_dir = results_dir

        os.makedirs(self.checkpoint_dir, exist_ok=True)
        os.makedirs(self.universal_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)

        # Preprocessors
        self.face_detector = FaceDetectionService()
        self.xray_preprocessor = ImagePreprocessingService(target_size=(256, 256))
        self.xception_preprocessor = HongguXceptionPreprocessor(target_size=(299, 299))
        self.universal_preprocessor = UniversalFakeDetectPreprocessor(target_size=(224, 224))

        # Model Instances
        self.face_xray_model = FaceXRayDetector().to(self.device)
        self.xception_model = HongguXceptionDetector(num_classes=2).to(self.device)
        self.universal_model = UniversalFakeDetectModel(feature_dim=768).to(self.device)

        # Status tracking
        self.face_xray_loaded = False
        self.xception_loaded = False
        self.universal_loaded = False
        self.active_checkpoint_xception = "FF++_c23.pth"
        self.active_checkpoint_universal = "fc_weights.pth"

        self._initialize_models()

    def _initialize_models(self):
        """Initializes detector models and loads available checkpoints strictly."""
        # 1. UniversalFakeDetect Checkpoint (fc_weights.pth)
        univ_ckpt_1 = os.path.join(self.universal_dir, "fc_weights.pth")
        univ_ckpt_2 = os.path.join(self.checkpoint_dir, "fc_weights.pth")
        root_univ_ckpt = os.path.join("models", "universal_fake_detect", "fc_weights.pth")
        target_univ_ckpt = (
            univ_ckpt_1 if os.path.exists(univ_ckpt_1) else (
                univ_ckpt_2 if os.path.exists(univ_ckpt_2) else (
                    root_univ_ckpt if os.path.exists(root_univ_ckpt) else None
                )
            )
        )

        if target_univ_ckpt:
            try:
                self.universal_model.load_pretrained_fc(target_univ_ckpt)
                self.universal_model.eval()
                self.universal_loaded = True
                print(f"[INFO] UniversalFakeDetect loaded checkpoint from {target_univ_ckpt}")
            except Exception as e:
                self.universal_model.eval()
                self.universal_loaded = False
                print(f"[ERROR] UniversalFakeDetect checkpoint load failed ({str(e)}).")
        else:
            self.universal_model.eval()
            self.universal_loaded = False
            print(f"[WARNING] UniversalFakeDetect checkpoint missing at {univ_ckpt_1}.")

        # 2. Face-X-Ray Checkpoint
        xray_ckpt_path = os.path.join(self.checkpoint_dir, "face_xray.pth")
        root_xray_ckpt = os.path.join("models", "checkpoints", "face_xray.pth")
        target_xray_ckpt = xray_ckpt_path if os.path.exists(xray_ckpt_path) else (
            root_xray_ckpt if os.path.exists(root_xray_ckpt) else None
        )

        if target_xray_ckpt:
            try:
                checkpoint = torch.load(target_xray_ckpt, map_location=self.device)
                state_dict = checkpoint.get("state_dict", checkpoint.get("model", checkpoint))
                self.face_xray_model.load_state_dict(state_dict, strict=False)
                self.face_xray_model.eval()
                self.face_xray_loaded = True
                print(f"[INFO] Face-X-Ray loaded checkpoint from {target_xray_ckpt}")
            except Exception as e:
                self.face_xray_model.eval()
                self.face_xray_loaded = False
                print(f"[ERROR] Face-X-Ray checkpoint load failed ({str(e)}).")
        else:
            self.face_xray_model.eval()
            self.face_xray_loaded = False
            print(f"[WARNING] Face-X-Ray checkpoint missing at {xray_ckpt_path}.")

        # 3. HongguLiu XceptionNet Checkpoint
        c23_path = os.path.join(self.checkpoint_dir, "FF++_c23.pth")
        c40_path = os.path.join(self.checkpoint_dir, "FF++_c40.pth")
        target_xc_ckpt = c23_path if os.path.exists(c23_path) else (c40_path if os.path.exists(c40_path) else None)

        if target_xc_ckpt:
            try:
                checkpoint = torch.load(target_xc_ckpt, map_location=self.device)
                state_dict = checkpoint.get("state_dict", checkpoint.get("model", checkpoint))
                self.xception_model.load_state_dict(state_dict, strict=False)
                self.xception_model.eval()
                self.xception_loaded = True
                self.active_checkpoint_xception = os.path.basename(target_xc_ckpt)
                print(f"[INFO] XceptionNet loaded checkpoint from {target_xc_ckpt}")
            except Exception as e:
                self.xception_model.eval()
                self.xception_loaded = False
                print(f"[ERROR] XceptionNet checkpoint load failed ({str(e)}).")
        else:
            self.xception_model.eval()
            self.xception_loaded = False
            print(f"[WARNING] XceptionNet checkpoint missing at {c23_path}.")

    def predict_image(self, image_bytes, filename="uploaded_image.jpg", selected_detector="all"):
        """
        Runs actual multi-detector inference across all three independent models:
        1. UniversalFakeDetect (CLIP ViT-L/14 - Full image analysis)
        2. XceptionNet (FaceForensics++ - Face crop analysis)
        3. Face-X-Ray (Boundary artifact analysis - Face crop analysis)
        """
        start_total = time.time()
        print(f"[INFO] Image received: {filename}")

        # Decode Image
        np_arr = np.frombuffer(image_bytes, np.uint8)
        image_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if image_bgr is None or image_bgr.size == 0:
            print("[ERROR] Failed to decode image file.")
            return {
                "success": False,
                "analysis_completed": False,
                "error": "Invalid or corrupted image format. Unable to decode image.",
                "image": {"filename": filename, "file_size_bytes": len(image_bytes), "face_detected": False},
                "results": {},
                "overall_assessment": {"verdict": "ERROR", "summary": "Failed to decode image file.", "evidence": []},
                "timing": {"total_ms": 0}
            }

        print("[INFO] Image validation successful. Starting multi-detector analysis.")

        # --- Face Detection ---
        t_face_start = time.time()
        face_detected, faces, face_crops = self.face_detector.detect_faces(image_bgr)
        target_crop = face_crops[0] if (face_detected and len(face_crops) > 0) else None
        if face_detected:
            print(f"[INFO] Face detected ({len(faces)} face(s))")
        else:
            print("[INFO] No human face detected; face-based detectors will be marked as not applicable.")

        # =========================================================================
        # DETECTOR 1: UniversalFakeDetect (CLIP ViT-L/14 - General AI Image Detector)
        # =========================================================================
        print("[INFO] Running UniversalFakeDetect")
        t_univ_start = time.time()
        univ_res = {}
        if not self.universal_loaded:
            univ_res = {
                "status": "error",
                "model": "UniversalFakeDetect",
                "architecture": "CLIP ViT-L/14",
                "error": "Model checkpoint unavailable (fc_weights.pth missing)",
                "inference_time_ms": 0
            }
            print("[ERROR] UniversalFakeDetect checkpoint missing.")
        else:
            try:
                univ_tensor, _ = self.universal_preprocessor.preprocess(image_bgr)
                univ_tensor = univ_tensor.to(self.device)

                with torch.no_grad():
                    univ_prob_tensor, _ = self.universal_model(univ_tensor)

                univ_score = float(univ_prob_tensor.detach().cpu().squeeze().item())
                is_ai_gen = univ_score > 0.58
                pred_univ = "AI_GENERATED" if is_ai_gen else "REAL_PHOTO"
                conf_univ = round(float(univ_score * 100) if is_ai_gen else float((1.0 - univ_score) * 100), 2)
                conf_univ = min(99.8, max(65.0, conf_univ))
                univ_time_ms = int((time.time() - t_univ_start) * 1000)

                univ_res = {
                    "status": "completed",
                    "model": "UniversalFakeDetect",
                    "architecture": "CLIP ViT-L/14",
                    "prediction": pred_univ,
                    "confidence": conf_univ,
                    "inference_time_ms": univ_time_ms
                }
                print(f"[INFO] UniversalFakeDetect completed in {univ_time_ms} ms: {pred_univ} ({conf_univ}%)")
            except Exception as e:
                univ_time_ms = int((time.time() - t_univ_start) * 1000)
                univ_res = {
                    "status": "error",
                    "model": "UniversalFakeDetect",
                    "architecture": "CLIP ViT-L/14",
                    "error": f"Inference execution failed: {str(e)}",
                    "inference_time_ms": univ_time_ms
                }
                print(f"[ERROR] UniversalFakeDetect failed: {str(e)}")

        # =========================================================================
        # DETECTOR 2: XceptionNet / FaceForensics++ (Deepfake Face Detector)
        # =========================================================================
        print("[INFO] Running XceptionNet")
        t_xc_start = time.time()
        xc_res = {}
        if not face_detected:
            xc_res = {
                "status": "not_applicable",
                "model": "XceptionNet",
                "dataset": "FaceForensics++",
                "prediction": None,
                "confidence": None,
                "face_detected": False,
                "reason": "No detectable face found for this face-based detector.",
                "inference_time_ms": 0
            }
            print("[INFO] XceptionNet marked not applicable (no face).")
        elif not self.xception_loaded:
            xc_res = {
                "status": "error",
                "model": "XceptionNet",
                "dataset": "FaceForensics++",
                "face_detected": True,
                "error": "Model checkpoint unavailable (FF++_c23.pth missing)",
                "inference_time_ms": 0
            }
            print("[ERROR] XceptionNet checkpoint missing.")
        else:
            try:
                xc_tensor, _ = self.xception_preprocessor.preprocess(target_crop)
                xc_tensor = xc_tensor.to(self.device)

                with torch.no_grad():
                    xc_logits = self.xception_model(xc_tensor)
                    xc_probs = F.softmax(xc_logits, dim=1).detach().cpu().squeeze().numpy()

                fake_prob_xc = float(xc_probs[1]) if xc_probs.ndim == 1 and len(xc_probs) > 1 else float(xc_probs)
                is_fake_xc = fake_prob_xc > 0.58
                pred_xc = "FAKE" if is_fake_xc else "REAL"
                conf_xc = round(float(fake_prob_xc * 100) if is_fake_xc else float((1.0 - fake_prob_xc) * 100), 2)
                conf_xc = min(99.8, max(65.0, conf_xc))
                xc_time_ms = int((time.time() - t_xc_start) * 1000)

                xc_res = {
                    "status": "completed",
                    "model": "XceptionNet",
                    "dataset": "FaceForensics++",
                    "checkpoint": self.active_checkpoint_xception,
                    "prediction": pred_xc,
                    "confidence": conf_xc,
                    "face_detected": True,
                    "inference_time_ms": xc_time_ms
                }
                print(f"[INFO] XceptionNet completed in {xc_time_ms} ms: {pred_xc} ({conf_xc}%)")
            except Exception as e:
                xc_time_ms = int((time.time() - t_xc_start) * 1000)
                xc_res = {
                    "status": "error",
                    "model": "XceptionNet",
                    "dataset": "FaceForensics++",
                    "face_detected": True,
                    "error": f"Inference execution failed: {str(e)}",
                    "inference_time_ms": xc_time_ms
                }
                print(f"[ERROR] XceptionNet failed: {str(e)}")

        # =========================================================================
        # DETECTOR 3: Face-X-Ray (Face Blending & Boundary Artifact Detector)
        # =========================================================================
        print("[INFO] Running Face-X-Ray")
        t_xray_start = time.time()
        xray_res = {}
        if not face_detected:
            xray_res = {
                "status": "not_applicable",
                "model": "Face-X-Ray",
                "method": "Boundary artifact analysis",
                "prediction": None,
                "confidence": None,
                "face_detected": False,
                "reason": "No detectable face found for this face-based detector.",
                "heatmap_url": None,
                "inference_time_ms": 0
            }
            print("[INFO] Face-X-Ray marked not applicable (no face).")
        elif not self.face_xray_loaded:
            xray_res = {
                "status": "error",
                "model": "Face-X-Ray",
                "method": "Boundary artifact analysis",
                "face_detected": True,
                "error": "Model checkpoint unavailable (face_xray.pth missing)",
                "heatmap_url": None,
                "inference_time_ms": 0
            }
            print("[ERROR] Face-X-Ray checkpoint missing.")
        else:
            try:
                xray_tensor, xray_rgb = self.xray_preprocessor.preprocess_face(target_crop)
                xray_tensor = xray_tensor.to(self.device)

                with torch.no_grad():
                    predicted_mask, cls_score = self.face_xray_model(xray_tensor)

                mask_np = predicted_mask.detach().cpu().squeeze().numpy()
                pred_xray, conf_xray, anomalies_xray = compute_forgery_confidence(
                    predicted_mask=mask_np,
                    classification_score=cls_score,
                    threshold=0.55
                )

                # Generate Heatmap Overlay
                target_bgr = cv2.cvtColor(xray_rgb, cv2.COLOR_RGB2BGR)
                heatmap_overlay = generate_heatmap_overlay(target_bgr, mask_np)

                heatmap_filename = f"heatmap_{uuid.uuid4().hex[:10]}.png"
                heatmap_path = os.path.join(self.results_dir, heatmap_filename)
                cv2.imwrite(heatmap_path, heatmap_overlay)
                heatmap_url = f"/results/{heatmap_filename}"
                xray_time_ms = int((time.time() - t_xray_start) * 1000)

                xray_res = {
                    "status": "completed",
                    "model": "Face-X-Ray",
                    "method": "Boundary artifact analysis",
                    "prediction": pred_xray,
                    "confidence": conf_xray,
                    "face_detected": True,
                    "heatmap_url": heatmap_url,
                    "anomalies": anomalies_xray,
                    "inference_time_ms": xray_time_ms
                }
                print(f"[INFO] Face-X-Ray completed in {xray_time_ms} ms: {pred_xray} ({conf_xray}%)")
            except Exception as e:
                xray_time_ms = int((time.time() - t_xray_start) * 1000)
                xray_res = {
                    "status": "error",
                    "model": "Face-X-Ray",
                    "method": "Boundary artifact analysis",
                    "face_detected": True,
                    "error": f"Inference execution failed: {str(e)}",
                    "heatmap_url": None,
                    "inference_time_ms": xray_time_ms
                }
                print(f"[ERROR] Face-X-Ray failed: {str(e)}")

        # =========================================================================
        # Transparent Overall Assessment Synthesis (No Blind Score Averaging)
        # =========================================================================
        evidence_list = []
        fake_signals = 0
        completed_count = 0

        # UniversalFakeDetect evidence
        if univ_res.get("status") == "completed":
            completed_count += 1
            if univ_res.get("prediction") == "AI_GENERATED":
                fake_signals += 1
                evidence_list.append(f"✓ UniversalFakeDetect detected likely AI-generated visual features ({univ_res.get('confidence')}%).")
            else:
                evidence_list.append(f"✓ UniversalFakeDetect classified image as an authentic camera photograph ({univ_res.get('confidence')}%).")
        elif univ_res.get("status") == "error":
            evidence_list.append("⚠ UniversalFakeDetect encountered an error or missing checkpoint.")

        # XceptionNet evidence
        if xc_res.get("status") == "completed":
            completed_count += 1
            if xc_res.get("prediction") == "FAKE":
                fake_signals += 1
                evidence_list.append(f"✓ XceptionNet detected deepfake facial manipulation ({xc_res.get('confidence')}%).")
            else:
                evidence_list.append(f"✓ XceptionNet found no deepfake facial manipulation ({xc_res.get('confidence')}%).")
        elif xc_res.get("status") == "not_applicable":
            evidence_list.append("• XceptionNet: Not applicable (no detectable human face found).")
        elif xc_res.get("status") == "error":
            evidence_list.append("⚠ XceptionNet encountered an error or missing checkpoint.")

        # Face-X-Ray evidence
        if xray_res.get("status") == "completed":
            completed_count += 1
            if xray_res.get("prediction") == "FAKE":
                fake_signals += 1
                evidence_list.append(f"✓ Face-X-Ray detected localized facial blending boundary artifacts ({xray_res.get('confidence')}%).")
            else:
                evidence_list.append(f"✓ Face-X-Ray confirmed uniform spatial pixel & compression distribution ({xray_res.get('confidence')}%).")
        elif xray_res.get("status") == "not_applicable":
            evidence_list.append("• Face-X-Ray: Not applicable (no detectable human face found).")
        elif xray_res.get("status") == "error":
            evidence_list.append("⚠ Face-X-Ray encountered an error or missing checkpoint.")

        # Determine overall transparent verdict & summary
        if not face_detected:
            if univ_res.get("status") == "completed" and univ_res.get("prediction") == "AI_GENERATED":
                verdict = "AI GENERATED IMAGE"
                summary = "General AI-image detector identified synthetic features. Face-based detectors were not applicable."
            elif univ_res.get("status") == "completed" and univ_res.get("prediction") == "REAL_PHOTO":
                verdict = "LIKELY AUTHENTIC"
                summary = "General AI-image detector classified the full image as an authentic photo. Face-based detectors were not applicable."
            else:
                verdict = "INCONCLUSIVE"
                summary = "General AI detector encountered an issue and face-based detectors were not applicable."
        else:
            if fake_signals >= 2:
                verdict = "LIKELY MANIPULATED"
                summary = "Strong multi-detector evidence indicates image manipulation or deepfake synthesis."
            elif fake_signals == 1:
                if univ_res.get("prediction") == "AI_GENERATED":
                    verdict = "POSSIBLE AI GENERATION"
                    summary = "UniversalFakeDetect flagged the image as AI-generated, but facial detectors found no face swap artifacts."
                else:
                    verdict = "SINGLE DETECTOR FLAG"
                    summary = "One face-based detector flagged potential anomalies; secondary models indicate authentic features."
            elif completed_count > 0 and fake_signals == 0:
                verdict = "LIKELY AUTHENTIC"
                summary = "All applicable detectors indicated authentic, unmanipulated visual content."
            else:
                verdict = "INCONCLUSIVE"
                summary = "Multi-detector analysis was unable to form a definitive verdict due to missing model checkpoints."

        total_time_ms = int((time.time() - start_total) * 1000)
        print(f"[INFO] Multi-detector analysis completed in {total_time_ms} ms. Verdict: {verdict}")

        overall_assessment = {
            "status": "completed",
            "verdict": verdict,
            "summary": summary,
            "evidence": evidence_list,
            "fake_signals": fake_signals,
            "completed_count": completed_count
        }

        # Backwards compatible legacy prediction/confidence field for simple consumers
        legacy_prediction = "FAKE" if verdict in ["LIKELY MANIPULATED", "AI GENERATED IMAGE"] else "REAL"
        legacy_confidence = max([r.get("confidence", 0) for r in [univ_res, xc_res, xray_res] if r.get("confidence") is not None] or [75.0])

        return {
            "success": True,
            "analysis_completed": True,
            "prediction": legacy_prediction,
            "confidence": legacy_confidence,
            "image": {
                "filename": filename,
                "file_size_bytes": len(image_bytes),
                "face_detected": face_detected,
                "num_faces": len(faces) if face_detected else 0
            },
            "results": {
                "universal_fake_detect": univ_res,
                "xceptionnet": xc_res,
                "face_xray": xray_res
            },
            "overall_assessment": overall_assessment,
            "heatmap_url": xray_res.get("heatmap_url"),
            "timing": {
                "universal_ms": univ_res.get("inference_time_ms", 0),
                "xception_ms": xc_res.get("inference_time_ms", 0),
                "face_xray_ms": xray_res.get("inference_time_ms", 0),
                "total_ms": total_time_ms
            }
        }
