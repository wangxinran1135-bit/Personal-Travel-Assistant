import json
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class UserPreferences:
    user_id: int
    interests: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    travel_pace: str = "normal"
    travel_style: str = "Comfort"

class KnowledgeBase:
    # 模拟的站位知识库 测试用
    def get_place_details(self, place_id: int) -> Dict[str, Any]:
        mock_places = {
            1: {"name": "Sydney Opera House", "category": "landmark", "opening_hours": "09:00-17:00"},
            2: {"name": "Doyle's Seafood", "category": "seafood", "opening_hours": "12:00-21:00"},
            3: {"name": "Art Gallery of NSW", "category": "museum", "opening_hours": "10:00-17:00"},
            4: {"name": "Taronga Zoo", "category": "zoo", "opening_hours": "09:30-16:30"},
            5: {"name": "Mr. Wong", "category": "restaurant", "opening_hours": "17:30-23:00"}
        }
        return mock_places.get(place_id)

    def find_places_by_interests(self, interests: List[str]) -> List[Dict[str, Any]]:
        all_places = [
            {"place_id_suggestion": 1, "name": "Sydney Opera House", "category": "landmark"},
            {"place_id_suggestion": 2, "name": "Doyle's Seafood", "category": "seafood"},
            {"place_id_suggestion": 3, "name": "Art Gallery of NSW", "category": "museum"},
            {"place_id_suggestion": 4, "name": "Taronga Zoo", "category": "zoo"},
            {"place_id_suggestion": 5, "name": "Mr. Wong", "category": "restaurant"}
        ]
        relevant_places = [p for p in all_places if any(interest in p['category'] for interest in interests)]
        return relevant_places

class ItineraryPlanner:

    def __init__(self, knowledge_base: KnowledgeBase):
        # 初始化的私后传入一个知识库实例
        self.kb = knowledge_base
        print("Initialized")

    def _build_candidate_generation_prompt(self, preferences: UserPreferences, available_places: List[Dict[str, Any]]) -> str:
        prompt = f"""
        You are a creative and pragmatic Sydney travel planner. Your task is to recommend a list of 5-7 potential activities based on the user's preferences.

        **User Preferences:**
        -   Interests: {', '.join(preferences.interests)}
        -   Travel Style: {preferences.travel_style}
        -   Travel Pace: {preferences.travel_pace}
        -   Constraints: {json.dumps(preferences.constraints)}

        **Available Sydney Places (Please use these for recommendations):**
        {json.dumps(available_places, indent=2)}

        **Instructions:**
        1.  Generate a list of activities based on user preferences.
        2.  For each activity, you must use the `place_id_suggestion` provided in the "Available Places" list above.
        3.  Your output must be a single, valid JSON object representing a list of activities. Do not include any other text or explanations.
        4.  Each object in the list must contain the following keys: "type" (string: 'VisitPOI' or 'Meal'), "place_name" (string), and "place_id_suggestion" (integer).

        **Your JSON Output (List of Activities):**
        """
        return prompt.strip()

    def _generate_candidates_with_llm(self, preferences: UserPreferences) -> List[Dict[str, Any]]:
        known_places = self.kb.find_places_by_interests(preferences.interests)
        if not known_places:
            print("Could not find relevant places.")
            return []
        
        prompt = self._build_candidate_generation_prompt(preferences, known_places)
        print("Sending prompt to LLM")
        print(prompt)

        # 模拟llmapi调用 在真实场景中是response_text = llm_client.generate(prompt)
        response_text = json.dumps([
            {"type": "VisitPOI", "place_name": "Sydney Opera House", "place_id_suggestion": 1},
            {"type": "Meal", "place_name": "Mr. Wong", "place_id_suggestion": 5},
            {"type": "VisitPOI", "place_name": "Art Gallery of NSW", "place_id_suggestion": 3}
        ])
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            print("Error decoding JSON from LLM.")
            return []

    def _validate_and_enrich(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        validated_activities = []
        print("\nValidating")
        for candidate in candidates:
            place_id = candidate.get("place_id_suggestion")
            if not place_id:
                print(f"Warning: Candidate '{candidate.get('place_name')}' is missing a place_id and was skipped.")
                continue
            
            place_details = self.kb.get_place_details(place_id)
            

            if not place_details:
                print(f"Validation failed: Place ID {place_id} ('{candidate.get('place_name')}') does not exist in the knowledge base. Discarded.")
                continue

            print(f"Validation successful: '{place_details['name']}' (ID: {place_id}) is a valid place.")

            enriched_activity = {
                "activity_type": candidate.get("type"),
                "place_id": place_id,
                "name": place_details.get("name"),
                "category": place_details.get("category"), 
                "opening_hours": place_details.get("opening_hours")
            }
            validated_activities.append(enriched_activity)
        
        return validated_activities

    def _score_and_sort(self, activities: List[Dict[str, Any]], preferences: UserPreferences) -> List[Dict[str, Any]]:
        print("\nScoring and sorting validated activities")
        
        for activity in activities:
            score = 0
            if activity.get("category") in preferences.interests:
                score += 10
                print(f"'{activity['name']}' matches interest '{activity['category']}', score +10.")
            else:
                score += 1
                print(f"'{activity['name']}' is a general recommendation, score +1.")
            activity['score'] = score
            
        return sorted(activities, key=lambda x: x['score'], reverse=True)

    def plan_itinerary(self, preferences: UserPreferences) -> Dict[str, Any]:
        candidates = self._generate_candidates_with_llm(preferences)
        if not candidates:
            print("Failed to generate any candidate activities.")
            return {"error": "Failed to generate candidates."}

        validated_activities = self._validate_and_enrich(candidates)
        if not validated_activities:
            print("No candidate activities passed validation.")
            return {"error": "No valid activities found after validation."}

        sorted_activities = self._score_and_sort(validated_activities, preferences)

        final_plan = {
            "itinerary_title": f"{preferences.travel_style} Sydney Trip",
            "status": "Planned",
            "days": [{"day_number": 1, "activities": sorted_activities}]
        }
        print("Complete")
        return final_plan