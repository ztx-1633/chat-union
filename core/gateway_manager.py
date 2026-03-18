import uuid
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from .database_schema import init_databases


class GatewayManager:
    def __init__(self):
        dbs = init_databases()
        self.db = dbs['gateway']
        self.audit_db = dbs['audit']
    
    def register_gateway(self, name: str, version: str, endpoint: str, 
                         config: Optional[Dict] = None) -> Dict[str, Any]:
        gateway_id = str(uuid.uuid4())
        
        self.db.add_gateway(gateway_id, name, version, endpoint, config)
        
        self.audit_db.add_log(
            user_id=None,
            action='gateway_register',
            resource_type='gateway',
            resource_id=gateway_id,
            details=f'注册新网关: {name}, 版本: {version}'
        )
        
        return {
            'gateway_id': gateway_id,
            'name': name,
            'version': version,
            'endpoint': endpoint,
            'status': 'offline'
        }
    
    def update_gateway_heartbeat(self, gateway_id: str) -> bool:
        result = self.db.update_gateway_status(gateway_id, 'online')
        return result is not None
    
    def get_gateway_info(self, gateway_id: str) -> Optional[Dict[str, Any]]:
        gateway = self.db.get_gateway(gateway_id)
        if not gateway:
            return None
        
        return {
            'id': gateway[0],
            'gateway_id': gateway[1],
            'name': gateway[2],
            'version': gateway[3],
            'status': gateway[4],
            'endpoint': gateway[5],
            'last_heartbeat': gateway[6],
            'created_at': gateway[7],
            'updated_at': gateway[8],
            'config': json.loads(gateway[9]) if gateway[9] else None
        }
    
    def list_all_gateways(self) -> List[Dict[str, Any]]:
        gateways = self.db.get_all_gateways()
        result = []
        for gateway in gateways:
            result.append({
                'id': gateway[0],
                'gateway_id': gateway[1],
                'name': gateway[2],
                'version': gateway[3],
                'status': gateway[4],
                'endpoint': gateway[5],
                'last_heartbeat': gateway[6],
                'created_at': gateway[7],
                'updated_at': gateway[8]
            })
        return result
    
    def deploy_gateway_version(self, gateway_id: str, version: str, 
                                change_log: str, deployed_by: str) -> bool:
        result = self.db.update_gateway_version(gateway_id, version, change_log, deployed_by)
        
        self.audit_db.add_log(
            user_id=deployed_by,
            action='gateway_deploy',
            resource_type='gateway',
            resource_id=gateway_id,
            details=f'部署网关版本: {version}'
        )
        
        return result is not None
    
    def report_metrics(self, gateway_id: str, metrics: Dict[str, Any]) -> bool:
        self.update_gateway_heartbeat(gateway_id)
        result = self.db.add_gateway_metrics(gateway_id, metrics)
        return result is not None
    
    def get_gateway_metrics(self, gateway_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        metrics_list = self.db.get_gateway_metrics(gateway_id, limit)
        result = []
        for metric in metrics_list:
            result.append({
                'id': metric[0],
                'gateway_id': metric[1],
                'timestamp': metric[2],
                'cpu_usage': metric[3],
                'memory_usage': metric[4],
                'network_in_bytes': metric[5],
                'network_out_bytes': metric[6],
                'active_connections': metric[7],
                'request_count': metric[8],
                'error_count': metric[9]
            })
        return result
    
    def get_all_versions(self) -> Dict[str, List[Dict[str, Any]]]:
        gateways = self.list_all_gateways()
        versions_by_gateway = {}
        
        for gateway in gateways:
            gateway_id = gateway['gateway_id']
            versions_by_gateway[gateway_id] = {
                'name': gateway['name'],
                'current_version': gateway['version'],
                'status': gateway['status'],
                'last_heartbeat': gateway['last_heartbeat']
            }
        
        return versions_by_gateway


_gateway_manager_instance = None


def get_gateway_manager() -> GatewayManager:
    global _gateway_manager_instance
    if _gateway_manager_instance is None:
        _gateway_manager_instance = GatewayManager()
    return _gateway_manager_instance
