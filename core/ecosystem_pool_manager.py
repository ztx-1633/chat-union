from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .database_schema import init_databases


class EcosystemPoolManager:
    def __init__(self):
        dbs = init_databases()
        self.db = dbs['revenue']
        self.audit_db = dbs['audit']
    
    def get_pool_balance(self) -> float:
        return self.db.get_ecosystem_pool_balance()
    
    def get_pool_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        history = self.db.get_ecosystem_pool_history(limit)
        return [self._format_pool_entry(entry) for entry in history]
    
    def deposit_to_pool(self, transaction_id: str, amount: float,
                        description: str) -> Dict[str, Any]:
        result = self.db.add_to_ecosystem_pool(
            transaction_id=transaction_id,
            amount=amount,
            transaction_type='deposit',
            description=description
        )
        
        self.audit_db.add_log(
            user_id=None,
            action='ecosystem_pool_deposit',
            resource_type='ecosystem_pool',
            details=f'存入生态池: {amount}, 描述: {description}'
        )
        
        return {
            'transaction_id': transaction_id,
            'amount': amount,
            'description': description,
            'new_balance': self.get_pool_balance()
        }
    
    def withdraw_from_pool(self, transaction_id: str, amount: float,
                          description: str, approved_by: str) -> Optional[Dict[str, Any]]:
        current_balance = self.get_pool_balance()
        
        if amount > current_balance:
            return None
        
        result = self.db.add_to_ecosystem_pool(
            transaction_id=transaction_id,
            amount=-amount,
            transaction_type='withdrawal',
            description=description
        )
        
        self.audit_db.add_log(
            user_id=approved_by,
            action='ecosystem_pool_withdrawal',
            resource_type='ecosystem_pool',
            details=f'从生态池取出: {amount}, 描述: {description}, 批准人: {approved_by}'
        )
        
        return {
            'transaction_id': transaction_id,
            'amount': -amount,
            'description': description,
            'approved_by': approved_by,
            'new_balance': self.get_pool_balance()
        }
    
    def get_pool_statistics(self, days: int = 30) -> Dict[str, Any]:
        since = datetime.now() - timedelta(days=days)
        
        history = self.db.fetch_all(
            '''SELECT * FROM ecosystem_pool WHERE created_at >= ? ORDER BY created_at''',
            (since.isoformat(),)
        )
        
        total_deposits = 0
        total_withdrawals = 0
        deposit_count = 0
        withdrawal_count = 0
        
        for entry in history:
            amount = entry[2]
            if amount > 0:
                total_deposits += amount
                deposit_count += 1
            else:
                total_withdrawals += abs(amount)
                withdrawal_count += 1
        
        return {
            'period_days': days,
            'current_balance': self.get_pool_balance(),
            'total_deposits': total_deposits,
            'total_withdrawals': total_withdrawals,
            'deposit_count': deposit_count,
            'withdrawal_count': withdrawal_count,
            'net_growth': total_deposits - total_withdrawals,
            'average_deposit': total_deposits / deposit_count if deposit_count > 0 else 0,
            'average_withdrawal': total_withdrawals / withdrawal_count if withdrawal_count > 0 else 0
        }
    
    def get_pool_history_by_type(self, transaction_type: str, 
                                  limit: int = 100) -> List[Dict[str, Any]]:
        history = self.db.fetch_all(
            '''SELECT * FROM ecosystem_pool 
               WHERE transaction_type = ? 
               ORDER BY created_at DESC LIMIT ?''',
            (transaction_type, limit)
        )
        return [self._format_pool_entry(entry) for entry in history]
    
    def get_pool_history_by_date_range(self, start_date: datetime, 
                                        end_date: datetime) -> List[Dict[str, Any]]:
        history = self.db.fetch_all(
            '''SELECT * FROM ecosystem_pool 
               WHERE created_at BETWEEN ? AND ? 
               ORDER BY created_at''',
            (start_date.isoformat(), end_date.isoformat())
        )
        return [self._format_pool_entry(entry) for entry in history]
    
    def get_monthly_summary(self, year: int, month: int) -> Dict[str, Any]:
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        history = self.get_pool_history_by_date_range(start_date, end_date)
        
        total_deposits = 0
        total_withdrawals = 0
        daily_balances = {}
        
        for entry in history:
            amount = entry['amount']
            created_at = datetime.fromisoformat(entry['created_at'])
            day_key = created_at.strftime('%Y-%m-%d')
            
            if amount > 0:
                total_deposits += amount
            else:
                total_withdrawals += abs(amount)
            
            daily_balances[day_key] = entry['balance']
        
        return {
            'year': year,
            'month': month,
            'total_deposits': total_deposits,
            'total_withdrawals': total_withdrawals,
            'net_growth': total_deposits - total_withdrawals,
            'daily_balances': daily_balances,
            'end_balance': list(daily_balances.values())[-1] if daily_balances else 0
        }
    
    def _format_pool_entry(self, entry: tuple) -> Dict[str, Any]:
        return {
            'id': entry[0],
            'transaction_id': entry[1],
            'amount': entry[2],
            'transaction_type': entry[3],
            'description': entry[4],
            'balance': entry[5],
            'created_at': entry[6]
        }


_ecosystem_pool_manager_instance = None


def get_ecosystem_pool_manager() -> EcosystemPoolManager:
    global _ecosystem_pool_manager_instance
    if _ecosystem_pool_manager_instance is None:
        _ecosystem_pool_manager_instance = EcosystemPoolManager()
    return _ecosystem_pool_manager_instance
