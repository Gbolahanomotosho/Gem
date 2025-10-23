"""
Gem AI Flask Application
Web server for hosting on Render
FIXED VERSION - PDF Generation Working with Better Error Handling
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from pathlib import Path
import logging
from datetime import datetime
import json
from werkzeug.utils import secure_filename
import base64
import traceback

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

# Global variables for system components
ai_provider = None
grading_system = None
db = None

def initialize_system():
    """Initialize AI Provider and Grading System with robust error handling"""
    global ai_provider, grading_system, db
    
    try:
        logger.info("Initializing Gem AI system...")
        
        # Initialize AI Provider
        ai_provider = AIProviderManager()
        logger.info(f"AI Provider initialized: {ai_provider.active_provider}")
        
        # Initialize Database
        db = Database()
        logger.info("Database initialized successfully")
        
        # Initialize Grading System with explicit provider
        grading_system = GemAIGradingSystem(ai_provider=ai_provider, db_path="gem_ai.db")
        logger.info("Grading system initialized successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"CRITICAL: Failed to initialize system: {e}")
        logger.error(traceback.format_exc())
        
        # Try to initialize with minimal components
        try:
            logger.warning("Attempting minimal initialization...")
            ai_provider = AIProviderManager()
            grading_system = GemAIGradingSystem(ai_provider=ai_provider)
            db = grading_system.db if hasattr(grading_system, 'db') else None
            logger.info("Minimal initialization successful")
            return True
        except Exception as e2:
            logger.error(f"Minimal initialization also failed: {e2}")
            return False

# Initialize system on startup
system_initialized = initialize_system()

if not system_initialized:
    logger.error("="*80)
    logger.error("WARNING: System initialization failed!")
    logger.error("PDF generation and grading features may not work")
    logger.error("="*80)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def ensure_system_initialized():
    """Ensure system is initialized, try to reinitialize if needed"""
    global grading_system, ai_provider, db
    
    if grading_system is None:
        logger.warning("Grading system not initialized, attempting reinitialization...")
        success = initialize_system()
        if not success:
            raise RuntimeError("Failed to initialize grading system")
    
    return grading_system is not None


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
    try:
        ensure_system_initialized()
        provider_info = ai_provider.get_provider_info() if ai_provider else {'error': 'Not initialized'}
        
        return jsonify({
            'status': 'healthy' if grading_system else 'degraded',
            'timestamp': datetime.now().isoformat(),
            'ai_provider': provider_info,
            'database': 'connected' if db else 'disconnected',
            'grading_system': 'initialized' if grading_system else 'not initialized',
            'system_ready': grading_system is not None
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/provider-info')
def provider_info():
    """Get AI provider information"""
    try:
        ensure_system_initialized()
        if not ai_provider:
            return jsonify({'error': 'AI provider not initialized'}), 500
        return jsonify(ai_provider.get_provider_info())
    except Exception as e:
        logger.error(f"Provider info error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    """Generate PDF report for results - FIXED VERSION with Better Error Handling"""
    try:
        # Ensure system is initialized
        if not ensure_system_initialized():
            logger.error("Cannot generate report: System not initialized")
            return jsonify({
                'error': 'Grading system not initialized. Please contact administrator.',
                'details': 'The AI grading system failed to start properly.'
            }), 500
        
        if grading_system is None:
            logger.error("Grading system is None after initialization check")
            return jsonify({
                'error': 'Grading system is not available',
                'details': 'System initialization failed'
            }), 500
        
        # Get request data
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        results = data.get('results', [])
        exam_config = data.get('exam_config', {})
        
        if not results:
            return jsonify({'error': 'No results to generate report'}), 400
        
        logger.info(f"Generating PDF report for {len(results)} results...")
        
        # Normalize results to ensure all required fields exist
        normalized_results = []
        for idx, result in enumerate(results):
            try:
                # Make sure student_info exists with all required fields
                if 'student_info' not in result:
                    result['student_info'] = {
                        'name': result.get('studentName', f'Student {idx+1}'),
                        'student_id': result.get('studentId', f'ST{idx+1:03d}'),
                        'exam_name': exam_config.get('exam_name', 'Exam'),
                        'subject': exam_config.get('subject', 'Subject')
                    }
                
                # Ensure all required fields exist
                normalized_result = {
                    'student_info': result.get('student_info', {}),
                    'score': result.get('score', 0),
                    'total_points': result.get('totalPoints', exam_config.get('rubric', {}).get('total_points', 100)),
                    'percentage': result.get('percentage', 0),
                    'grade': result.get('grade', 'N/A'),
                    'feedback': result.get('feedback', 'No feedback available'),
                    'strengths': result.get('strengths', []),
                    'improvements': result.get('improvements', []),
                    'breakdown': result.get('breakdown', ''),
                    'corrections': result.get('corrections', ''),
                    'recommendations': result.get('recommendations', '')
                }
                
                normalized_results.append(normalized_result)
                
            except Exception as e:
                logger.error(f"Error normalizing result {idx}: {e}")
                # Continue with other results
                continue
        
        if not normalized_results:
            return jsonify({'error': 'No valid results to generate report'}), 400
        
        # Ensure exam_config has rubric
        if 'rubric' not in exam_config:
            exam_config['rubric'] = {
                'total_points': 100
            }
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"Gem_AI_Report_{timestamp}.pdf"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        logger.info(f"Generating PDF at: {output_path}")
        
        # Generate PDF using the grading system
        try:
            grading_system.generate_pdf_report(normalized_results, output_path, exam_config)
            logger.info(f"PDF generated successfully: {output_path}")
        except Exception as pdf_error:
            logger.error(f"PDF generation error: {pdf_error}")
            logger.error(traceback.format_exc())
            return jsonify({
                'error': f'Failed to generate PDF: {str(pdf_error)}',
                'details': 'PDF generation failed during report creation'
            }), 500
        
        # Check if file was created
        if not os.path.exists(output_path):
            logger.error(f"PDF file not found after generation: {output_path}")
            return jsonify({
                'error': 'PDF file was not created',
                'details': 'Report generation completed but file is missing'
            }), 500
        
        # Read PDF and convert to base64
        try:
            with open(output_path, 'rb') as pdf_file:
                pdf_data = pdf_file.read()
                pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            
            logger.info(f"PDF encoded successfully, size: {len(pdf_base64)} bytes")
            
        except Exception as read_error:
            logger.error(f"Error reading PDF file: {read_error}")
            return jsonify({
                'error': f'Failed to read PDF: {str(read_error)}',
                'details': 'PDF was created but could not be read'
            }), 500
        
        # Clean up file
        try:
            os.remove(output_path)
            logger.info(f"Temporary PDF file removed: {output_path}")
        except Exception as cleanup_error:
            logger.warning(f"Failed to remove temporary file: {cleanup_error}")
        
        return jsonify({
            'success': True,
            'pdf_data': pdf_base64,
            'filename': filename,
            'message': 'PDF generated successfully'
        })
        
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': f'Failed to generate report: {str(e)}',
            'details': 'Unexpected error during report generation',
            'traceback': traceback.format_exc()
        }), 500


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
    try:
        ensure_system_initialized()
        
        if not grading_system:
            return jsonify({'error': 'Grading system not initialized'}), 500
        
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
            'ai_provider': ai_provider.active_provider if ai_provider else 'unknown'
        })
        
    except Exception as e:
        logger.error(f"Grading error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/grade-text', methods=['POST'])
def grade_text():
    """Grade text directly without file upload"""
    try:
        ensure_system_initialized()
        
        if not grading_system:
            return jsonify({'error': 'Grading system not initialized'}), 500
        
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
            'ai_provider': ai_provider.active_provider if ai_provider else 'unknown'
        })
        
    except Exception as e:
        logger.error(f"Text grading error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats')
def get_statistics():
    """Get overall system statistics"""
    try:
        ensure_system_initialized()
        
        if not db:
            return jsonify({'error': 'Database not available'}), 500
        
        session = db.get_session()
        from database import Student, Exam, Result
        
        stats = {
            'total_students': session.query(Student).count(),
            'total_exams': session.query(Exam).count(),
            'total_results': session.query(Result).count(),
            'ai_provider': ai_provider.get_provider_info() if ai_provider else None,
            'system_status': 'operational' if grading_system else 'degraded'
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
    logger.error(traceback.format_exc())
    return jsonify({
        'error': 'Internal server error',
        'details': str(error)
    }), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    
    # Final check before starting server
    if not system_initialized or grading_system is None:
        logger.error("="*80)
        logger.error("CRITICAL WARNING: System not properly initialized!")
        logger.error("The application will start but may not function correctly.")
        logger.error("="*80)
    else:
        logger.info("="*80)
        logger.info("Gem AI System Ready!")
        logger.info(f"AI Provider: {ai_provider.active_provider}")
        logger.info(f"Database: {'Connected' if db else 'Disconnected'}")
        logger.info("="*80)
    
    app.run(host='0.0.0.0', port=port, debug=os.getenv('DEBUG', 'False').lower() == 'true')
