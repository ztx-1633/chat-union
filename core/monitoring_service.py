from typing import Dict, Any, List
from datetime import datetime, timedelta
from .database_schema import init_databases


class MonitoringService:
    def __init__(self):
        dbs = init_databases()
        self.db = dbs['gateway']
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        gateways = self.db.get_all_gateways()
        
        online_count = 0
        offline_count = 0
        total_requests = 0
        total_errors = 0
        
        for gateway in gateways:
            status = gateway[4]
            if status == 'online':
                online_count += 1
            else:
                offline_count += 1
            
            metrics = self.db.get_gateway_metrics(gateway[1], limit=1)
            if metrics:
                total_requests += metrics[0][8] or 0
                total_errors += metrics[0][9] or 0
        
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'total_gateways': len(gateways),
            'online_gateways': online_count,
            'offline_gateways': offline_count,
            'total_requests': total_requests,
            'total_errors': total_errors,
            'error_rate': round(error_rate, 2),
            'updated_at': datetime.now().isoformat()
        }
    
    def get_gateway_performance(self, gateway_id: str, hours: int = 24) -> Dict[str, Any]:
        since = datetime.now() - timedelta(hours=hours)
        metrics = self.db.get_gateway_metrics(gateway_id, limit=1000)
        
        cpu_usage_values = []
        memory_usage_values = []
        request_counts = []
        error_counts = []
        timestamps = []
        
        for metric in metrics:
            ts = datetime.fromisoformat(metric[2]) if isinstance(metric[2], str) else metric[2]
            if ts >= since:
                timestamps.append(ts.isoformat())
                cpu_usage_values.append(metric[3] or 0)
                memory_usage_values.append(metric[4] or 0)
                request_counts.append(metric[8] or 0)
                error_counts.append(metric[9] or 0)
        
        avg_cpu = sum(cpu_usage_values) / len(cpu_usage_values) if cpu_usage_values else 0
        avg_memory = sum(memory_usage_values) / len(memory_usage_values) if memory_usage_values else 0
        total_requests = sum(request_counts)
        total_errors = sum(error_counts)
        
        return {
            'gateway_id': gateway_id,
            'period_hours': hours,
            'avg_cpu_usage': round(avg_cpu, 2),
            'avg_memory_usage': round(avg_memory, 2),
            'total_requests': total_requests,
            'total_errors': total_errors,
            'error_rate': round((total_errors / total_requests * 100) if total_requests > 0 else 0, 2),
            'metrics_history': {
                'timestamps': timestamps,
                'cpu_usage': cpu_usage_values,
                'memory_usage': memory_usage_values,
                'requests': request_counts,
                'errors': error_counts
            }
        }
    
    def get_all_gateways_status(self) -> List[Dict[str, Any]]:
        gateways = self.db.get_all_gateways()
        result = []
        
        for gateway in gateways:
            gateway_id = gateway[1]
            latest_metrics = self.db.get_gateway_metrics(gateway_id, limit=1)
            
            status_info = {
                'gateway_id': gateway_id,
                'name': gateway[2],
                'version': gateway[3],
                'status': gateway[4],
                'endpoint': gateway[5],
                'last_heartbeat': gateway[6],
                'updated_at': gateway[8]
            }
            
            if latest_metrics:
                metric = latest_metrics[0]
                status_info.update({
                    'current_cpu': metric[3],
                    'current_memory': metric[4],
                    'active_connections': metric[7],
                    'recent_requests': metric[8],
                    'recent_errors': metric[9]
                })
            
            result.append(status_info)
        
        return result
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        alerts = []
        gateways = self.db.get_all_gateways()
        
        for gateway in gateways:
            gateway_id = gateway[1]
            status = gateway[4]
            name = gateway[2]
            
            if status == 'offline':
                alerts.append({
                    'severity': 'critical',
                    'gateway_id': gateway_id,
                    'gateway_name': name,
                    'alert_type': 'gateway_offline',
                    'message': f'网关 {name} 已离线',
                    'timestamp': datetime.now().isoformat()
                })
            
            latest_metrics = self.db.get_gateway_metrics(gateway_id, limit=1)
            if latest_metrics:
                metric = latest_metrics[0]
                
                if metric[3] and metric[3] > 80:
                    alerts.append({
                        'severity': 'warning',
                        'gateway_id': gateway_id,
                        'gateway_name': name,
                        'alert_type': 'high_cpu',
                        'message': f'网关 {name} CPU使用率过高: {metric[3]}%',
                        'timestamp': metric[2]
                    })
                
                if metric[4] and metric[4] > 80:
                    alerts.append({
                        'severity': 'warning',
                        'gateway_id': gateway_id,
                        'gateway_name': name,
                        'alert_type': 'high_memory',
                        'message': f'网关 {name} 内存使用率过高: {metric[4]}%',
                        'timestamp': metric[2]
                    })
                
                if metric[9] and metric[9] > 0:
                    error_rate = (metric[9] / metric[8] * 100) if metric[8] > 0 else 100
                    if error_rate > 5:
                        alerts.append({
                            'severity': 'warning',
                            'gateway_id': gateway_id,
                            'gateway_name': name,
                            'alert_type': 'high_error_rate',
                            'message': f'网关 {name} 错误率过高: {round(error_rate, 2)}%',
                            'timestamp': metric[2]
                        })
        
        return alerts


_monitoring_service_instance = None


def get_monitoring_service() -> MonitoringService:
    global _monitoring_service_instance
    if _monitoring_service_instance is None:
        _monitoring_service_instance = MonitoringService()
    return _monitoring_service_instance
