from PIL import Image, ImageEnhance
import cv2
import numpy as np
import os

# Folder paths
input_folder = "./proc1"  # Folder containing input images
output_folder = "./proc2"  # Folder to save processed images

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

# Process each image in the input folder
for filename in os.listdir(input_folder):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.bmp')):
        image_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)

        # Open the image using Pillow
        image = Image.open(image_path)

        # Crop the boarders, remove 10% of the width and height from all sides
        width, height = image.size
        left = width * 0.1
        top = height * 0.1
        right = width * 0.9
        bottom = height * 0.9
        image_cropped = image.crop((left, top, right, bottom))

        # Convert to numpy array for further processing with OpenCV
        image_array = np.array(image_cropped)

        # Convert to BGR for OpenCV processing
        image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

        # Apply a blue tint using color balance adjustments
        blue_channel = image_bgr[:, :, 0]
        green_channel = image_bgr[:, :, 1]
        red_channel = image_bgr[:, :, 2]

        # Increase the blue channel intensity and slightly adjust others
        blue_channel = cv2.addWeighted(blue_channel, 1.3, blue_channel, 0, 20) #@skachur adjusting blue chanel balance 1.3 originally
        green_channel = cv2.addWeighted(green_channel, 1.1, green_channel, 0, 10)
        red_channel = cv2.addWeighted(red_channel, 0.9, red_channel, 0, -10) #@skachur adjusting blue chanel balance 0.9 originally 

        # Merge channels back
        image_bgr_tinted = cv2.merge((blue_channel, green_channel, red_channel))

        # Convert back to RGB for saving
        image_rgb_tinted = cv2.cvtColor(image_bgr_tinted, cv2.COLOR_BGR2RGB)

        # Convert back to PIL image
        image_final = Image.fromarray(image_rgb_tinted)

        # Save the processed image
        image_final.save(output_path)

        print(f"Processed image saved at: {output_path}")
