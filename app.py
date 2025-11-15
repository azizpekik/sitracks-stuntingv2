from flask import Flask, request, render_template, jsonify, send_file
import os
from excel_to_json_anak import process_excel_to_json, validate_template_compliance

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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

            # Build appropriate message based on validation results
            message = 'File uploaded and processed successfully'
            if validation_result.get('warnings'):
                message += f' (dengan {len(validation_result["warnings"])} peringatan)'

            return jsonify({
                'success': True,
                'message': message,
                'data': result
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)