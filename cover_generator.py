import os
import logging
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import tempfile

class CoverGenerator:
    """Handles KDP-compliant wraparound cover generation"""
    
    # Standard KDP trim sizes (width x height in inches)
    TRIM_SIZES = {
        '5x8': (5.0, 8.0),
        '5.25x8': (5.25, 8.0),
        '5.5x8.5': (5.5, 8.5),
        '6x9': (6.0, 9.0),
        '6.14x9.21': (6.14, 9.21),  # A5
        '6.69x9.61': (6.69, 9.61),  # 17x24.4 cm
        '7x10': (7.0, 10.0),
        '7.44x9.69': (7.44, 9.69),  # B5
        '7.5x9.25': (7.5, 9.25),
        '8x10': (8.0, 10.0),
        '8.25x6': (8.25, 6.0),
        '8.25x8.25': (8.25, 8.25),
        '8.5x8.5': (8.5, 8.5),
        '8.5x11': (8.5, 11.0)
    }
    
    # Bleed margin in inches (KDP requirement)
    BLEED_MARGIN = 0.125
    
    # Safe text margin in inches (additional margin inside bleed)
    SAFE_MARGIN = 0.25
    
    # DPI for final output
    DPI = 300
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_spine_width(self, page_count):
        """Calculate spine width based on page count (in inches)"""
        # KDP formula: spine width = (page count ÷ 2) × 0.0025"
        # This is an approximation for standard paper weight
        spine_width = (page_count / 2) * 0.0025
        return max(spine_width, 0.06)  # Minimum spine width
    
    def get_cover_dimensions(self, trim_size, page_count):
        """Calculate total cover dimensions including bleed"""
        if trim_size not in self.TRIM_SIZES:
            raise ValueError(f"Unsupported trim size: {trim_size}")
        
        width, height = self.TRIM_SIZES[trim_size]
        spine_width = self.calculate_spine_width(page_count)
        
        # Total width = back + spine + front + bleed on both sides
        total_width = (width * 2) + spine_width + (self.BLEED_MARGIN * 2)
        total_height = height + (self.BLEED_MARGIN * 2)
        
        return total_width, total_height, spine_width
    
    def get_dominant_edge_color(self, img, edge_width=10):
        """Get the dominant color from the edges of an image for background extension"""
        try:
            # Sample pixels from all four edges
            edge_pixels = []
            
            # Top and bottom edges
            for y in [0, img.height - 1]:
                for x in range(0, img.width, max(1, img.width // 20)):
                    edge_pixels.append(img.getpixel((x, y)))
            
            # Left and right edges
            for x in [0, img.width - 1]:
                for y in range(0, img.height, max(1, img.height // 20)):
                    edge_pixels.append(img.getpixel((x, y)))
            
            # Calculate average color
            if edge_pixels:
                avg_r = sum(pixel[0] for pixel in edge_pixels) // len(edge_pixels)
                avg_g = sum(pixel[1] for pixel in edge_pixels) // len(edge_pixels)
                avg_b = sum(pixel[2] for pixel in edge_pixels) // len(edge_pixels)
                return (avg_r, avg_g, avg_b)
            else:
                return (255, 255, 255)  # Default to white
                
        except Exception:
            return (255, 255, 255)  # Default to white if color detection fails

    def create_blurred_background(self, img, target_width, target_height):
        """Create a blurred background from the source image for professional extension"""
        try:
            from PIL import ImageFilter
            
            # Scale image to fill the entire target area (may crop)
            img_ratio = img.width / img.height
            target_ratio = target_width / target_height
            
            if img_ratio > target_ratio:
                # Image is wider - scale by height to fill
                scale_factor = target_height / img.height
                new_height = target_height
                new_width = int(img.width * scale_factor)
            else:
                # Image is taller - scale by width to fill
                scale_factor = target_width / img.width
                new_width = target_width
                new_height = int(img.height * scale_factor)
            
            # Create oversized version for cropping
            oversized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Crop to exact target size from center
            left = (new_width - target_width) // 2
            top = (new_height - target_height) // 2
            right = left + target_width
            bottom = top + target_height
            
            background = oversized.crop((left, top, right, bottom))
            
            # Apply blur for background effect
            background = background.filter(ImageFilter.GaussianBlur(radius=15))
            
            # Reduce opacity by blending with dominant color
            bg_color = self.get_dominant_edge_color(img)
            overlay = Image.new('RGB', (target_width, target_height), bg_color)
            
            # Blend for subtle background effect
            background = Image.blend(background, overlay, 0.3)
            
            return background
            
        except Exception as e:
            self.logger.error(f"Error creating blurred background: {str(e)}")
            # Fallback to solid color
            bg_color = self.get_dominant_edge_color(img)
            return Image.new('RGB', (target_width, target_height), bg_color)

    def extend_image_intelligently(self, img, target_width, target_height):
        """Extend image using intelligent background creation for professional appearance"""
        try:
            # Calculate position and scaling to fit image optimally
            img_ratio = img.width / img.height
            target_ratio = target_width / target_height
            
            # Determine if we should fit by width or height, with professional scaling
            min_fill_ratio = 0.85  # Ensure image takes up at least 85% of the area
            
            if img_ratio > target_ratio:
                # Image is wider - fit by width but ensure good coverage
                scale_factor = target_width / img.width
                new_width = target_width
                new_height = int(img.height * scale_factor)
                
                # If height coverage is too small, scale up more
                height_ratio = new_height / target_height
                if height_ratio < min_fill_ratio:
                    scale_factor = (target_height * min_fill_ratio) / img.height
                    new_height = int(img.height * scale_factor)
                    new_width = int(img.width * scale_factor)
            else:
                # Image is taller - fit by height but ensure good coverage
                scale_factor = target_height / img.height
                new_height = target_height
                new_width = int(img.width * scale_factor)
                
                # If width coverage is too small, scale up more
                width_ratio = new_width / target_width
                if width_ratio < min_fill_ratio:
                    scale_factor = (target_width * min_fill_ratio) / img.width
                    new_width = int(img.width * scale_factor)
                    new_height = int(img.height * scale_factor)
            
            # Resize the image with high quality
            scaled_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create professional background
            if new_width >= target_width and new_height >= target_height:
                # Image is larger than target - crop from center
                left = (new_width - target_width) // 2
                top = (new_height - target_height) // 2
                right = left + target_width
                bottom = top + target_height
                return scaled_img.crop((left, top, right, bottom))
            else:
                # Create blurred background for professional extension
                background = self.create_blurred_background(img, target_width, target_height)
                
                # Center the scaled image on the background
                final_x = (target_width - new_width) // 2
                final_y = (target_height - new_height) // 2
                background.paste(scaled_img, (final_x, final_y))
                
                return background
            
        except Exception as e:
            self.logger.error(f"Error in intelligent image extension: {str(e)}")
            # Fallback to simple centering
            return self.simple_resize_fallback(img, target_width, target_height)

    def simple_resize_fallback(self, img, target_width, target_height):
        """Fallback method for image resizing"""
        # Scale to fit
        img_ratio = img.width / img.height
        target_ratio = target_width / target_height
        
        if img_ratio > target_ratio:
            new_height = target_height
            new_width = int(new_height * img_ratio)
        else:
            new_width = target_width
            new_height = int(new_width / img_ratio)
        
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Center on white background
        final_img = Image.new('RGB', (target_width, target_height), (255, 255, 255))
        x_offset = (target_width - new_width) // 2
        y_offset = (target_height - new_height) // 2
        final_img.paste(resized_img, (x_offset, y_offset))
        
        return final_img

    def load_and_resize_image(self, image_path, target_width, target_height):
        """Load and professionally resize image to exact target dimensions"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Use intelligent extension for professional appearance
                final_img = self.extend_image_intelligently(img, target_width, target_height)
                
                return final_img
                
        except Exception as e:
            self.logger.error(f"Error loading image {image_path}: {str(e)}")
            raise
    
    def get_font(self, size):
        """Get font for text rendering"""
        try:
            # Try to use a system font
            return ImageFont.truetype("/System/Library/Fonts/Arial.ttf", size)
        except:
            try:
                return ImageFont.truetype("arial.ttf", size)
            except:
                # Fallback to default font
                return ImageFont.load_default()
    
    def draw_text_centered(self, draw, text, position, font, fill, max_width=None):
        """Draw text centered at position with optional width constraint"""
        if not text.strip():
            return
            
        # If max_width is specified, wrap text if necessary
        if max_width:
            words = text.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font)
                line_width = bbox[2] - bbox[0]
                
                if line_width <= max_width or not current_line:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
        else:
            lines = [text]
        
        # Calculate total height for vertical centering
        line_height = font.getbbox('Ay')[3] - font.getbbox('Ay')[1]
        total_height = len(lines) * line_height
        
        # Draw each line
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            
            x = position[0] - text_width // 2
            y = position[1] - total_height // 2 + i * line_height
            
            draw.text((x, y), line, font=font, fill=fill)
    
    def generate_cover(self, front_image_path, book_data, output_path, back_image_path=None):
        """Generate complete KDP wraparound cover"""
        try:
            # Get dimensions
            total_width, total_height, spine_width = self.get_cover_dimensions(
                book_data['trim_size'], 
                book_data['page_count']
            )
            
            # Convert to pixels
            width_px = int(total_width * self.DPI)
            height_px = int(total_height * self.DPI)
            spine_width_px = int(spine_width * self.DPI)
            
            trim_width, trim_height = self.TRIM_SIZES[book_data['trim_size']]
            front_width_px = int(trim_width * self.DPI)
            front_height_px = int(trim_height * self.DPI)
            
            bleed_px = int(self.BLEED_MARGIN * self.DPI)
            safe_margin_px = int(self.SAFE_MARGIN * self.DPI)
            
            # Create base cover image
            cover = Image.new('RGB', (width_px, height_px), (255, 255, 255))
            
            # Load and position back cover image (left side of the wraparound)
            if back_image_path:
                back_img = self.load_and_resize_image(
                    back_image_path, 
                    front_width_px, 
                    front_height_px
                )
                back_x = bleed_px
                back_y = bleed_px
                cover.paste(back_img, (back_x, back_y))
            
            # Load and position front cover image (right side of the wraparound)
            front_img = self.load_and_resize_image(
                front_image_path, 
                front_width_px, 
                front_height_px
            )
            
            # Position front cover (right side of the wraparound)
            front_x = width_px - bleed_px - front_width_px
            front_y = bleed_px
            cover.paste(front_img, (front_x, front_y))
            
            # Create drawing context for text
            draw = ImageDraw.Draw(cover)
            
            # Add text to front cover
            self.add_front_cover_text(
                draw, book_data, 
                front_x + safe_margin_px, 
                front_y + safe_margin_px,
                front_width_px - (2 * safe_margin_px),
                front_height_px - (2 * safe_margin_px)
            )
            
            # Add back cover text if provided
            if back_image_path and book_data.get('back_cover_text', '').strip():
                self.add_back_cover_text(
                    draw, book_data,
                    bleed_px + safe_margin_px,
                    bleed_px + safe_margin_px,
                    front_width_px - (2 * safe_margin_px),
                    front_height_px - (2 * safe_margin_px)
                )
            
            # Add spine text
            if book_data['spine_text'].strip():
                self.add_spine_text(
                    draw, book_data,
                    front_x - spine_width_px,
                    front_y,
                    spine_width_px,
                    front_height_px
                )
            
            # Save as temporary image file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                cover.save(tmp_file.name, 'PNG', dpi=(self.DPI, self.DPI))
                temp_image_path = tmp_file.name
            
            # Convert to PDF
            self.create_pdf(temp_image_path, output_path, total_width, total_height)
            
            # Clean up temporary file
            os.unlink(temp_image_path)
            
            self.logger.info(f"Cover generated successfully: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating cover: {str(e)}")
            return False
    
    def add_front_cover_text(self, draw, book_data, x, y, width, height):
        """Add title, subtitle, and author text to front cover"""
        try:
            # Parse color
            color = book_data['text_color']
            if color.startswith('#'):
                color = color[1:]
            color_rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            
            # Calculate positions (divide front cover into sections)
            title_y = y + height // 4
            subtitle_y = title_y + int(book_data['title_font_size'] * 1.5)
            author_y = y + height - height // 4
            
            # Title
            title_font = self.get_font(book_data['title_font_size'])
            self.draw_text_centered(
                draw, book_data['title'], 
                (x + width // 2, title_y), 
                title_font, color_rgb, width
            )
            
            # Subtitle
            if book_data['subtitle'].strip():
                subtitle_font = self.get_font(book_data['title_font_size'] // 2)
                self.draw_text_centered(
                    draw, book_data['subtitle'], 
                    (x + width // 2, subtitle_y), 
                    subtitle_font, color_rgb, width
                )
            
            # Author
            author_font = self.get_font(book_data['author_font_size'])
            self.draw_text_centered(
                draw, book_data['author'], 
                (x + width // 2, author_y), 
                author_font, color_rgb, width
            )
            
        except Exception as e:
            self.logger.error(f"Error adding front cover text: {str(e)}")
    
    def add_spine_text(self, draw, book_data, x, y, width, height):
        """Add rotated text to spine"""
        try:
            if not book_data['spine_text'].strip():
                return
                
            # Calculate appropriate font size for spine
            spine_font_size = max(min(int(width * 0.6), 20), 8)
            font = self.get_font(spine_font_size)
            
            # Parse color
            color = book_data['text_color']
            if color.startswith('#'):
                color = color[1:]
            color_rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            
            # Create temporary image for the text
            temp_img = Image.new('RGBA', (height, width), (0, 0, 0, 0))
            temp_draw = ImageDraw.Draw(temp_img)
            
            # Get text dimensions
            bbox = temp_draw.textbbox((0, 0), book_data['spine_text'], font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center the text in the temporary image
            text_x = (height - text_width) // 2
            text_y = (width - text_height) // 2
            
            # Draw text on temporary image
            temp_draw.text((text_x, text_y), book_data['spine_text'], font=font, fill=color_rgb)
            
            # Rotate the text image 90 degrees counterclockwise
            rotated_img = temp_img.rotate(90, expand=True)
            
            # Calculate position to center the rotated text on the spine
            spine_center_x = x + width // 2
            spine_center_y = y + height // 2
            
            rotated_width, rotated_height = rotated_img.size
            paste_x = spine_center_x - rotated_width // 2
            paste_y = spine_center_y - rotated_height // 2
            
            # Create a copy of the current image to work with
            current_img = draw._image.copy()
            
            # Paste the rotated text
            if rotated_img.mode == 'RGBA':
                current_img.paste(rotated_img, (paste_x, paste_y), rotated_img)
            else:
                current_img.paste(rotated_img, (paste_x, paste_y))
            
            # Update the drawing context
            draw._image.paste(current_img)
            
        except Exception as e:
            self.logger.error(f"Error adding spine text: {str(e)}")
    
    def add_back_cover_text(self, draw, book_data, x, y, width, height):
        """Add description text to back cover"""
        try:
            back_text = book_data.get('back_cover_text', '').strip()
            if not back_text:
                return
            
            # Parse color
            color = book_data['text_color']
            if color.startswith('#'):
                color = color[1:]
            color_rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            
            # Use a smaller font for back cover description
            desc_font_size = max(book_data['author_font_size'] - 4, 12)
            font = self.get_font(desc_font_size)
            
            # Position text in upper portion of back cover
            text_y_start = y + height // 8
            text_area_height = height // 2
            
            # Split text into paragraphs and wrap lines
            paragraphs = back_text.split('\n')
            all_lines = []
            
            for paragraph in paragraphs:
                if paragraph.strip():
                    # Wrap paragraph text
                    words = paragraph.split()
                    lines = []
                    current_line = []
                    
                    for word in words:
                        test_line = ' '.join(current_line + [word])
                        bbox = draw.textbbox((0, 0), test_line, font=font)
                        line_width = bbox[2] - bbox[0]
                        
                        if line_width <= width or not current_line:
                            current_line.append(word)
                        else:
                            if current_line:
                                lines.append(' '.join(current_line))
                            current_line = [word]
                    
                    if current_line:
                        lines.append(' '.join(current_line))
                    
                    all_lines.extend(lines)
                    all_lines.append('')  # Add blank line between paragraphs
            
            # Remove trailing blank line
            if all_lines and all_lines[-1] == '':
                all_lines.pop()
            
            # Calculate line height and total text height
            line_height = font.getbbox('Ay')[3] - font.getbbox('Ay')[1] + 4
            total_text_height = len(all_lines) * line_height
            
            # Center text vertically in the available area
            start_y = text_y_start + (text_area_height - total_text_height) // 2
            
            # Draw each line
            for i, line in enumerate(all_lines):
                if line.strip():  # Skip empty lines
                    bbox = draw.textbbox((0, 0), line, font=font)
                    text_width = bbox[2] - bbox[0]
                    
                    # Center align text
                    line_x = x + (width - text_width) // 2
                    line_y = start_y + i * line_height
                    
                    draw.text((line_x, line_y), line, font=font, fill=color_rgb)
            
        except Exception as e:
            self.logger.error(f"Error adding back cover text: {str(e)}")
    
    def create_pdf(self, image_path, output_path, width_inches, height_inches):
        """Convert image to PDF at 300 DPI"""
        try:
            # Create PDF canvas
            c = canvas.Canvas(output_path, pagesize=(width_inches * inch, height_inches * inch))
            
            # Add image to PDF
            c.drawImage(
                image_path, 
                0, 0, 
                width=width_inches * inch, 
                height=height_inches * inch,
                preserveAspectRatio=True
            )
            
            c.save()
            
        except Exception as e:
            self.logger.error(f"Error creating PDF: {str(e)}")
            raise
