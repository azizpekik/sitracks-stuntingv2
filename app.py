from flask import Flask, request, render_template, jsonify, send_file, session
from flask_session import Session
import os
from datetime import datetime
from excel_to_json_anak import process_excel_to_json, validate_template_compliance
from export_analisis import export_analisis_from_json

app = Flask(__name__)

# Configuration for both development and production
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sitrek_stunting_secret_key_2024')

# Use file-based session to avoid cookie size limit
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = 'flask_sessions'
app.config['SESSION_FILE_THRESHOLD'] = 500
app.config['SESSION_PERMANENT'] = False

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('flask_sessions', exist_ok=True)

# Initialize session
sess = Session(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file selected'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if file and file.filename.endswith(('.xlsx', '.xls')):
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Validate template compliance first
            is_valid, validation_result = validate_template_compliance(filepath)

            if not is_valid:
                # Template validation failed - return detailed error
                return jsonify({
                    'success': False,
                    'message': 'Template validation failed',
                    'validation_error': True,
                    'validation': validation_result,
                    'error': f'Template tidak sesuai: {"; ".join(validation_result.get("errors", ["Unknown error"]))}'
                }), 400

            # Process Excel file to JSON
            result = process_excel_to_json(filepath)

            # Add validation information to the result
            result['validation'] = validation_result

            # Store processed data in session for export functionality
            session['processed_data'] = result
            session['upload_timestamp'] = datetime.now().isoformat()

            # Build appropriate message based on validation results
            message = 'File uploaded and processed successfully'
            if validation_result.get('warnings'):
                message += f' (dengan {len(validation_result["warnings"])} peringatan)'

            return jsonify({
                'success': True,
                'message': message,
                'data': result,
                'has_export_data': True
            })
        else:
            return jsonify({'error': 'Please upload an Excel file (.xlsx or .xls)'}), 400

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/files')
def list_files():
    try:
        files = []
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if filename.endswith(('.xlsx', '.xls')):
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                files.append({
                    'name': filename,
                    'size': os.path.getsize(file_path)
                })
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/health')
def health():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': 'SiTrack Stunting',
        'version': '1.0.0'
    })

@app.route('/download-template')
def download_template():
    """
    Download template reference file
    """
    try:
        template_path = os.path.join('data test', 'Data Test.xlsx')
        if os.path.exists(template_path):
            return send_file(template_path,
                           as_attachment=True,
                           download_name='Template_Data_Anak.xlsx',
                           mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            return jsonify({'error': 'Template file not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Error downloading template: {str(e)}'}), 500

@app.route('/export-analisis')
def export_analisis():
    """
    Export analisis data pertumbuhan anak ke Excel dengan format analisis
    """
    try:
        # Check if we have processed data in session
        if 'processed_data' not in session:
            return jsonify({'error': 'Tidak ada data untuk di-export. Silakan upload file terlebih dahulu.'}), 400

        processed_data = session['processed_data']

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Analisis_Pertumbuhan_Anak_{timestamp}.xlsx"

        # Export to Excel using the export function
        success, result = export_analisis_from_json(processed_data, filename)

        if success:
            # Return the generated file for download
            return send_file(result,
                           as_attachment=True,
                           download_name=filename,
                           mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            return jsonify({'error': f'Gagal membuat file export: {result}'}), 500

    except Exception as e:
        return jsonify({'error': f'Error during export: {str(e)}'}), 500

@app.route('/check-export-data')
def check_export_data():
    """
    Check if there's data available for export
    """
    try:
        has_data = 'processed_data' in session
        upload_time = session.get('upload_timestamp', None)

        # Get some statistics about the data if available
        stats = {}
        if has_data:
            data = session.get('processed_data', {})
            stats = {
                'total_children': data.get('total_children', 0),
                'total_periods': data.get('total_periods', 0),
                'file_name': data.get('file_name', 'Unknown'),
                'format_type': data.get('format_type', 'Unknown')
            }

        return jsonify({
            'has_export_data': has_data,
            'upload_timestamp': upload_time,
            'stats': stats
        })

    except Exception as e:
        return jsonify({'error': f'Error checking export data: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    host = os.environ.get('HOST', '0.0.0.0')
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'

    app.run(debug=debug_mode, host=host, port=port)