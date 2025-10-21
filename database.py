from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class Student(Base):
    """Student model for storing student information"""
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    department = Column(String(100))
    level = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    results = relationship("Result", back_populates="student")
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'department': self.department,
            'level': self.level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

class Lecturer(Base):
    """Lecturer model for storing lecturer information"""
    __tablename__ = 'lecturers'
    
    id = Column(Integer, primary_key=True)
    lecturer_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50))
    department = Column(String(100))
    title = Column(String(100))  # Prof, Dr, Mr, Ms, etc.
    specialization = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    exams = relationship("Exam", back_populates="lecturer")
    
    def to_dict(self):
        return {
            'id': self.id,
            'lecturer_id': self.lecturer_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'department': self.department,
            'title': self.title,
            'specialization': self.specialization,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

class Subject(Base):
    """Subject model for storing subject information"""
    __tablename__ = 'subjects'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    credit_units = Column(Integer, default=3)
    department = Column(String(100))
    level = Column(String(50))
    semester = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    exams = relationship("Exam", back_populates="subject")
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'credit_units': self.credit_units,
            'department': self.department,
            'level': self.level,
            'semester': self.semester,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

class Exam(Base):
    """Exam model for storing exam information"""
    __tablename__ = 'exams'
    
    id = Column(Integer, primary_key=True)
    exam_name = Column(String(255), nullable=False)
    exam_code = Column(String(50), unique=True)
    exam_type = Column(String(50))  # Midterm, Final, Quiz, Assignment, etc.
    subject_id = Column(Integer, ForeignKey('subjects.id'))
    lecturer_id = Column(Integer, ForeignKey('lecturers.id'))
    total_points = Column(Float, default=100.0)
    duration_minutes = Column(Integer)
    exam_date = Column(DateTime)
    instructions = Column(Text)
    model_answer = Column(Text)
    rubric = Column(Text)  # JSON string of rubric criteria
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    subject = relationship("Subject", back_populates="exams")
    lecturer = relationship("Lecturer", back_populates="exams")
    results = relationship("Result", back_populates="exam")
    questions = relationship("Question", back_populates="exam")
    
    def to_dict(self):
        return {
            'id': self.id,
            'exam_name': self.exam_name,
            'exam_code': self.exam_code,
            'exam_type': self.exam_type,
            'subject_id': self.subject_id,
            'lecturer_id': self.lecturer_id,
            'total_points': self.total_points,
            'duration_minutes': self.duration_minutes,
            'exam_date': self.exam_date.isoformat() if self.exam_date else None,
            'instructions': self.instructions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

class Question(Base):
    """Question model for storing individual questions"""
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True)
    exam_id = Column(Integer, ForeignKey('exams.id'))
    question_number = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50))  # Essay, MCQ, Short Answer, etc.
    points = Column(Float, default=10.0)
    model_answer = Column(Text)
    marking_criteria = Column(Text)  # JSON string
    difficulty_level = Column(String(20))  # Easy, Medium, Hard
    learning_objective = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    exam = relationship("Exam", back_populates="questions")
    answers = relationship("Answer", back_populates="question")
    
    def to_dict(self):
        return {
            'id': self.id,
            'exam_id': self.exam_id,
            'question_number': self.question_number,
            'question_text': self.question_text,
            'question_type': self.question_type,
            'points': self.points,
            'model_answer': self.model_answer,
            'difficulty_level': self.difficulty_level,
            'learning_objective': self.learning_objective,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

class Answer(Base):
    """Answer model for storing student answers"""
    __tablename__ = 'answers'
    
    id = Column(Integer, primary_key=True)
    result_id = Column(Integer, ForeignKey('results.id'))
    question_id = Column(Integer, ForeignKey('questions.id'))
    student_answer = Column(Text)
    score_earned = Column(Float, default=0.0)
    points_possible = Column(Float, default=0.0)
    feedback = Column(Text)
    is_correct = Column(Boolean, default=False)
    time_spent_seconds = Column(Integer)
    confidence_score = Column(Float)  # AI confidence in grading
    plagiarism_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    result = relationship("Result", back_populates="answers")
    question = relationship("Question", back_populates="answers")
    
    def to_dict(self):
        return {
            'id': self.id,
            'result_id': self.result_id,
            'question_id': self.question_id,
            'student_answer': self.student_answer,
            'score_earned': self.score_earned,
            'points_possible': self.points_possible,
            'feedback': self.feedback,
            'is_correct': self.is_correct,
            'time_spent_seconds': self.time_spent_seconds,
            'confidence_score': self.confidence_score,
            'plagiarism_score': self.plagiarism_score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Result(Base):
    """Result model for storing exam results"""
    __tablename__ = 'results'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'))
    exam_id = Column(Integer, ForeignKey('exams.id'))
    total_score = Column(Float, default=0.0)
    total_possible = Column(Float, default=100.0)
    percentage = Column(Float, default=0.0)
    letter_grade = Column(String(5))
    gpa_points = Column(Float, default=0.0)
    time_taken_minutes = Column(Integer)
    submission_timestamp = Column(DateTime, default=datetime.utcnow)
    grading_timestamp = Column(DateTime)
    overall_feedback = Column(Text)
    strengths = Column(Text)  # JSON string
    improvements = Column(Text)  # JSON string
    corrections = Column(Text)
    recommendations = Column(Text)
    ai_confidence = Column(Float, default=0.0)
    manual_review_required = Column(Boolean, default=False)
    status = Column(String(20), default='completed')  # pending, completed, reviewed
    detailed_results = Column(Text)  # JSON string of full results
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = relationship("Student", back_populates="results")
    exam = relationship("Exam", back_populates="results")
    answers = relationship("Answer", back_populates="result")
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'exam_id': self.exam_id,
            'total_score': self.total_score,
            'total_possible': self.total_possible,
            'percentage': self.percentage,
            'letter_grade': self.letter_grade,
            'gpa_points': self.gpa_points,
            'time_taken_minutes': self.time_taken_minutes,
            'submission_timestamp': self.submission_timestamp.isoformat() if self.submission_timestamp else None,
            'grading_timestamp': self.grading_timestamp.isoformat() if self.grading_timestamp else None,
            'overall_feedback': self.overall_feedback,
            'ai_confidence': self.ai_confidence,
            'manual_review_required': self.manual_review_required,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class SystemSettings(Base):
    """System settings for Gem AI"""
    __tablename__ = 'system_settings'
    
    id = Column(Integer, primary_key=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_value = Column(Text)
    description = Column(Text)
    data_type = Column(String(20), default='string')  # string, integer, float, boolean, json
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'setting_key': self.setting_key,
            'setting_value': self.setting_value,
            'description': self.description,
            'data_type': self.data_type,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class AuditLog(Base):
    """Audit log for tracking system activities"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50))  # Could be student_id or lecturer_id
    user_type = Column(String(20))  # student, lecturer, admin
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))  # exam, result, student, etc.
    entity_id = Column(Integer)
    old_values = Column(Text)  # JSON string
    new_values = Column(Text)  # JSON string
    ip_address = Column(String(45))
    user_agent = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_type': self.user_type,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class Database:
    """Database manager for Gem AI system"""
    
    def __init__(self, database_url: str = "sqlite:///gem_ai.db"):
        """Initialize database connection"""
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()
        self.initialize_default_settings()
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    def initialize_default_settings(self):
        """Initialize default system settings"""
        default_settings = [
            ('openai_api_key', '', 'OpenAI API key for AI grading', 'string'),
            ('max_file_size_mb', '50', 'Maximum file size for uploads in MB', 'integer'),
            ('supported_formats', '["pdf","docx","txt","jpg","png","mp3","mp4"]', 'Supported file formats', 'json'),
            ('grading_confidence_threshold', '0.8', 'Minimum AI confidence for auto-grading', 'float'),
            ('email_notifications_enabled', 'true', 'Enable email notifications', 'boolean'),
            ('batch_processing_limit', '100', 'Maximum files per batch', 'integer'),
            ('ai_model', 'gpt-4', 'AI model to use for grading', 'string'),
            ('plagiarism_threshold', '30', 'Plagiarism detection threshold (%)', 'integer'),
            ('default_grading_scale', '{"A+":97,"A":93,"A-":90,"B+":87,"B":83,"B-":80,"C+":77,"C":73,"C-":70,"D+":67,"D":60,"F":0}', 'Default grading scale', 'json')
        ]
        
        session = self.get_session()
        try:
            for key, value, desc, data_type in default_settings:
                setting = session.query(SystemSettings).filter_by(setting_key=key).first()
                if not setting:
                    setting = SystemSettings(
                        setting_key=key,
                        setting_value=value,
                        description=desc,
                        data_type=data_type
                    )
                    session.add(setting)
            session.commit()
            logger.info("Default settings initialized")
        except Exception as e:
            session.rollback()
            logger.error(f"Error initializing settings: {str(e)}")
        finally:
            session.close()
    
    def get_or_create_student(self, student_id: str, name: str, **kwargs) -> Student:
        """Get existing student or create new one"""
        session = self.get_session()
        try:
            student = session.query(Student).filter_by(student_id=student_id).first()
            if not student:
                student = Student(student_id=student_id, name=name, **kwargs)
                session.add(student)
                session.commit()
                logger.info(f"Created new student: {name} ({student_id})")
            return student
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating/getting student: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_or_create_lecturer(self, lecturer_id: str, name: str, email: str, **kwargs) -> Lecturer:
        """Get existing lecturer or create new one"""
        session = self.get_session()
        try:
            lecturer = session.query(Lecturer).filter_by(lecturer_id=lecturer_id).first()
            if not lecturer:
                lecturer = Lecturer(lecturer_id=lecturer_id, name=name, email=email, **kwargs)
                session.add(lecturer)
                session.commit()
                logger.info(f"Created new lecturer: {name} ({lecturer_id})")
            return lecturer
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating/getting lecturer: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_or_create_subject(self, code: str, name: str, **kwargs) -> Subject:
        """Get existing subject or create new one"""
        session = self.get_session()
        try:
            subject = session.query(Subject).filter_by(code=code).first()
            if not subject:
                subject = Subject(code=code, name=name, **kwargs)
                session.add(subject)
                session.commit()
                logger.info(f"Created new subject: {name} ({code})")
            return subject
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating/getting subject: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_or_create_exam(self, exam_name: str, subject_name: str, total_points: float, **kwargs) -> Exam:
        """Get existing exam or create new one"""
        session = self.get_session()
        try:
            # Generate exam code if not provided
            exam_code = kwargs.get('exam_code', f"EX_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            exam = session.query(Exam).filter_by(exam_code=exam_code).first()
            if not exam:
                exam = Exam(
                    exam_name=exam_name,
                    exam_code=exam_code,
                    total_points=total_points,
                    **kwargs
                )
                session.add(exam)
                session.commit()
                logger.info(f"Created new exam: {exam_name} ({exam_code})")
            return exam
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating/getting exam: {str(e)}")
            raise
        finally:
            session.close()
    
    def save_result(self, student_id: int, exam_id: int, total_score: float, 
                   percentage: float, letter_grade: str, detailed_results: str, **kwargs) -> Result:
        """Save exam result"""
        session = self.get_session()
        try:
            result = Result(
                student_id=student_id,
                exam_id=exam_id,
                total_score=total_score,
                percentage=percentage,
                letter_grade=letter_grade,
                detailed_results=detailed_results,
                grading_timestamp=datetime.utcnow(),
                **kwargs
            )
            session.add(result)
            session.commit()
            logger.info(f"Saved result for student {student_id}, exam {exam_id}: {total_score}")
            return result
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving result: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_student_results(self, student_id: str) -> dict:
        """Get all results for a student"""
        session = self.get_session()
        try:
            student = session.query(Student).filter_by(student_id=student_id).first()
            if not student:
                return []
            
            results = session.query(Result).filter_by(student_id=student.id).all()
            return [result.to_dict() for result in results]
        except Exception as e:
            logger.error(f"Error getting student results: {str(e)}")
            return []
        finally:
            session.close()
    
    def get_exam_results(self, exam_id: int) -> dict:
        """Get all results for an exam"""
        session = self.get_session()
        try:
            results = session.query(Result).filter_by(exam_id=exam_id).all()
            return [result.to_dict() for result in results]
        except Exception as e:
            logger.error(f"Error getting exam results: {str(e)}")
            return []
        finally:
            session.close()
    
    def get_exam_statistics(self, exam_id: int) -> dict:
        """Get statistical information for an exam"""
        session = self.get_session()
        try:
            results = session.query(Result).filter_by(exam_id=exam_id).all()
            if not results:
                return {}
            
            scores = [r.total_score for r in results]
            percentages = [r.percentage for r in results]
            
            import numpy as np
            
            stats = {
                'total_students': len(results),
                'average_score': np.mean(scores),
                'median_score': np.median(scores),
                'highest_score': np.max(scores),
                'lowest_score': np.min(scores),
                'standard_deviation': np.std(scores),
                'average_percentage': np.mean(percentages),
                'pass_rate': len([p for p in percentages if p >= 60]) / len(percentages) * 100,
                'grade_distribution': {}
            }
            
            # Calculate grade distribution
            grades = [r.letter_grade for r in results]
            for grade in set(grades):
                stats['grade_distribution'][grade] = grades.count(grade)
            
            return stats
        except Exception as e:
            logger.error(f"Error getting exam statistics: {str(e)}")
            return {}
        finally:
            session.close()
    
    def log_activity(self, user_id: str, user_type: str, action: str, 
                    entity_type: str, entity_id: int = None, **kwargs):
        """Log system activity for audit purposes"""
        session = self.get_session()
        try:
            audit_log = AuditLog(
                user_id=user_id,
                user_type=user_type,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                old_values=json.dumps(kwargs.get('old_values', {})),
                new_values=json.dumps(kwargs.get('new_values', {})),
                ip_address=kwargs.get('ip_address'),
                user_agent=kwargs.get('user_agent')
            )
            session.add(audit_log)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error logging activity: {str(e)}")
        finally:
            session.close()
    
    def get_setting(self, key: str, default=None):
        """Get system setting value"""
        session = self.get_session()
        try:
            setting = session.query(SystemSettings).filter_by(setting_key=key, is_active=True).first()
            if not setting:
                return default
            
            # Convert based on data type
            value = setting.setting_value
            if setting.data_type == 'integer':
                return int(value)
            elif setting.data_type == 'float':
                return float(value)
            elif setting.data_type == 'boolean':
                return value.lower() in ('true', '1', 'yes')
            elif setting.data_type == 'json':
                return json.loads(value)
            else:
                return value
        except Exception as e:
            logger.error(f"Error getting setting {key}: {str(e)}")
            return default
        finally:
            session.close()
    
    def set_setting(self, key: str, value, description: str = "", data_type: str = "string"):
        """Set system setting value"""
        session = self.get_session()
        try:
            setting = session.query(SystemSettings).filter_by(setting_key=key).first()
            
            # Convert value to string based on type
            if data_type == 'json':
                value_str = json.dumps(value)
            else:
                value_str = str(value)
            
            if setting:
                setting.setting_value = value_str
                setting.updated_at = datetime.utcnow()
            else:
                setting = SystemSettings(
                    setting_key=key,
                    setting_value=value_str,
                    description=description,
                    data_type=data_type
                )
                session.add(setting)
            
            session.commit()
            logger.info(f"Updated setting {key}: {value}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error setting {key}: {str(e)}")
            raise
        finally:
            session.close()
    
    def close(self):
        """Close database connection"""
        self.engine.dispose()
        logger.info("Database connection closed")
