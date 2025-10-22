# from Database import get_db_connection
# from BookingHandler import BookingHandler
# from BudgetEvaluator import BudgetEvaluator
# from GoalManager import GoalManager, UserPreferences
# from ItineraryPlanner import ItineraryPlanner
# from KnowledgeBase import KnowledgeBase
# from ReplanEngine import ReplanEngine

# if __name__ == "__main__":
#     conn = get_db_connection()

#     # 1. 预订
#     booking_handler = BookingHandler(conn)
#     booking_result = booking_handler.create_booking(activity_id=1, provider_id=1, price=100)
#     print("Booking:", booking_result)

#     # 2. 预算
#     budget_evaluator = BudgetEvaluator(conn)
#     budget_evaluator.check_budget_and_alert(itinerary_id=1, proposed_cost=50)

#     # 3. 偏好
#     goal_manager = GoalManager(conn)
#     prefs = UserPreferences(user_id=1, interests=["museum"], constraints={}, travel_pace="slow", travel_style="Comfort")
#     goal_manager.save_preferences(prefs)

#     # 4. 行程
#     kb = KnowledgeBase(conn)
#     planner = ItineraryPlanner(kb)
#     plan = planner.plan_itinerary(prefs)
#     print("Itinerary Plan:", plan)

#     # 5. 重规划
#     replan_engine = ReplanEngine(planner, booking_handler, conn)
#     disruption = {"type": "weather", "detail": "heavy_rain"}
#     replan_engine.replan_for_disruption(itinerary_id=1, user_preferences=prefs, disruption=disruption)

#     conn.close()
# main.py
# main.py
from Database import get_db_connection
from BookingHandler import BookingHandler
from BudgetEvaluator import BudgetEvaluator
from GoalManager import GoalManager, UserPreferences
from ItineraryPlanner import ItineraryPlanner
from KnowledgeBase import KnowledgeBase
from ReplanEngine import ReplanEngine

if __name__ == "__main__":
    conn = get_db_connection()

    # 1. 预订 - 使用未被占用的activity_id
    booking_handler = BookingHandler(conn)
    # 使用Insert.sql中已存在的provider_id=1，但使用未被占用的activity_id=4
    booking_result = booking_handler.create_booking(activity_id=4, provider_id=1, price=120)
    print("Booking:", booking_result)

    # 2. 预算 - 使用已存在的itinerary_id
    budget_evaluator = BudgetEvaluator(conn)
    # 使用Insert.sql中已存在的itinerary_id=1
    budget_evaluator.check_budget_and_alert(itinerary_id=1, proposed_cost=50)

    # 3. 偏好 - 使用已存在的user_id
    goal_manager = GoalManager(conn)
    # 使用Insert.sql中已存在的user_id=1，与数据库中保持一致的travel_pace
    prefs = UserPreferences(user_id=1, interests=["museum"], constraints={}, travel_pace="Normal", travel_style="Comfort")
    goal_manager.save_preferences(prefs)

    # 4. 行程 - 使用已存在的user_id
    kb = KnowledgeBase(conn)
    planner = ItineraryPlanner(kb)
    plan = planner.plan_itinerary(prefs)
    print("Itinerary Plan:", plan)

    # 5. 重规划 - 使用已存在的itinerary_id
    replan_engine = ReplanEngine(planner, booking_handler, conn)
    disruption = {"type": "weather", "detail": "heavy_rain"}
    # 使用Insert.sql中已存在的itinerary_id=1
    replan_engine.replan_for_disruption(itinerary_id=1, user_preferences=prefs, disruption=disruption)

    conn.close()