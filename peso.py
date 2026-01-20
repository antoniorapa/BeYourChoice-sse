import os

input_folder = "public/img_optimized"

for filename in os.listdir(input_folder):
    if filename.lower().endswith((".jpg", ".jpeg")):
        img_path = os.path.join(input_folder, filename)
        size_kb = os.path.getsize(img_path) / 1024
        print(f"{filename}: {size_kb:.1f} KB")