from PIL import Image
import os

def convert_to_icon(input_image_path):
    # Open the image
    img = Image.open(input_image_path)
    
    # Convert to RGBA if not already
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Create icon sizes
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    
    # Create a list to store different size versions
    icon_sizes = []
    
    for size in sizes:
        # Create a copy of the image with an alpha channel
        resized_img = img.copy()
        # Resize the image, using high-quality resampling
        resized_img.thumbnail(size, Image.Resampling.LANCZOS)
        
        # If the resized image is not square, create a square image with the image centered
        if resized_img.width != resized_img.height:
            square_size = max(resized_img.width, resized_img.height)
            new_img = Image.new('RGBA', (square_size, square_size), (0, 0, 0, 0))
            paste_x = (square_size - resized_img.width) // 2
            paste_y = (square_size - resized_img.height) // 2
            new_img.paste(resized_img, (paste_x, paste_y))
            resized_img = new_img
            
        # Resize to exact size if needed
        if resized_img.size != size:
            resized_img = resized_img.resize(size, Image.Resampling.LANCZOS)
            
        icon_sizes.append(resized_img)
    
    # Save as ICO
    icon_path = 'app_icon.ico'
    icon_sizes[0].save(icon_path, format='ICO', sizes=sizes, append_images=icon_sizes[1:])
    print(f"Successfully created icon at {icon_path}")
    return icon_path

if __name__ == "__main__":
    # Convert the Shinobi Tenno image to icon
    input_image = "shinobi tenno.webp"
    if os.path.exists(input_image):
        convert_to_icon(input_image)
    else:
        print(f"Error: Could not find {input_image} in the current directory")
