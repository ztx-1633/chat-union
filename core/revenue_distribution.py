import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .database_schema import init_databases


class RevenueDistributionService:
    def __init__(self):
        dbs = init_databases()
        self.db = dbs['revenue']
        self.audit_db = dbs['audit']
    
    def create_transaction(self, source_gateway_id: str, 
                          target_gateway_id: Optional[str],
                          amount: float, 
                          transaction_type: str,
                          details: Optional[str] = None) -> Dict[str, Any]:
        transaction_id = str(uuid.uuid4())
        
        config = self.db.get_fee_rates()
        source_fee = amount * config['source_gateway_fee_rate']
        ecosystem_fee = amount * config['ecosystem_pool_fee_rate']
        net_amount = amount - source_fee - ecosystem_fee
        
        self.db.add_transaction(
            transaction_id=transaction_id,
            source_gateway_id=source_gateway_id,
            target_gateway_id=target_gateway_id,
            amount=amount,
            transaction_type=transaction_type,
            details=details
        )
        
        self.audit_db.add_log(
            user_id=None,
            action='transaction_create',
            resource_type='transaction',
            resource_id=transaction_id,
            details=f'创建交易: {transaction_type}, 金额: {amount}'
        )
        
        return {
            'transaction_id': transaction_id,
            'source_gateway_id': source_gateway_id,
            'target_gateway_id': target_gateway_id,
            'amount': amount,
            'transaction_type': transaction_type,
            'source_gateway_fee': source_fee,
            'ecosystem_pool_fee': ecosystem_fee,
            'net_amount': net_amount,
            'fee_rates': config
        }
    
    def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        result = self.db.fetch_one(
            '''SELECT * FROM revenue_transactions WHERE transaction_id = ?''',
            (transaction_id,)
        )
        if not result:
            return None
        
        return self._format_transaction(result)
    
    def get_transactions(self, limit: int = 100) -> List[Dict[str, Any]]:
        transactions = self.db.get_transactions(limit)
        return [self._format_transaction(tx) for tx in transactions]
    
    def get_transactions_by_gateway(self, gateway_id: str, 
                                    limit: int = 100) -> List[Dict[str, Any]]:
        transactions = self.db.fetch_all(
            '''SELECT * FROM revenue_transactions 
               WHERE source_gateway_id = ? OR target_gateway_id = ?
               ORDER BY created_at DESC LIMIT ?''',
            (gateway_id, gateway_id, limit)
        )
        return [self._format_transaction(tx) for tx in transactions]
    
    def get_gateway_revenue_summary(self, gateway_id: str, 
                                     days: int = 30) -> Dict[str, Any]:
        since = datetime.now() - timedelta(days=days)
        
        source_transactions = self.db.fetch_all(
            '''SELECT * FROM revenue_transactions 
               WHERE source_gateway_id = ? AND created_at >= ?''',
            (gateway_id, since.isoformat())
        )
        
        target_transactions = self.db.fetch_all(
            '''SELECT * FROM revenue_transactions 
               WHERE target_gateway_id = ? AND created_at >= ?''',
            (gateway_id, since.isoformat())
        )
        
        total_source_amount = sum(tx[4] for tx in source_transactions)
        total_source_fee = sum(tx[6] for tx in source_transactions)
        total_target_amount = sum(tx[8] for tx in target_transactions)
        
        return {
            'gateway_id': gateway_id,
            'period_days': days,
            'as_source': {
                'transaction_count': len(source_transactions),
                'total_amount': total_source_amount,
                'total_fee_earned': total_source_fee
            },
            'as_target': {
                'transaction_count': len(target_transactions),
                'total_net_amount': total_target_amount
            },
            'net_revenue': total_source_fee + total_target_amount
        }
    
    def get_overall_statistics(self, days: int = 30) -> Dict[str, Any]:
        since = datetime.now() - timedelta(days=days)
        
        transactions = self.db.fetch_all(
            '''SELECT * FROM revenue_transactions WHERE created_at >= ?''',
            (since.isoformat(),)
        )
        
        total_amount = sum(tx[4] for tx in transactions)
        total_source_fee = sum(tx[6] for tx in transactions)
        total_ecosystem_fee = sum(tx[7] for tx in transactions)
        
        transaction_types = {}
        for tx in transactions:
            tx_type = tx[5]
            if tx_type not in transaction_types:
                transaction_types[tx_type] = {'count': 0, 'amount': 0}
            transaction_types[tx_type]['count'] += 1
            transaction_types[tx_type]['amount'] += tx[4]
        
        return {
            'period_days': days,
            'transaction_count': len(transactions),
            'total_amount': total_amount,
            'total_source_gateway_fee': total_source_fee,
            'total_ecosystem_pool_fee': total_ecosystem_fee,
            'average_transaction_amount': total_amount / len(transactions) if transactions else 0,
            'transaction_types': transaction_types,
            'ecosystem_pool_balance': self.db.get_ecosystem_pool_balance()
        }
    
    def update_fee_rates(self, source_gateway_rate: Optional[float] = None,
                         ecosystem_pool_rate: Optional[float] = None) -> Dict[str, Any]:
        if source_gateway_rate is not None:
            self.db.execute_query(
                '''UPDATE system_config SET value = ?, updated_at = CURRENT_TIMESTAMP 
                   WHERE key = ?''',
                (str(source_gateway_rate), 'source_gateway_fee_rate')
            )
        
        if ecosystem_pool_rate is not None:
            self.db.execute_query(
                '''UPDATE system_config SET value = ?, updated_at = CURRENT_TIMESTAMP 
                   WHERE key = ?''',
                (str(ecosystem_pool_rate), 'ecosystem_pool_fee_rate')
            )
        
        new_rates = self.db.get_fee_rates()
        
        self.audit_db.add_log(
            user_id=None,
            action='fee_rates_update',
            resource_type='system_config',
            details=f'更新分成比例: 源网关 {new_rates["source_gateway_fee_rate"]}, 生态池 {new_rates["ecosystem_pool_fee_rate"]}'
        )
        
        return new_rates
    
    def _format_transaction(self, tx: tuple) -> Dict[str, Any]:
        return {
            'id': tx[0],
            'transaction_id': tx[1],
            'source_gateway_id': tx[2],
            'target_gateway_id': tx[3],
            'amount': tx[4],
            'transaction_type': tx[5],
            'source_gateway_fee': tx[6],
            'ecosystem_pool_fee': tx[7],
            'net_amount': tx[8],
            'details': tx[9],
            'created_at': tx[10]
        }


_revenue_distribution_instance = None


def get_revenue_distribution_service() -> RevenueDistributionService:
    global _revenue_distribution_instance
    if _revenue_distribution_instance is None:
        _revenue_distribution_instance = RevenueDistributionService()
    return _revenue_distribution_instance
