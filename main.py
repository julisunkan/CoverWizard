import os
import logging
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import uuid
from cover_generator import CoverGenerator

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "your-secret-key-here")

# Configuration
UPLOAD_FOLDER = 'static/uploads'
OUTPUT_FOLDER = 'static/output'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    """Main page with form for cover generation"""
    if request.method == 'POST':
        try:
            # Validate front cover upload
            if 'front_cover_image' not in request.files:
                flash('No front cover image selected', 'error')
                return redirect(request.url)
            
            front_file = request.files['front_cover_image']
            if front_file.filename == '':
                flash('No front cover image selected', 'error')
                return redirect(request.url)
            
            if not allowed_file(front_file.filename):
                flash('Invalid file type for front cover. Please upload PNG, JPG, JPEG, GIF, BMP, or TIFF files.', 'error')
                return redirect(request.url)
            
            # Save front cover file
            front_filename = secure_filename(front_file.filename or "front_upload")
            unique_front_filename = f"{uuid.uuid4()}_front_{front_filename}"
            front_file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_front_filename)
            front_file.save(front_file_path)
            
            # Handle back cover upload (optional)
            back_file_path = None
            if 'back_cover_image' in request.files:
                back_file = request.files['back_cover_image']
                if back_file.filename and back_file.filename != '':
                    if not allowed_file(back_file.filename):
                        flash('Invalid file type for back cover. Please upload PNG, JPG, JPEG, GIF, BMP, or TIFF files.', 'error')
                        os.remove(front_file_path)  # Clean up front cover
                        return redirect(request.url)
                    
                    # Save back cover file
                    back_filename = secure_filename(back_file.filename or "back_upload")
                    unique_back_filename = f"{uuid.uuid4()}_back_{back_filename}"
                    back_file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_back_filename)
                    back_file.save(back_file_path)
            
            # Get form data
            book_data = {
                'title': request.form.get('title', '').strip(),
                'subtitle': request.form.get('subtitle', '').strip(),
                'author': request.form.get('author', '').strip(),
                'spine_text': request.form.get('spine_text', '').strip(),
                'back_cover_text': request.form.get('back_cover_text', '').strip(),
                'page_count': int(request.form.get('page_count', 100)),
                'trim_size': request.form.get('trim_size', '6x9'),
                'title_font_size': int(request.form.get('title_font_size', 48)),
                'author_font_size': int(request.form.get('author_font_size', 24)),
                'text_color': request.form.get('text_color', '#FFFFFF')
            }
            
            # Validate required fields
            if not book_data['title'] or not book_data['author']:
                flash('Title and Author are required fields', 'error')
                os.remove(front_file_path)  # Clean up uploaded files
                if back_file_path:
                    os.remove(back_file_path)
                return redirect(request.url)
            
            # Generate cover
            generator = CoverGenerator()
            output_filename = f"cover_{uuid.uuid4()}.pdf"
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            
            success = generator.generate_cover(
                front_image_path=front_file_path,
                back_image_path=back_file_path,
                book_data=book_data,
                output_path=output_path
            )
            
            # Clean up uploaded files
            os.remove(front_file_path)
            if back_file_path:
                os.remove(back_file_path)
            
            if success:
                flash('Cover generated successfully!', 'success')
                return send_file(output_path, as_attachment=True, download_name=f"{book_data['title']}_cover.pdf")
            else:
                flash('Error generating cover. Please try again.', 'error')
                return redirect(request.url)
                
        except Exception as e:
            logging.error(f"Error processing cover generation: {str(e)}")
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template('index.html')

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    flash('File is too large. Maximum size is 16MB.', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
