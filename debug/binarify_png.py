import base64

with open("edxd.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode("ascii")
with open("ICON_PNG_B64.txt", "w", encoding="utf-8") as out:
    out.write(b64)
