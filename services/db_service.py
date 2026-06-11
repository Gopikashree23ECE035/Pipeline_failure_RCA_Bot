from datetime import datetime
import logging
from models import db, Log, GithubAnalysis, Report

logger = logging.getLogger(__name__)

class DBService:
    @staticmethod
    def save_log(filename, log_type, content):
        """
        Saves a pipeline log to the logs table.
        """
        try:
            log = Log(
                filename=filename,
                log_type=log_type,
                content=content,
                uploaded_at=datetime.utcnow()
            )
            db.session.add(log)
            db.session.commit()
            return log
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving log to PostgreSQL: {e}")
            raise

    @staticmethod
    def get_latest_success_log():
        """
        Retrieves the most recently uploaded successful pipeline log.
        """
        try:
            return Log.query.filter_by(log_type='success').order_by(Log.uploaded_at.desc()).first()
        except Exception as e:
            logger.error(f"Error fetching latest success log: {e}")
            return None

    @staticmethod
    def save_github_analysis(commit_id, changed_files, diff_summary):
        """
        Saves GitHub analysis results to the database.
        """
        try:
            github_analysis = GithubAnalysis(
                commit_id=commit_id,
                changed_files=changed_files or [],
                diff_summary=diff_summary,
                analyzed_at=datetime.utcnow()
            )
            db.session.add(github_analysis)
            db.session.commit()
            return github_analysis
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving GitHub analysis to PostgreSQL: {e}")
            raise

    @staticmethod
    def save_report(failure_summary, root_cause, severity, confidence_score, recommendation, retry_steps, log_id=None, github_analysis_id=None):
        """
        Saves an RCA report to the database.
        """
        try:
            report = Report(
                failure_summary=failure_summary,
                root_cause=root_cause,
                severity=severity,
                confidence_score=confidence_score,
                recommendation=recommendation,
                retry_steps=retry_steps,
                created_at=datetime.utcnow(),
                log_id=log_id,
                github_analysis_id=github_analysis_id
            )
            db.session.add(report)
            db.session.commit()
            return report
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving report to PostgreSQL: {e}")
            raise

    @staticmethod
    def get_report_by_id(report_id):
        """
        Retrieves a report by its primary key ID.
        """
        try:
            return Report.query.get(report_id)
        except Exception as e:
            logger.error(f"Error fetching report by id: {e}")
            return None

    @staticmethod
    def get_all_reports():
        """
        Retrieves all generated reports, ordered newest first.
        """
        try:
            return Report.query.order_by(Report.created_at.desc()).all()
        except Exception as e:
            logger.error(f"Error fetching all reports: {e}")
            return []

    @staticmethod
    def get_dashboard_stats():
        """
        Gathers key statistics for the dashboard UI.
        """
        try:
            total_reports = Report.query.count()
            total_logs = Log.query.count()

            severity_counts = {
                "Critical": Report.query.filter_by(severity="Critical").count(),
                "High": Report.query.filter_by(severity="High").count(),
                "Medium": Report.query.filter_by(severity="Medium").count(),
                "Low": Report.query.filter_by(severity="Low").count(),
            }

            reports = Report.query.all()
            total_conf = 0.0
            conf_count = 0
            for r in reports:
                conf_str = r.confidence_score
                if conf_str:
                    clean_conf = str(conf_str).replace('%', '').strip()
                    try:
                        total_conf += float(clean_conf)
                        conf_count += 1
                    except ValueError:
                        val_map = {"high": 85.0, "medium": 65.0, "low": 45.0}
                        mapped_val = val_map.get(clean_conf.lower())
                        if mapped_val is not None:
                            total_conf += mapped_val
                            conf_count += 1

            avg_confidence = f"{round(total_conf / conf_count, 1)}%" if conf_count > 0 else "N/A"
            recent_reports = Report.query.order_by(Report.created_at.desc()).limit(5).all()

            return {
                "total_reports": total_reports,
                "total_logs": total_logs,
                "severity_counts": severity_counts,
                "avg_confidence": avg_confidence,
                "recent_reports": recent_reports
            }
        except Exception as e:
            logger.error(f"Error computing dashboard statistics: {e}")
            return {
                "total_reports": 0,
                "total_logs": 0,
                "severity_counts": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
                "avg_confidence": "N/A",
                "recent_reports": []
            }
