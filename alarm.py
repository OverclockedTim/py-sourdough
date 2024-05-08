import torch
import torchvision
import cv2
import json
import os
import sys
import numpy as np
import datetime
from tqdm import tqdm
import time

print("PyTorch version:", torch.__version__)
print("Torchvision version:", torchvision.__version__)
print("CUDA is available:", torch.cuda.is_available())

# Load the config setup (written out by the notebook).
try:
    with open('data/config.json') as f:
        data = json.load(f)

        input_points = data['input_points']
        input_labels = data['input_labels']
        folder_path = data['folder_path']
except FileNotFoundError:
    print("No saved sourdough coordinates found. Please run the sourdough notebook to target the right points in your webcam image and save the coordinates before trying again")
    exit()


print("Loaded saved config:")
print(f"  Input Points: {input_points}")
print(f"  Input Labels: {input_labels}")
print(f"  Sourdough Stills Folder: {folder_path}")


# Load the Segment Anything 

sys.path.append("..")
from segment_anything import sam_model_registry, SamPredictor


print("Loading SAM model...")
sam_checkpoint = "models/sam_vit_h_4b8939.pth"
model_type = "vit_h"

device = "cuda"

sam = sam_model_registry[model_type](checkpoint=sam_checkpoint)
sam.to(device=device)

predictor = SamPredictor(sam)

print("SAM model loaded...")




def get_sourdough_mask_from_image(image, input_points, input_labels):
    predictor.set_image(image)

    # if input_points is not a np array, convert it to one
    if not isinstance(input_points, np.ndarray):
        input_points = np.array(input_points)

    # if input_labels is not a np array, convert it to one
    if not isinstance(input_labels, np.ndarray):
        input_labels = np.array(input_labels)

    masks, scores, logits = predictor.predict(
        point_coords=input_points,
        point_labels=input_labels,
        multimask_output=True,
    )


    best_mask = masks[1]

    return best_mask

def center_crop_cv2(image, crop_percentage=0.3):
    """
    Center-crops an OpenCV image (NumPy array) by removing the specified percentage from both sides.
    
    Args:
        image (numpy.ndarray): Input image (OpenCV format).
        crop_percentage (float, optional): Percentage of width to crop from both sides. Defaults to 0.3 (30%).
    
    Returns:
        numpy.ndarray: Center-cropped image (OpenCV format).
    """
    # Get image dimensions
    height, width, _ = image.shape
    
    # Calculate cropping boundaries
    crop_width = int(width * (1 - 2 * crop_percentage))
    left = (width - crop_width) // 2
    right = left + crop_width
    
    # Crop the center of the image
    cropped_image = image[:, left:right]
    
    return cropped_image

# Define a function to quickly list all files in a directory
def list_files(directory):
    # Initialize an empty list to store file names
    file_list = []
    # Walk through the directory
    for root, dirs, files in os.walk(directory):
        # Add the files to the list
        file_list.extend(files)
    return file_list

def sort_and_filter_files(filenames):
    # Filter the filenames to include only those with the 'jpg' extension
    filtered_files = [file for file in filenames if file.lower().endswith('.jpg')]
    # Sort the filtered files in ascending order
    sorted_and_filtered_files = sorted(filtered_files)
    return sorted_and_filtered_files

filenames = list_files(folder_path)
file_list = sort_and_filter_files(filenames)



def convert_filename_to_datetime(filename):
    #get last index of "." from filename
    last_dot_index = filename.rfind(".")
    last_slash_index = filename.rfind("/")
    utc_time_string = filename[last_slash_index+1:last_dot_index]

    try:
        # Parse the UTC time string into a datetime object
        start_date_time = datetime.datetime.strptime(utc_time_string, '%Y-%m-%dT%H_%M_%S.%f')
        return start_date_time
    except ValueError:
        print(f"Invalid UTC datetime format: {utc_time_string} Please provide a valid string (e.g., '2024-04-27T20_41_44.755476').")
        return None

start_date_time = convert_filename_to_datetime(file_list[0])

def calculate_time_difference_string(current_date_time, start_date_time):
    # Calculate the time difference
    time_delta = current_date_time - start_date_time

    # Extract hours, minutes, and seconds
    total_seconds = time_delta.total_seconds()
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Format the result as hh:mm:ss
    time_difference_str = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    return time_difference_str


