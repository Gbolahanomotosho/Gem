"""
Gem AI Flask Application
Web server for hosting on Render
UPDATED VERSION - Added Model Answer Upload Support
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

# CRITICAL: Load environment variables from .env file FIRST
from dotenv import load_dotenv
load_dotenv()  # This loads your .env file with API keys

from ai_providers import AIProviderManager
from teacher import GemAIGradingSystem
from database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# VERIFY API KEYS ARE LOADED
logger.info("="*80)
logger.info("🔍 CHECKING ENVIRONMENT VARIABLES...")
api_keys_found = []
for key in ['OPENAI_API_KEY', 'GEMINI_API_KEY', 'ANTHROPIC_API_KEY', 'GROQ_API_KEY', 'GROK_API_KEY', 'COHERE_API_KEY']:
    value = os.getenv(key)
    if value:
        masked_value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
        logger.info(f"✅ {key} is set: {masked_value}")
        api_keys_found.append(key)
    else:
        logger.info(f"❌ {key} is NOT set")

if not api_keys_found:
    logger.error("⚠️  WARNING: NO API KEYS FOUND!")
    logger.error("⚠️  AI grading will use FALLBACK mode (generic feedback)")
    logger.error("⚠️  Please set at least one AI API key in your .env file or environment")
else:
    logger.info(f"✅ Found {len(api_keys_found)} API key(s): {', '.join(api_keys_found)}")
logger.info("="*80)

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
        logger.info("="*80)
        logger.info("🚀 Initializing Gem AI system...")
        
        # Initialize AI Provider
        try:
            ai_provider = AIProviderManager()
            provider_info = ai_provider.get_provider_info()
            logger.info(f"✅ AI Provider initialized: {ai_provider.active_provider}")
            logger.info(f"✅ Provider Info: {provider_info}")
            
            if not provider_info.get('is_initialized'):
                logger.error("❌ AI Provider failed to initialize properly!")
                logger.error("❌ Grading will use FALLBACK mode")
            
        except Exception as e:
            logger.error(f"❌ CRITICAL: AI Provider initialization failed: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            logger.error("❌ System will continue but grading will use FALLBACK mode")
            ai_provider = None
        
        # Initialize Database
        try:
            db = Database()
            logger.info("✅ Database initialized successfully")
        except Exception as e:
            logger.error(f"⚠️  Database initialization warning: {e}")
            db = None
        
        # Initialize Grading System
        try:
            grading_system = GemAIGradingSystem(ai_provider=ai_provider, db_path="sqlite:///gem_ai.db")
            logger.info("✅ Grading system initialized successfully")
        except Exception as e:
            logger.error(f"❌ CRITICAL: Grading system initialization failed: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            grading_system = None
        
        logger.info("="*80)
        
        if grading_system and ai_provider:
            logger.info("✅✅✅ GEM AI SYSTEM READY - REAL AI GRADING ENABLED ✅✅✅")
        elif grading_system and not ai_provider:
            logger.warning("⚠️⚠️⚠️  GEM AI RUNNING IN FALLBACK MODE - GENERIC FEEDBACK ⚠️⚠️⚠️")
        else:
            logger.error("❌❌❌ GEM AI SYSTEM FAILED TO INITIALIZE ❌❌❌")
        
        logger.info("="*80)
        
        return grading_system is not None
        
    except Exception as e:
        logger.error(f"❌ CRITICAL: System initialization completely failed: {e}")
        logger.error(traceback.format_exc())
        return False

# Initialize system on startup
system_initialized = initialize_system()

if not system_initialized:
    logger.error("="*80)
    logger.error("❌ WARNING: System initialization failed!")
    logger.error("❌ PDF generation and grading features may not work")
    logger.error("="*80)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def ensure_system_initialized():
    """Ensure system is initialized, try to reinitialize if needed"""
    global grading_system, ai_provider, db
    
    if grading_system is None:
        logger.warning("⚠️  Grading system not initialized, attempting reinitialization...")
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
        
        # Detailed health status
        health_status = {
            'status': 'healthy' if grading_system else 'degraded',
            'timestamp': datetime.now().isoformat(),
            'ai_provider': provider_info,
            'database': 'connected' if db else 'disconnected',
            'grading_system': 'initialized' if grading_system else 'not initialized',
            'system_ready': grading_system is not None,
            'ai_grading_enabled': ai_provider is not None and ai_provider.client is not None,
            'fallback_mode': ai_provider is None or ai_provider.client is None
        }
        
        if health_status['fallback_mode']:
            health_status['warning'] = 'AI grading is in FALLBACK mode - feedback will be generic. Please set an AI API key.'
        
        return jsonify(health_status)
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
            return jsonify({
                'error': 'AI provider not initialized',
                'fallback_mode': True,
                'message': 'System will use similarity-based grading with generic feedback'
            }), 500
        
        info = ai_provider.get_provider_info()
        info['fallback_mode'] = False
        return jsonify(info)
    except Exception as e:
        logger.error(f"Provider info error: {e}")
        return jsonify({'error': str(e), 'fallback_mode': True}), 500


# NEW: Extract Model Answer from Uploaded File
@app.route('/api/extract-model-answer', methods=['POST'])
def extract_model_answer():
    """Extract text from model answer file"""
    try:
        if not ensure_system_initialized():
            return jsonify({'error': 'Grading system not initialized'}), 500
        
        data = request.json
        file_path = data.get('filePath')
        
        if not file_path:
            return jsonify({'error': 'File path is required'}), 400
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        logger.info(f"📄 Extracting model answer from: {file_path}")
        
        # Extract text using grading system
        extraction_result = grading_system.extract_text_from_file(file_path)
        
        logger.info(f"✅ Extracted {len(extraction_result['text'])} characters from model answer file")
        
        return jsonify({
            'success': True,
            'text': extraction_result['text'],
            'extraction_method': extraction_result['extraction_method'],
            'confidence': extraction_result['confidence'],
            'file_type': extraction_result['file_type']
        })
        
    except Exception as e:
        logger.error(f"❌ Model answer extraction error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': f'Failed to extract model answer: {str(e)}',
            'details': 'Could not process the model answer file'
        }), 500


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
        
        logger.info(f"📄 Generating PDF report for {len(results)} results...")
        
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
        
        logger.info(f"📄 Generating PDF at: {output_path}")
        
        # Generate PDF using the grading system
        try:
            grading_system.generate_pdf_report(normalized_results, output_path, exam_config)
            logger.info(f"✅ PDF generated successfully: {output_path}")
        except Exception as pdf_error:
            logger.error(f"❌ PDF generation error: {pdf_error}")
            logger.error(traceback.format_exc())
            return jsonify({
                'error': f'Failed to generate PDF: {str(pdf_error)}',
                'details': 'PDF generation failed during report creation'
            }), 500
        
        # Check if file was created
        if not os.path.exists(output_path):
            logger.error(f"❌ PDF file not found after generation: {output_path}")
            return jsonify({
                'error': 'PDF file was not created',
                'details': 'Report generation completed but file is missing'
            }), 500
        
        # Read PDF and convert to base64
        try:
            with open(output_path, 'rb') as pdf_file:
                pdf_data = pdf_file.read()
                pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            
            logger.info(f"✅ PDF encoded successfully, size: {len(pdf_base64)} bytes")
            
        except Exception as read_error:
            logger.error(f"❌ Error reading PDF file: {read_error}")
            return jsonify({
                'error': f'Failed to read PDF: {str(read_error)}',
                'details': 'PDF was created but could not be read'
            }), 500
        
        # Clean up file
        try:
            os.remove(output_path)
            logger.info(f"🗑️  Temporary PDF file removed: {output_path}")
        except Exception as cleanup_error:
            logger.warning(f"⚠️  Failed to remove temporary file: {cleanup_error}")
        
        return jsonify({
            'success': True,
            'pdf_data': pdf_base64,
            'filename': filename,
            'message': 'PDF generated successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Report generation error: {e}")
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
        if file and file.filename:  # Allow all file types
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
            logger.info(f"📤 Uploaded: {file.filename} ({os.path.getsize(filepath)} bytes)")
    
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
        model_answer_mode = data.get('modelAnswerMode', 'type')  # NEW
        lecturer_name = data.get('lecturerName', 'Instructor')
        lecturer_email = data.get('lecturerEmail', '')
        file_paths = data.get('filePaths', [])
        
        if not model_answer:
            return jsonify({'error': 'Model answer is required'}), 400
        
        if not file_paths:
            return jsonify({'error': 'No files to grade'}), 400
        
        logger.info("="*80)
        logger.info(f"🎓 Starting grading for {len(file_paths)} file(s)")
        logger.info(f"📚 Exam: {exam_name} ({subject})")
        logger.info(f"📝 Model Answer Length: {len(model_answer)} characters")
        logger.info(f"📎 Model Answer Mode: {model_answer_mode}")
        logger.info("="*80)
        
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
        for idx, file_path in enumerate(file_paths, 1):
            try:
                logger.info(f"📄 Grading file {idx}/{len(file_paths)}: {file_path}")
                
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
                
                logger.info(f"✅ Graded {student_info['name']}: {result['score']}/{result['total_points']} ({result['grade']})")
                
            except Exception as e:
                logger.error(f"❌ Error grading {file_path}: {e}")
                logger.error(traceback.format_exc())
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
            
            logger.info("="*80)
            logger.info("📊 GRADING STATISTICS:")
            logger.info(f"   Total Students: {statistics['total_students']}")
            logger.info(f"   Average Score: {statistics['average_score']:.2f}")
            logger.info(f"   Pass Rate: {statistics['pass_rate']:.1f}%")
            logger.info("="*80)
        else:
            statistics = {}
        
        return jsonify({
            'success': True,
            'results': results,
            'statistics': statistics,
            'ai_provider': ai_provider.active_provider if ai_provider else 'fallback_mode',
            'fallback_mode': ai_provider is None or ai_provider.client is None
        })
        
    except Exception as e:
        logger.error(f"❌ Grading error: {e}")
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
            'ai_provider': ai_provider.active_provider if ai_provider else 'fallback_mode',
            'fallback_mode': ai_provider is None or ai_provider.client is None
        })
        
    except Exception as e:
        logger.error(f"❌ Text grading error: {e}")
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
            'system_status': 'operational' if grading_system else 'degraded',
            'fallback_mode': ai_provider is None or ai_provider.client is None
        }
        
        session.close()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"❌ Stats error: {e}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 50MB'}), 413


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"❌ Internal error: {error}")
    logger.error(traceback.format_exc())
    return jsonify({
        'error': 'Internal server error',
        'details': str(error)
    }), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    
    # Final check before starting server
    logger.info("="*80)
    if not system_initialized or grading_system is None:
        logger.error("❌❌❌ CRITICAL WARNING: System not properly initialized! ❌❌❌")
        logger.error("❌ The application will start but may not function correctly.")
        logger.error("❌ Please check your API keys and environment variables.")
    elif ai_provider is None or ai_provider.client is None:
        logger.warning("⚠️⚠️⚠️  WARNING: Running in FALLBACK MODE ⚠️⚠️⚠️")
        logger.warning("⚠️  AI grading will use generic feedback")
        logger.warning("⚠️  Please set an AI API key for dynamic feedback")
    else:
        logger.info("✅✅✅ Gem AI System Ready! ✅✅✅")
        logger.info(f"✅ AI Provider: {ai_provider.active_provider}")
        logger.info(f"✅ Database: {'Connected' if db else 'Disconnected'}")
        logger.info(f"✅ Real AI Grading: ENABLED")
    logger.info("="*80)
    
    app.run(host='0.0.0.0', port=port, debug=os.getenv('DEBUG', 'False').lower() == 'true')
