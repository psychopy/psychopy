import os
import random
from PIL import Image, ImageDraw

# Grid parameters
grid_size = 100  # Size of each grid square
gap_size = 5     # Size of the gap between grid squares
num_rows = 3     # Number of rows in the grid
num_cols = 3     # Number of columns in the grid
total_grids = num_rows * num_cols
num_images = 10  # Number of images to create

# Specify the number of white and pink squares you want in each image
# Possibly to use 0 if you don't want that colour
num_white_squares = 1
num_pink_squares = 1

# Create the "stimuli" folder if it doesn't exist
if not os.path.exists("stimuli"):
    os.makedirs("stimuli")

# Calculate total image size including gaps
image_width = num_cols * (grid_size + gap_size) - gap_size
image_height = num_rows * (grid_size + gap_size) - gap_size

# Create 10 images
for image_index in range(1, num_images + 1):  # Start indexing from 1
    # Create a new blank image
    image = Image.new("RGB", (image_width, image_height), "white")
    draw = ImageDraw.Draw(image)

    # Randomly choose positions for the white grids
    white_grid_indices = random.sample(range(total_grids), num_white_squares)
    
    # Randomly choose positions for the pink grids, excluding white grid positions
    pink_grid_indices = random.sample([i for i in range(total_grids) if i not in white_grid_indices], num_pink_squares)

    # Fill the grids with black, white, and pink colors
    for row in range(num_rows):
        for col in range(num_cols):
            x0 = col * (grid_size + gap_size)
            y0 = row * (grid_size + gap_size)
            x1 = x0 + grid_size
            y1 = y0 + grid_size

            grid_index = row * num_cols + col

            if grid_index in white_grid_indices:
                color = "white"
            elif grid_index in pink_grid_indices:
                color = "pink"
            else:
                color = "black"

            draw.rectangle([x0, y0, x1, y1], fill=color)

    # Save the image in the "stimuli" folder
    image_path = os.path.join("stimuli", f"grid_image_{image_index}.png")
    image.save(image_path)

print("Images created and saved in the 'stimuli' folder.")
