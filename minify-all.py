import os
import re
import subprocess
from rcssmin import cssmin

CSS_FOLDER = "public/css"
JS_FOLDER = "public/javascript"
TEMPLATE_FOLDER = "app/templates"

def minify_css():
    for root, dirs, files in os.walk(CSS_FOLDER):
        for file in files:
            if file.endswith(".css") and not file.endswith(".min.css"):
                input_path = os.path.join(root, file)
                output_path = os.path.join(root, file.replace(".css", ".min.css"))

                with open(input_path, "r", encoding="utf-8") as f:
                    content = f.read()

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(cssmin(content))

                print(f"✔ Minified CSS: {file}")

def minify_js():
    for root, dirs, files in os.walk(JS_FOLDER):
        for file in files:
            if file.endswith(".js") and not file.endswith(".min.js"):
                input_path = os.path.join(root, file)
                output_path = os.path.join(root, file.replace(".js", ".min.js"))

                print(f"✔ Minifying JS: {file}")

                subprocess.run(
                    f"npx terser {input_path} -c -m -o {output_path}",
                    shell=True,
                    check=True
                )

def update_html():
    for root, dirs, files in os.walk(TEMPLATE_FOLDER):
        for file in files:
            if file.endswith(".html"):
                path = os.path.join(root, file)

                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

                content = re.sub(
                    r"(url_for\('static', filename='css/([a-zA-Z0-9_-]+)\.css'\))",
                    r"url_for('static', filename='css/\\2.min.css')",
                    content
                )

                content = re.sub(
                    r"(url_for\('static', filename='js/([a-zA-Z0-9_-]+)\.js'\))",
                    r"url_for('static', filename='js/\\2.min.js')",
                    content
                )

                content = content.replace(
                    "https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.js",
                    "https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"
                )

                content = content.replace(
                    "https://cdnjs.cloudflare.com/ajax/libs/toastr.js/latest/toastr.css",
                    "https://cdnjs.cloudflare.com/ajax/libs/toastr.js/latest/toastr.min.css"
                )

                content = content.replace(
                    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.css",
                    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"
                )

                # AGGIUNTA: print.css -> print.min.css
                content = content.replace(
                    "css/print.css",
                    "css/print.min.css"
                )

                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)

                print(f"✔ Template aggiornato: {file}")

minify_css()
minify_js()
update_html()

print("✅ DONE")