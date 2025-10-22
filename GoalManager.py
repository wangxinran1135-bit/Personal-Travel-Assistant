import json
from dataclasses import dataclass, field
from typing import List, Dict, Any

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser



@dataclass
class UserPreferences:
    user_id: int
    interests: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    travel_pace: str = "normal"
    travel_style: str = "Comfort"

class ParsedPreferences(BaseModel):
    interests: List[str] = Field(description="List of user's interests, e.g.: ['museum', 'seafood']")
    constraints: Dict[str, Any] = Field(description="User's constraints, e.g.: {'dietary': 'seafood_lover'}")
    travel_pace: str = Field(description="Travel pace, must be one of 'slow', 'normal', or 'fast'")
    travel_style: str = Field(description="Travel style, must be one of 'Economy', 'Comfort', 'Premium', or 'Luxury'")
    confidence: float = Field(description="Parsing confidence (0.0 to 1.0)")



class GoalManager:
    def __init__(self, db_connection):
        self.conn = db_connection
        
        self.llm = ChatOpenAI(temperature=0, model="gpt-4-turbo")

        self.parser = PydanticOutputParser(pydantic_object=ParsedPreferences)

        prompt_string = self._build_parsing_prompt_template_string()
        self.prompt_template = ChatPromptTemplate.from_template(
            template=prompt_string,
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )

        self.chain = self.prompt_template | self.llm | self.parser
        
        print("GoalManager initialized with LangChain chain.")

    def save_preferences(self, preferences: UserPreferences):

        try:
            with self.conn.cursor() as cur:
                sql = """
                    INSERT INTO preferences (user_id, interests, constraints, travel_pace, travel_style)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (user_id)
                    DO UPDATE SET 
                        interests = EXCLUDED.interests,
                        constraints = EXCLUDED.constraints,
                        travel_pace = EXCLUDED.travel_pace,
                        travel_style = EXCLUDED.travel_style,
                        updated_at = CURRENT_TIMESTAMP
                """
                cur.execute(sql, (
                    preferences.user_id,
                    json.dumps(preferences.interests),
                    json.dumps(preferences.constraints),
                    preferences.travel_pace,
                    preferences.travel_style
                ))
                self.conn.commit()
                print(f"Saved preferences for user {preferences.user_id}")
        except Exception as e:
            self.conn.rollback()
            print(f"Error saving preferences: {e}")
            
    def _build_parsing_prompt_template_string(self) -> str:
   
        prompt = """
        You are an expert travel assistant. Your task is to analyze the user's text and form data to extract their travel preferences into a structured JSON format.

        **Instructions:**
        1.  Identify key interests, constraints (like dietary needs, accessibility), desired travel pace, and travel style.
        2.  The travel pace must be one of: "slow", "normal", "fast".
        3.  The travel style must be one of: "Economy", "Comfort", "Premium", "Luxury".
        4.  Your output MUST be a single, valid JSON object and nothing else.
        5.  You MUST adhere *strictly* to the following JSON schema:
            {format_instructions}

        **User Input:**
        -   Raw Text: "{text}"
        -   Form Data: "{form_data}"

        **Your JSON Output (JSON only):**
        """
        return prompt.strip()

    def _call_llm_for_parsing(self, text: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
     
        print("GoalManager: Sending Prompt to LLM via LangChain...")
        
        try:

            parsed_result: ParsedPreferences = self.chain.invoke({
                "text": text,
                "form_data": json.dumps(form_data) 
            })
            
            return parsed_result.model_dump()
        
        except Exception as e:
            print(f"LangChain chain call failed {e}")
            return {} 

    def parse_preferences(self, user_id: int, raw_text: str, form_data: Dict[str, Any]) -> UserPreferences:
    
        parsed_data = self._call_llm_for_parsing(raw_text, form_data)
        if not parsed_data:
            return UserPreferences(user_id=user_id)

        preferences = UserPreferences(
            user_id=user_id,
            interests=parsed_data.get("interests", []),
            constraints=parsed_data.get("constraints", {}),
            travel_pace=parsed_data.get("travel_pace", "normal"),
            travel_style=parsed_data.get("travel_style", "Comfort")
        )
        
        print(f"Parsing complete for user {user_id}.")
        return preferences
