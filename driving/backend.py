#!/usr/bin/env python3
"""
Flask backend for the Interactive Driving Study Material
Serves content from SQLite database
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

DATABASE = 'driving_study_material.db'

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/sections', methods=['GET'])
def get_sections():
    """Get all sections"""
    conn = get_db_connection()
    sections = conn.execute('SELECT * FROM Section').fetchall()
    conn.close()
    
    return jsonify([dict(section) for section in sections])

@app.route('/api/sections/<int:section_id>', methods=['GET'])
def get_section(section_id):
    """Get specific section by ID"""
    conn = get_db_connection()
    section = conn.execute('SELECT * FROM Section WHERE id = ?', (section_id,)).fetchone()
    conn.close()
    
    if section is None:
        return jsonify({'error': 'Section not found'}), 404
    
    return jsonify(dict(section))

@app.route('/api/quiz/<int:section_id>', methods=['GET'])
def get_quiz_questions(section_id):
    """Get quiz questions for a specific section"""
    conn = get_db_connection()
    questions = conn.execute(
        'SELECT * FROM QuizQuestion WHERE section_id = ?', 
        (section_id,)
    ).fetchall()
    conn.close()
    
    quiz_data = []
    for question in questions:
        quiz_item = dict(question)
        quiz_item['options'] = json.loads(quiz_item['options'])
        quiz_data.append(quiz_item)
    
    return jsonify(quiz_data)

@app.route('/api/quiz/all', methods=['GET'])
def get_all_quiz_questions():
    """Get all quiz questions"""
    conn = get_db_connection()
    questions = conn.execute('SELECT * FROM QuizQuestion').fetchall()
    conn.close()
    
    quiz_data = []
    for question in questions:
        quiz_item = dict(question)
        quiz_item['options'] = json.loads(quiz_item['options'])
        quiz_data.append(quiz_item)
    
    return jsonify(quiz_data)

@app.route('/api/search', methods=['GET'])
def search_content():
    """Search content across sections"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    conn = get_db_connection()
    results = conn.execute(
        'SELECT * FROM Section WHERE title LIKE ? OR content LIKE ?',
        (f'%{query}%', f'%{query}%')
    ).fetchall()
    conn.close()
    
    return jsonify([dict(result) for result in results])

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get application statistics"""
    conn = get_db_connection()
    
    section_count = conn.execute('SELECT COUNT(*) as count FROM Section').fetchone()['count']
    question_count = conn.execute('SELECT COUNT(*) as count FROM QuizQuestion').fetchone()['count']
    
    conn.close()
    
    return jsonify({
        'total_sections': section_count,
        'total_questions': question_count
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Backend is running'})

if __name__ == '__main__':
    print("Starting Flask backend...")
    print("API will be available at: http://localhost:5001")
    print("Available endpoints:")
    print("  - GET /api/sections - Get all sections")
    print("  - GET /api/sections/<id> - Get specific section")
    print("  - GET /api/quiz/<section_id> - Get quiz questions for section")
    print("  - GET /api/quiz/all - Get all quiz questions")
    print("  - GET /api/search?q=<query> - Search content")
    print("  - GET /api/stats - Get statistics")
    print("  - GET /api/health - Health check")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
