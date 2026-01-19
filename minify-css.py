import os
import re
from rcssmin import cssmin

# ============================
# CONFIG
# ============================
CSS_FOLDER = "public/css"
TEMPLATE_FOLDER = "app/templates"

# ============================
# 1️⃣ MINIFICA SOLO I CSS
# ============================
for root, dirs, files in os.walk(CSS_FOLDER):
    for file in files:
        if file.endswith(".css") and not file.endswith(".min.css"):
            input_path = os.path.join(root, file)
            output_path = os.path.join(root, file.replace(".css", ".min.css"))

            with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
                css = f.read()

            minified_css = cssmin(css)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(minified_css)

            print(f"✔ CSS minified: {file}")

# ============================
# 2️⃣ AGGIORNA GLI HTML
# ============================
for root, dirs, files in os.walk(TEMPLATE_FOLDER):
    for file in files:
        if file.endswith(".html"):
            path = os.path.join(root, file)

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # url_for('static', filename='css/xxx.css') → xxx.min.css
            content = re.sub(
                r"url_for\(\s*'static'\s*,\s*filename\s*=\s*'css/([^']+?)\.css'\s*\)",
                r"url_for('static', filename='css/\1.min.css')",
                content
            )

            # <link href="...css"> → <link href="...min.css"> (NO CDN)
            content = re.sub(
                r'(<link[^>]+href=["\'])(?!https?://)([^"\']+?)\.css(["\'])',
                r'\1\2.min.css\3',
                content
            )

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"✔ HTML aggiornato: {file}")

print("\n✅ COMPLETATO: solo CSS minificati e HTML aggiornati correttamente")