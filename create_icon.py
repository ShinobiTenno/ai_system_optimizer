from cairosvg import svg2png
from PIL import Image
import io

# Convert SVG to PNG
svg_data = open('cpu.svg', 'rb').read()
png_data = svg2png(bytestring=svg_data, output_width=256, output_height=256)

# Convert PNG to ICO
img = Image.open(io.BytesIO(png_data))
img.save('app_icon.ico', format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
