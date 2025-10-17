from typing import Dict, Any, List
import datetime

class KnowledgeBase:

    def __init__(self):
        # 就是在这里初始化数据库连接池和我们API客户端
        print("ok")

    def get_place_details(self, place_id: int) -> Dict[str, Any]:
        print(f"Querying the database for place {place_id}")
        # 这里我模拟数据库返回的数据
        mock_places = {
            1: {"name": "Sydney Opera House", "category": "Attraction", "opening_hours": "09:00-17:00"},
            2: {"name": "Doyle's Seafood", "category": "Restaurant", "opening_hours": "12:00-21:00"},
        }
        return mock_places.get(place_id, {})

    def get_inventory(self, offering_id: int, date: datetime.date) -> List[Dict[str, Any]]:
        print(f"Querying inventory for service {offering_id} on {date}...")
        # 我在这里模拟的是数据库返回的数据
        return [
            {"time_slot": "18:00-20:00", "available": 5, "capacity": 20},
            {"time_slot": "20:00-22:00", "available": 10, "capacity": 20},
        ]

    def get_external_weather(self, location: str, date: datetime.date) -> Dict[str, Any]:
        print(f"Calling external API to query the weather for {location} on {date}...")
        return {"condition": "Sunny", "temperature_celsius": 25}

    def get_external_traffic_eta(self, origin_id: int, destination_id: int) -> datetime.timedelta:
        print(f"Calling external API to query the travel time from {origin_id} to {destination_id}...")
        return datetime.timedelta(minutes=30)