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
            # Validate file upload
            if 'cover_image' not in request.files:
                flash('No file selected', 'error')
                return redirect(request.url)
            
            file = request.files['cover_image']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)
            
            if not allowed_file(file.filename):
                flash('Invalid file type. Please upload PNG, JPG, JPEG, GIF, BMP, or TIFF files.', 'error')
                return redirect(request.url)
            
            # Save uploaded file
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            # Get form data
            book_data = {
                'title': request.form.get('title', '').strip(),
                'subtitle': request.form.get('subtitle', '').strip(),
                'author': request.form.get('author', '').strip(),
                'spine_text': request.form.get('spine_text', '').strip(),
                'page_count': int(request.form.get('page_count', 100)),
                'trim_size': request.form.get('trim_size', '6x9'),
                'title_font_size': int(request.form.get('title_font_size', 48)),
                'author_font_size': int(request.form.get('author_font_size', 24)),
                'text_color': request.form.get('text_color', '#FFFFFF')
            }
            
            # Validate required fields
            if not book_data['title'] or not book_data['author']:
                flash('Title and Author are required fields', 'error')
                os.remove(file_path)  # Clean up uploaded file
                return redirect(request.url)
            
            # Generate cover
            generator = CoverGenerator()
            output_filename = f"cover_{uuid.uuid4()}.pdf"
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            
            success = generator.generate_cover(
                front_image_path=file_path,
                book_data=book_data,
                output_path=output_path
            )
            
            # Clean up uploaded file
            os.remove(file_path)
            
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
