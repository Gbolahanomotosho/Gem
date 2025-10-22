"""
Gem AI Flask Application
Web server for hosting on Render
FIXED VERSION - PDF Generation + Groq Client
"""

from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
import os
from pathlib import Path
import logging
from datetime import datetime
import json
from werkzeug.utils import secure_filename
import base64

from ai_providers import AIProviderManager
from teacher import GemAIGradingSystem
from database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'mp3', 'mp4', 'wav'}

# Create upload folder
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)

# Initialize AI Provider and Grading System
try:
    ai_provider = AIProviderManager()
    grading_system = GemAIGradingSystem(ai_provider=ai_provider)
    db = grading_system.db
    logger.info("Gem AI system initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize system: {e}")
    ai_provider = None
    grading_system = None
    db = None


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    """Serve the main HTML page"""
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({'error': 'index.html not found'}), 404


@app.route('/health')
def health():
    """Health check endpoint"""
    provider_info = ai_provider.get_provider_info() if ai_provider else {'error': 'Not initialized'}
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'ai_provider': provider_info,
        'database': 'connected' if db else 'disconnected'
    })


@app.route('/api/provider-info')
def provider_info():
    """Get AI provider information"""
    if not ai_provider:
        return jsonify({'error': 'AI provider not initialized'}), 500
    return jsonify(ai_provider.get_provider_info())


@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Handle file uploads"""
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    uploaded_files = []
    
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            uploaded_files.append({
                'filename': file.filename,
                'filepath': filepath,
                'size': os.path.getsize(filepath)
            })
    
    return jsonify({
        'success': True,
        'files': uploaded_files,
        'count': len(uploaded_files)
    })


@app.route('/api/grade', methods=['POST'])
def grade_submission():
    """Grade a single or multiple submissions"""
    if not grading_system:
        return jsonify({'error': 'Grading system not initialized'}), 500
    
    try:
        data = request.json
        
        # Extract grading parameters
        exam_name = data.get('examName', 'Exam')
        subject = data.get('subject', 'General')
        total_points = int(data.get('totalPoints', 100))
        question_number = int(data.get('questionNumber', 1))
        model_answer = data.get('modelAnswer', '')
        lecturer_name = data.get('lecturerName', 'Instructor')
        lecturer_email = data.get('lecturerEmail', '')
        file_paths = data.get('filePaths', [])
        
        if not model_answer:
            return jsonify({'error': 'Model answer is required'}), 400
        
        if not file_paths:
            return jsonify({'error': 'No files to grade'}), 400
        
        # Prepare rubric
        rubric = {
            'total_points': total_points,
            'question_number': question_number,
            'subject': subject,
            'difficulty': 'Medium',
            'criteria': {
                'accuracy': 30,
                'completeness': 25,
                'clarity': 20,
                'examples': 15,
                'grammar': 10
            }
        }
        
        # Grade each file
        results = []
        for file_path in file_paths:
            try:
                # Extract text
                extraction_result = grading_system.extract_text_from_file(file_path)
                
                # Prepare student info
                student_info = {
                    'name': Path(file_path).stem.split('_', 2)[-1] if '_' in file_path else Path(file_path).stem,
                    'student_id': f'ST{len(results)+1:03d}',
                    'exam_name': exam_name,
                    'subject': subject
                }
                
                # Grade
                result = grading_system.advanced_ai_grading(
                    extraction_result['text'],
                    model_answer,
                    rubric,
                    student_info
                )
                
                result['filename'] = Path(file_path).name
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error grading {file_path}: {e}")
                results.append({
                    'filename': Path(file_path).name,
                    'error': str(e)
                })
        
        # Calculate statistics
        successful_results = [r for r in results if 'error' not in r]
        if successful_results:
            scores = [r['score'] for r in successful_results]
            percentages = [r['percentage'] for r in successful_results]
            
            statistics = {
                'total_students': len(successful_results),
                'average_score': sum(scores) / len(scores),
                'average_percentage': sum(percentages) / len(percentages),
                'highest_score': max(scores),
                'lowest_score': min(scores),
                'pass_rate': len([p for p in percentages if p >= 60]) / len(percentages) * 100
            }
        else:
            statistics = {}
        
        return jsonify({
            'success': True,
            'results': results,
            'statistics': statistics,
            'ai_provider': ai_provider.active_provider
        })
        
    except Exception as e:
        logger.error(f"Grading error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/grade-text', methods=['POST'])
def grade_text():
    """Grade text directly without file upload"""
    if not grading_system:
        return jsonify({'error': 'Grading system not initialized'}), 500
    
    try:
        data = request.json
        
        student_answer = data.get('studentAnswer', '')
        model_answer = data.get('modelAnswer', '')
        exam_name = data.get('examName', 'Exam')
        subject = data.get('subject', 'General')
        total_points = int(data.get('totalPoints', 100))
        
        if not student_answer or not model_answer:
            return jsonify({'error': 'Both student answer and model answer are required'}), 400
        
        rubric = {
            'total_points': total_points,
            'question_number': 1,
            'subject': subject,
            'difficulty': 'Medium',
            'criteria': {
                'accuracy': 30,
                'completeness': 25,
                'clarity': 20,
                'examples': 15,
                'grammar': 10
            }
        }
        
        student_info = {
            'name': data.get('studentName', 'Student'),
            'student_id': data.get('studentId', 'DEMO'),
            'exam_name': exam_name,
            'subject': subject
        }
        
        result = grading_system.advanced_ai_grading(
            student_answer,
            model_answer,
            rubric,
            student_info
        )
        
        return jsonify({
            'success': True,
            'result': result,
            'ai_provider': ai_provider.active_provider
        })
        
    except Exception as e:
        logger.error(f"Text grading error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    """Generate PDF report for results"""
    if not grading_system:
        return jsonify({'error': 'Grading system not initialized'}), 500
    
    try:
        data = request.json
        results = data.get('results', [])
        exam_config = data.get('exam_config', {})
        
        if not results:
            return jsonify({'error': 'No results to generate report'}), 400
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"Gem_AI_Report_{timestamp}.pdf"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Generate PDF
        grading_system.generate_pdf_report(results, output_path, exam_config)
        
        # Read PDF and convert to base64
        with open(output_path, 'rb') as pdf_file:
            pdf_data = pdf_file.read()
            pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
        
        # Clean up file
        try:
            os.remove(output_path)
        except:
            pass
        
        return jsonify({
            'success': True,
            'pdf_data': pdf_base64,
            'filename': filename
        })
        
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats')
def get_statistics():
    """Get overall system statistics"""
    if not db:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        session = db.get_session()
        from database import Student, Exam, Result
        
        stats = {
            'total_students': session.query(Student).count(),
            'total_exams': session.query(Exam).count(),
            'total_results': session.query(Result).count(),
            'ai_provider': ai_provider.get_provider_info() if ai_provider else None
        }
        
        session.close()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 50MB'}), 413


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('DEBUG', 'False').lower() == 'true')