cache_file_path = 'data/sourdough_size_cache.json'

# Function to load the existing data
def load_cache():
    if os.path.exists(cache_file_path):
        with open(cache_file_path, 'r') as cache_file:
            try:
                return json.load(cache_file)
            except json.JSONDecodeError:
                return []
    else:
        return []

# Function to save the updated cache
def save_cache(cache_data):
    # Ensure the 'data' directory exists
    os.makedirs(os.path.dirname(cache_file_path), exist_ok=True)
    
    # Save the cache data to the file, creating the file if it doesn't exist
    with open(cache_file_path, 'w') as cache_file:
        json.dump(cache_data, cache_file, indent=4)

# Load the current cache
cache = load_cache()

def get_rolling_average(input_array, window_size):
  """
  This function takes in an input array and a window size and outputs a new array
  where the values are the rolling averages of the input array over the window size.

  Args:
      input_array: A NumPy array of any shape.
      window_size: An integer specifying the window size for the rolling average.

  Returns:
      A NumPy array of the same shape as the input array, containing the rolling averages.
  """
  if window_size < 1:
      raise ValueError("Window size must be a positive integer")
  if window_size > len(input_array):
      raise ValueError("Window size cannot be greater than the length of the input array")

  rolling_average_array = np.empty(len(input_array))
  for i in range(len(input_array)):
      start_index = max(0, i - window_size + 1)
      end_index = i + 1
      window = input_array[start_index:end_index]
      rolling_average_array[i] = np.mean(window)
  return rolling_average_array


import smtplib
from email.message import EmailMessage
from email.utils import make_msgid
import mimetypes

def send_email(subject: str, body: str, image: str):
    """
    Sends an email with the given subject and body.

    Args:
        subject (str): Subject line of the email.
        body (str): Body content of the email.
    """
    sender_email = os.environ['EMAIL']
    recipient_email = os.environ['EMAIL']

    msg = EmailMessage()

    # generic email headers
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email

    # set the plain text body
    msg.set_content(body)

    # now create a Content-ID for the image
    image_cid = make_msgid(domain='xyz.com')
    # if `domain` argument isn't provided, it will 
    # use your computer's name

    # set an alternative html body
    msg.add_alternative("""\
    <html>
        <body>
            <p>""" + body + """
            </p>
            <img src="cid:{image_cid}">
        </body>
    </html>
    """.format(image_cid=image_cid[1:-1]), subtype='html')
    # image_cid looks like <long.random.number@xyz.com>
    # to use it as the img src, we don't need `<` or `>`
    # so we use [1:-1] to strip them off


    # now open the image and attach it to the email
    with open(image, 'rb') as img:

        # know the Content-Type of the image
        maintype, subtype = mimetypes.guess_type(img.name)[0].split('/')

        # attach it
        msg.get_payload()[1].add_related(img.read(), 
                                            maintype=maintype, 
                                            subtype=subtype, 
                                            cid=image_cid)

    # Establish an SMTP session
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            app_password = os.environ['GMAIL_APP_PASSWORD']
            server.login(sender_email, app_password)
            server.send_message(msg)
        print("Email sent successfully!")
    except smtplib.SMTPException as e:
        print(f"Error sending email: {e}")

def create_animated_gif(folder_path, output_path, file_list):

    # Define the output path
    output_path = 'data/sourdough_growth.gif'

    # Desired frame rate and duration
    frame_rate = 30
    duration_in_seconds = 10
    total_frames = frame_rate * duration_in_seconds

    # If there are more images than needed, select every nth image to achieve the desired frame rate
    if len(file_list) > total_frames:
        step = len(file_list) // total_frames
        selected_files = file_list[::step][:total_frames]
    else:
        selected_files = file_list

    # Generate a temporary text file with the list of selected images
    with open('data/temp_file_list.txt', 'w') as file:
        for image in selected_files:
            #write the full path to the image, including folder_path and the image 
            file.write(f"file '{os.path.join(folder_path, image)}'\n")

    # Create the ffmpeg command to generate the GIF using the list of selected images
    ffmpeg_command = f"ffmpeg -y -f concat -safe 0 -i data/temp_file_list.txt -vf 'fps={frame_rate},scale=320:-1:flags=lanczos' -c:v gif -loop 0 {output_path}"

    # Use os.system to call the ffmpeg command
    os.system(ffmpeg_command)

    # Remove the temporary file list
    os.remove('data/temp_file_list.txt')


