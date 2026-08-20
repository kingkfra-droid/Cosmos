import flask
from flask import jsonify, request, render_template
import sqlite3
import os
from datetime import datetime
import json

# Initialize Flask app
app = flask.Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Database configuration
DATABASE = 'cosmos_facts.db'

def get_db_connection():
    """Establish database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with schema if it doesn't exist"""
    if not os.path.exists(DATABASE):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create claims table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                claim_text TEXT NOT NULL,
                verification_status TEXT NOT NULL,
                sources TEXT,
                author TEXT DEFAULT 'Anonymous',
                engagement INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create myths table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS myths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                myth_title TEXT NOT NULL,
                myth_description TEXT NOT NULL,
                debunked_explanation TEXT NOT NULL,
                scientific_evidence TEXT NOT NULL,
                sources TEXT,
                author TEXT DEFAULT 'Anonymous',
                engagement INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create quiz questions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                claim_id INTEGER,
                myth_id INTEGER,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                difficulty TEXT DEFAULT 'medium',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

# Simple AI-like responses using pattern matching
class CosmosAI:
    """Simple AI quiz generator for claims and myths"""
    
    @staticmethod
    def generate_quiz_question(claim_text: str, is_myth: bool = False) -> dict:
        """Generate a quiz question based on a claim"""
        question = ""
        answer = ""
        
        # Pattern-based question generation
        if is_myth:
            question = f"Is the following statement true or false: '{claim_text}'"
            answer = "This statement is FALSE according to scientific evidence. Use the debunked explanation and evidence provided to understand why."
        else:
            question = f"Can you verify this claim: '{claim_text}'"
            answer = "This claim requires scientific review. Check the sources and verification status to determine its validity."
        
        return {
            "question": question,
            "answer": answer,
            "explanation": "This is an AI-generated quiz based on the claim or myth in the database."
        }
    
    @staticmethod
    def analyze_claim(claim_text: str, sources: str = "") -> dict:
        """Analyze a claim and provide insights"""
        analysis = {
            "summary": f"Analyzing claim: {claim_text[:100]}...",
            "key_points": [
                "Check if the claim makes verifiable assertions",
                "Identify the scientific domain (physics, biology, medicine, etc.)",
                "Look for specific evidence or citations",
                "Consider alternative explanations"
            ],
            "questions_to_ask": [
                "What is the source of this claim?",
                "Can this be tested or verified?",
                "Are there peer-reviewed studies supporting it?",
                "Have other experts addressed this claim?"
            ],
            "confidence": "Medium - AI analysis provides guidance, human verification recommended"
        }
        return analysis
    
    @staticmethod
    def get_ai_response(query: str, context: str = "") -> dict:
        """Get AI response to user questions about claims"""
        responses = {
            "true": "Based on scientific evidence and peer-reviewed research, this claim appears to be TRUE.",
            "false": "This claim has been debunked by scientific evidence and research.",
            "pending": "This claim requires further scientific review and evidence gathering.",
            "misleading": "This claim may contain some truth but is misleading or oversimplified.",
            "unknown": "There is insufficient evidence to verify this claim at this time."
        }
        
        # Simple keyword matching
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['true', 'correct', 'verified', 'accurate']):
            response_type = "true"
        elif any(word in query_lower for word in ['false', 'wrong', 'debunk', 'incorrect']):
            response_type = "false"
        elif any(word in query_lower for word in ['maybe', 'possibly', 'unknown', 'uncertain']):
            response_type = "unknown"
        else:
            response_type = "pending"
        
        return {
            "response": responses.get(response_type, responses["pending"]),
            "type": response_type,
            "context": context,
            "ai_note": "This AI response is generated based on pattern matching. For critical decisions, consult scientific databases and peer-reviewed research."
        }

