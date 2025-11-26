# main.py
import base64
import google.generativeai as genai
import re
from PIL import Image

class HTMLGenerator:
    def __init__(self):
        # Configure Gemini with your hardcoded API key
        api_key = ""  # ← PUT YOUR ACTUAL KEY HERE
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')
    
    def encode_image(self, image_file):
        """Encode uploaded image to base64 (original size)"""
        # Reset file pointer to beginning
        image_file.seek(0)
        image_bytes = image_file.read()
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def generate_html_with_image_placeholders(self, image_b64, image_width, image_height):
        """Generate HTML code from image using Gemini with original dimensions"""
        try:
            prompt = f"""
            Analyze this image and create EXACT HTML code that matches the design pixel-perfect. 
            The original image dimensions are {image_width}x{image_height} pixels.

            CRITICAL REQUIREMENTS:
            - Preserve the EXACT layout and proportions from the original {image_width}x{image_height} image
            - Maintain original spacing, margins, and element positioning
            - Use the same color tone scheme and typography
            - Keep all text content exactly as shown in the image
            - Make it responsive but maintain the original design integrity

            IMAGE AREAS:
            - Identify ALL images, photos, graphics in the design
            - For each image area, create a placeholder with this exact format:
              <!-- IMAGE_START_1 --><!-- IMAGE_END_1 -->
            - Include the original dimensions and description in comments
            - Create visible placeholder divs that match the original image positions

            OUTPUT FORMAT:
            Start with: <!-- TOTAL_IMAGES:X --> where X is number of images found
            For each image: <!-- IMAGE_1: width=300 height=200 description -->
            Then: <!-- IMAGE_START_1 --><div class="image-placeholder">...</div><!-- IMAGE_END_1 -->

            IMPORTANT: The HTML should look identical to the original image when rendered.
            Output ONLY the HTML code.
            """

            response = self.model.generate_content([
                prompt,
                {"mime_type": "image/jpeg", "data": image_b64}
            ])
            
            return response.text
            
        except Exception as e:
            raise Exception(f"Error: {str(e)}")
    
    def replace_image_placeholders(self, html_content, image_replacements):
        """Replace placeholders with actual uploaded images"""
        for img_id, image_file in image_replacements.items():
            # Reset file pointer and encode image
            image_file.seek(0)
            image_b64 = base64.b64encode(image_file.read()).decode('utf-8')
            mime_type = image_file.type
            
            # Create img tag with uploaded image
            img_tag = f'<img src="data:{mime_type};base64,{image_b64}" alt="Uploaded image {img_id}" style="width: 100%; height: auto; display: block;">'
            
            # Replace the placeholder area
            start_pattern = f'<!-- IMAGE_START_{img_id} -->'
            end_pattern = f'<!-- IMAGE_END_{img_id} -->'
            
            # Find the content between start and end markers
            pattern = f'{re.escape(start_pattern)}.*?{re.escape(end_pattern)}'
            html_content = re.sub(pattern, f'{start_pattern}{img_tag}{end_pattern}', html_content, flags=re.DOTALL)
        
        return html_content

def extract_image_info(html_content):
    """Extract information about image placeholders from HTML"""
    image_info = {}
    
    # Find total images count
    total_match = re.search(r'<!-- TOTAL_IMAGES:(\d+) -->', html_content)
    if total_match:
        total_images = int(total_match.group(1))
    else:
        # Fallback: count image markers
        matches = re.findall(r'<!-- IMAGE_(\d+):', html_content)
        total_images = len(matches)
    
    # Extract individual image info
    matches = re.findall(r'<!-- IMAGE_(\d+): width=(\d+) height=(\d+) (.*?) -->', html_content)
    
    for match in matches:
        img_id, width, height, description = match
        image_info[int(img_id)] = {
            'width': width,
            'height': height,
            'description': description.strip(),
            'uploaded': False
        }
    
    # If no images found with detailed info, create basic entries
    if not image_info and total_images > 0:
        for i in range(1, total_images + 1):
            image_info[i] = {
                'width': '300',
                'height': '200', 
                'description': f'Image area {i}',
                'uploaded': False
            }
    
    return image_info

def get_image_dimensions(image_file):
    """Get original image dimensions"""
    try:
        image = Image.open(image_file)
        return image.size  # (width, height)
    except:
        return (0, 0)