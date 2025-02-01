import cv2
import os
import re

def extract_order(filename):
    """Extract the numeric order before '.acun.tif' in the filename."""
    match = re.search(r'\.(\d+)\.acun\.tif$', filename)
    return int(match.group(1)) if match else float('inf')

def create_video_from_tif(image_folder, output_video, fps=1, frame_size=None):
    # Get all TIF images and sort based on extracted order number
    images = sorted(
        [img for img in os.listdir(image_folder) if img.lower().endswith(('.tif', '.tiff'))],
        key=extract_order
    )

    if not images: 
        print("No TIF images found")
        return 

    first_image = cv2.imread(os.path.join(image_folder, images[0]), cv2.IMREAD_UNCHANGED)
    if first_image is None:
        print('Error loading the first image')
        return

    if frame_size is None: 
        frame_size = (first_image.shape[1], first_image.shape[0])

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_video, fourcc, fps, frame_size)

    for image in images: 
        img_path = os.path.join(image_folder, image)
        img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)

        if img is None: 
            print(f"Could not read {image}, skipping.")
            continue

        img_resized = cv2.resize(img, frame_size)
        video_writer.write(img_resized)
        print(f"Image {image} added.")

    video_writer.release()
    print(f"Video saved as {output_video}")

#To run the code    
create_video_from_tif("./proc2", "sentry754_2.mp4", fps=0.5)



