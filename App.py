import flask
from flask import jsonify, request, render_template
import sqlite3
import os
from datetime import datetime

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
        
        conn.commit()
        conn.close()

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
