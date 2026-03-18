from typing import Dict, Any, List, Optional
from datetime import datetime
from .database_schema import init_databases


class AuditLogManager:
    def __init__(self):
        dbs = init_databases()
        self.db = dbs['audit']
    
    def log_action(self, user_id: Optional[str], action: str, 
                  resource_type: Optional[str] = None, 
                  resource_id: Optional[str] = None,
                  details: Optional[str] = None,
                  ip_address: Optional[str] = None,
                  user_agent: Optional[str] = None,
                  status: str = 'success') -> int:
        return self.db.add_log(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status
        )
    
    def get_logs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        logs = self.db.get_logs(limit, offset)
        return self._format_logs(logs)
    
    def get_logs_by_user(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        logs = self.db.get_logs_by_user(user_id, limit)
        return self._format_logs(logs)
    
    def get_logs_by_action(self, action: str, limit: int = 100) -> List[Dict[str, Any]]:
        logs = self.db.fetch_all(
            '''SELECT * FROM audit_logs WHERE action = ? ORDER BY created_at DESC LIMIT ?''',
            (action, limit)
        )
        return self._format_logs(logs)
    
    def get_logs_by_resource(self, resource_type: str, resource_id: str, 
                            limit: int = 100) -> List[Dict[str, Any]]:
        logs = self.db.fetch_all(
            '''SELECT * FROM audit_logs 
               WHERE resource_type = ? AND resource_id = ? 
               ORDER BY created_at DESC LIMIT ?''',
            (resource_type, resource_id, limit)
        )
        return self._format_logs(logs)
    
    def get_logs_by_date_range(self, start_date: datetime, end_date: datetime,
                               limit: int = 1000) -> List[Dict[str, Any]]:
        logs = self.db.fetch_all(
            '''SELECT * FROM audit_logs 
               WHERE created_at BETWEEN ? AND ? 
               ORDER BY created_at DESC LIMIT ?''',
            (start_date.isoformat(), end_date.isoformat(), limit)
        )
        return self._format_logs(logs)
    
    def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        from datetime import timedelta
        
        since = datetime.now() - timedelta(hours=hours)
        
        total_logs = self.db.fetch_one(
            '''SELECT COUNT(*) FROM audit_logs WHERE created_at >= ?''',
            (since.isoformat(),)
        )[0]
        
        success_logs = self.db.fetch_one(
            '''SELECT COUNT(*) FROM audit_logs WHERE created_at >= ? AND status = 'success' ''',
            (since.isoformat(),)
        )[0]
        
        failed_logs = self.db.fetch_one(
            '''SELECT COUNT(*) FROM audit_logs WHERE created_at >= ? AND status = 'failed' ''',
            (since.isoformat(),)
        )[0]
        
        action_stats = self.db.fetch_all(
            '''SELECT action, COUNT(*) as count 
               FROM audit_logs 
               WHERE created_at >= ? 
               GROUP BY action 
               ORDER BY count DESC''',
            (since.isoformat(),)
        )
        
        user_stats = self.db.fetch_all(
            '''SELECT user_id, COUNT(*) as count 
               FROM audit_logs 
               WHERE created_at >= ? AND user_id IS NOT NULL
               GROUP BY user_id 
               ORDER BY count DESC 
               LIMIT 10''',
            (since.isoformat(),)
        )
        
        return {
            'period_hours': hours,
            'total_logs': total_logs,
            'success_logs': success_logs,
            'failed_logs': failed_logs,
            'success_rate': round((success_logs / total_logs * 100) if total_logs > 0 else 0, 2),
            'action_breakdown': {action: count for action, count in action_stats},
            'top_users': {user: count for user, count in user_stats}
        }
    
    def export_logs(self, logs: List[Dict[str, Any]]) -> str:
        import csv
        from io import StringIO
        
        if not logs:
            return ''
        
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=logs[0].keys())
        writer.writeheader()
        writer.writerows(logs)
        
        return output.getvalue()
    
    def _format_logs(self, logs: List[tuple]) -> List[Dict[str, Any]]:
        result = []
        for log in logs:
            result.append({
                'id': log[0],
                'user_id': log[1],
                'action': log[2],
                'resource_type': log[3],
                'resource_id': log[4],
                'details': log[5],
                'ip_address': log[6],
                'user_agent': log[7],
                'status': log[8],
                'created_at': log[9]
            })
        return result


_audit_log_manager_instance = None


def get_audit_log_manager() -> AuditLogManager:
    global _audit_log_manager_instance
    if _audit_log_manager_instance is None:
        _audit_log_manager_instance = AuditLogManager()
    return _audit_log_manager_instance
