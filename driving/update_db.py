#!/usr/bin/env python3
"""
Python script to update the SQLite database using JSON content files.
"""

import json
import sqlite3
import os

# Database connection
DB_PATH = 'driving_study_material.db'

# Open database connection
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Clear existing tables
cursor.execute('DELETE FROM Section')
cursor.execute('DELETE FROM QuizQuestion')

# Function to load section data from JSON
def load_sections_from_json(file_path):
    with open(file_path, 'r') as json_file:
        sections = json.load(json_file)
        for section in sections:
            title = section['title']
            content = section['content']
            cursor.execute('''
                INSERT INTO Section (title, content) VALUES (?, ?)
            ''', (title, content))

# Function to load quiz data from JSON
def load_quizzes_from_json(file_path):
    with open(file_path, 'r') as json_file:
        quizzes = json.load(json_file)
        for quiz in quizzes:
            section_id = quiz['section_id']
            question = quiz['question']
            options = json.dumps(quiz['options'])
            answer = quiz['answer']
            explanation = quiz['explanation']
            cursor.execute('''
                INSERT INTO QuizQuestion (section_id, question, options, answer, explanation) 
                VALUES (?, ?, ?, ?, ?)
            ''', (section_id, question, options, answer, explanation))

# Section JSON files to process
section_files = [
    'section_batch_1.json', 
    'section_batch_2.json', 
    'section_batch_3.json',
    'comprehesive_section.json',
    'generated_sections.json'
]

print("Loading sections...")
for json_file in section_files:
    if os.path.exists(json_file):
        load_sections_from_json(json_file)
        print(f"Loaded {json_file}")
    else:
        print(f"{json_file} not found!")

# Quiz JSON files to process
quiz_files = [
    'quiz_batch_1.json', 
    'quiz_batch_2.json', 
    'quiz_batch_3.json',
    'comprehenisve_quizz.json',
    'generated_quizzes.json',
    'additional_quizzes.json'
]

print("Loading quiz questions...")
for json_file in quiz_files:
    if os.path.exists(json_file):
        load_quizzes_from_json(json_file)
        print(f"Loaded {json_file}")
    else:
        print(f"{json_file} not found!")

# Commit changes and close connection
conn.commit()
conn.close()
print('Database updated with comprehensive content and quiz questions from JSON files!')

