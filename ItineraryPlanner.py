import json
from dataclasses import dataclass, field
from typing import List, Dict, Any
from GoalManager import UserPreferences 


from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser


class CandidateActivity(BaseModel):
    type: str = Field(description="Activity type, must be 'VisitPOI' or 'Meal'")
    place_name: str = Field(description="Name of the place")
    place_id_suggestion: int = Field(description="The place_id_suggestion from the 'Available Places' list")

class ActivityList(BaseModel):
    activities: List[CandidateActivity] = Field(description="List of 5-7 recommended activities")


class ItineraryPlanner:

    def __init__(self, knowledge_base):

        self.kb = knowledge_base

        self.llm = ChatOpenAI(temperature=0.7, model="gpt-4-turbo")

        self.parser = PydanticOutputParser(pydantic_object=ActivityList)


        prompt_string = self._build_candidate_generation_prompt_string()
        self.prompt_template = ChatPromptTemplate.from_template(
            template=prompt_string,
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )

        self.chain = self.prompt_template | self.llm | self.parser
        
        print("ItineraryPlanner initialized with LangChain chain.")


    def _build_candidate_generation_prompt_string(self) -> str:

        prompt = """
        You are a creative and pragmatic Sydney travel planner. Your task is to recommend a list of 5-7 potential activities based on the user's preferences.

        **User Preferences:**
        -   Interests: {interests}
        -   Travel Style: {travel_style}
        -   Travel Pace: {travel_pace}
        -   Constraints: {constraints}

        **Available Sydney Places (Please use these for recommendations):**
        {available_places}

        **Instructions:**
        1.  Generate a list of 5-7 activities based on user preferences.
        2.  For each activity, you must use the `place_id_suggestion` provided in the "Available Places" list above.
        3.  Your output must be a single, valid JSON object. Do not include any other text, markdown, or explanations.
        4.  The JSON object must *strictly* adhere to the following format:
            {format_instructions}

        **Your JSON Output (JSON only):**
        """
        return prompt.strip()

    def _generate_candidates_with_llm(self, preferences: UserPreferences) -> List[Dict[str, Any]]:

        known_places = self.kb.find_places_by_interests(preferences.interests)
        if not known_places:
            print("Could not find relevant places.")
            return []
        
        print("Sending prompt to LLM via LangChain...")
        
        try:
            activity_list_obj: ActivityList = self.chain.invoke({
                "interests": ', '.join(preferences.interests),
                "travel_style": preferences.travel_style,
                "travel_pace": preferences.travel_pace,
                "constraints": json.dumps(preferences.constraints),
                "available_places": json.dumps(known_places, indent=2)
            })

            return [activity.model_dump() for activity in activity_list_obj.activities]

        except Exception as e:
            print(f"Error calling chain or decoding JSON from LLM: {e}")
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
