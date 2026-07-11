import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from resume_analyzer import process_resume
from db_integration import get_user_ai_profile

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"success": True, "message": "AutoJobApply AI Engine running ✅"})

@app.route('/api/ai/analyze_resume', methods=['POST'])
def analyze_resume_endpoint():
    """
    POST /api/ai/analyze_resume
    Body: { "user_id": int, "resume_text": str }
    """
    data = request.json or {}
    user_id = data.get('user_id')
    resume_text = data.get('resume_text', '').strip()
    
    if not user_id or not resume_text:
        return jsonify({"success": False, "message": "user_id and resume_text are required"}), 400
        
    try:
        results = process_resume(int(user_id), resume_text)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/ai/profile_summary', methods=['GET'])
def get_profile_summary():
    """
    GET /api/ai/profile_summary?user_id=1
    """
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "user_id is required"}), 400
        
    try:
        profile = get_user_ai_profile(int(user_id))
        if not profile:
            return jsonify({"success": False, "message": "Profile not found"}), 404
            
        return jsonify({"success": True, "summary": profile.get("summary")})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/ai/generated_keywords', methods=['GET'])
def get_generated_keywords():
    """
    GET /api/ai/generated_keywords?user_id=1
    """
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "user_id is required"}), 400
        
    try:
        profile = get_user_ai_profile(int(user_id))
        if not profile:
            return jsonify({"success": False, "message": "Profile not found"}), 404
            
        return jsonify({"success": True, "keywords": profile.get("ai_keywords", [])})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/ai/job_titles', methods=['GET'])
def get_job_titles():
    """
    GET /api/ai/job_titles?user_id=1
    """
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "user_id is required"}), 400
        
    try:
        profile = get_user_ai_profile(int(user_id))
        if not profile:
            return jsonify({"success": False, "message": "Profile not found"}), 404
            
        return jsonify({"success": True, "job_titles": profile.get("ai_job_titles", [])})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    # Run on a different port than Node (3000) and Automation (5001)
    port = int(os.environ.get('AI_PORT', 5002))
    print(f"\n🧠 AutoJobApply AI Engine started on http://localhost:{port}\n")
    app.run(host='0.0.0.0', port=port, debug=False)
