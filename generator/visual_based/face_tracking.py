import cv2
import sys
import os

def get_focal_point_ratios(video_path: str, start: float, end: float) -> tuple:
    """
    Analyzes a video segment and returns the average X, Y ratio of the primary face detected.
    Returns (0.5, 0.5) if no face is detected.
    """
    if not os.path.exists(video_path):
        return (0.5, 0.5)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return (0.5, 0.5)

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30
    
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    
    if width == 0 or height == 0:
        return (0.5, 0.5)

    # Load Haar cascade
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)

    # Seek to start
    cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)

    # We will sample 2 frames per second
    sample_rate_sec = 0.5
    frames_to_skip = int(fps * sample_rate_sec)
    
    current_sec = start
    faces_centers = []

    while current_sec < end:
        ret, frame = cap.read()
        if not ret:
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        if len(faces) > 0:
            # Find largest face (assuming it's the primary speaker)
            largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
            x, y, w, h = largest_face
            # Calculate center
            center_x = x + w / 2.0
            center_y = y + h / 2.0
            faces_centers.append((center_x, center_y))

        # Skip frames
        for _ in range(frames_to_skip - 1):
            ret = cap.grab()
            if not ret:
                break
                
        current_sec += sample_rate_sec

    cap.release()

    if not faces_centers:
        return (0.5, 0.5)

    # Average the centers
    avg_x = sum(cx for cx, cy in faces_centers) / len(faces_centers)
    avg_y = sum(cy for cx, cy in faces_centers) / len(faces_centers)

    return (avg_x / width, avg_y / height)

if __name__ == "__main__":
    # Simple test logic if run directly
    if len(sys.argv) > 1:
        vid_path = sys.argv[1]
        start_t = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
        end_t = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0
        print(get_focal_point_ratios(vid_path, start_t, end_t))
