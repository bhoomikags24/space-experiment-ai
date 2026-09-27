import cv2
import mediapipe as mp
from ultralytics import YOLO
import requests
import time


# ==========================================
# YOLO MODEL
# ==========================================

model = YOLO("yolo11n.pt")


# ==========================================
# EXPERIMENT STEPS
# ==========================================

steps = [
    "PICK OBJECT",
    "SHOW OBJECT",
    "PLACE OBJECT",
    "CLOSE CONTAINER",
    "RAISE HAND"
]


current_step = 0

BACKEND_URL = "http://127.0.0.1:8000"


# ==========================================
# MEDIAPIPE HANDS
# ==========================================

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


# ==========================================
# CAMERA
# ==========================================

cap = cv2.VideoCapture(0)


if not cap.isOpened():

    print("❌ Camera not found")

    exit()


print("✅ Camera opened")


# ==========================================
# SEQUENCE SETTINGS
# ==========================================

correct_frames = 0

REQUIRED_FRAMES = 8

last_transition_time = 0

TRANSITION_DELAY = 1.0


# ==========================================
# MAIN LOOP
# ==========================================

while True:

    ret, frame = cap.read()


    if not ret:

        print("❌ Cannot read camera")

        break


    height, width, _ = frame.shape


    # ======================================
    # DEFAULT VALUES FOR THIS FRAME
    # ======================================

    observed_activity = "NO ACTIVITY"

    status = "WAITING"

    bottle_detected = False

    bottle_confidence = 0.0

    bottle_center_x = 0

    bottle_center_y = 0

    hand_raised = False

    hand_detected = False


    # ======================================
    # BLUE PLACE ZONE
    # ======================================

    place_x1 = int(width * 0.20)
    place_y1 = int(height * 0.55)

    place_x2 = int(width * 0.80)
    place_y2 = int(height * 0.95)


    cv2.rectangle(
        frame,
        (place_x1, place_y1),
        (place_x2, place_y2),
        (255, 0, 0),
        5
    )


    cv2.putText(
        frame,
        "PLACE BOTTLE HERE",
        (place_x1 + 30, place_y1 + 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 0, 0),
        3
    )


    # ======================================
    # ORANGE CLOSE ZONE
    # ======================================

    close_x1 = int(width * 0.20)
    close_y1 = int(height * 0.10)

    close_x2 = int(width * 0.80)
    close_y2 = int(height * 0.40)


    cv2.rectangle(
        frame,
        (close_x1, close_y1),
        (close_x2, close_y2),
        (0, 165, 255),
        6
    )


    cv2.putText(
        frame,
        "CLOSE CONTAINER HERE",
        (close_x1 + 20, close_y1 + 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 165, 255),
        3
    )


    # ======================================
    # YOLO DETECTION
    # ======================================

    yolo_results = model(
        frame,
        verbose=False
    )


    for result in yolo_results:

        for box in result.boxes:

            class_id = int(
                box.cls[0]
            )

            confidence = float(
                box.conf[0]
            )


            object_name = model.names[
                class_id
            ]


            if (
                object_name == "bottle"
                and confidence > 0.5
            ):

                bottle_detected = True


                # IMPORTANT:
                # This is the confidence
                # from the CURRENT frame.

                bottle_confidence = confidence


                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0]
                )


                bottle_center_x = (
                    x1 + x2
                ) // 2


                bottle_center_y = (
                    y1 + y2
                ) // 2


                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    3
                )


                cv2.putText(
                    frame,
                    "BOTTLE "
                    + str(
                        round(
                            confidence * 100
                        )
                    )
                    + "%",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2
                )


    # ======================================
    # MEDIAPIPE HAND DETECTION
    # ======================================

    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )


    hand_results = hands.process(
        rgb_frame
    )


    if hand_results.multi_hand_landmarks:

        hand_detected = True


        for hand_landmarks in (
            hand_results.multi_hand_landmarks
        ):

            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )


            wrist_y = (
                hand_landmarks
                .landmark[
                    mp_hands.HandLandmark.WRIST
                ]
                .y
            )


            if wrist_y < 0.45:

                hand_raised = True


    # ======================================
    # ACTIVITY RECOGNITION
    # ======================================

    if current_step == 0:

        if bottle_detected:

            observed_activity = (
                "PICK OBJECT"
            )


    else:

        if hand_raised:

            observed_activity = (
                "RAISE HAND"
            )


        elif bottle_detected:

            if (
                place_x1
                < bottle_center_x
                < place_x2
                and
                place_y1
                < bottle_center_y
                < place_y2
            ):

                observed_activity = (
                    "PLACE OBJECT"
                )


            elif (
                close_x1
                < bottle_center_x
                < close_x2
                and
                close_y1
                < bottle_center_y
                < close_y2
            ):

                observed_activity = (
                    "CLOSE CONTAINER"
                )


            else:

                observed_activity = (
                    "SHOW OBJECT"
                )


    # ======================================
    # EXPECTED ACTIVITY
    # ======================================

    if current_step < len(steps):

        expected_activity = (
            steps[current_step]
        )

    else:

        expected_activity = "COMPLETED"


    # ======================================
    # SEQUENCE VALIDATION
    # ======================================

    now = time.time()


    if current_step < len(steps):

        if observed_activity == "NO ACTIVITY":

            correct_frames = 0

            status = "WAITING"


        elif observed_activity == expected_activity:

            correct_frames += 1

            status = "CORRECT"


            if (
                correct_frames >= REQUIRED_FRAMES
                and
                now - last_transition_time
                > TRANSITION_DELAY
            ):

                print(
                    "🟢 CORRECT - "
                    + expected_activity
                )


                current_step += 1

                correct_frames = 0

                last_transition_time = now


        else:

            correct_frames = 0

            status = "WRONG"


            print(
                "🔴 WRONG SEQUENCE"
            )


            print(
                "Expected:",
                expected_activity
            )


            print(
                "Detected:",
                observed_activity
            )


    else:

        status = "CORRECT"


    # ======================================
    # BACKEND STEP
    # ======================================

    if current_step < len(steps):

        backend_step = (
            current_step + 1
        )

    else:

        backend_step = len(steps)


    # ======================================
    # SEND CURRENT FRAME DATA
    # ======================================

    try:

        requests.post(

            BACKEND_URL + "/update",

            json={

                "activity":
                    observed_activity,

                "step":
                    backend_step,

                "status":
                    status,

                "confidence":
                    bottle_confidence

            },

            timeout=0.2

        )

    except requests.exceptions.RequestException:

        pass


    # ======================================
    # DISPLAY AI INFORMATION
    # ======================================

    cv2.putText(
        frame,
        "Detected: "
        + observed_activity,
        (20, 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )


    if current_step < len(steps):

        cv2.putText(
            frame,
            "Expected: "
            + expected_activity,
            (20, 85),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )


    cv2.putText(
        frame,
        "Object Confidence: "
        + str(
            round(
                bottle_confidence * 100
            )
        )
        + "%",
        (20, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )


    cv2.putText(
        frame,
        "Hand Detected: "
        + (
            "YES"
            if hand_detected
            else "NO"
        ),
        (20, 155),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )


    # ======================================
    # STATUS ON CAMERA
    # ======================================

    if status == "WRONG":

        cv2.putText(
            frame,
            "WRONG SEQUENCE!",
            (20, 195),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            3
        )


    elif status == "CORRECT":

        cv2.putText(
            frame,
            "CORRECT SEQUENCE",
            (20, 195),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )


    # ======================================
    # COMPLETED
    # ======================================

    if current_step == len(steps):

        cv2.putText(
            frame,
            "EXPERIMENT COMPLETED!",
            (20, 240),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            3
        )


    # ======================================
    # SEND CAMERA FRAME TO BACKEND
    # ======================================

    try:

        success, encoded_frame = (
            cv2.imencode(
                ".jpg",
                frame
            )
        )


        if success:

            requests.post(

                BACKEND_URL + "/frame",

                data=encoded_frame.tobytes(),

                headers={
                    "Content-Type":
                    "image/jpeg"
                },

                timeout=0.05

            )

    except requests.exceptions.RequestException:

        pass


    # ======================================
    # SHOW CAMERA WINDOW
    # ======================================

    cv2.imshow(
        "SPACE EXPERIMENT AI",
        frame
    )


    key = cv2.waitKey(1) & 0xFF


    if key == ord("q"):

        break


# ==========================================
# CLEANUP
# ==========================================

cap.release()

cv2.destroyAllWindows()
