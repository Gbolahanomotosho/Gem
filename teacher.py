"""
Gem AI - Advanced Grading System with Multi-Provider Support
FIXED VERSION - Better AI error handling and logging
"""

import os
import fitz  # PyMuPDF
import docx
import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Optional, Any
import json
import re
from datetime import datetime
import cv2
import pytesseract
from PIL import Image
import speech_recognition as sr
from textblob import TextBlob
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import openpyxl
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import matplotlib.pyplot as plt
import seaborn as sns
from database import Database, Student, Exam, Result
import logging
import traceback
from email_service import EmailService
from ai_providers import AIProviderManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GemAIGradingSystem:
    """
    Gem 💎 AI - The World's Most Advanced Exam Grading System
    
    Features:
    - Multi-format file support (PDF, DOCX, TXT, Images, Audio, Video)
    - Handwritten text recognition (OCR)
    - Voice/Video exam processing
    - Advanced AI grading with detailed feedback (supports multiple AI providers)
    - Plagiarism detection
    - Statistical analysis and reporting
    - Email notifications
    - PDF report generation
    - Database integration
    - Batch processing
    - Custom rubrics and grading criteria
    """
    
    def __init__(self, ai_provider: AIProviderManager = None, db_path: str = "gem_ai.db"):
        """Initialize the Gem AI Grading System with flexible AI provider"""
        logger.info("="*80)
        logger.info("Initializing Gem AI Grading System...")
        
        self.ai_provider = ai_provider or AIProviderManager()
        self.db = Database(db_path)
        self.email_service = EmailService()
        
        # Verify AI provider is working
        if self.ai_provider and self.ai_provider.client:
            logger.info(f"✅ Gem AI initialized with {self.ai_provider.active_provider} provider")
            logger.info(f"✅ AI Provider Status: {self.ai_provider.get_provider_info()}")
        else:
            logger.error("❌ AI Provider NOT properly initialized!")
            logger.error("❌ Grading will use fallback mode (static feedback)")
        
        logger.info("="*80)
        
        # Download required NLTK data
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
        except:
            pass
    
    def extract_text_from_file(self, file_path: str) -> Dict[str, Any]:
        """Extract text from various file formats with metadata"""
        ext = os.path.splitext(file_path)[1].lower()
        extraction_info = {
            'text': '',
            'file_type': ext,
            'extraction_method': '',
            'confidence': 1.0,
            'metadata': {}
        }
        
        try:
            if ext == ".txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    extraction_info['text'] = f.read()
                extraction_info['extraction_method'] = 'direct_read'
                
            elif ext == ".pdf":
                doc = fitz.open(file_path)
                text = ""
                for page_num, page in enumerate(doc):
                    page_text = page.get_text()
                    if not page_text.strip():  # If no text, try OCR
                        pix = page.get_pixmap()
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        page_text = pytesseract.image_to_string(img)
                        extraction_info['extraction_method'] = 'ocr_hybrid'
                    text += f"\n--- Page {page_num + 1} ---\n{page_text}"
                extraction_info['text'] = text
                extraction_info['metadata'] = {'pages': doc.page_count}
                if not extraction_info['extraction_method']:
                    extraction_info['extraction_method'] = 'pdf_text_extraction'
                
            elif ext == ".docx":
                doc = docx.Document(file_path)
                text = "\n".join([para.text for para in doc.paragraphs])
                # Extract tables too
                for table in doc.tables:
                    for row in table.rows:
                        row_text = "\t".join([cell.text for cell in row.cells])
                        text += f"\n{row_text}"
                extraction_info['text'] = text
                extraction_info['extraction_method'] = 'structured_read'
                
            elif ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
                img = Image.open(file_path)
                text = pytesseract.image_to_string(img, config='--psm 6')
                extraction_info['text'] = text
                extraction_info['extraction_method'] = 'ocr'
                extraction_info['confidence'] = 0.85
                
            elif ext in [".xlsx", ".xls"]:
                df = pd.read_excel(file_path)
                text = df.to_string()
                extraction_info['text'] = text
                extraction_info['extraction_method'] = 'spreadsheet_read'
                
            elif ext == ".csv":
                df = pd.read_csv(file_path)
                text = df.to_string()
                extraction_info['text'] = text
                extraction_info['extraction_method'] = 'csv_read'
                
            else:
                raise ValueError(f"Unsupported file format: {ext}")
            
            logger.info(f"✅ Extracted {len(extraction_info['text'])} characters from {file_path}")
                
        except Exception as e:
            logger.error(f"❌ Error extracting text from {file_path}: {str(e)}")
            raise
            
        return extraction_info
    
    def advanced_ai_grading(self, student_answer: str, model_answer: str, 
                           rubric: Dict[str, Any], student_info: Dict[str, str]) -> Dict[str, Any]:
        """Advanced AI grading with detailed analysis using any AI provider"""
        
        logger.info("="*80)
        logger.info(f"🎓 Starting AI Grading for: {student_info.get('name', 'Unknown')}")
        logger.info(f"📝 Student Answer Length: {len(student_answer)} characters")
        logger.info(f"📝 Model Answer Length: {len(model_answer)} characters")
        
        # Analyze answer quality
        quality_metrics = self._analyze_answer_quality(student_answer, model_answer)
        logger.info(f"📊 Quality Metrics: {quality_metrics}")
        
        # Check for plagiarism
        plagiarism_score = self._check_plagiarism(student_answer, model_answer)
        logger.info(f"🔍 Plagiarism Score: {plagiarism_score}%")
        
        # Generate comprehensive feedback
        grading_prompt = f"""You are Gem 💎 AI, the world's most advanced AI teacher and grading system. 

Grade this student's answer with extreme precision and provide comprehensive feedback:

STUDENT INFORMATION:
- Name: {student_info.get('name', 'N/A')}
- ID: {student_info.get('student_id', 'N/A')}
- Exam: {student_info.get('exam_name', 'N/A')}

GRADING CRITERIA:
- Total Points: {rubric.get('total_points', 100)}
- Question Number: {rubric.get('question_number', 1)}
- Subject: {rubric.get('subject', 'General')}
- Difficulty Level: {rubric.get('difficulty', 'Medium')}

RUBRIC BREAKDOWN:
{json.dumps(rubric.get('criteria', {}), indent=2)}

STUDENT'S ANSWER:
\"\"\"
{student_answer[:2000]}
\"\"\"

MODEL ANSWER:
\"\"\"
{model_answer[:2000]}
\"\"\"

QUALITY METRICS:
- Word Count: {quality_metrics['word_count']}
- Readability Score: {quality_metrics['readability']:.1f}
- Grammar Score: {quality_metrics['grammar_score']:.1f}
- Key Terms Coverage: {quality_metrics['key_terms_coverage']:.1f}%

Provide a detailed grading response in this exact format:

SCORE: X/{rubric.get('total_points', 100)}
PERCENTAGE: XX.X%
GRADE: [A+/A/B+/B/C+/C/D+/D/F]

DETAILED BREAKDOWN:
[Provide detailed scoring for each criterion]

STRENGTHS:
- [List 3-5 specific strengths based on the student's actual answer]

AREAS FOR IMPROVEMENT:
- [List 3-5 specific areas needing improvement with suggestions based on what the student actually wrote]

CORRECTIONS:
[For any incorrect information in the student's answer, provide the correct information]

FEEDBACK:
[Provide encouraging, constructive, and detailed feedback specific to this student's answer]

RECOMMENDATIONS:
[Specific study recommendations and resources based on this student's performance]
"""

        try:
            logger.info("🤖 Calling AI provider for grading...")
            logger.info(f"🤖 Using Provider: {self.ai_provider.active_provider}")
            
            # Use the AI provider manager to generate completion
            ai_feedback = self.ai_provider.generate_completion(
                grading_prompt,
                max_tokens=2000,
                temperature=0.3
            )
            
            logger.info(f"✅ AI Response received ({len(ai_feedback)} characters)")
            logger.info(f"📄 AI Response Preview: {ai_feedback[:200]}...")
            
            parsed_result = self._parse_ai_response(ai_feedback)
            logger.info(f"✅ Parsed Result: Score={parsed_result['score']}/{parsed_result['total_points']}, Grade={parsed_result['grade']}")
            
            # Add technical metrics
            parsed_result.update({
                'quality_metrics': quality_metrics,
                'plagiarism_score': plagiarism_score,
                'grading_timestamp': datetime.now().isoformat(),
                'ai_confidence': 0.95,
                'ai_provider': self.ai_provider.active_provider,
                'student_info': student_info,
                'rubric_used': rubric
            })
            
            logger.info("="*80)
            return parsed_result
            
        except Exception as e:
            logger.error("❌ AI GRADING FAILED!")
            logger.error(f"❌ Error Type: {type(e).__name__}")
            logger.error(f"❌ Error Message: {str(e)}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            logger.error("❌ Falling back to similarity-based grading...")
            logger.info("="*80)
            
            return self._generate_fallback_grade(student_answer, model_answer, rubric, student_info)
    
    def _analyze_answer_quality(self, answer: str, model_answer: str) -> Dict[str, Any]:
        """Analyze the quality of the student's answer"""
        try:
            blob = TextBlob(answer)
            model_blob = TextBlob(model_answer)
            
            # Calculate similarity
            vectorizer = TfidfVectorizer()
            try:
                tfidf_matrix = vectorizer.fit_transform([answer, model_answer])
                similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            except:
                similarity = 0.0
            
            return {
                'word_count': len(answer.split()),
                'sentence_count': len(blob.sentences),
                'readability': min(100, max(0, (similarity * 100))),
                'grammar_score': min(100, max(0, blob.sentiment.polarity * 100 + 50)),
                'key_terms_coverage': self._calculate_key_terms_coverage(answer, model_answer),
                'similarity_to_model': similarity * 100
            }
        except Exception as e:
            logger.error(f"Error analyzing answer quality: {str(e)}")
            return {
                'word_count': len(answer.split()),
                'sentence_count': 0,
                'readability': 50.0,
                'grammar_score': 50.0,
                'key_terms_coverage': 50.0,
                'similarity_to_model': 50.0
            }
    
    def _calculate_key_terms_coverage(self, answer: str, model_answer: str) -> float:
        """Calculate how many key terms from model answer are covered"""
        try:
            answer_lower = answer.lower()
            model_words = set(re.findall(r'\b\w+\b', model_answer.lower()))
            common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                          'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                          'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
                          'could', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
            key_terms = model_words - common_words
            
            if not key_terms:
                return 100.0
                
            covered_terms = sum(1 for term in key_terms if term in answer_lower)
            return (covered_terms / len(key_terms)) * 100
        except Exception as e:
            logger.error(f"Error calculating key terms coverage: {str(e)}")
            return 50.0
    
    def _check_plagiarism(self, answer: str, reference: str) -> float:
        """Simple plagiarism detection"""
        try:
            answer_sentences = re.split(r'[.!?]+', answer.lower())
            reference_sentences = re.split(r'[.!?]+', reference.lower())
            
            matches = 0
            total_sentences = len(answer_sentences)
            
            for ans_sent in answer_sentences:
                ans_sent = ans_sent.strip()
                if len(ans_sent) < 10:
                    continue
                for ref_sent in reference_sentences:
                    ref_sent = ref_sent.strip()
                    if ans_sent in ref_sent or ref_sent in ans_sent:
                        matches += 1
                        break
            
            return (matches / max(1, total_sentences)) * 100
        except Exception as e:
            logger.error(f"Error checking plagiarism: {str(e)}")
            return 0.0
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse the AI grading response into structured data"""
        result = {
            'score': 0,
            'total_points': 100,
            'percentage': 0.0,
            'grade': 'F',
            'breakdown': '',
            'strengths': [],
            'improvements': [],
            'corrections': '',
            'feedback': '',
            'recommendations': ''
        }
        
        try:
            lines = response.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('SCORE:'):
                    score_match = re.search(r'(\d+)/(\d+)', line)
                    if score_match:
                        result['score'] = int(score_match.group(1))
                        result['total_points'] = int(score_match.group(2))
                        
                elif line.startswith('PERCENTAGE:'):
                    percentage_match = re.search(r'(\d+\.?\d*)', line)
                    if percentage_match:
                        result['percentage'] = float(percentage_match.group(1))
                        
                elif line.startswith('GRADE:'):
                    grade_text = line.replace('GRADE:', '').strip()
                    # Extract just the grade letter(s)
                    grade_match = re.search(r'([A-F][+-]?)', grade_text)
                    if grade_match:
                        result['grade'] = grade_match.group(1)
                    else:
                        result['grade'] = grade_text[:2] if len(grade_text) >= 2 else grade_text
                    
                elif line.startswith('DETAILED BREAKDOWN:'):
                    current_section = 'breakdown'
                    continue
                elif line.startswith('STRENGTHS:'):
                    current_section = 'strengths'
                    continue
                elif line.startswith('AREAS FOR IMPROVEMENT:'):
                    current_section = 'improvements'
                    continue
                elif line.startswith('CORRECTIONS:'):
                    current_section = 'corrections'
                    continue
                elif line.startswith('FEEDBACK:'):
                    current_section = 'feedback'
                    continue
                elif line.startswith('RECOMMENDATIONS:'):
                    current_section = 'recommendations'
                    continue
                    
                # Add content to appropriate section
                if current_section == 'breakdown':
                    result['breakdown'] += line + '\n'
                elif current_section == 'strengths' and line.startswith('-'):
                    result['strengths'].append(line[1:].strip())
                elif current_section == 'improvements' and line.startswith('-'):
                    result['improvements'].append(line[1:].strip())
                elif current_section == 'corrections':
                    result['corrections'] += line + '\n'
                elif current_section == 'feedback':
                    result['feedback'] += line + ' '
                elif current_section == 'recommendations':
                    result['recommendations'] += line + ' '
            
            # Clean up feedback and recommendations
            result['feedback'] = result['feedback'].strip()
            result['recommendations'] = result['recommendations'].strip()
            result['corrections'] = result['corrections'].strip()
            result['breakdown'] = result['breakdown'].strip()
                    
        except Exception as e:
            logger.error(f"Error parsing AI response: {str(e)}")
            
        return result
    
    def _generate_fallback_grade(self, answer: str, model_answer: str, rubric: Dict, student_info: Dict) -> Dict[str, Any]:
        """Generate a basic grade when AI grading fails - THIS IS THE FALLBACK!"""
        logger.warning("⚠️ Using FALLBACK grading mode - feedback will be generic!")
        
        quality = self._analyze_answer_quality(answer, model_answer)
        score = int(quality['similarity_to_model'] * rubric.get('total_points', 100) / 100)
        
        return {
            'score': score,
            'total_points': rubric.get('total_points', 100),
            'percentage': quality['similarity_to_model'],
            'grade': self._score_to_grade(quality['similarity_to_model']),
            'feedback': f"⚠️ FALLBACK MODE: Automated grading based on similarity analysis. Score: {score}/{rubric.get('total_points', 100)}. AI grading failed - please check your API key configuration.",
            'strengths': ['Answer provided', 'Attempt made'],
            'improvements': ['More detail needed', 'Review model answer'],
            'corrections': 'AI grading unavailable - manual review recommended',
            'recommendations': 'Review course materials and model answer. Note: This is automated fallback grading.',
            'breakdown': f"Similarity to model answer: {quality['similarity_to_model']:.1f}%\n⚠️ This is fallback grading - AI provider failed",
            'quality_metrics': quality,
            'ai_confidence': 0.60,
            'ai_provider': f"{self.ai_provider.active_provider} (FALLBACK MODE)",
            'student_info': student_info,
            'rubric_used': rubric
        }
    
    def _score_to_grade(self, percentage: float) -> str:
        """Convert percentage to letter grade"""
        if percentage >= 97: return 'A+'
        elif percentage >= 93: return 'A'
        elif percentage >= 90: return 'A-'
        elif percentage >= 87: return 'B+'
        elif percentage >= 83: return 'B'
        elif percentage >= 80: return 'B-'
        elif percentage >= 77: return 'C+'
        elif percentage >= 73: return 'C'
        elif percentage >= 70: return 'C-'
        elif percentage >= 67: return 'D+'
        elif percentage >= 60: return 'D'
        else: return 'F'
    
    def batch_grade_exams(self, exam_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Grade multiple exams in batch"""
        results = []
        
        for student_file in exam_config['student_files']:
            try:
                student_info = self._extract_student_info(student_file, exam_config)
                extraction_result = self.extract_text_from_file(student_file)
                student_answer = extraction_result['text']
                
                grading_result = self.advanced_ai_grading(
                    student_answer,
                    exam_config['model_answer'],
                    exam_config['rubric'],
                    student_info
                )
                
                grading_result['file_path'] = student_file
                grading_result['extraction_info'] = extraction_result
                results.append(grading_result)
                
                self._save_result_to_db(grading_result, exam_config)
                
                logger.info(f"Graded: {student_info.get('name', 'Unknown')} - Score: {grading_result['score']}/{grading_result['total_points']}")
                
            except Exception as e:
                logger.error(f"Failed to grade {student_file}: {str(e)}")
                results.append({
                    'file_path': student_file,
                    'error': str(e),
                    'score': 0,
                    'total_points': exam_config['rubric'].get('total_points', 100)
                })
        
        return results
    
    def _extract_student_info(self, file_path: str, exam_config: Dict) -> Dict[str, str]:
        """Extract student information from filename or config"""
        filename = os.path.basename(file_path)
        pattern_matches = re.search(r'([^_]+)_([^_]+)_(\d+)', filename)
        
        if pattern_matches:
            return {
                'name': f"{pattern_matches.group(1)} {pattern_matches.group(2)}",
                'student_id': pattern_matches.group(3),
                'exam_name': exam_config.get('exam_name', 'Unknown Exam'),
                'subject': exam_config.get('subject', 'Unknown Subject')
            }
        
        return {
            'name': filename.split('.')[0],
            'student_id': 'Unknown',
            'exam_name': exam_config.get('exam_name', 'Unknown Exam'),
            'subject': exam_config.get('subject', 'Unknown Subject')
        }
    
    def _save_result_to_db(self, result: Dict, exam_config: Dict):
        """Save grading result to database"""
        try:
            student_info = result['student_info']
            student = self.db.get_or_create_student(
                student_info['student_id'],
                student_info['name']
            )
            
            exam = self.db.get_or_create_exam(
                exam_config.get('exam_name', 'Unknown'),
                exam_config.get('subject', 'Unknown'),
                exam_config['rubric'].get('total_points', 100)
            )
            
            self.db.save_result(
                student.id,
                exam.id,
                result['score'],
                result['percentage'],
                result['grade'],
                json.dumps(result)
            )
            
        except Exception as e:
            logger.error(f"Failed to save result to database: {str(e)}")
    
    def generate_pdf_report(self, results: List[Dict], output_path: str, exam_config: Dict):
        """Generate comprehensive PDF report"""
        try:
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.darkblue,
                alignment=1,
                spaceAfter=30
            )
            
            story.append(Paragraph("Gem 💎 AI - Grading Report", title_style))
            story.append(Spacer(1, 20))
            
            exam_info = f"""
            <b>Exam:</b> {exam_config.get('exam_name', 'Unknown')}<br/>
            <b>Subject:</b> {exam_config.get('subject', 'Unknown')}<br/>
            <b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
            <b>Total Students:</b> {len(results)}<br/>
            <b>Total Points:</b> {exam_config.get('rubric', {}).get('total_points', 100)}
            """
            story.append(Paragraph(exam_info, styles['Normal']))
            story.append(Spacer(1, 30))
            
            if results:
                scores = [r.get('score', 0) for r in results if 'score' in r and 'error' not in r]
                if scores:
                    stats = f"""
                    <b>Statistics:</b><br/>
                    Average Score: {np.mean(scores):.2f}<br/>
                    Highest Score: {max(scores)}<br/>
                    Lowest Score: {min(scores)}<br/>
                    Standard Deviation: {np.std(scores):.2f}
                    """
                    story.append(Paragraph(stats, styles['Normal']))
                    story.append(Spacer(1, 30))
            
            story.append(Paragraph("Individual Results", styles['Heading2']))
            story.append(Spacer(1, 20))
            
            for i, result in enumerate(results, 1):
                if 'error' in result:
                    continue
                    
                student_info = result.get('student_info', {})
                
                student_header = f"""
                <b>Student {i}:</b> {student_info.get('name', 'Unknown')}<br/>
                <b>ID:</b> {student_info.get('student_id', 'Unknown')}<br/>
                <b>Score:</b> {result.get('score', 0)}/{result.get('total_points', 100)} ({result.get('percentage', 0):.1f}%)<br/>
                <b>Grade:</b> {result.get('grade', 'F')}
                """
                story.append(Paragraph(student_header, styles['Normal']))
                story.append(Spacer(1, 10))
                
                if result.get('feedback'):
                    story.append(Paragraph("<b>Feedback:</b>", styles['Normal']))
                    feedback_text = result['feedback'][:500]  # Limit length
                    story.append(Paragraph(feedback_text, styles['Normal']))
                    story.append(Spacer(1, 10))
                
                if result.get('strengths'):
                    story.append(Paragraph("<b>Strengths:</b>", styles['Normal']))
                    for strength in result['strengths'][:3]:
                        story.append(Paragraph(f"• {strength}", styles['Normal']))
                    story.append(Spacer(1, 10))
                
                if result.get('improvements'):
                    story.append(Paragraph("<b>Areas for Improvement:</b>", styles['Normal']))
                    for improvement in result['improvements'][:3]:
                        story.append(Paragraph(f"• {improvement}", styles['Normal']))
                    story.append(Spacer(1, 10))
                
                story.append(Spacer(1, 20))
                
                if i % 2 == 0:
                    story.append(PageBreak())
            
            doc.build(story)
            logger.info(f"PDF report generated: {output_path}")
        except Exception as e:
            logger.error(f"Failed to generate PDF report: {str(e)}")
    
    def generate_statistics_charts(self, results: List[Dict], output_dir: str):
        """Generate statistical charts and visualizations"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            scores = [r.get('score', 0) for r in results if 'score' in r and 'error' not in r]
            grades = [r.get('grade', 'F') for r in results if 'grade' in r and 'error' not in r]
            
            if not scores:
                logger.warning("No scores to generate charts")
                return
            
            # Score distribution
            plt.figure(figsize=(10, 6))
            plt.hist(scores, bins=20, edgecolor='black', alpha=0.7, color='skyblue')
            plt.title('Score Distribution', fontsize=16, fontweight='bold')
            plt.xlabel('Score', fontsize=12)
            plt.ylabel('Frequency', fontsize=12)
            plt.grid(axis='y', alpha=0.3)
            plt.savefig(os.path.join(output_dir, 'score_distribution.png'), dpi=300, bbox_inches='tight')
            plt.close()
            
            # Grade distribution
            if grades:
                grade_counts = pd.Series(grades).value_counts()
                plt.figure(figsize=(10, 6))
                grade_counts.plot(kind='bar', color='coral', edgecolor='black')
                plt.title('Grade Distribution', fontsize=16, fontweight='bold')
                plt.xlabel('Grade', fontsize=12)
                plt.ylabel('Count', fontsize=12)
                plt.xticks(rotation=0)
                plt.grid(axis='y', alpha=0.3)
                plt.tight_layout()
                plt.savefig(os.path.join(output_dir, 'grade_distribution.png'), dpi=300, bbox_inches='tight')
                plt.close()
            
            logger.info(f"Charts generated in: {output_dir}")
        except Exception as e:
            logger.error(f"Failed to generate statistics charts: {str(e)}")

