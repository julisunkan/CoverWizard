# Overview

KDP Cover Creator is a Flask-based web application that generates professional KDP (Kindle Direct Publishing) compliant wraparound book covers. The application creates complete PDF covers with front cover, spine, and back cover sections, including proper bleed margins and spine calculations based on page count and trim size specifications. Users can upload separate front and back cover images and customize various aspects of their book covers including dimensions, colors, and text elements.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5 dark theme for responsive UI
- **Styling**: Custom CSS with Font Awesome icons for enhanced visual appeal
- **Form Handling**: Multi-part form uploads with client-side validation
- **User Feedback**: Flash message system for error handling and success notifications

## Backend Architecture
- **Framework**: Flask web framework with route-based request handling
- **File Processing**: PIL (Python Imaging Library) for image manipulation and resizing
- **PDF Generation**: ReportLab library for creating KDP-compliant PDF outputs
- **File Management**: Secure file upload handling with extension validation and size limits
- **Cover Generation Logic**: Dedicated CoverGenerator class handling KDP specifications including:
  - Complete wraparound cover layout (back + spine + front)
  - Standard trim sizes (5x8, 6x9, 8.5x11, etc.)
  - Automatic spine width calculation based on page count
  - Bleed margin compliance (0.125" standard)
  - Safe text margin enforcement (0.25" additional)
  - Front and back cover image support with optional back cover
  - Text overlay system for front cover and back cover descriptions
  - Rotated spine text with proper centering
  - 300 DPI output resolution

## Data Storage
- **File Storage**: Local filesystem for uploaded images and generated covers
- **Session Management**: Flask sessions with configurable secret key
- **Temporary Files**: System temp directory for intermediate processing

## Configuration Management
- **Environment Variables**: SESSION_SECRET for security
- **File Limits**: 16MB maximum upload size with multiple image format support
- **Directory Structure**: Organized static folders for uploads and outputs

# External Dependencies

## Core Libraries
- **Flask**: Web framework for request handling and templating
- **PIL (Pillow)**: Image processing and manipulation
- **ReportLab**: PDF generation with precise layout control
- **Werkzeug**: Secure filename handling and utilities

## Frontend Dependencies
- **Bootstrap 5**: CSS framework with dark theme
- **Font Awesome 6.0**: Icon library for UI enhancement
- **Replit Bootstrap Theme**: Custom dark theme integration

## File Format Support
- **Input Formats**: PNG, JPG, JPEG, GIF, BMP, TIFF
- **Output Format**: PDF with KDP compliance standards

## System Requirements
- **Python Environment**: Standard library modules (os, logging, tempfile, uuid)
- **File System**: Read/write access for upload and output directories