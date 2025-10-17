import psycopg2  
from typing import Dict, Any

class BudgetEvaluator:

    def __init__(self, db_connection):

        self.conn = db_connection

    def _get_budget_limits(self, itinerary_id: int) -> Dict[str, float]:

        print(f"正在为行程 {itinerary_id} 从数据库查询预算")

        limits = {"total_limit": 0.0, "daily_limit": 0.0}   

        with self.conn.cursor() as cur:
            sql = "SELECT total_limit, daily_limit FROM Budget WHERE itinerary_id = %s"
            cur.execute(sql, (itinerary_id,))
            result = cur.fetchone()
            
            if result:
                limits["total_limit"] = float(result)
                limits["daily_limit"] = float(result[1])
        
        return limits

    def _get_total_expenses(self, itinerary_id: int) -> float:

        print(f"正在为行程 {itinerary_id} 从数据库查询历史总支出...")
        total_expenses = 0.0
        
        with self.conn.cursor() as cur:
            sql = "SELECT SUM(amount) FROM Expense WHERE itinerary_id = %s"
            cur.execute(sql, (itinerary_id,))
            result = cur.fetchone()
            
            if result and result is not None:
                total_expenses = float(result)
                
        return total_expenses

    def check_budget_and_alert(self, itinerary_id: int, proposed_cost: float) -> str:

        budget = self._get_budget_limits(itinerary_id)
        current_expenses = self._get_total_expenses(itinerary_id)
        
        projected_total = current_expenses + proposed_cost
        total_limit = budget.get("total_limit", 0)
        
        print(f"当前支出: ${current_expenses}, 新增成本: ${proposed_cost}, 预计总支出: ${projected_total}, 总预算: ${total_limit}")

        if total_limit > 0 and (projected_total / total_limit) > 0.8:
            alert_message = f"警告: 预计总支出将达到预算的 {projected_total / total_limit:.0%}。建议寻找更经济的替代方案。"
            print(alert_message)
            return alert_message
        
        message = "预算充足"
        print(message)
        return message

