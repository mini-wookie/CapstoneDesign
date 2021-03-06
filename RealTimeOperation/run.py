import os
import cv2
import time
import tensorflow as tf

from my_utils import get_all_face_box, find_face_box_to_track, track_face_box, get_command, visualize_box

def load_model(model_path):
    model = tf.saved_model.load(model_path)
    model = model.signatures['serving_default']

    return model


def main():
    # Load face detector
    detection_model_path = './models/face_detection_model'
    face_detector = load_model(detection_model_path)

    # Load hand sign classifier
    classification_model_path = './models/hand_sign.h5'
    hand_sign_classifier = tf.keras.models.load_model(classification_model_path)

    # Frame's Width, Height
    FRAME_WIDTH = 640
    FRAME_HEIGHT = 480

    # Initialize webcam feed
    # video = cv2.VideoCapture(0) # laptop webcam
    video = cv2.VideoCapture(2) # external webcam
    if not video.isOpened():
        print("Cannot open video")
        exit()
        
    # Set frame size
    video.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    video.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)   

    # Print current fps
    current_fps = video.get(cv2.CAP_PROP_FPS)
    print('Current FPS : ', current_fps)

    hand_sign_classes = ["0_front", "1_back", "1_front", "2_back", "2_front", "5_front", "ILU"]
    command_classes = ["ON/OFF", "TEMP_DOWN", "TEMP_UP", "SPEED_DOWN", "SPEED_UP", "COMMAND", "ROTATION"]
    exit_flag = False

    while(True):
        ret, frame = video.read()
        if ret is False:
            print("Can't receive frame")
            break
        
        # Detect all faces
        face_boxes = get_all_face_box(face_detector, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), 10)
        
        if len(face_boxes) != 0:
            # Find face with hand sign 5 in the right area
            target_face_box = find_face_box_to_track(hand_sign_classifier, frame, face_boxes)
            cv2.imshow('Frame', frame)
            if cv2.waitKey(1) == 27:
                break 
            
            if target_face_box is not None:
                # Start command mode for 3 seconds
                start_wait = time.time()
                commands = []
                while(time.time() - start_wait < 3):
                    cv2.imshow('Frame', frame)
                    if cv2.waitKey(1) == 27:
                        exit_flag = True
                        break
                    
                    ret, frame = video.read()
                    if ret is False:
                        print("Can't receive frame")
                        exit_flag = True
                        break
                    
                    # Face tracking
                    face_boxes = get_all_face_box(face_detector, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), 10)
                    if len(face_boxes) == 0:
                        continue    
                    tracked_face_box = track_face_box(target_face_box, face_boxes)
                    if tracked_face_box is None:
                        continue

                    # Get command sign
                    command_result = get_command(hand_sign_classifier, frame, tracked_face_box)
                    if command_result is not None:
                        hand_area = command_result[0]
                        class_idx = command_result[1]
                        
                        if class_idx == 5:
                            visualize_box(frame, hand_area, hand_sign_classes[class_idx], 'LightGray')
                        else:
                            commands.append(class_idx)
                            visualize_box(frame, hand_area, hand_sign_classes[class_idx], 'Green')
                
                # Print command
                if len(commands) > current_fps/3:
                    command_idx = max(set(commands), key = commands.count)
                    print(command_classes[command_idx])
                    
                if exit_flag is True:
                    break

        cv2.imshow('Frame', frame)
        if cv2.waitKey(1) == 27:
            break 

    # Clean up
    video.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # execute only if run as a script
    main()