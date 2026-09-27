import cv2
import mediapipe as mp
from ultralytics import YOLO

# YOLO model
model = YOLO("yolo11n.pt")

# MediaPipe hands
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Camera
cap = cv2.VideoCapture(0)

while True:

    ret, frame = cap.read()

    if not ret:
        print("Camera not found")
        break

    # ---------------- YOLO ----------------
    results = model(frame)

    annotated_frame = results[0].plot()

    # ---------------- MediaPipe ----------------
    rgb_frame = cv2.cvtColor(
        annotated_frame,
        cv2.COLOR_BGR2RGB
    )

    hand_results = hands.process(rgb_frame)

    if hand_results.multi_hand_landmarks:

        for hand_landmarks in hand_results.multi_hand_landmarks:

            mp_draw.draw_landmarks(
                annotated_frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

    # Show result
    cv2.imshow(
        "Space Experiment AI",
        annotated_frame
    )

    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
