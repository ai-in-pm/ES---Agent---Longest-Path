"""Database module for storing and retrieving ES analysis results"""
import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional


class ESDatabase:
    """SQLite database for Earned Schedule analysis results"""
    
    def __init__(self, db_path: str = "es_analysis.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.initialize_db()
    
    def initialize_db(self) -> None:
        """Create database and tables if they don't exist"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Create projects table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            planned_duration REAL,
            start_date TEXT,
            created_at TEXT NOT NULL,
            excel_file TEXT
        )
        """)
        
        # Create analyses table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            analysis_date TEXT NOT NULL,
            num_periods INTEGER,
            final_es REAL,
            final_spi_t REAL,
            final_ieac_t REAL,
            controlling_path TEXT,
            has_anomalies INTEGER,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
        """)
        
        # Create periods table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS periods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER NOT NULL,
            period_num INTEGER NOT NULL,
            overall_es REAL,
            overall_spi_t REAL,
            overall_ieac_t REAL,
            controlling_path TEXT,
            path_metrics TEXT,  -- JSON string of path metrics
            is_anomaly INTEGER,
            FOREIGN KEY (analysis_id) REFERENCES analyses(id)
        )
        """)
        
        self.conn.commit()
    
    def close(self) -> None:
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def add_project(self, name: str, planned_duration: float, 
                   start_date: Optional[datetime] = None,
                   excel_file: Optional[str] = None) -> int:
        """Add a new project to the database"""
        created_at = datetime.now().isoformat()
        start_date_str = start_date.isoformat() if start_date else None
        
        self.cursor.execute("""
        INSERT INTO projects (name, planned_duration, start_date, created_at, excel_file)
        VALUES (?, ?, ?, ?, ?)
        """, (name, planned_duration, start_date_str, created_at, excel_file))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def add_analysis(self, project_id: int, results: Dict) -> int:
        """Add analysis results to the database"""
        analysis_date = datetime.now().isoformat()
        num_periods = len(results['overall_metrics'])
        
        # Get final metrics
        final_es = results['overall_metrics'][-1][0]
        final_spi_t = results['overall_metrics'][-1][1]
        final_ieac_t = results['overall_metrics'][-1][2]
        
        # Get final controlling path
        controlling_path = results['controlling_path'][-1] if results['controlling_path'] else None
        
        # Check if there are anomalies
        has_anomalies = 1 if results.get('anomalies') else 0
        
        self.cursor.execute("""
        INSERT INTO analyses 
        (project_id, analysis_date, num_periods, final_es, final_spi_t, final_ieac_t, 
         controlling_path, has_anomalies)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (project_id, analysis_date, num_periods, final_es, final_spi_t, final_ieac_t,
              controlling_path, has_anomalies))
        
        analysis_id = self.cursor.lastrowid
        
        # Add period-by-period data
        for period in range(num_periods):
            overall_es = results['overall_metrics'][period][0]
            overall_spi_t = results['overall_metrics'][period][1]
            overall_ieac_t = results['overall_metrics'][period][2]
            
            # Get controlling path for this period
            period_controlling_path = results['controlling_path'][period] if period < len(results['controlling_path']) else None
            
            # Collect path metrics for this period
            path_metrics = {}
            for path, metrics in results['path_metrics'].items():
                if period < len(metrics):
                    path_metrics[path] = {
                        'es': metrics[period][0],
                        'spi_t': metrics[period][1],
                        'sv_t': metrics[period][2],
                        'ieac_t': metrics[period][3]
                    }
            
            # Check if this period has an anomaly
            is_anomaly = 1 if period in results.get('anomalies', {}) else 0
            
            self.cursor.execute("""
            INSERT INTO periods 
            (analysis_id, period_num, overall_es, overall_spi_t, overall_ieac_t,
             controlling_path, path_metrics, is_anomaly)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (analysis_id, period, overall_es, overall_spi_t, overall_ieac_t,
                  period_controlling_path, json.dumps(path_metrics), is_anomaly))
        
        self.conn.commit()
        return analysis_id
    
    def get_projects(self) -> List[Dict]:
        """Get all projects"""
        self.cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")
        columns = [col[0] for col in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
    
    def get_analyses(self, project_id: int) -> List[Dict]:
        """Get all analyses for a project"""
        self.cursor.execute("""
        SELECT * FROM analyses 
        WHERE project_id = ? 
        ORDER BY analysis_date DESC
        """, (project_id,))
        
        columns = [col[0] for col in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
    
    def get_periods(self, analysis_id: int) -> List[Dict]:
        """Get all periods for an analysis"""
        self.cursor.execute("""
        SELECT * FROM periods 
        WHERE analysis_id = ? 
        ORDER BY period_num
        """, (analysis_id,))
        
        columns = [col[0] for col in self.cursor.description]
        periods = []
        
        for row in self.cursor.fetchall():
            period_dict = dict(zip(columns, row))
            # Parse JSON string back to dictionary
            period_dict['path_metrics'] = json.loads(period_dict['path_metrics'])
            periods.append(period_dict)
            
        return periods


# Function to get database instance
def get_db_instance(db_path: str = "es_analysis.db") -> ESDatabase:
    """Get a database instance"""
    return ESDatabase(db_path)
