import os
import re

template_folder = "app/templates"

for root, dirs, files in os.walk(template_folder):
    for file in files:
        if file.endswith(".html"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # Ripristina .min.js a .js
            content_new = re.sub(r"\.min\.js", ".js", content)

            # Ripristina .min.css a .css (se per caso è stato cambiato)
            content_new = re.sub(r"\.min\.css", ".css", content_new)

            with open(path, "w", encoding="utf-8") as f:
                f.write(content_new)

            print(f"✔ Ripristinato: {file}")

print("✅ Ripristino completato!")