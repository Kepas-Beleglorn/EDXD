import base64

files = ("circle_blue.png", "circle_orange.png", "line_blue.png", "line_orange.png")

for file in files:
    with open(file, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    with open(file + "_ICON_PNG_B64.txt", "w", encoding="utf-8") as out:
        out.write(b64)
