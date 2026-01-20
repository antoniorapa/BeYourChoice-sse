import os
import subprocess

input_folder = "public/img_optimized"
magick_path = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"

for filename in os.listdir(input_folder):
    if filename.lower().endswith((".jpg", ".jpeg")):
        img_path = os.path.join(input_folder, filename)
        tmp_path = os.path.join(input_folder, "tmp_" + filename)

        subprocess.run([
            magick_path,
            img_path,
            "-strip",
            "-interlace", "Plane",
            "-sampling-factor", "4:2:0",
            "-quality", "50",
            "-resize", "700x700",
            "-define", "jpeg:extent=80KB",
            tmp_path
        ], check=True)

        os.replace(tmp_path, img_path)
        print(f"Optimized: {filename}")