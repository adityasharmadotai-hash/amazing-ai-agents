"""
Database Module - SQLite backend for Competitor Intelligence Agent
Manages competitors, changes, pricing, jobs, products, and alerts
"""

import sqlite3
import json
from datetime import datetime
import pytz
from contextlib import contextmanager

class Database:
    """SQLite database for competitor intelligence"""
    
    def __init__(self, db_path="competitors.db"):
        self.db_path = db_path
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_db(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Competitors table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS competitors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    website_url TEXT,
                    linkedin_url TEXT,
                    twitter_handle TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_scanned TIMESTAMP
                )
            ''')
            
            # Changes tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    competitor_id INTEGER NOT NULL,
                    change_type TEXT NOT NULL,
                    description TEXT,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    severity TEXT DEFAULT 'medium',
                    FOREIGN KEY (competitor_id) REFERENCES competitors(id)
                )
            ''')
            
            # Pricing history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    competitor_id INTEGER NOT NULL,
                    pricing_data TEXT,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (competitor_id) REFERENCES competitors(id)
                )
            ''')
            
            # Job openings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS job_openings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    competitor_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    department TEXT,
                    description TEXT,
                    posted_at TIMESTAMP,
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    url TEXT,
                    FOREIGN KEY (competitor_id) REFERENCES competitors(id)
                )
            ''')
            
            # Product launches table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS product_launches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    competitor_id INTEGER NOT NULL,
                    product_name TEXT NOT NULL,
                    description TEXT,
                    url TEXT,
                    announced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (competitor_id) REFERENCES competitors(id)
                )
            ''')
            
            # Alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    competitor_id INTEGER NOT NULL,
                    change_id INTEGER,
                    description TEXT NOT NULL,
                    severity TEXT DEFAULT 'medium',
                    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent BOOLEAN DEFAULT 0,
                    FOREIGN KEY (competitor_id) REFERENCES competitors(id),
                    FOREIGN KEY (change_id) REFERENCES changes(id)
                )
            ''')
            
            # Website snapshots table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS website_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    competitor_id INTEGER NOT NULL,
                    snapshot_hash TEXT,
                    content TEXT,
                    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (competitor_id) REFERENCES competitors(id)
                )
            ''')
            
            conn.commit()
    
    # ==================== COMPETITORS ====================
    def add_competitor(self, name, website_url, linkedin_url=None, twitter_handle=None):
        """Add a new competitor"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO competitors (name, website_url, linkedin_url, twitter_handle)
                VALUES (?, ?, ?, ?)
            ''', (name, website_url, linkedin_url, twitter_handle))
            conn.commit()
            return cursor.lastrowid
    
    def get_competitors(self):
        """Get all competitors"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM competitors ORDER BY added_at DESC')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_competitor(self, competitor_id):
        """Get specific competitor"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM competitors WHERE id = ?', (competitor_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_last_scanned(self, competitor_id):
        """Update last scanned time"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE competitors SET last_scanned = ? WHERE id = ?',
                (datetime.now(pytz.UTC), competitor_id)
            )
            conn.commit()
    
    # ==================== CHANGES ====================
    def add_change(self, competitor_id, change_type, description, severity='medium'):
        """Record a change"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO changes (competitor_id, change_type, description, severity)
                VALUES (?, ?, ?, ?)
            ''', (competitor_id, change_type, description, severity))
            conn.commit()
            return cursor.lastrowid
    
    def get_competitor_changes(self, competitor_id, days=30):
        """Get recent changes for a competitor"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM changes
                WHERE competitor_id = ?
                AND datetime(detected_at) > datetime('now', '-' || ? || ' days')
                ORDER BY detected_at DESC
            ''', (competitor_id, days))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_changes(self, days=7):
        """Get recent changes across all competitors"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.*, comp.name as competitor_name
                FROM changes c
                JOIN competitors comp ON c.competitor_id = comp.id
                WHERE datetime(c.detected_at) > datetime('now', '-' || ? || ' days')
                ORDER BY c.detected_at DESC
            ''', (days,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== PRICING ====================
    def add_price_change(self, competitor_id, pricing_data):
        """Record a pricing change"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO price_changes (competitor_id, pricing_data)
                VALUES (?, ?)
            ''', (competitor_id, pricing_data))
            conn.commit()
    
    def get_price_changes(self, days=30):
        """Get recent price changes"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT competitor_id FROM price_changes
                WHERE datetime(detected_at) > datetime('now', '-' || ? || ' days')
            ''', (days,))
            return cursor.fetchall()
    
    def get_competitor_price_history(self, competitor_id):
        """Get price history for competitor"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM price_changes
                WHERE competitor_id = ?
                ORDER BY detected_at DESC
                LIMIT 10
            ''', (competitor_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== JOB OPENINGS ====================
    def add_job_opening(self, competitor_id, title, department=None, description=None, url=None):
        """Add a job opening"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Check if job already exists (avoid duplicates)
            cursor.execute('''
                SELECT id FROM job_openings
                WHERE competitor_id = ? AND title = ? AND department = ?
                AND discovered_at > datetime('now', '-1 days')
            ''', (competitor_id, title, department))
            
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO job_openings (competitor_id, title, department, description, url)
                    VALUES (?, ?, ?, ?, ?)
                ''', (competitor_id, title, department, description, url))
                conn.commit()
    
    def get_competitor_job_openings(self, competitor_id):
        """Get active job openings"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM job_openings
                WHERE competitor_id = ?
                ORDER BY discovered_at DESC
            ''', (competitor_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_job_openings(self):
        """Get all job openings across competitors"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT jo.*, comp.name as competitor_name FROM job_openings jo
                JOIN competitors comp ON jo.competitor_id = comp.id
                ORDER BY jo.discovered_at DESC
                LIMIT 100
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== PRODUCT LAUNCHES ====================
    def add_product_launch(self, competitor_id, product_name, description=None, url=None):
        """Record a product launch"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO product_launches (competitor_id, product_name, description, url)
                VALUES (?, ?, ?, ?)
            ''', (competitor_id, product_name, description, url))
            conn.commit()
    
    def get_competitor_product_launches(self, competitor_id):
        """Get product launches for competitor"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM product_launches
                WHERE competitor_id = ?
                ORDER BY announced_at DESC
            ''', (competitor_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_product_launches(self):
        """Get all product launches"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT pl.*, comp.name as competitor_name FROM product_launches pl
                JOIN competitors comp ON pl.competitor_id = comp.id
                ORDER BY pl.announced_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== ALERTS ====================
    def add_alert(self, competitor_id, description, severity='medium', change_id=None):
        """Create an alert"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO alerts (competitor_id, change_id, description, severity)
                VALUES (?, ?, ?, ?)
            ''', (competitor_id, change_id, description, severity))
            conn.commit()
            return cursor.lastrowid
    
    def get_all_alerts(self, unsent_only=False):
        """Get all alerts"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = '''
                SELECT al.*, comp.name as competitor_name FROM alerts al
                JOIN competitors comp ON al.competitor_id = comp.id
            '''
            
            if unsent_only:
                query += ' WHERE al.sent = 0'
            
            query += ' ORDER BY al.triggered_at DESC LIMIT 50'
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_alerts_sent(self, alert_ids):
        """Mark alerts as sent"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for alert_id in alert_ids:
                cursor.execute('UPDATE alerts SET sent = 1 WHERE id = ?', (alert_id,))
            conn.commit()
    
    # ==================== WEBSITE SNAPSHOTS ====================
    def add_website_snapshot(self, competitor_id, snapshot_hash, content):
        """Store website snapshot"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO website_snapshots (competitor_id, snapshot_hash, content)
                VALUES (?, ?, ?)
            ''', (competitor_id, snapshot_hash, content))
            conn.commit()
    
    def get_latest_snapshot(self, competitor_id):
        """Get latest snapshot for competitor"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM website_snapshots
                WHERE competitor_id = ?
                ORDER BY captured_at DESC
                LIMIT 1
            ''', (competitor_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # ==================== UTILITY ====================
    def get_last_scan_time(self):
        """Get last scan time across all competitors"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT MAX(last_scanned) as last_scan FROM competitors
            ''')
            result = cursor.fetchone()
            if result and result['last_scan']:
                return datetime.fromisoformat(result['last_scan'])
            return None
    
    def get_database_stats(self):
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {
                'competitors': cursor.execute('SELECT COUNT(*) as count FROM competitors').fetchone()['count'],
                'changes': cursor.execute('SELECT COUNT(*) as count FROM changes').fetchone()['count'],
                'price_changes': cursor.execute('SELECT COUNT(*) as count FROM price_changes').fetchone()['count'],
                'job_openings': cursor.execute('SELECT COUNT(*) as count FROM job_openings').fetchone()['count'],
                'product_launches': cursor.execute('SELECT COUNT(*) as count FROM product_launches').fetchone()['count'],
                'alerts': cursor.execute('SELECT COUNT(*) as count FROM alerts').fetchone()['count'],
            }
            return stats
