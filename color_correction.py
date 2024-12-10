import cv2
import os
import numpy as np

def apply_underwater_color_correction_v2(image):
    """
    Underwater color correction.
    """
    # Step 1: White balance by scaling the red channel
    b, g, r = cv2.split(image)
    r = np.clip(r * 1.5, 0, 255).astype(np.uint8)  # Boost red channel
    corrected_image = cv2.merge((b, g, r))

    # Step 2: Apply CLAHE to avoid over-brightening
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    b = clahe.apply(b)
    g = clahe.apply(g)
    r = clahe.apply(r)
    contrast_enhanced_image = cv2.merge((b, g, r))

    # Step 3: Apply gamma correction
    gamma = 0.8  # Lower gamma to reduce brightness of light areas
    inv_gamma = 1.0 / gamma
    gamma_table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype("uint8")
    final_image = cv2.LUT(contrast_enhanced_image, gamma_table)

    return final_image

def process_images(input_folder, output_folder):
    """
    Process all images in the input folder and save them to the output folder.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    image_files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if not image_files:
        print("No images found in the input folder.")
        return

    for i, filename in enumerate(image_files):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)

        print(f"Processing {filename} ({i + 1}/{len(image_files)})")
        image = cv2.imread(input_path)
        if image is None:
            print(f"Failed to load: {filename}")
            continue

        # Applying the underwater color correction
        corrected_image = apply_underwater_color_correction_v2(image)

        cv2.imwrite(output_path, corrected_image)
        print(f"Saved corrected image to: {output_path}")

# Paths to input and output folders
input_folder = "./diver"  # Replace with your actual input folder path
output_folder = "./processed_images"  # Replace with your actual output folder path

# Process all images in the input folder and save them to the output folder
process_images(input_folder, output_folder)
