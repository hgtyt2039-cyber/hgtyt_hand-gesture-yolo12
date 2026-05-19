import sys, time
from collections import deque

import cv2
from ultralytics import YOLO
import torch

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer, QObject, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap, QPainter


MODEL_PATH = r"D:\KLTN\hand-gesture-yolo12\runs\detect\gesture_v2_L2_all\weights\best.pt"
CLASS_NAMES = ["call", "fist", "palm", "peace", "stop", "like"]

CONF_THRESHOLD = 0.45
SMOOTH_WINDOW = 5
INFER_W, INFER_H = 320, 180

class RoomSimulation(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background:#f4f6f9;border-radius:12px;")
        self.setRenderHints(self.renderHints() |
                            QPainter.RenderHint.Antialiasing |
                            QPainter.RenderHint.SmoothPixmapTransform)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.bg = QGraphicsPixmapItem(QPixmap("assets/room.png"))
        self.scene.addItem(self.bg)

        self.setSceneRect(self.bg.boundingRect())
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

class YoloWorker(QObject):
    result_ready = pyqtSignal(list, str, float)

    def __init__(self, model, class_names, conf_threshold=0.45, device="cpu"):
        super().__init__()
        self.model = model
        self.class_names = class_names
        self.conf_threshold = conf_threshold
        self.device = device

    @pyqtSlot(object)
    def run_infer(self, frame):
        gesture_label = ""
        best_conf = 0.0
        detections = []

        try:
            orig_h, orig_w = frame.shape[:2]
            infer = cv2.resize(frame, (INFER_W, INFER_H))

            results = self.model.predict(
                infer,
                conf=self.conf_threshold,
                verbose=False,
                device=self.device,
                imgsz=INFER_W,
                half=(self.device == "cuda")
            )

            r = results[0]
            sx = orig_w / INFER_W
            sy = orig_h / INFER_H

            if r.boxes:
                for box in r.boxes:
                    conf = float(box.conf[0])
                    if conf < self.conf_threshold:
                        continue

                    cls = int(box.cls[0])
                    label = self.class_names[cls]

                    if conf > best_conf:
                        best_conf = conf
                        gesture_label = label

                    x1i, y1i, x2i, y2i = box.xyxy[0].cpu().numpy()
                    x1 = int(x1i * sx)
                    y1 = int(y1i * sy)
                    x2 = int(x2i * sx)
                    y2 = int(y2i * sy)

                    detections.append((x1, y1, x2, y2, label, conf))

        except Exception as e:
            print("YOLO worker error:", e)

        self.result_ready.emit(detections, gesture_label, best_conf)

class GestureApp(QMainWindow):
    request_infer = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Assistive Hand Gesture System (YOLOv12)")
        self.resize(1400, 800)

        # YOLO
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = YOLO(MODEL_PATH)
        if self.device == "cuda":
            self.model.to("cuda")

        self.infer_busy = False
        self.last_detections = []
        self.label_history = deque(maxlen=SMOOTH_WINDOW)
        self.fps_history = deque(maxlen=15)
        self.prev_time = None

        self.system_state = {
            "door": "closed",
            "light": "off",
            "bed": "flat",
            "alert": False
        }

        self.init_ui()
        self.setup_worker()
        self.start_camera()

    def init_ui(self):
        central = QWidget()
        main = QVBoxLayout(central)
        main.setSpacing(12)

        top = QHBoxLayout()
        self.lbl_gesture = QLabel("CỬ CHỈ: ---")
        self.lbl_fps = QLabel("FPS: 0")

        self.lbl_gesture.setStyleSheet("font-size:24pt;font-weight:800;color:#1e88e5;")
        self.lbl_fps.setStyleSheet("font-size:18pt;font-weight:700;color:#fb8c00;")

        top.addWidget(self.lbl_gesture)
        top.addStretch()
        top.addWidget(self.lbl_fps)

        content = QHBoxLayout()

        self.lbl_camera = QLabel()
        self.lbl_camera.setMinimumWidth(420)
        self.lbl_camera.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_camera.setStyleSheet("background:black;border-radius:12px;")

        center = QVBoxLayout()
        self.room = RoomSimulation()
        self.room.setMaximumHeight(260)

        self.status = QLabel()
        self.status.setStyleSheet("""
            background:white;
            border-radius:12px;
            padding:14px;
            font-size:12pt;
        """)

        center.addWidget(self.room)
        center.addWidget(self.status)

        side = QLabel("📌 HỆ THỐNG HỖ TRỢ\n\n• Nhận diện cử chỉ\n• Điều khiển môi trường\n• Hỗ trợ người khuyết tật")
        side.setMinimumWidth(260)
        side.setStyleSheet("""
            background:#f8f9fa;
            border-radius:12px;
            padding:16px;
            font-size:12pt;
        """)

        content.addWidget(self.lbl_camera, 3)
        content.addLayout(center, 3)
        content.addWidget(side, 2)

        main.addLayout(top)
        main.addLayout(content)
        self.setCentralWidget(central)

    def setup_worker(self):
        self.worker_thread = QThread()
        self.worker = YoloWorker(self.model, CLASS_NAMES, CONF_THRESHOLD, self.device)
        self.worker.moveToThread(self.worker_thread)

        self.request_infer.connect(self.worker.run_infer)
        self.worker.result_ready.connect(self.handle_result)

        self.worker_thread.start()

    def start_camera(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, INFER_W)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, INFER_H)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def handle_result(self, detections, label, conf):
        self.infer_busy = False
        self.last_detections = detections

        if label:
            self.label_history.append(label)
            final_label = max(set(self.label_history), key=self.label_history.count)
            self.lbl_gesture.setText(f"CỬ CHỈ: {final_label.upper()} ({conf:.2f})")

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        if not self.infer_busy:
            self.infer_busy = True
            self.request_infer.emit(frame.copy())

        for x1,y1,x2,y2,label,conf in self.last_detections:
            cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),2)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h,w,c = rgb.shape
        qimg = QImage(rgb.data, w, h, w*c, QImage.Format.Format_RGB888)

        self.lbl_camera.setPixmap(QPixmap.fromImage(qimg).scaled(
            self.lbl_camera.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

        now = time.time()
        if self.prev_time:
            fps = 1/(now-self.prev_time)
            self.fps_history.append(fps)
            self.lbl_fps.setText(f"FPS: {sum(self.fps_history)/len(self.fps_history):.1f}")
        self.prev_time = now

        self.update_status()

    def update_status(self):
        s = self.system_state
        self.status.setText(
            "📊 TRẠNG THÁI HỆ THỐNG\n\n"
            f"🚪 Cửa: {s['door']}\n"
            f"💡 Đèn: {s['light']}\n"
            f"🛏 Giường: {s['bed']}\n\n"
            f"🛡 Trạng thái: {'GỌI TRỢ GIÚP' if s['alert'] else 'AN TOÀN'}"
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = GestureApp()
    win.show()
    sys.exit(app.exec())
