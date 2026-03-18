import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List
import threading
import json


class DatabaseManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str = "chat_union.db"):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.db_path = db_path
                    cls._instance._initialize_database()
        return cls._instance
    
    def _get_connection(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)
    
    def _initialize_database(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gateways (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gateway_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                status TEXT DEFAULT 'offline',
                endpoint TEXT NOT NULL,
                last_heartbeat DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                config TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gateway_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gateway_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                cpu_usage REAL,
                memory_usage REAL,
                network_in_bytes INTEGER,
                network_out_bytes INTEGER,
                active_connections INTEGER,
                request_count INTEGER,
                error_count INTEGER,
                FOREIGN KEY (gateway_id) REFERENCES gateways(gateway_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                action TEXT NOT NULL,
                resource_type TEXT,
                resource_id TEXT,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                status TEXT DEFAULT 'success',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS revenue_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE NOT NULL,
                source_gateway_id TEXT NOT NULL,
                target_gateway_id TEXT,
                amount REAL NOT NULL,
                transaction_type TEXT NOT NULL,
                source_gateway_fee REAL DEFAULT 0,
                ecosystem_pool_fee REAL DEFAULT 0,
                net_amount REAL NOT NULL,
                details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_gateway_id) REFERENCES gateways(gateway_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ecosystem_pool (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT NOT NULL,
                amount REAL NOT NULL,
                transaction_type TEXT NOT NULL,
                description TEXT,
                balance REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (transaction_id) REFERENCES revenue_transactions(transaction_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS version_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gateway_id TEXT NOT NULL,
                version TEXT NOT NULL,
                change_log TEXT,
                deployed_by TEXT,
                deployed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (gateway_id) REFERENCES gateways(gateway_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                description TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT OR IGNORE INTO system_config (key, value, description) VALUES
            ('source_gateway_fee_rate', '0.05', '源网关分成比例 (5%)'),
            ('ecosystem_pool_fee_rate', '0.05', '生态流水池比例 (5%)')
        ''')
        
        conn.commit()
        conn.close()
    
    def execute_query(self, query: str, params: tuple = ()):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        result = cursor.lastrowid
        conn.close()
        return result
    
    def fetch_all(self, query: str, params: tuple = ()) -> List[tuple]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchall()
        conn.close()
        return result
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[tuple]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.close()
        return result


class GatewayDB:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def add_gateway(self, gateway_id: str, name: str, version: str, endpoint: str, config: Optional[Dict] = None):
        config_str = json.dumps(config) if config else None
        return self.db.execute_query(
            '''INSERT INTO gateways (gateway_id, name, version, endpoint, config) 
               VALUES (?, ?, ?, ?, ?)''',
            (gateway_id, name, version, endpoint, config_str)
        )
    
    def update_gateway_status(self, gateway_id: str, status: str):
        return self.db.execute_query(
            '''UPDATE gateways SET status = ?, last_heartbeat = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP 
               WHERE gateway_id = ?''',
            (status, gateway_id)
        )
    
    def get_all_gateways(self):
        return self.db.fetch_all('SELECT * FROM gateways ORDER BY created_at DESC')
    
    def get_gateway(self, gateway_id: str):
        result = self.db.fetch_one('SELECT * FROM gateways WHERE gateway_id = ?', (gateway_id,))
        return result
    
    def update_gateway_version(self, gateway_id: str, version: str, change_log: str, deployed_by: str):
        self.db.execute_query(
            '''UPDATE gateways SET version = ?, updated_at = CURRENT_TIMESTAMP WHERE gateway_id = ?''',
            (version, gateway_id)
        )
        return self.db.execute_query(
            '''INSERT INTO version_history (gateway_id, version, change_log, deployed_by) 
               VALUES (?, ?, ?, ?)''',
            (gateway_id, version, change_log, deployed_by)
        )
    
    def add_gateway_metrics(self, gateway_id: str, metrics: Dict[str, Any]):
        return self.db.execute_query(
            '''INSERT INTO gateway_metrics 
               (gateway_id, cpu_usage, memory_usage, network_in_bytes, network_out_bytes, 
                active_connections, request_count, error_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (gateway_id, metrics.get('cpu_usage'), metrics.get('memory_usage'),
             metrics.get('network_in_bytes'), metrics.get('network_out_bytes'),
             metrics.get('active_connections'), metrics.get('request_count'),
             metrics.get('error_count'))
        )
    
    def get_gateway_metrics(self, gateway_id: str, limit: int = 100):
        return self.db.fetch_all(
            '''SELECT * FROM gateway_metrics WHERE gateway_id = ? ORDER BY timestamp DESC LIMIT ?''',
            (gateway_id, limit)
        )


class AuditLogDB:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def add_log(self, user_id: Optional[str], action: str, resource_type: Optional[str] = None,
                resource_id: Optional[str] = None, details: Optional[str] = None,
                ip_address: Optional[str] = None, user_agent: Optional[str] = None,
                status: str = 'success'):
        return self.db.execute_query(
            '''INSERT INTO audit_logs 
               (user_id, action, resource_type, resource_id, details, ip_address, user_agent, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (user_id, action, resource_type, resource_id, details, ip_address, user_agent, status)
        )
    
    def get_logs(self, limit: int = 100, offset: int = 0):
        return self.db.fetch_all(
            '''SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ? OFFSET ?''',
            (limit, offset)
        )
    
    def get_logs_by_user(self, user_id: str, limit: int = 100):
        return self.db.fetch_all(
            '''SELECT * FROM audit_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?''',
            (user_id, limit)
        )


class RevenueDB:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def add_transaction(self, transaction_id: str, source_gateway_id: str, 
                        target_gateway_id: Optional[str], amount: float, 
                        transaction_type: str, details: Optional[str] = None):
        config = self.get_fee_rates()
        source_fee = amount * config['source_gateway_fee_rate']
        ecosystem_fee = amount * config['ecosystem_pool_fee_rate']
        net_amount = amount - source_fee - ecosystem_fee
        
        transaction_result = self.db.execute_query(
            '''INSERT INTO revenue_transactions 
               (transaction_id, source_gateway_id, target_gateway_id, amount, transaction_type,
                source_gateway_fee, ecosystem_pool_fee, net_amount, details)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (transaction_id, source_gateway_id, target_gateway_id, amount, transaction_type,
             source_fee, ecosystem_fee, net_amount, details)
        )
        
        if ecosystem_fee > 0:
            self.add_to_ecosystem_pool(transaction_id, ecosystem_fee, 'revenue', 
                                       f'生态分成来自交易: {transaction_id}')
        
        return transaction_result
    
    def add_to_ecosystem_pool(self, transaction_id: str, amount: float, 
                              transaction_type: str, description: str):
        current_balance = self.get_ecosystem_pool_balance()
        new_balance = current_balance + amount
        
        return self.db.execute_query(
            '''INSERT INTO ecosystem_pool (transaction_id, amount, transaction_type, description, balance)
               VALUES (?, ?, ?, ?, ?)''',
            (transaction_id, amount, transaction_type, description, new_balance)
        )
    
    def get_ecosystem_pool_balance(self) -> float:
        result = self.db.fetch_one(
            '''SELECT balance FROM ecosystem_pool ORDER BY id DESC LIMIT 1'''
        )
        return result[0] if result else 0.0
    
    def get_fee_rates(self) -> Dict[str, float]:
        results = self.db.fetch_all(
            '''SELECT key, value FROM system_config WHERE key IN (?, ?)''',
            ('source_gateway_fee_rate', 'ecosystem_pool_fee_rate')
        )
        rates = {}
        for key, value in results:
            rates[key] = float(value) if value else 0.0
        return {
            'source_gateway_fee_rate': rates.get('source_gateway_fee_rate', 0.05),
            'ecosystem_pool_fee_rate': rates.get('ecosystem_pool_fee_rate', 0.05)
        }
    
    def get_transactions(self, limit: int = 100):
        return self.db.fetch_all(
            '''SELECT * FROM revenue_transactions ORDER BY created_at DESC LIMIT ?''',
            (limit,)
        )
    
    def get_ecosystem_pool_history(self, limit: int = 100):
        return self.db.fetch_all(
            '''SELECT * FROM ecosystem_pool ORDER BY created_at DESC LIMIT ?''',
            (limit,)
        )


def init_databases():
    db = DatabaseManager()
    return {
        'gateway': GatewayDB(db),
        'audit': AuditLogDB(db),
        'revenue': RevenueDB(db),
        'db': db
    }
