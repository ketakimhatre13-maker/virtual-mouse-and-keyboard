"""
🖐️ Virtual Mouse & Keyboard using Hand Gestures
================================================
Libraries needed: opencv-python, mediapipe, pyautogui

HOW TO USE:
- ☝️  Index finger up       → Move mouse
- 🤏  Pinch (Index + Thumb) → Left Click
- ✌️  Two fingers up        → Right Click
- 👍  Thumbs up             → Press SPACE (play/pause)
- 🤙  Pinky up only         → Press ESC
"""

import cv2
import mediapipe as mp
import pyautogui
import time

# ─────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────

# PyAutoGUI safety: disable the fail-safe corner (optional)
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0  # No delay between actions (faster response)

# Get screen size so we can map hand position → screen position
SCREEN_W, SCREEN_H = pyautogui.size()

# MediaPipe hands setup
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,          # Only track one hand
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# Open webcam
cap = cv2.VideoCapture(0)

# Cooldown to avoid accidental repeated clicks
last_action_time = 0
COOLDOWN = 0.8  # seconds between gestures


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def get_landmarks(hand_landmarks, img_w, img_h):
    """Convert MediaPipe landmarks to pixel (x, y) coordinates."""
    points = {}
    for i, lm in enumerate(hand_landmarks.landmark):
        points[i] = (int(lm.x * img_w), int(lm.y * img_h))
    return points


def finger_is_up(points, tip, pip):
    """Check if a finger is raised (tip is above its base joint)."""
    return points[tip][1] < points[pip][1]


def get_fingers_up(points):
    """Return which fingers are up: [Thumb, Index, Middle, Ring, Pinky]"""
    fingers = []

    # Thumb: compare x position (left/right) instead of y
    fingers.append(points[4][0] < points[3][0])  # True if thumb is open

    # Four fingers: tip landmark vs PIP (knuckle) landmark
    for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)]:
        fingers.append(finger_is_up(points, tip, pip))

    return fingers  # [Thumb, Index, Middle, Ring, Pinky]


def distance(p1, p2):
    """Calculate distance between two points."""
    return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2) ** 0.5


def map_to_screen(x, y, cam_w, cam_h):
    """Map webcam coordinates to screen coordinates."""
    # Add padding so you don't need to reach the very edges of the camera
    padding = 80
    x = max(padding, min(cam_w - padding, x))
    y = max(padding, min(cam_h - padding, y))

    screen_x = int((x - padding) / (cam_w - 2 * padding) * SCREEN_W)
    screen_y = int((y - padding) / (cam_h - 2 * padding) * SCREEN_H)
    return screen_x, screen_y


# ─────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────

print("✅ Virtual Mouse & Keyboard is running!")
print("👋 Show your hand to the webcam")
print("Press Q to quit\n")

# Smooth mouse movement (average of last few positions)
prev_x, prev_y = 0, 0
smoothing = 5  # Higher = smoother but slightly slower

while True:
    success, frame = cap.read()
    if not success:
        break

    # Flip the frame so it acts like a mirror
    frame = cv2.flip(frame, 1)
    cam_h, cam_w, _ = frame.shape

    # Convert to RGB for MediaPipe
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    gesture_text = "No hand detected"

    if result.multi_hand_landmarks:
        for hand_lms in result.multi_hand_landmarks:

            # Draw hand skeleton on screen
            mp_draw.draw_landmarks(frame, hand_lms, mp_hands.HAND_CONNECTIONS)

            # Get all 21 landmark points as pixel coordinates
            pts = get_landmarks(hand_lms, cam_w, cam_h)

            # Which fingers are up?
            fingers = get_fingers_up(pts)
            # fingers = [Thumb, Index, Middle, Ring, Pinky]

            now = time.time()
            can_act = (now - last_action_time) > COOLDOWN

            # ── GESTURE 1: Move Mouse ──────────────────────
            # Only index finger up → move the mouse
            if fingers == [False, True, False, False, False]:
                gesture_text = "🖱️ Moving Mouse"
                index_tip = pts[8]
                sx, sy = map_to_screen(index_tip[0], index_tip[1], cam_w, cam_h)

                # Smooth the movement
                sx = prev_x + (sx - prev_x) // smoothing
                sy = prev_y + (sy - prev_y) // smoothing
                prev_x, prev_y = sx, sy

                pyautogui.moveTo(sx, sy)

            # ── GESTURE 2: Left Click ──────────────────────
            # Pinch: thumb and index finger close together
            elif distance(pts[4], pts[8]) < 40 and can_act:
                gesture_text = "👆 Left Click!"
                pyautogui.click()
                last_action_time = now

            # ── GESTURE 3: Right Click ─────────────────────
            # Index + Middle fingers up (peace sign ✌️)
            elif fingers == [False, True, True, False, False] and can_act:
                gesture_text = "👉 Right Click!"
                pyautogui.rightClick()
                last_action_time = now

            # ── GESTURE 4: Space Key (play/pause) ──────────
            # Thumbs up: only thumb up, all fingers closed
            elif fingers == [True, False, False, False, False] and can_act:
                gesture_text = "👍 SPACE pressed!"
                pyautogui.press('space')
                last_action_time = now

            # ── GESTURE 5: Escape Key ──────────────────────
            # Only pinky finger up
            elif fingers == [False, False, False, False, True] and can_act:
                gesture_text = "🤙 ESC pressed!"
                pyautogui.press('escape')
                last_action_time = now

            # ── GESTURE 6: Scroll Up ───────────────────────
            # All fingers open (open palm)
            elif fingers == [True, True, True, True, True] and can_act:
                gesture_text = "⬆️ Scroll Up"
                pyautogui.scroll(3)
                last_action_time = now

            # ── GESTURE 7: Scroll Down ─────────────────────
            # All fingers closed (fist ✊)
            elif fingers == [False, False, False, False, False] and can_act:
                gesture_text = "⬇️ Scroll Down"
                pyautogui.scroll(-3)
                last_action_time = now

            else:
                gesture_text = "Waiting..."

    # ─────────────────────────────────────────
    # DISPLAY INFO ON SCREEN
    # ─────────────────────────────────────────

    # Background box for text
    cv2.rectangle(frame, (0, 0), (400, 80), (0, 0, 0), -1)

    cv2.putText(frame, "Virtual Mouse & Keyboard",
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.putText(frame, gesture_text,
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 200, 255), 2)

    cv2.putText(frame, "Press Q to quit",
                (cam_w - 170, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 180, 180), 1)

    cv2.imshow("Virtual Mouse & Keyboard", frame)

    # Quit on pressing 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ─────────────────────────────────────────────
# CLEANUP
# ─────────────────────────────────────────────
cap.release()
cv2.destroyAllWindows()
print("👋 Program closed. Goodbye!")