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

if __name__ == "__main__":
    # Path to the image on your computer
    image_path = '/Users/edwin/Projects/WhatsHerAt/photo.jpeg'  # Replace with your image file path

    if os.path.exists(image_path):
        process_image(image_path)
    else:
        print(f"Image at {image_path} does not exist.")
