from PIL import Image

# Create a small 100x100 red image
img = Image.new('RGB', (100, 100), color = 'red')
img.save('tests/test_image.png')
