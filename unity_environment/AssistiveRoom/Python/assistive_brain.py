from ultralytics import YOLO
import cv2
import socket
import time
from collections import deque
import torch
import numpy as np

# ================= CONFIG =================
CONF_THRESHOLD = 0.75
STABLE_FRAMES = 6
FRAME_SKIP = 2
ACTION_COOLDOWN = 2.0
DIRECTION_COOLDOWN = 0.5

HOST = "127.0.0.1"
PORT = 8052

GESTURE_MAP = {
    "palm":  "OPEN_DOOR",
    "fist":  "CLOSE_DOOR",
    "call":  "CALL_NURSE",
    "peace": "TOGGLE_BED",
    "stop":  "TOGGLE_LIGHT"
}

# ================= SOCKET =================
def send_command(cmd):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        s.send(cmd.encode())
        s.close()
        print("Sent:", cmd)
    except Exception as e:
        print("Send error:", e)

# ================= DEVICE =================
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print("Device:", DEVICE)
torch.backends.cudnn.benchmark = True

# ================= MODEL =================
model = YOLO("best.pt")
model.to(DEVICE)
model.fuse()

if DEVICE == "cuda":
    model.model.half()

# ================= CAMERA =================
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

gesture_buffer = deque(maxlen=STABLE_FRAMES)

prev_time = time.time()
fps_smooth = 0
frame_count = 0

last_direction = None
last_direction_time = 0
last_gesture_cmd = None
last_action_time = 0

detected = None
conf = 0
box_xy = None

def get_direction(x_center, y_center):
    if y_center > 480 * 0.9:  # chỉ STOP khi tay gần sát đáy màn hình
        return "STOP"
    elif x_center < 640 * 0.4:
        return "MOVE_LEFT"
    elif x_center > 640 * 0.6:
        return "MOVE_RIGHT"
    else:
        return "MOVE_FORWARD"

# ================= MAIN LOOP =================
with torch.no_grad():
    while True:

        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # ===== FPS =====
        now = time.time()
        fps = 1 / (now - prev_time)
        fps_smooth = fps_smooth * 0.9 + fps * 0.1
        prev_time = now

        # ===== DETECT =====
        if frame_count % FRAME_SKIP == 0:

            small = cv2.resize(
                frame, (320, 240),
                interpolation=cv2.INTER_NEAREST
            )

            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

            results = model.predict(
                rgb,
                conf=CONF_THRESHOLD,
                imgsz=320,
                verbose=False,
                device=DEVICE,
                half=(DEVICE == "cuda")
            )

            best_detected = None
            best_conf = 0
            best_box = None

            for r in results:
                for box in r.boxes:
                    c = float(box.conf[0])
                    if c > best_conf:
                        best_conf = c
                        cls_id = int(box.cls[0])
                        best_detected = model.names[cls_id]

                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        x1 *= 2
                        x2 *= 2
                        y1 *= 2
                        y2 *= 2
                        best_box = [int(x1), int(y1), int(x2), int(y2)]

            if best_detected:
                detected = best_detected
                conf = best_conf
                box_xy = best_box
                gesture_buffer.append(detected)
            else:
                detected = None
                conf = 0
                box_xy = None

        stable_gesture = None
        if len(gesture_buffer) == STABLE_FRAMES and len(set(gesture_buffer)) == 1:
            stable_gesture = gesture_buffer[0]

        direction = "STOP"

        if stable_gesture == "like" and box_xy:
            x1, y1, x2, y2 = box_xy
            x_center = (x1 + x2) / 2
            y_center = (y1 + y2) / 2
            direction = get_direction(x_center, y_center)

        # ===== SEND DIRECTION =====
        if direction != last_direction and (time.time() - last_direction_time) > DIRECTION_COOLDOWN:
            send_command(direction)
            last_direction = direction
            last_direction_time = time.time()

        # ===== SEND GESTURE ACTION =====
        if stable_gesture in GESTURE_MAP:
            cmd = GESTURE_MAP[stable_gesture]
            if cmd != last_gesture_cmd and (time.time() - last_action_time) > ACTION_COOLDOWN:
                send_command(cmd)
                last_gesture_cmd = cmd
                last_action_time = time.time()

        # ===== DRAW BOX =====
        if box_xy and conf > CONF_THRESHOLD:
            x1, y1, x2, y2 = box_xy
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 255), 2)
            cv2.putText(frame,
                        f"{detected.upper()} {conf:.2f}",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 200, 255),
                        2)

        # ===== UI =====
        cv2.rectangle(frame, (0, 0), (640, 110), (20, 20, 20), -1)

        cv2.putText(frame,
                    "ASSISTIVE ROOM - AI CONTROL",
                    (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 200, 300),
                    2)

        if stable_gesture:
            status_text = f"GESTURE: {stable_gesture.upper()}"
            status_color = (0, 255, 0)
        elif detected:
            status_text = f"DETECTING: {detected.upper()}"
            status_color = (0, 200, 255)
        else:
            status_text = "GESTURE: NONE"
            status_color = (0, 0, 255)

        cv2.putText(frame,
                    status_text,
                    (20, 65),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    status_color,
                    2)

        if stable_gesture in GESTURE_MAP:
            action_text = f"ACTION: {GESTURE_MAP[stable_gesture]}"
        else:
            action_text = f"ACTION: {direction}"

        cv2.putText(frame,
                    action_text,
                    (20, 95),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 180, 0),
                    2)

        cv2.putText(frame,
                    f"FPS: {int(fps_smooth)}",
                    (500, 65),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 120),
                    2)

        cv2.imshow("Assistive AI System", frame)

        if cv2.waitKey(1) == 27:
            break

cap.release()
cv2.destroyAllWindows()