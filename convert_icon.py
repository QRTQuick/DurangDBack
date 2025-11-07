from PIL import Image
import cairosvg
import io

# Convert SVG to PNG using cairosvg
png_data = cairosvg.svg2png(url="assets/app_icon.svg")

# Save the PNG
with open("assets/app_icon.png", "wb") as f:
    f.write(png_data)