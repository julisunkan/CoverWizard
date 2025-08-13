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
    
    def load_and_resize_image(self, image_path, target_width, target_height):
        """Load and resize image to fit target dimensions while maintaining aspect ratio"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Calculate scaling to fit within target dimensions
                img_ratio = img.width / img.height
                target_ratio = target_width / target_height
                
                if img_ratio > target_ratio:
                    # Image is wider, scale by height
                    new_height = target_height
                    new_width = int(new_height * img_ratio)
                else:
                    # Image is taller, scale by width
                    new_width = target_width
                    new_height = int(new_width / img_ratio)
                
                # Resize image
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Create new image with target dimensions and center the resized image
                final_img = Image.new('RGB', (target_width, target_height), (255, 255, 255))
                x_offset = (target_width - new_width) // 2
                y_offset = (target_height - new_height) // 2
                final_img.paste(resized_img, (x_offset, y_offset))
                
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
    
    def generate_cover(self, front_image_path, book_data, output_path):
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
            
            # Load and position front cover image
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
                
            # Create temporary image for rotated text
            spine_font_size = min(int(width * 0.8), 24)
            font = self.get_font(spine_font_size)
            
            # Parse color
            color = book_data['text_color']
            if color.startswith('#'):
                color = color[1:]
            color_rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            
            # Create text image
            text_img = Image.new('RGBA', (height, width), (0, 0, 0, 0))
            text_draw = ImageDraw.Draw(text_img)
            
            # Draw text horizontally first
            bbox = text_draw.textbbox((0, 0), book_data['spine_text'], font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            text_x = (height - text_width) // 2
            text_y = (width - text_height) // 2
            
            text_draw.text((text_x, text_y), book_data['spine_text'], font=font, fill=color_rgb)
            
            # Rotate 90 degrees counterclockwise
            rotated_text = text_img.rotate(90, expand=True)
            
            # Paste onto main cover
            cover_img = Image.new('RGBA', draw.im.size, (0, 0, 0, 0))
            cover_img.paste(rotated_text, (x, y), rotated_text)
            
            # Convert back to RGB and paste
            cover_rgb = Image.new('RGB', draw.im.size, (255, 255, 255))
            cover_rgb.paste(draw.im, (0, 0))
            cover_rgb.paste(cover_img, (0, 0), cover_img)
            
            # Update the draw object
            draw.im.paste(cover_rgb, (0, 0))
            
        except Exception as e:
            self.logger.error(f"Error adding spine text: {str(e)}")
    
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
