import os
import cv2
from deepface import DeepFace

# Function to process the image, detect faces and filter by gender
def process_image(image_path):
    # Load the image
    image = cv2.imread(image_path)

    # Check if image was loaded correctly
    if image is None:
        print(f"Error: Failed to load image from {image_path}.")
        return
    
    # Use DeepFace to analyze the image for faces and gender
    try:  
        analysis = DeepFace.analyze(image, actions=['gender'], enforce_detection=False)

        # Filter by gender: Check if the detected person is a woman
        for face in analysis:
            gender = face['dominant_gender']
            print(f"Detected {gender} in the image.")

            # If the face is of a woman, save the image
            if gender == 'Woman':
                print("Saving the woman's face...")

                # Extract the face coordinates safely
                region = face['region']
                print("Face region details:", region)    

                # Safely extract x, y, w, h values with defaults in case keys are missing
                x = region.get('x', 0)
                y = region.get('y', 0)
                w = region.get('w', 0)
                h = region.get('h', 0)

                # Check if the dimensions are valid (non-zero width and height)
                if w > 0 and h > 0:

                    # Crop the face from the image
                    cropped_face = image[y:y+h, x:x+w]

                    # Save the cropped face as a new image
                    face_filename = 'detected_woman_face.jpg'
                    cv2.imwrite(face_filename, cropped_face)
                    print(f"Saved face as {face_filename}")
                    return face_filename  # Return the saved image file name
                else:
                    print("Invalid face region dimensions. Skipping cropping.")

        print("No woman detected in the image.")
    except Exception as e:
        print(f"Error during face analysis: {e}")
        return None
    
# Function to process the video and detect faces in each frame
def process_video(video_path):
    # Open the video file
    video_capture = cv2.VideoCapture(video_path)

    if not video_capture.isOpened():
        print(f"Error: Unable to open video file {video_path}.")
        return

    frame_count = 0
    first_woman_detected = False  # Flag to check if a woman has already been detected

    while True:
        # Read the next frame from the video
        ret, frame = video_capture.read()
        if not ret:
            break  # End of video

        frame_count += 1
        print(f"Processing frame {frame_count}...")

        # Use DeepFace to analyze the frame for faces and gender
        try:
            analysis = DeepFace.analyze(frame, actions=['gender'], enforce_detection=False)

            # Filter by gender: Check if the detected person is a woman
            for face in analysis:
                gender = face['dominant_gender']
                print(f"Detected {gender} in the frame.")

                # If the face is of a woman and no woman has been detected before
                if gender == 'Woman' and not first_woman_detected:
                    print("Saving the woman's face...")

                    # Extract the face coordinates safely
                    region = face['region']
                    print("Face region details:", region)    

                    # Safely extract x, y, w, h values with defaults in case keys are missing
                    x = region.get('x', 0)
                    y = region.get('y', 0)
                    w = region.get('w', 0)
                    h = region.get('h', 0)

                    # Check if the dimensions are valid (non-zero width and height)
                    if w > 0 and h > 0:

                        # Crop the face from the frame
                        cropped_face = frame[y:y+h, x:x+w]

                        # Save the cropped face as a new image
                        face_filename = f"detected_woman_face_{frame_count}.jpg"
                        cv2.imwrite(face_filename, cropped_face)
                        print(f"Saved face as {face_filename}")

                        first_woman_detected = True

                        print("First woman's face detected. Stopping video processing.")
                        break

        except Exception as e:
            print(f"Error during face analysis in frame {frame_count}: {e}")

        if first_woman_detected:
            break

    # Release the video capture object
    video_capture.release()
    print("Video processing complete.")

if __name__ == "__main__":
    # Path to the image or video
    input_path = '/Users/edwin/Projects/WhatsHerAt/media/path3.mp4' 

    # Check if it's an image or a video based on the file extension
    if input_path.lower().endswith(('.jpg', '.jpeg', '.png')):
        if os.path.exists(input_path):
            process_image(input_path)
        else:
            print(f"Image at {input_path} does not exist.")
    elif input_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
        if os.path.exists(input_path):
            process_video(input_path)
        else:
            print(f"Video at {input_path} does not exist.")
    else:
        print("Unsupported file format. Please provide an image or video.")
