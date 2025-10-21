import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import List, Dict, Optional, Any
import logging
from jinja2 import Template
from datetime import datetime
import base64

logger = logging.getLogger(__name__)

class EmailService:
    """
    Advanced Email Service for Gem 💎 AI
    
    Features:
    - HTML email templates
    - File attachments
    - Bulk email sending
    - Email templates for different scenarios
    - SSL/TLS security
    - Multiple email providers support
    """
    
    def __init__(self, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587,
                 email: str = "", password: str = ""):
        """Initialize email service"""
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """Load email templates"""
        return {
            'result_notification': '''
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }
                    .content { padding: 20px; }
                    .result-box { background: #f8f9fa; border-left: 4px solid #28a745; padding: 15px; margin: 15px 0; }
                    .grade { font-size: 24px; font-weight: bold; color: #28a745; }
                    .footer { background: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }
                    .btn { display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>💎 Gem AI - Exam Results</h1>
                </div>
                <div class="content">
                    <h2>Hello {{student_name}},</h2>
                    <p>Your exam results for <strong>{{exam_name}}</strong> are ready!</p>
                    
                    <div class="result-box">
                        <div class="grade">Grade: {{grade}} ({{percentage}}%)</div>
                        <p><strong>Score:</strong> {{score}}/{{total_points}}</p>
                        <p><strong>Subject:</strong> {{subject}}</p>
                        <p><strong>Date:</strong> {{exam_date}}</p>
                    </div>
                    
                    {% if feedback %}
                    <h3>Feedback:</h3>
                    <p>{{feedback}}</p>
                    {% endif %}
                    
                    {% if strengths %}
                    <h3>Strengths:</h3>
                    <ul>
                    {% for strength in strengths %}
                        <li>{{strength}}</li>
                    {% endfor %}
                    </ul>
                    {% endif %}
                    
                    {% if improvements %}
                    <h3>Areas for Improvement:</h3>
                    <ul>
                    {% for improvement in improvements %}
                        <li>{{improvement}}</li>
                    {% endfor %}
                    </ul>
                    {% endif %}
                    
                    {% if recommendations %}
                    <h3>Recommendations:</h3>
                    <p>{{recommendations}}</p>
                    {% endif %}
                    
                    <p>Best regards,<br>
                    <strong>{{lecturer_name}}</strong><br>
                    {{subject}} Instructor</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from Gem 💎 AI - The World's Most Advanced Grading System</p>
                    <p>If you have questions, please contact your instructor.</p>
                </div>
            </body>
            </html>
            ''',
            
            'lecturer_summary': '''
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }
                    .content { padding: 20px; }
                    .stats { display: flex; justify-content: space-around; margin: 20px 0; }
                    .stat-box { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; min-width: 150px; }
                    .stat-number { font-size: 24px; font-weight: bold; color: #007bff; }
                    .table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                    .table th, .table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
                    .table th { background-color: #f8f9fa; font-weight: bold; }
                    .footer { background: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>💎 Gem AI - Grading Complete</h1>
                </div>
                <div class="content">
                    <h2>Hello {{lecturer_name}},</h2>
                    <p>Grading has been completed for <strong>{{exam_name}}</strong> ({{subject}}).</p>
                    
                    <div class="stats">
                        <div class="stat-box">
                            <div class="stat-number">{{total_students}}</div>
                            <div>Students</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number">{{average_score}}%</div>
                            <div>Average Score</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number">{{pass_rate}}%</div>
                            <div>Pass Rate</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number">{{highest_score}}%</div>
                            <div>Highest Score</div>
                        </div>
                    </div>
                    
                    <h3>Grade Distribution:</h3>
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Grade</th>
                                <th>Count</th>
                                <th>Percentage</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for grade, count in grade_distribution.items() %}
                            <tr>
                                <td>{{grade}}</td>
                                <td>{{count}}</td>
                                <td>{{(count/total_students*100)|round(1)}}%</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    
                    <p>A detailed PDF report has been attached to this email.</p>
                    
                    <p>Best regards,<br>
                    <strong>Gem 💎 AI System</strong></p>
                </div>
                <div class="footer">
                    <p>Gem 💎 AI - Making Education Assessment Effortless</p>
                </div>
            </body>
            </html>
            ''',
            
            'batch_completion': '''
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .header { background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 20px; text-align: center; }
                    .content { padding: 20px; }
                    .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 5px; margin: 15px 0; }
                    .warning { background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 5px; margin: 15px 0; }
                    .error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 5px; margin: 15px 0; }
                    .footer { background: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>💎 Gem AI - Batch Processing Complete</h1>
                </div>
                <div class="content">
                    <h2>Hello {{lecturer_name}},</h2>
                    <p>Your batch grading process has been completed!</p>
                    
                    <div class="success">
                        <strong>✅ Success:</strong> {{successful_count}} out of {{total_files}} files processed successfully.
                    </div>
                    
                    {% if failed_count > 0 %}
                    <div class="error">
                        <strong>❌ Failed:</strong> {{failed_count}} files failed to process.
                    </div>
                    {% endif %}
                    
                    {% if warnings %}
                    <div class="warning">
                        <strong>⚠️ Warnings:</strong>
                        <ul>
                        {% for warning in warnings %}
                            <li>{{warning}}</li>
                        {% endfor %}
                        </ul>
                    </div>
                    {% endif %}
                    
                    <h3>Processing Summary:</h3>
                    <ul>
                        <li><strong>Exam:</strong> {{exam_name}}</li>
                        <li><strong>Subject:</strong> {{subject}}</li>
                        <li><strong>Processing Time:</strong> {{processing_time}}</li>
                        <li><strong>Average Confidence:</strong> {{avg_confidence}}%</li>
                    </ul>
                    
                    <p>All results have been saved to the database and individual notifications have been sent to students.</p>
                    
                    <p>Best regards,<br>
                    <strong>Gem 💎 AI System</strong></p>
                </div>
                <div class="footer">
                    <p>Gem 💎 AI - Revolutionizing Education Assessment</p>
                </div>
            </body>
            </html>
            ''',
            
            'welcome': '''
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .header { background: linear-gradient(135deg, #ff6b6b 0%, #4ecdc4 100%); color: white; padding: 20px; text-align: center; }
                    .content { padding: 20px; }
                    .feature { background: #f8f9fa; padding: 15px; margin: 10px 0; border-left: 4px solid #007bff; }
                    .cta { text-align: center; margin: 30px 0; }
                    .btn { display: inline-block; padding: 15px 30px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }
                    .footer { background: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Welcome to Gem 💎 AI</h1>
                    <p>The World's Most Advanced Exam Grading System</p>
                </div>
                <div class="content">
                    <h2>Hello {{user_name}},</h2>
                    <p>Welcome to Gem 💎 AI! You now have access to the most advanced AI-powered grading system in the world.</p>
                    
                    <h3>🚀 Key Features:</h3>
                    
                    <div class="feature">
                        <h4>📄 Universal File Support</h4>
                        <p>Grade any format: PDF, Word, images, audio, video, handwritten texts, and more!</p>
                    </div>
                    
                    <div class="feature">
                        <h4>🧠 Advanced AI Grading</h4>
                        <p>Powered by GPT-4 with detailed feedback, corrections, and personalized recommendations.</p>
                    </div>
                    
                    <div class="feature">
                        <h4>📊 Comprehensive Analytics</h4>
                        <p>Detailed statistics, grade distributions, and performance insights.</p>
                    </div>
                    
                    <div class="feature">
                        <h4>⚡ Batch Processing</h4>
                        <p>Grade hundreds of exams simultaneously with automated email notifications.</p>
                    </div>
                    
                    <div class="feature">
                        <h4>🔍 Plagiarism Detection</h4>
                        <p>Built-in plagiarism detection and similarity analysis.</p>
                    </div>
                    
                    <div class="feature">
                        <h4>📧 Smart Notifications</h4>
                        <p>Automated email reports for students and lecturers with detailed feedback.</p>
                    </div>
                    
                    <div class="cta">
                        <h3>🎉 Your 5-Day FREE Trial Starts Now!</h3>
                        <p>Experience the future of education assessment at no cost.</p>
                    </div>
                    
                    <h3>Getting Started:</h3>
                    <ol>
                        <li>Upload your exam files (any format)</li>
                        <li>Set your grading criteria and rubric</li>
                        <li>Let Gem AI work its magic</li>
                        <li>Review results and send notifications</li>
                    </ol>
                    
                    <p>Need help? Our support team is available 24/7.</p>
                    
                    <p>Best regards,<br>
                    <strong>The Gem 💎 AI Team</strong></p>
                </div>
                <div class="footer">
                    <p>Gem 💎 AI - Transforming Education, One Grade at a Time</p>
                    <p>Contact: support@gemai.com | Web: www.gemai.com</p>
                </div>
            </body>
            </html>
            '''
        }
    
    def send_email(self, to_email: str, subject: str, html_content: str, 
                   attachments: Optional[List[str]] = None, 
                   cc: Optional[List[str]] = None,
                   bcc: Optional[List[str]] = None) -> bool:
        """Send email with HTML content and attachments"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                msg['Bcc'] = ', '.join(bcc)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    if os.path.isfile(file_path):
                        with open(file_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {os.path.basename(file_path)}'
                        )
                        msg.attach(part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email, self.password)
                
                recipients = [to_email]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)
                
                server.sendmail(self.email, recipients, msg.as_string())
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_result_notification(self, student_email: str, student_name: str,
                                result_data: Dict[str, Any], lecturer_name: str = "Your Instructor") -> bool:
        """Send exam result notification to student"""
        try:
            template = Template(self.templates['result_notification'])
            
            # Prepare template data
            template_data = {
                'student_name': student_name,
                'exam_name': result_data.get('exam_name', 'Exam'),
                'grade': result_data.get('grade', 'N/A'),
                'percentage': result_data.get('percentage', 0),
                'score': result_data.get('score', 0),
                'total_points': result_data.get('total_points', 100),
                'subject': result_data.get('subject', 'Subject'),
                'exam_date': datetime.now().strftime('%Y-%m-%d'),
                'feedback': result_data.get('feedback', ''),
                'strengths': result_data.get('strengths', []),
                'improvements': result_data.get('improvements', []),
                'recommendations': result_data.get('recommendations', ''),
                'lecturer_name': lecturer_name
            }
            
            html_content = template.render(**template_data)
            subject = f"📊 Your {result_data.get('exam_name', 'Exam')} Results - Grade: {result_data.get('grade', 'N/A')}"
            
            return self.send_email(student_email, subject, html_content)
            
        except Exception as e:
            logger.error(f"Failed to send result notification: {str(e)}")
            return False
    
    def send_lecturer_summary(self, lecturer_email: str, lecturer_name: str,
                             exam_data: Dict[str, Any], statistics: Dict[str, Any],
                             pdf_report_path: Optional[str] = None) -> bool:
        """Send grading summary to lecturer"""
        try:
            template = Template(self.templates['lecturer_summary'])
            
            # Prepare template data
            template_data = {
                'lecturer_name': lecturer_name,
                'exam_name': exam_data.get('exam_name', 'Exam'),
                'subject': exam_data.get('subject', 'Subject'),
                'total_students': statistics.get('total_students', 0),
                'average_score': round(statistics.get('average_percentage', 0), 1),
                'pass_rate': round(statistics.get('pass_rate', 0), 1),
                'highest_score': round(statistics.get('highest_score', 0), 1),
                'grade_distribution': statistics.get('grade_distribution', {})
            }
            
            html_content = template.render(**template_data)
            subject = f"📈 Grading Complete: {exam_data.get('exam_name', 'Exam')} - {statistics.get('total_students', 0)} Students"
            
            attachments = [pdf_report_path] if pdf_report_path and os.path.exists(pdf_report_path) else None
            
            return self.send_email(lecturer_email, subject, html_content, attachments)
            
        except Exception as e:
            logger.error(f"Failed to send lecturer summary: {str(e)}")
            return False
    
    def send_batch_completion(self, lecturer_email: str, lecturer_name: str,
                             batch_results: Dict[str, Any]) -> bool:
        """Send batch processing completion notification"""
        try:
            template = Template(self.templates['batch_completion'])
            
            html_content = template.render(
                lecturer_name=lecturer_name,
                **batch_results
            )
            
            subject = f"✅ Batch Processing Complete - {batch_results.get('exam_name', 'Exam')}"
            
            return self.send_email(lecturer_email, subject, html_content)
            
        except Exception as e:
            logger.error(f"Failed to send batch completion notification: {str(e)}")
            return False
    
    def send_welcome_email(self, user_email: str, user_name: str, user_type: str = "lecturer") -> bool:
        """Send welcome email to new users"""
        try:
            template = Template(self.templates['welcome'])
            
            html_content = template.render(
                user_name=user_name,
                user_type=user_type
            )
            
            subject = "🎉 Welcome to Gem 💎 AI - Your 5-Day FREE Trial Starts Now!"
            
            return self.send_email(user_email, subject, html_content)
            
        except Exception as e:
            logger.error(f"Failed to send welcome email: {str(e)}")
            return False
    
    def send_bulk_notifications(self, recipients: List[Dict[str, Any]], 
                               notification_type: str, **kwargs) -> Dict[str, Any]:
        """Send bulk email notifications"""
        results = {
            'successful': 0,
            'failed': 0,
            'failed_emails': []
        }
        
        for recipient in recipients:
            try:
                if notification_type == 'result':
                    success = self.send_result_notification(
                        recipient['email'],
                        recipient['name'],
                        recipient['result_data'],
                        kwargs.get('lecturer_name', 'Your Instructor')
                    )
                elif notification_type == 'welcome':
                    success = self.send_welcome_email(
                        recipient['email'],
                        recipient['name'],
                        recipient.get('user_type', 'lecturer')
                    )
                else:
                    success = False
                
                if success:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                    results['failed_emails'].append(recipient['email'])
                    
            except Exception as e:
                logger.error(f"Failed to send bulk email to {recipient.get('email', 'unknown')}: {str(e)}")
                results['failed'] += 1
                results['failed_emails'].append(recipient.get('email', 'unknown'))
        
        logger.info(f"Bulk email results: {results['successful']} successful, {results['failed']} failed")
        return results
    
    def create_custom_template(self, template_name: str, html_content: str):
        """Add custom email template"""
        self.templates[template_name] = html_content
        logger.info(f"Added custom template: {template_name}")
    
    def test_email_connection(self) -> bool:
        """Test email server connection"""
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email, self.password)
                server.noop()
            
            logger.info("Email connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"Email connection test failed: {str(e)}")
            return False
    
    def get_email_statistics(self) -> Dict[str, int]:
        """Get email sending statistics (would need to be implemented with proper tracking)"""
        # This is a placeholder - in a real implementation, you'd track this in the database
        return {
            'total_sent': 0,
            'successful': 0,
            'failed': 0,
            'today_sent': 0
        }
