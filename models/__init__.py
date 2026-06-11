import logging
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger(__name__)

db = SQLAlchemy()

class Log(db.Model):
    __tablename__ = 'logs'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    log_type = db.Column(db.String(32), nullable=False)
    content = db.Column(db.Text, nullable=False)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    reports = db.relationship('Report', back_populates='log', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Log id={self.id} filename={self.filename} log_type={self.log_type}>"

class GithubAnalysis(db.Model):
    __tablename__ = 'github_analysis'

    id = db.Column(db.Integer, primary_key=True)
    commit_id = db.Column(db.String(128), nullable=True)
    changed_files = db.Column(db.JSON, nullable=False, default=list)
    diff_summary = db.Column(db.Text, nullable=True)
    analyzed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    report = db.relationship('Report', back_populates='github_analysis', uselist=False)

    def __repr__(self):
        return f"<GithubAnalysis id={self.id} commit_id={self.commit_id}>"

class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    failure_summary = db.Column(db.Text, nullable=False)
    root_cause = db.Column(db.Text, nullable=True)
    severity = db.Column(db.String(32), nullable=True)
    confidence_score = db.Column(db.String(32), nullable=True)
    recommendation = db.Column(db.Text, nullable=True)
    retry_steps = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    log_id = db.Column(db.Integer, db.ForeignKey('logs.id'), nullable=True)
    github_analysis_id = db.Column(db.Integer, db.ForeignKey('github_analysis.id'), nullable=True)

    log = db.relationship('Log', back_populates='reports')
    github_analysis = db.relationship('GithubAnalysis', back_populates='report')

    def __repr__(self):
        return f"<Report id={self.id} severity={self.severity}>"


def init_db(app):
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
    db.init_app(app)
    with app.app_context():
        db.create_all()

    logger.info('Initialized PostgreSQL database and created tables.')