is_done = False
while not is_done:
    filenames = list_files(folder_path)
    file_list = sort_and_filter_files(filenames)
    mask_sizes = []
    minutes = []
    growth_percentages = []

    #Go through all the files currently there, and calculate the sourdough size for each one.
    for file in tqdm(file_list):
        image_path = os.path.join(folder_path, file)
        # Here, we have a choice. We either get the mask size from the image, or we get it from the cache

        # Check if the file already exists in the cache
        existing_entry = next((item for item in cache if file in item), None)
        if existing_entry:
            sourdough_size = existing_entry[file]
            mask_sizes.append(sourdough_size)
        else:    
            
            
            # Load the image from the file
            image = cv2.imread(image_path)
            # Convert the image from BGR to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Center-crop the image (mostly to match the notebook's image size and therefore coordinates)
            image = center_crop_cv2(image)

            # Get the sourdough mask from the image
            mask = get_sourdough_mask_from_image(image, input_points, input_labels)
            # Apply the mask to the image

            sourdough_size = np.sum(mask).item()
            mask_sizes.append(sourdough_size)
            # Add the new file and sourdough_size association
            cache.append({file: sourdough_size})
            # Save the updated cache
            save_cache(cache)
    
    current_date_time = convert_filename_to_datetime(image_path)
    time_difference = current_date_time - start_date_time

    time_difference_minutes = int(time_difference.total_seconds() / 60)
    minutes.append(time_difference_minutes)

    # Calculate both the growth percentage and the time.
    # As of right now, calculating and remembering the time is probably unnecessary as it is simply
    # one per minute. However, by getting this in below as a calculation, it enables us to change the
    # frame rate of the capture without breaking this part of the code, so we will just do the extra
    # calculations for now for the sake of redundancy.
    time_difference_string = calculate_time_difference_string(current_date_time, start_date_time)
    growth_percentage = (sourdough_size - mask_sizes[0]) / mask_sizes[0] * 100
    growth_percentages.append(growth_percentage)

    #print("Growth Percentage:", growth_percentage)

    if len(file_list) < 240:
        print("Not enough data points yet, will wait until at least four hours have passed before checking for growth.")
    else:
        # Peak activity detector. We are going to take a look at the rate of change of the growth percentage. When it goes negative after 4 hours, that will be the peak activity time.
        growth_percentage_rolling_avg = get_rolling_average(growth_percentages, 120)
        hours = np.array(minutes) / 60
        
        # Calculate the rate of change of the growth percentage
        growth_percentage_rate = np.diff(growth_percentage_rolling_avg)

        # Find the index where the rate of change goes negative after 4 hours
        peak_activity_index = np.argmax((hours[1:] > 4) & (growth_percentage_rate < 0))

        if peak_activity_index == 0:
            print("Peak activity not detected yet. Continuing to monitor growth...")
            is_done = False
        else:
            is_done = True

        # Get the peak activity time in hours
        peak_activity_time = hours[peak_activity_index]

        file_name = file_list[peak_activity_index + 1]

        # Extract the timestamp part from the filename
        timestamp_str = file_name.split('.')[0]  # Remove the file extension
        timestamp_str = timestamp_str.replace('T', ' ').replace('_', ':')  # Format to a recognizable datetime string

        # Parse the timestamp into a datetime object
        timestamp_dt = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')

        # Format the datetime object into the desired human-readable form
        human_readable = timestamp_dt.strftime('%A, %B %d @ %I:%M %p')

        print(f"Peak activity detected at {peak_activity_time:.2f} hours, corresponding to: {human_readable}")

        #Now send myself an email letting me know that the sourdough starter is fully active.
        subject = "PySourdough Alert: Peak Sourdough Activity Detected"
        body = f"The sourdough starter has reached peak activity at {human_readable}."

        print("Creating animated gif to send in email...")
        output_path = 'data/sourdough_growth.gif'
        create_animated_gif(folder_path, output_path, file_list)

        print("Sending email...")
        send_email(subject, body, output_path)
    
    if is_done:
        break
    else:
        print("Sleeping for 60 seconds before checking for more growth.")
        time.sleep(60)


