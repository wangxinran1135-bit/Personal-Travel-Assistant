from typing import Dict, Any, List
import datetime
import psycopg2

class KnowledgeBase:

    def __init__(self, db_connection):
        # 就是在这里初始化数据库连接池和我们API客户端
        self.conn = db_connection
        print("KnowledgeBase initialized with database connection")

    #获取地点详细信息
    def get_place_details(self, place_id: int) -> Dict[str, Any]:
        print(f"Querying the database for place {place_id}")
        try:
            with self.conn.cursor() as cur:
                sql = "SELECT place_id, name, category, description, address, opening_hours FROM places WHERE place_id = %s"
                cur.execute(sql, (place_id,))
                result = cur.fetchone()
                
                if result:
                    return {
                        "place_id": result[0],
                        "name": result[1],
                        "category": result[2],
                        "description": result[3],
                        "address": result[4],
                        "opening_hours": result[5]
                    }
            return {}
        except Exception as e:
            print(f"Error querying place details: {e}")
            return {}

    #行程规划的核心步骤
    def find_places_by_interests(self, interests: List[str]) -> List[Dict[str, Any]]:
        """根据兴趣查找地点"""
        if not interests:
            return []
        
        try:
            with self.conn.cursor() as cur:
                # 构建查询条件
                conditions = []
                params = []
                for interest in interests:
                    conditions.append("category ILIKE %s")
                    params.append(f"%{interest}%")
            
                where_clause = " OR ".join(conditions)
                sql = f"SELECT place_id, name, category FROM places WHERE {where_clause}"
                cur.execute(sql, params)
                results = cur.fetchall()
                
                return [
                    {
                        "place_id_suggestion": row[0],
                        "name": row[1],
                        "category": row[2]
                    }
                    for row in results
                ]
        except Exception as e:
            print(f"Error finding places by interests: {e}")
            return []
    #获取库存信息
    def get_inventory(self, offering_id: int, date: datetime.date) -> List[Dict[str, Any]]:
        print(f"Querying inventory for service {offering_id} on {date}...")
        try:
            with self.conn.cursor() as cur:
                sql = """
                    SELECT time_slot, available, capacity, status
                    FROM inventories
                    WHERE offering_id = %s AND date = %s
                """
                cur.execute(sql, (offering_id, date))
                results = cur.fetchall()
                
                return [
                    {
                        "time_slot": row[0],
                        "available": row[1],
                        "capacity": row[2],
                        "status": row[3]
                    }
                    for row in results
                ]
        except Exception as e:
            print(f"Error querying inventory: {e}")
            return []

    def get_external_weather(self, location: str, date: datetime.date) -> Dict[str, Any]:
        print(f"Calling external API to query the weather for {location} on {date}...")
        return {"condition": "Sunny", "temperature_celsius": 25}

    def get_external_traffic_eta(self, origin_id: int, destination_id: int) -> datetime.timedelta:
        print(f"Calling external API to query the travel time from {origin_id} to {destination_id}...")
        return datetime.timedelta(minutes=30)
