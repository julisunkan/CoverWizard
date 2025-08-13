import os
import logging
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import uuid
from cover_generator import CoverGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Use INFO for production, DEBUG for development
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "your-secret-key-here")

# Disable debug mode for production
app.debug = os.environ.get("FLASK_ENV") == "development"

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

# Configure request timeout and buffer size for large uploads
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year for static files

def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def cleanup_files(file_paths):
    """Safely remove uploaded files"""
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logging.error(f"Error removing file {file_path}: {str(e)}")

@app.route('/', methods=['GET', 'POST'])
def index():
    """Main page with form for cover generation"""
    if request.method == 'POST':
        front_file_path = None
        back_file_path = None
        
        try:
            # Check content length first to avoid parsing large requests
            content_length = request.content_length
            if content_length and content_length > MAX_FILE_SIZE * 2:  # Allow for form data overhead
                flash('Request too large. Please reduce file sizes.', 'error')
                return redirect(request.url)
            
            # Check content type and handle potential errors
            if not request.content_type or not request.content_type.startswith('multipart/form-data'):
                flash('Invalid request format. Please use the form to upload files.', 'error')
                return redirect(request.url)
            
            # Check if request has files - with proper error handling and timeout protection
            try:
                files = request.files
                form_data = request.form
            except (UnicodeDecodeError, ValueError) as e:
                logging.error(f"Error parsing form data: {str(e)}")
                flash('Invalid form data encoding. Please try again.', 'error')
                return redirect(request.url)
            except Exception as e:
                logging.error(f"Error accessing request data: {str(e)}")
                flash('Error processing request. Please try again with smaller files.', 'error')
                return redirect(request.url)
            
            if not files:
                flash('No files uploaded', 'error')
                return redirect(request.url)
            
            # Validate front cover upload
            if 'front_cover_image' not in files:
                flash('No front cover image selected', 'error')
                return redirect(request.url)
            
            front_file = files['front_cover_image']
            if not front_file or front_file.filename == '':
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
            if 'back_cover_image' in files:
                back_file = files['back_cover_image']
                if back_file and back_file.filename and back_file.filename != '':
                    if not allowed_file(back_file.filename):
                        flash('Invalid file type for back cover. Please upload PNG, JPG, JPEG, GIF, BMP, or TIFF files.', 'error')
                        if os.path.exists(front_file_path):
                            os.remove(front_file_path)  # Clean up front cover
                        return redirect(request.url)
                    
                    # Save back cover file
                    back_filename = secure_filename(back_file.filename or "back_upload")
                    unique_back_filename = f"{uuid.uuid4()}_back_{back_filename}"
                    back_file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_back_filename)
                    back_file.save(back_file_path)
            
            # Get form data with error handling (already accessed above)
            try:
                book_data = {
                    'title': form_data.get('title', '').strip(),
                    'subtitle': form_data.get('subtitle', '').strip(),
                    'author': form_data.get('author', '').strip(),
                    'spine_text': form_data.get('spine_text', '').strip(),
                    'back_cover_text': form_data.get('back_cover_text', '').strip(),
                    'page_count': int(form_data.get('page_count', 100)),
                    'trim_size': form_data.get('trim_size', '6x9'),
                    'title_font_size': int(form_data.get('title_font_size', 48)),
                    'author_font_size': int(form_data.get('author_font_size', 24)),
                    'text_color': form_data.get('text_color', '#FFFFFF')
                }
            except (ValueError, TypeError) as e:
                logging.error(f"Error processing form data: {str(e)}")
                flash('Invalid form data. Please check your inputs and try again.', 'error')
                cleanup_files([front_file_path, back_file_path])
                return redirect(request.url)
            
            # Validate required fields
            if not book_data['title'] or not book_data['author']:
                flash('Title and Author are required fields', 'error')
                # Clean up uploaded files
                cleanup_files([front_file_path, back_file_path])
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
            
            # Always clean up uploaded files
            cleanup_files([front_file_path, back_file_path])
            
            if success:
                flash('Cover generated successfully!', 'success')
                return send_file(output_path, as_attachment=True, download_name=f"{book_data['title']}_cover.pdf")
            else:
                flash('Error generating cover. Please try again.', 'error')
                return redirect(request.url)
                
        except Exception as e:
            logging.error(f"Error processing cover generation: {str(e)}")
            # Clean up any uploaded files on error
            cleanup_files([front_file_path, back_file_path])
            
            flash(f'An error occurred while processing your request. Please try again.', 'error')
            return redirect(request.url)
    
    return render_template('index.html')

@app.route('/manifest.json')
def manifest():
    """Serve PWA manifest file"""
    try:
        return send_file('static/manifest.json', mimetype='application/json')
    except Exception as e:
        logging.error(f"Error serving manifest: {str(e)}")
        return "Manifest not found", 404

@app.route('/sw.js')
def service_worker():
    """Serve service worker file"""
    try:
        return send_file('static/sw.js', mimetype='application/javascript')
    except Exception as e:
        logging.error(f"Error serving service worker: {str(e)}")
        return "Service worker not found", 404

@app.route('/offline')
def offline():
    """Serve offline page"""
    try:
        return send_file('static/offline.html')
    except Exception as e:
        logging.error(f"Error serving offline page: {str(e)}")
        return "Offline page not found", 404

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    logging.warning("File upload too large")
    flash('File is too large. Maximum size is 16MB per file.', 'error')
    return redirect(url_for('index'))

@app.errorhandler(400)
def bad_request(e):
    """Handle bad request errors"""
    logging.warning(f"Bad request: {str(e)}")
    flash('Invalid request. Please check your form data and try again.', 'error')
    return redirect(url_for('index'))

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    logging.error(f"Internal server error: {str(e)}")
    flash('An internal error occurred. Please try again.', 'error')
    return redirect(url_for('index'))

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle any uncaught exceptions"""
    logging.error(f"Uncaught exception: {str(e)}")
    flash('An unexpected error occurred. Please try again.', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
