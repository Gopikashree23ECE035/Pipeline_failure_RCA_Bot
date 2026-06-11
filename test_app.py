import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("RCA-PostgreSQL-Test")

def check_imports():
    logger.info("Step 1: Checking imports...")
    try:
        import flask
        import flask_sqlalchemy
        import psycopg2
        import requests
        import dotenv
        import reportlab
        logger.info("SUCCESS: All required packages (including SQLAlchemy and ReportLab) imported correctly.")
        return True
    except ImportError as e:
        logger.error(f"FAILURE: Missing package. Install using: pip install -r requirements.txt. Details: {e}")
        return False

def verify_app_and_db():
    logger.info("Step 2: Checking Flask app connection to PostgreSQL database...")
    try:
        from app import create_app
        from models import db, Log
        from services.db_service import DBService
        
        app = create_app()
        with app.app_context():
            log_count = Log.query.count()
            logger.info(f"DB STATUS: SQLAlchemy database connected. Existing logs count: {log_count}")

            stats = DBService.get_dashboard_stats()
            logger.info(f"SUCCESS: Statistics query verified. Existing reports: {stats['total_reports']}, Logs: {stats['total_logs']}")
            
        return True
    except Exception as e:
        logger.error(f"FAILURE: Could not verify App or PostgreSQL initialization. Details: {e}")
        return False

def verify_ollama():
    logger.info("Step 3: Checking Ollama service status...")
    from config import Config
    from services.ollama_service import OllamaService
    
    ollama = OllamaService(Config.OLLAMA_API_URL, Config.OLLAMA_MODEL)
    if ollama.check_connection():
        logger.info(f"SUCCESS: Ollama connected successfully at {Config.OLLAMA_API_URL}. Model '{Config.OLLAMA_MODEL}' status verified.")
    else:
        logger.warning(f"OFFLINE: Ollama is unreachable at {Config.OLLAMA_API_URL}. AI analysis will run in local rule-based simulation fallback mode.")
    return True

def verify_pdf():
    logger.info("Step 4: Checking PDF generation pipeline...")
    try:
        from services.pdf_service import PDFService
        from datetime import datetime
        
        class MockReport:
            id = 9999
            failure_summary = "Sanity test failure log summary."
            root_cause = "Sanity test root cause trace."
            severity = "High"
            confidence_score = "99%"
            recommendation = "Patch verification code."
            retry_steps = "1. Clean up.\n2. Rerun script."
            created_at = datetime.utcnow()
            github_analysis = None

        report = MockReport()
        pdf_stream = PDFService.generate_rca_pdf(report)
        pdf_size = len(pdf_stream.getvalue())
        
        if pdf_size > 0:
            logger.info(f"SUCCESS: PDF generated correctly. Compiled size: {pdf_size} bytes.")
            return True
        else:
            logger.error("FAILURE: Generated PDF was empty.")
            return False
    except Exception as e:
        logger.error(f"FAILURE: PDF generation compilation crashed. Error details: {e}")
        return False

if __name__ == '__main__':
    logger.info("=== STARTING PIPELINE FAILURE RCA BOT SANITY VERIFICATION (PostgreSQL) ===")
    
    # Run tests
    all_ok = True
    all_ok &= check_imports()
    all_ok &= verify_app_and_db()
    all_ok &= verify_ollama()
    all_ok &= verify_pdf()
    
    if all_ok:
        logger.info("=== ALL SANITY TESTS COMPLETED SUCCESSFULLY ===")
        sys.exit(0)
    else:
        logger.error("=== SOME SANITY CHECKS FAILED ===")
        sys.exit(1)
