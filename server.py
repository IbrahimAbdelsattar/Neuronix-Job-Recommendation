from flask import Flask, request, jsonify, send_from_directory, send_file, make_response
from flask_cors import CORS
import os
import hashlib
from werkzeug.utils import secure_filename

# Use enhanced versions with fallback to original
try:
    from scraper_enhanced import scrape_jobs
    print("✓ Using enhanced scraper")
except ImportError:
    from scraper import scrape_jobs
    print("⚠ Using original scraper")

try:
    from matcher_enhanced import match_jobs
    print("✓ Using enhanced matcher")
except ImportError:
    from matcher import match_jobs
    print("⚠ Using original matcher")

from cv_parser import CVParser
import database as db
import email_utils
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
from datetime import datetime

app = Flask(__name__, static_folder='src')
CORS(app)

# Initialize database
db.init_database()

# Serve static files (Frontend)
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# Helper function
def hash_password(password):
    """Simple password hashing (use bcrypt in production)."""
    return hashlib.sha256(password.encode()).hexdigest()

# ============= JOB RECOMMENDATION ENDPOINTS =============

@app.route('/api/recommend/form', methods=['POST'])
def recommend_form():
    try:
        data = request.json
        jobs = scrape_jobs(data.get('job_title', ''), data.get('location', ''))
        matched_jobs = match_jobs(data, jobs)
        
        user_id = data.get('user_id')
        keywords = ', '.join(data.get('skills', [])) if isinstance(data.get('skills'), list) else data.get('skills', '')
        search_id = db.save_search(user_id, 'form', data, keywords)
        db.save_job_results(search_id, matched_jobs)
        
        return jsonify({"status": "success", "jobs": matched_jobs, "search_id": search_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/recommend/chat', methods=['POST'])
def recommend_chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        
        jobs = scrape_jobs(user_message, "")
        matched_jobs = match_jobs({"keywords": user_message}, jobs)
        
        user_id = data.get('user_id')
        search_id = db.save_search(user_id, 'chat', {'message': user_message}, user_message[:100])
        db.save_job_results(search_id, matched_jobs)
        
        return jsonify({"status": "success", "jobs": matched_jobs, "search_id": search_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/recommend/cv', methods=['POST'])
def recommend_cv():
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file uploaded"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No selected file"}), 400
            
        # Save file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join("temp_uploads", filename)
        os.makedirs("temp_uploads", exist_ok=True)
        file.save(temp_path)
        
        try:
            # Parse CV
            parser = CVParser()
            parsed_data = parser.parse(temp_path)
            
            if "error" in parsed_data:
                return jsonify({"status": "error", "message": parsed_data["error"]}), 400
                
            extracted_skills = parsed_data.get("skills", [])
            job_title = parsed_data.get("job_title", "Unknown")
            
            # Convert list to string for matching if needed, or keep as list
            # The matcher expects a dictionary with 'skills'
            
            # Scrape jobs based on extracted job title or skills
            search_query = job_title if job_title != "Unknown" else "Software Engineer"
            if not search_query and extracted_skills:
                search_query = extracted_skills[0]
                
            jobs = scrape_jobs(search_query, "")
            
            # Match jobs
            user_profile = {
                "skills": extracted_skills,
                "job_title": job_title
            }
            matched_jobs = match_jobs(user_profile, jobs)
            
            user_id = request.form.get('user_id')
            skills_str = ", ".join(extracted_skills) if extracted_skills else ""
            
            search_id = db.save_search(user_id, 'cv', {'filename': filename, 'parsed_data': parsed_data}, skills_str)
            db.save_job_results(search_id, matched_jobs)
            
            return jsonify({
                "status": "success", 
                "jobs": matched_jobs, 
                "search_id": search_id,
                "parsed_data": parsed_data
            })
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ============= AUTHENTICATION ENDPOINTS =============

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')
        
        if not all([email, password]):
            return jsonify({"status": "error", "message": "Email and password required"}), 400
        
        password_hash = hash_password(password)
        user_id = db.create_user(email, password_hash, full_name)
        
        if user_id is None:
            return jsonify({"status": "error", "message": "Email already exists"}), 400
        
        # Send welcome email
        email_utils.send_welcome_email(email, full_name or 'User')
        
        return jsonify({"status": "success", "message": "Account created successfully", "user_id": user_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not all([email, password]):
            return jsonify({"status": "error", "message": "Email and password required"}), 400
        
        user = db.get_user_by_email(email)
        
        if not user or user['password_hash'] != hash_password(password):
            return jsonify({"status": "error", "message": "Invalid credentials"}), 401
        
        db.update_last_login(user['id'])
        
        return jsonify({
            "status": "success",
            "message": "Login successful",
            "user": {
                "id": user['id'],
                "email": user['email'],
                "full_name": user['full_name']
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.json
        email = data.get('email')
        
        if not email:
            return jsonify({"status": "error", "message": "Email required"}), 400
        
        # Get user to check if email exists and get name
        user = db.get_user_by_email(email)
        if not user:
            # Don't reveal if email exists or not for security
            return jsonify({
                "status": "success",
                "message": "If the email exists, a reset link has been sent"
            })
        
        token = db.create_reset_token(email)
        
        if not token:
            return jsonify({"status": "error", "message": "Failed to generate reset token"}), 500
        
        # Send email with reset link
        email_sent = email_utils.send_password_reset_email(email, token, user.get('full_name'))
        
        if email_sent:
            return jsonify({
                "status": "success",
                "message": "Password reset instructions have been sent to your email"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to send email. Please try again later."
            }), 500
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.json
        token = data.get('token')
        new_password = data.get('new_password')
        
        if not all([token, new_password]):
            return jsonify({"status": "error", "message": "Token and new password required"}), 400
        
        user_id = db.verify_reset_token(token)
        
        if not user_id:
            return jsonify({"status": "error", "message": "Invalid or expired token"}), 400
        
        new_password_hash = hash_password(new_password)
        db.update_user_password(user_id, new_password_hash)
        db.mark_token_used(token)
        
        return jsonify({"status": "success", "message": "Password reset successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ============= USER PROFILE ENDPOINTS =============

@app.route('/api/user/profile', methods=['GET'])
def get_profile():
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"status": "error", "message": "User ID required"}), 400
        
        user = db.get_user_by_id(int(user_id))
        
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404
        
        # Don't send password hash
        user.pop('password_hash', None)
        
        return jsonify({"status": "success", "user": user})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/user/profile', methods=['PUT'])
def update_profile():
    try:
        data = request.json
        user_id = data.get('user_id')
        full_name = data.get('full_name')
        email = data.get('email')
        
        if not user_id:
            return jsonify({"status": "error", "message": "User ID required"}), 400
        
        success = db.update_user_profile(int(user_id), full_name, email)
        
        if not success:
            return jsonify({"status": "error", "message": "Email already exists"}), 400
        
        return jsonify({"status": "success", "message": "Profile updated successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/user/change-password', methods=['POST'])
def change_password():
    try:
        data = request.json
        user_id = data.get('user_id')
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not all([user_id, current_password, new_password]):
            return jsonify({"status": "error", "message": "All fields required"}), 400
        
        user = db.get_user_by_id(int(user_id))
        
        if not user or user['password_hash'] != hash_password(current_password):
            return jsonify({"status": "error", "message": "Current password incorrect"}), 401
        
        new_password_hash = hash_password(new_password)
        db.update_user_password(int(user_id), new_password_hash)
        
        return jsonify({"status": "success", "message": "Password changed successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/user/upload-photo', methods=['POST'])
def upload_photo():
    try:
        if 'photo' not in request.files:
            return jsonify({"status": "error", "message": "No photo uploaded"}), 400
        
        user_id = request.form.get('user_id')
        if not user_id:
            return jsonify({"status": "error", "message": "User ID required"}), 400
        
        photo = request.files['photo']
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        filename = photo.filename
        if not filename or '.' not in filename:
            return jsonify({"status": "error", "message": "Invalid file"}), 400
        
        ext = filename.rsplit('.', 1)[1].lower()
        if ext not in allowed_extensions:
            return jsonify({"status": "error", "message": "Invalid file type. Allowed: png, jpg, jpeg, gif, webp"}), 400
        
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(app.static_folder, 'uploads', 'profiles')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Generate unique filename
        import uuid
        unique_filename = f"{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
        filepath = os.path.join(uploads_dir, unique_filename)
        
        # Save file
        photo.save(filepath)
        
        # Update database
        photo_url = f"/uploads/profiles/{unique_filename}"
        db.update_profile_photo(int(user_id), photo_url)
        
        return jsonify({
            "status": "success",
            "message": "Photo uploaded successfully",
            "photo_url": photo_url
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ============= SEARCH HISTORY & SAVED JOBS =============

@app.route('/api/user/searches', methods=['GET'])
def get_searches():
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"status": "error", "message": "User ID required"}), 400
        
        searches = db.get_user_searches(int(user_id))
        
        return jsonify({"status": "success", "searches": searches})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/search/<int:search_id>/results', methods=['GET'])
def get_search_results_api(search_id):
    try:
        results = db.get_search_results(search_id)
        return jsonify({"status": "success", "jobs": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/user/save-job', methods=['POST'])
def save_job_endpoint():
    try:
        data = request.json
        user_id = data.get('user_id')
        job_result_id = data.get('job_result_id')
        notes = data.get('notes', '')
        
        if not all([user_id, job_result_id]):
            return jsonify({"status": "error", "message": "User ID and job ID required"}), 400
        
        saved_id = db.save_job(int(user_id), int(job_result_id), notes)
        
        if saved_id is None:
            return jsonify({"status": "error", "message": "Job already saved"}), 400
        
        return jsonify({"status": "success", "message": "Job saved successfully", "saved_id": saved_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/user/saved-jobs', methods=['GET'])
def get_saved_jobs_endpoint():
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"status": "error", "message": "User ID required"}), 400
        
        saved_jobs = db.get_saved_jobs(int(user_id))
        
        return jsonify({"status": "success", "jobs": saved_jobs})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/user/saved-job/<int:saved_id>', methods=['DELETE'])
def unsave_job_endpoint(saved_id):
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"status": "error", "message": "User ID required"}), 400
        
        db.unsave_job(int(user_id), saved_id)
        
        return jsonify({"status": "success", "message": "Job removed from saved"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ============= CONTACT FORM =============

@app.route('/api/contact', methods=['POST'])
def contact_submit():
    try:
        data = request.json
        name = data.get('name')
        email = data.get('email')
        subject = data.get('subject', '')
        message = data.get('message')
        
        if not all([name, email, message]):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400
        
        submission_id = db.save_contact_submission(name, email, subject, message)
        
        return jsonify({"status": "success", "message": "Thank you for contacting us!", "id": submission_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ============= PDF EXPORT =============

@app.route('/api/export/pdf', methods=['POST'])
def export_pdf():
    try:
        data = request.json
        jobs = data.get('jobs', [])
        user_name = data.get('user_name', 'User')
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#6366f1'),
            spaceAfter=30,
        )
        elements.append(Paragraph(f"Job Recommendations for {user_name}", title_style))
        elements.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Jobs
        for idx, job in enumerate(jobs, 1):
            # Job header
            job_title_style = ParagraphStyle(
                'JobTitle',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#1e293b'),
                spaceAfter=10,
            )
            elements.append(Paragraph(f"{idx}. {job.get('title', 'N/A')}", job_title_style))
            
            # Job details table
            job_data = [
                ['Company:', job.get('company', 'N/A')],
                ['Location:', job.get('location', 'N/A')],
                ['Match Score:', f"{job.get('match_score', 0)}%"],
                ['Platform:', job.get('platform', 'N/A')],
            ]
            
            job_table = Table(job_data, colWidths=[1.5*inch, 4.5*inch])
            job_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#64748b')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(job_table)
            elements.append(Spacer(1, 0.1*inch))
            
            # Description
            desc = job.get('description', 'No description available')[:300] + '...'
            elements.append(Paragraph(f"<b>Description:</b> {desc}", styles['Normal']))
            
            # Skills
            skills = job.get('skills', [])
            if skills:
                skills_text = ', '.join(skills[:10])
                elements.append(Paragraph(f"<b>Skills:</b> {skills_text}", styles['Normal']))
            
            elements.append(Spacer(1, 0.3*inch))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        # Send file
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'job_recommendations_{datetime.now().strftime("%Y%m%d")}.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("Starting Neuronix AI JobFlow Server...")
    app.run(debug=True, port=5000)
