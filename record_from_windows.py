import cv2
import msvcrt
import os
from datetime import datetime
import re
import shutil

# Function to check and handle the contents of the 'stills' directory
def handle_stills_directory():
    # Check if the 'stills' directory exists
    if os.path.exists('stills'):
        # Get the list of files in the 'stills' directory
        files = os.listdir('stills')
        # Check if there are any files in the directory
        if files:
            print("Files found in the stills directory. Do you want to [r]estart or [c]ontinue?")
            while True:
                # Wait for user input
                if msvcrt.kbhit():
                    choice = msvcrt.getch().lower()
                    # If user chooses to restart, delete all files
                    if choice == b'r':
                        shutil.rmtree('stills')
                        os.makedirs('stills')
                        print("All files deleted. Starting fresh...")
                        break
                    # If user chooses to continue, break the loop
                    elif choice == b'c':
                        print("Continuing with existing files...")
                        break

# Define the function to capture images
def capture_images(device_index=0):
    # Initialize the webcam
    cap = cv2.VideoCapture(device_index)
    
    # Check if the webcam is opened successfully
    if not cap.isOpened():
        raise IOError(f"Cannot open webcam at index {device_index}")
    
    try:
        while True:
            # Capture frame-by-frame
            ret, frame = cap.read()
            
            # Check if frame is read correctly
            if not ret:
                break
            
            # Get the current date and time in ISO format
            timestamp = datetime.now().isoformat()
            
            # Replace invalid characters in the filename
            safe_timestamp = re.sub(r'[\<>:\"/|?*]', '_', timestamp)
            
            # Define the filename with the current date and time
            filename = f"stills\\{safe_timestamp}.jpg"
            
            # Save the captured image with the filename
            if not cv2.imwrite(filename, frame):
                raise Exception(f"Could not write image to {filename}")
            else:
                print(f"Image saved as {filename}")
            
            # Wait for 1 second (1000 milliseconds) and check for 'q' key press
            start_time = datetime.now()
            while (datetime.now() - start_time).seconds < 60:
                if msvcrt.kbhit() and msvcrt.getch() == b'q':
                    cap.release()
                    cv2.destroyAllWindows()
                    return
                cv2.waitKey(30)

    finally:
        # When everything done, release the capture
        cap.release()
        cv2.destroyAllWindows()

# Check if the script is run from the command line
if __name__ == '__main__':
    # Handle the 'stills' directory before starting the capture process
    handle_stills_directory()
    
    # Output usage directions
    print("This script will capture images from your webcam and save them into a folder named 'stills'.")
    print("Each image will be named with the current date and time in ISO format.")
    print("Press 'q' to stop capturing images.")
    
    # Call the function to start capturing images
    capture_images(1)
