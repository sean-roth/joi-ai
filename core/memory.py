"""
Memory management for Joi
Stores conversations and retrieves relevant context
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import hashlib
from loguru import logger

class MemoryManager:
    """Manages Joi's long-term memory"""
    
    def __init__(self, db_path: str = "joi_memory.db"):
        self.db_path = db_path
        self.initialize_database()
    
    def initialize_database(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_message TEXT NOT NULL,
                joi_response TEXT NOT NULL,
                backend TEXT,
                model TEXT,
                embedding_hash TEXT,
                metadata TEXT
            )
        ''')
        
        # Topics table for semantic grouping
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TEXT,
                last_discussed TEXT
            )
        ''')
        
        # Conversation-topic mapping
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_topics (
                conversation_id INTEGER,
                topic_id INTEGER,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id),
                FOREIGN KEY (topic_id) REFERENCES topics (id)
            )
        ''')
        
        # Important memories (manually marked or auto-detected)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS important_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                importance_score REAL,
                note TEXT,
                created_at TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Memory database initialized")
    
    def store_conversation(self, user_message: str, joi_response: str, 
                          backend: str = None, model: str = None, 
                          metadata: Dict = None):
        """Store a conversation exchange"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Generate embedding hash (placeholder for actual embeddings)
        embedding_hash = hashlib.md5(
            (user_message + joi_response).encode()
        ).hexdigest()
        
        cursor.execute('''
            INSERT INTO conversations 
            (timestamp, user_message, joi_response, backend, model, embedding_hash, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            user_message,
            joi_response,
            backend,
            model,
            embedding_hash,
            json.dumps(metadata or {})
        ))
        
        conversation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Check if this should be marked as important
        self.check_importance(conversation_id, user_message, joi_response)
        
        return conversation_id
    
    def check_importance(self, conversation_id: int, user_message: str, joi_response: str):
        """Determine if a conversation should be marked as important"""
        importance_keywords = [
            'remember this', 'important', 'don\'t forget',
            'for future reference', 'keep in mind'
        ]
        
        importance_score = 0.0
        
        # Check for explicit importance markers
        for keyword in importance_keywords:
            if keyword in user_message.lower():
                importance_score = 1.0
                break
        
        # Check for personal information
        personal_markers = ['my name is', 'i work at', 'i live in', 'my favorite']
        for marker in personal_markers:
            if marker in user_message.lower():
                importance_score = max(importance_score, 0.8)
        
        # Store if important
        if importance_score > 0.5:
            self.mark_important(conversation_id, importance_score)
    
    def mark_important(self, conversation_id: int, importance_score: float, note: str = None):
        """Mark a conversation as important"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO important_memories (conversation_id, importance_score, note, created_at)
            VALUES (?, ?, ?, ?)
        ''', (
            conversation_id,
            importance_score,
            note,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        """Get recent conversation history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, user_message, joi_response, backend, model
            FROM conversations
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                'timestamp': row[0],
                'user_message': row[1],
                'joi_response': row[2],
                'backend': row[3],
                'model': row[4]
            })
        
        conn.close()
        return list(reversed(conversations))  # Return in chronological order
    
    def search_memories(self, query: str, limit: int = 5) -> List[Dict]:
        """Search through memories for relevant context"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Simple keyword search (can be enhanced with embeddings)
        cursor.execute('''
            SELECT c.timestamp, c.user_message, c.joi_response, 
                   im.importance_score
            FROM conversations c
            LEFT JOIN important_memories im ON c.id = im.conversation_id
            WHERE c.user_message LIKE ? OR c.joi_response LIKE ?
            ORDER BY im.importance_score DESC NULLS LAST, c.timestamp DESC
            LIMIT ?
        ''', (f'%{query}%', f'%{query}%', limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'timestamp': row[0],
                'user_message': row[1],
                'joi_response': row[2],
                'importance': row[3] if row[3] else 0.0
            })
        
        conn.close()
        return results
    
    def get_important_memories(self) -> List[Dict]:
        """Get all important memories"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.timestamp, c.user_message, c.joi_response, 
                   im.importance_score, im.note
            FROM important_memories im
            JOIN conversations c ON im.conversation_id = c.id
            ORDER BY im.importance_score DESC
        ''')
        
        memories = []
        for row in cursor.fetchall():
            memories.append({
                'timestamp': row[0],
                'user_message': row[1],
                'joi_response': row[2],
                'importance': row[3],
                'note': row[4]
            })
        
        conn.close()
        return memories
    
    def get_statistics(self) -> Dict:
        """Get memory statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM conversations')
        total_conversations = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM important_memories')
        important_memories = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT DATE(timestamp)) FROM conversations')
        days_active = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_conversations': total_conversations,
            'important_memories': important_memories,
            'days_active': days_active
        }
