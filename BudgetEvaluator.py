import psycopg2  
from typing import Dict, Any

class BudgetEvaluator:

    def __init__(self, db_connection):
        self.conn = db_connection

    def _get_budget_limits(self, itinerary_id: int) -> Dict[str, float]:
        print(f"Querying budget from database for itinerary {itinerary_id}...")
        limits = {"total_limit": 0.0, "daily_limit": 0.0}
        
        with self.conn.cursor() as cur:
            # 从budgets表查询
            sql = "SELECT total_limit, daily_limit FROM budgets WHERE itinerary_id = %s"
            cur.execute(sql, (itinerary_id,))
            result = cur.fetchone()
            
            if result:
                limits["total_limit"] = float(result[0]) if result[0] is not None else 0.0
                limits["daily_limit"] = float(result[1]) if result[1] is not None else 0.0
        
        return limits

    def _get_total_expenses(self, itinerary_id: int) -> float:
        print(f"Querying total historical expenses from database for itinerary {itinerary_id}...")
        total_expenses = 0.0
        
        with self.conn.cursor() as cur:
            # expenses表计算总和
            sql = "SELECT SUM(amount) FROM expenses WHERE itinerary_id = %s"
            cur.execute(sql, (itinerary_id,))
            result = cur.fetchone()
            
            if result and result[0] is not None:
                total_expenses = float(result[0])
                
        return total_expenses

    def check_budget_and_alert(self, itinerary_id: int, proposed_cost: float) -> str:
        budget = self._get_budget_limits(itinerary_id)
        current_expenses = self._get_total_expenses(itinerary_id)
        
        projected_total = current_expenses + proposed_cost
        total_limit = budget.get("total_limit", 0)
        
        print(f"Current expenses: ${current_expenses}, New cost: ${proposed_cost}, Projected total: ${projected_total}, Total budget: ${total_limit}")

        if total_limit > 0 and (projected_total / total_limit) > 0.8:
            alert_message = f"Warning: Projected total expenses will reach {projected_total / total_limit:.0%} of the budget."
            print(alert_message)
            return alert_message
        
        message = "Budget is sufficient."
        print(message)
        return message