# Routes
@app.route('/', methods=['GET'])
def home():
    """Home endpoint - returns beautiful HTML dashboard"""
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/claims', methods=['GET'])
def get_claims():
    """Retrieve all claims with verification status"""
    try:
        conn = get_db_connection()
        claims = conn.execute('SELECT * FROM claims ORDER BY created_at DESC').fetchall()
        conn.close()
        
        claims_list = [dict(claim) for claim in claims]
        return jsonify({
            'status': 'success',
            'data': claims_list,
            'count': len(claims_list)
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/claims/<int:claim_id>', methods=['GET'])
def get_claim(claim_id):
    """Retrieve a specific claim by ID"""
    try:
        conn = get_db_connection()
        claim = conn.execute('SELECT * FROM claims WHERE id = ?', (claim_id,)).fetchone()
        conn.close()
        
        if claim is None:
            return jsonify({
                'status': 'error',
                'message': 'Claim not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': dict(claim)
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/claims', methods=['POST'])
def create_claim():
    """Create a new claim for fact-checking"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'claim_text', 'verification_status']
        if not all(field in data for field in required_fields):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), 400
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO claims (title, description, claim_text, verification_status, sources, author, engagement)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['title'],
            data.get('description', ''),
            data['claim_text'],
            data['verification_status'],
            data.get('sources', ''),
            data.get('author', 'Anonymous'),
            0
        ))
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Claim created successfully'
        }), 201
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/myths', methods=['GET'])
def get_myths():
    """Retrieve all debunked myths"""
    try:
        conn = get_db_connection()
        myths = conn.execute('SELECT * FROM myths ORDER BY created_at DESC').fetchall()
        conn.close()
        
        myths_list = [dict(myth) for myth in myths]
        return jsonify({
            'status': 'success',
            'data': myths_list,
            'count': len(myths_list)
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/myths/<int:myth_id>', methods=['GET'])
def get_myth(myth_id):
    """Retrieve a specific myth by ID"""
    try:
        conn = get_db_connection()
        myth = conn.execute('SELECT * FROM myths WHERE id = ?', (myth_id,)).fetchone()
        conn.close()
        
        if myth is None:
            return jsonify({
                'status': 'error',
                'message': 'Myth not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': dict(myth)
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/myths', methods=['POST'])
def create_myth():
    """Create a new debunked myth entry"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['myth_title', 'debunked_explanation']
        if not all(field in data for field in required_fields):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), 400
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO myths (myth_title, myth_description, debunked_explanation, scientific_evidence, sources, author, engagement)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['myth_title'],
            data.get('myth_description', ''),
            data['debunked_explanation'],
            data.get('scientific_evidence', ''),
            data.get('sources', ''),
            data.get('author', 'Anonymous'),
            0
        ))
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Myth created successfully'
        }), 201
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# AI Quiz Routes
@app.route('/api/quiz/generate/<int:claim_id>', methods=['GET'])
def generate_quiz_claim(claim_id):
    """Generate a quiz question for a specific claim"""
    try:
        conn = get_db_connection()
        claim = conn.execute('SELECT * FROM claims WHERE id = ?', (claim_id,)).fetchone()
        conn.close()
        
        if claim is None:
            return jsonify({
                'status': 'error',
                'message': 'Claim not found'
            }), 404
        
        quiz = CosmosAI.generate_quiz_question(claim['claim_text'], is_myth=False)
        
        return jsonify({
            'status': 'success',
            'data': quiz,
            'claim_id': claim_id
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/quiz/generate/myth/<int:myth_id>', methods=['GET'])
def generate_quiz_myth(myth_id):
    """Generate a quiz question for a specific myth"""
    try:
        conn = get_db_connection()
        myth = conn.execute('SELECT * FROM myths WHERE id = ?', (myth_id,)).fetchone()
        conn.close()
        
        if myth is None:
            return jsonify({
                'status': 'error',
                'message': 'Myth not found'
            }), 404
        
        quiz = CosmosAI.generate_quiz_question(myth['myth_title'], is_myth=True)
        
        return jsonify({
            'status': 'success',
            'data': quiz,
            'myth_id': myth_id
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/ai/ask', methods=['POST'])
def ask_ai():
    """Ask the AI about a claim or get analysis"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        claim_id = data.get('claim_id')
        myth_id = data.get('myth_id')
        claim_text = data.get('claim_text', '')
        
        if not query:
            return jsonify({
                'status': 'error',
                'message': 'Query is required'
            }), 400
        
        context = ""
        
        # Get context from claim or myth
        if claim_id:
            conn = get_db_connection()
            claim = conn.execute('SELECT * FROM claims WHERE id = ?', (claim_id,)).fetchone()
            conn.close()
            if claim:
                context = f"Claim: {claim['claim_text']}"
                claim_text = claim['claim_text']
        elif myth_id:
            conn = get_db_connection()
            myth = conn.execute('SELECT * FROM myths WHERE id = ?', (myth_id,)).fetchone()
            conn.close()
            if myth:
                context = f"Myth: {myth['myth_title']}"
                claim_text = myth['myth_title']
        
        # Get AI response
        response = CosmosAI.get_ai_response(query, context)
        
        return jsonify({
            'status': 'success',
            'data': response
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/ai/analyze', methods=['POST'])
def analyze_claim_endpoint():
    """Analyze a claim using AI"""
    try:
        data = request.get_json()
        claim_text = data.get('claim_text', '')
        sources = data.get('sources', '')
        
        if not claim_text:
            return jsonify({
                'status': 'error',
                'message': 'Claim text is required'
            }), 400
        
        analysis = CosmosAI.analyze_claim(claim_text, sources)
        
        return jsonify({
            'status': 'success',
            'data': analysis
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
