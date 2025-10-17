import json
from dataclasses import dataclass, field
from typing import List, Dict, Any
# 这里api交互模块是模拟的 我们还没定用哪个
@dataclass
class UserPreferences:
    user_id: int
    interests: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    travel_pace: str = "normal"
    travel_style: str = "Comfort"

class GoalManager:

    def _build_parsing_prompt(self, text: str, form_data: Dict[str, Any]) -> str:
        # prompt还可以再优化和强调输出格式，这里先写个基础
        prompt = f"""
        You are an expert travel assistant. Your task is to analyze the user's text and form data to extract their travel preferences into a structured JSON format.

        **Instructions:**
        1.  Identify key interests, constraints (like dietary needs, accessibility), desired travel pace, and travel style.
        2.  The travel pace must be one of: "slow", "normal", "fast".
        3.  The travel style must be one of: "Economy", "Comfort", "Premium", "Luxury".
        4.  Your output MUST be a single, valid JSON object and nothing else.
        5.  The JSON object must conform to the following schema:
            {{
              "interests": ["string"],
              "constraints": {{ "key": "value" }},
              "travel_pace": "string",
              "travel_style": "string",
              "confidence": float (0.0 to 1.0)
            }}

        **User Input:**
        -   Raw Text: "{text}"
        -   Form Data: {json.dumps(form_data)}

        **Your JSON Output:**
        """
        return prompt.strip()

    def _call_llm_for_parsing(self, text: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_parsing_prompt(text, form_data)
        print("GoalManager: Sending Prompt to LLM")
        print(prompt)
        
        # 这里是模拟LLMapi的调用
        response_text = json.dumps({
            "interests": ["museum", "seafood"],
            "constraints": {"dietary": "seafood_lover"},
            "travel_pace": "slow",
            "travel_style": "Premium",
            "confidence": 0.95
        })
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            print("错误")
            return {} 

    def parse_preferences(self, user_id: int, raw_text: str, form_data: Dict[str, Any]) -> UserPreferences:
        """
        接收原始输入处理并返回结构化的偏好对象。
        """
        parsed_data = self._call_llm_for_parsing(raw_text, form_data)
        if not parsed_data:
            return UserPreferences(user_id=user_id)

        preferences = UserPreferences(
            user_id=user_id,
            interests=parsed_data.get("interests",),
            constraints=parsed_data.get("constraints", {}),
            travel_pace=parsed_data.get("travel_pace", "normal"),
            travel_style=parsed_data.get("travel_style", "Comfort")
        )
        
        print(f"用户 {user_id} 解析完成。")
        return preferences
