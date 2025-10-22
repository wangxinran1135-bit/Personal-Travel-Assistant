import psycopg2
from typing import Dict, Any, List

# Assuming these are valid imports from your project structure
from ItineraryPlanner import ItineraryPlanner
from KnowledgeBase import KnowledgeBase
from GoalManager import UserPreferences
from BookingHandler import BookingHandler

class ReplanEngine:

    def __init__(self, planner: 'ItineraryPlanner', booking_handler: 'BookingHandler', db_connection):
        self.planner = planner
        self.booking_handler = booking_handler
        self.conn = db_connection
        print("Initializing")

    def _get_current_itinerary_activities(self, itinerary_id: int) -> List[Dict[str, Any]]:
        activities = []
        with self.conn.cursor() as cur:
            # 查询活动  左连接地点表和预订表
            sql = """
                SELECT 
                    a.activity_id, a.type, p.name, b.booking_id, b.status as booking_status
                FROM activities a
                LEFT JOIN places p ON a.place_id = p.place_id
                LEFT JOIN bookings b ON a.activity_id = b.activity_id
                WHERE a.day_id IN (SELECT day_id FROM itinerary_days WHERE itinerary_id = %s)
                ORDER BY a.start_time;
            """
            cur.execute(sql, (itinerary_id,))
            for row in cur.fetchall():
                activities.append({
                    "activity_id": row[0],
                    "type": row[1],
                    "name": row[2],
                    "booking_id": row[3],
                    "booking_status": row[4]
                })
        return activities

    def _analyze_impact(self, activities: List[Dict[str, Any]], disruption: Dict[str, Any]) -> List[int]:
        affected_activity_ids = []
        if disruption.get("type") == "weather" and disruption.get("detail") == "heavy_rain":
            print("Heavy rain detected, analyzing affected outdoor activities...")
            for act in activities:
                if act['type'] == 'VisitPOI':
                    affected_activity_ids.append(act['activity_id'])
        return affected_activity_ids

    def _apply_new_plan(self, itinerary_id: int, old_activities: List[Dict[str, Any]], new_activities_plan: List[Dict[str, Any]]):
        print("Applying new itinerary plan...")
        old_activity_ids = {act['activity_id'] for act in old_activities}
        activities_to_cancel = [act for act in old_activities if act['activity_id'] in old_activity_ids]

        try:
            with self.conn.cursor() as cur:
                # 这个是取消和被移除活动关联的预订
                for act in activities_to_cancel:
                    if act.get("booking_id") and act.get("booking_status") == 'Confirmed':
                        print(f"Cancelling booking (Booking ID: {act['booking_id']}) for activity '{act['name']}' (ID: {act['activity_id']})...")
                        self.booking_handler.cancel_booking(act['booking_id'])

                # 这里在数据库中删除所有旧的活动
                day_ids_query = "SELECT day_id FROM itinerary_days WHERE itinerary_id = %s"
                cur.execute(day_ids_query, (itinerary_id,))
                day_ids = [row[0] for row in cur.fetchall()]
                if day_ids:
                    delete_sql = "DELETE FROM activities WHERE day_id IN %s"
                    cur.execute(delete_sql, (tuple(day_ids),))
                    print(f"All old activities for itinerary {itinerary_id} have been deleted.")

                #  在我们数据库中插入新的活动
                for new_act in new_activities_plan:
                    print(f"Inserting new activity: {new_act['name']}")
                    # cur.execute(INSERT_SQL, (...))
                
                self.conn.commit()
                print("Successfully applied to the database.")

        except Exception as e:
            self.conn.rollback()
            print(f"A database error occurred: {e}")

    def replan_for_disruption(self, itinerary_id: int, user_preferences: 'UserPreferences', disruption: Dict[str, Any]):
        current_activities = self._get_current_itinerary_activities(itinerary_id)
        affected_ids = self._analyze_impact(current_activities, disruption)
        if not affected_ids:
            print("No replanning needed.")
            return {"status": "NoChange", "itinerary": current_activities}

        print(f"The following activities are affected: {affected_ids}")
        
        # 生成临时约束并调用规划器 和之前差不多 调用的是self.planner来获取新的计划)
        new_plan_from_planner = {
            "activities": [
                {"name": "Visit indoor art gallery in the morning", "type": "Indoor"},
                {"name": "Visit aquarium in the afternoon", "type": "Indoor", "priority": "high"},
            ]
        }
        
        # 编排和执行变更
        user_accepted_new_plan = True 
        if user_accepted_new_plan:
            self._apply_new_plan(itinerary_id, current_activities, new_plan_from_planner['activities'])
            return {"status": "Replanned", "new_plan": new_plan_from_planner}
        else:
            print("User rejected the replanning suggestion.")
            return {"status": "Rejected", "itinerary": current_activities}
