from groq import Groq
import base64
import os
from typing import List, Dict, Union
import json
from dotenv import load_dotenv
load_dotenv()
class WasteAnalyzer:
    def __init__(self):
        """Initialize WasteAnalyzer with Groq client"""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set in the environment variables.")
        self.client = Groq(api_key=api_key)
        
    def encode_image(self, image_file) -> str:
        """Encode the uploaded file to base64"""
        try:
            image_file.seek(0)  # Reset file pointer
            encoded = base64.b64encode(image_file.read()).decode("utf-8")
            image_file.seek(0)  # Reset for future use
            return encoded
        except Exception as e:
            print(f"Error encoding image: {str(e)}")
            return ""

    def analyze_image(self, image_url) -> dict:
        """Get material analysis from image using Groq's image recognition"""
        if not image_url:
            print("No image URL provided")
            return {"success": False, "error": "No image URL provided"}
            
        try:
            # Make API call for material analysis using URL directly
            response = self.client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please identify and describe:\n1. Main materials or objects in the image\n2. Their condition and colors\n3. Approximate size/dimensions\n4. Any unique features or characteristics\n5. Potential for upcycling"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }],
                temperature=0.5,
                max_tokens=500
            )
            
            return {
                "success": True, 
                "analysis": response.choices[0].message.content
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error analyzing image: {error_msg}")
            return {"success": False, "error": error_msg}

    def generate_suggestions(self, analysis_data: dict) -> dict:
        """Generate upcycling suggestions based on image analysis and form data"""
        try:
            # Create comprehensive prompt for project suggestions
            prompt = f'''
Based on this waste item analysis:
{analysis_data['image_analysis']}

Item Description: {analysis_data['description']}
Type: {analysis_data['type']}
Category: {analysis_data['category']}
Condition: {analysis_data['condition']}
Quantity: {analysis_data['quantity']}
Additional Details:
- Dimensions: {analysis_data.get('dimensions', 'Not specified')}
- Weight: {analysis_data.get('weight', 'Not specified')}
- Color: {analysis_data.get('color', 'Not specified')}
- Material: {analysis_data.get('material', 'Not specified')}
- Location: {analysis_data.get('location', 'Not specified')}

Generate EXACTLY 3 practical upcycling project suggestions. Return them in VALID JSON format following this structure:

{{
  "suggestions": [
    {{
      "id": "1",
      "title": "Project Title",
      "description": "Brief description of the project",
      "difficulty": "Easy/Medium/Hard",
      "timeRequired": "X hours/minutes",
      "tools": ["tool1", "tool2"],
      "materials": ["material1", "material2"],
      "estimatedCost": "$X",
      "steps": ["step1", "step2", "step3"],
      "safetyTips": ["tip1", "tip2"],
      "ecoImpact": {{
        "co2Saved": 0.2,
        "wasteReduced": 0.05,
        "energySaved": 0.1
      }},
      "videoSearchQuery": "Search query for tutorial video"
    }}
  ]
}}

Ensure the suggestions are practical, match the material type and condition, and include realistic environmental impact estimates.

🪴 Description:
{{Short description of the finished product.}}

⏱️ Time Estimate: X-Y hours

🧰 Required Tools (count tools and list):
- Tool 1
- Tool 2

🧱 Materials:
- Material 1
- Material 2

💵 Estimated Cost: $X-Y

📋 Steps:
1. Step one...
2. Step two...
...
(10 steps max)

⚠️ Safety Tips:
- Tip 1
- Tip 2

🌱 Environmental Impact:
- CO2 Saved: X.X kg
- Waste Reduced: X.X kg
- Energy Saved: X.X kWh
---

Please provide two unique project ideas following this EXACT format.
Ensure projects are practical and match the available materials.
'''

            # Generate suggestions using a different model optimized for creative text
            # Generate creative suggestions
            chat_completion = self.client.chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                model="llama-3.3-70b-versatile",  # Model better suited for creative text generation
                temperature=0.7,
                max_tokens=2000
            )

            # Get the response
            response_text = chat_completion.choices[0].message.content

            response_text = sanitize_response(response_text)

            try:
                # Parse JSON from response
                suggestions_data = json.loads(response_text)
                
                # Validate structure
                if not isinstance(suggestions_data, dict) or 'suggestions' not in suggestions_data:
                    raise ValueError("Invalid response format")
                
                # Ensure each suggestion has required fields
                for suggestion in suggestions_data['suggestions']:
                    required_fields = [
                        'id', 'title', 'description', 'difficulty', 'timeRequired',
                        'tools', 'materials', 'estimatedCost', 'steps', 'safetyTips',
                        'ecoImpact', 'videoSearchQuery'
                    ]
                    for field in required_fields:
                        if field not in suggestion:
                            suggestion[field] = '' if field in ['id', 'title', 'description', 'difficulty', 
                                                              'timeRequired', 'estimatedCost', 'videoSearchQuery'] else []
                    
                    if 'ecoImpact' not in suggestion or not isinstance(suggestion['ecoImpact'], dict):
                        suggestion['ecoImpact'] = {
                            'co2Saved': 0.0,
                            'wasteReduced': 0.0,
                            'energySaved': 0.0
                        }

                return {
                    "success": True,
                    "suggestions": suggestions_data['suggestions']
                }
                
            except json.JSONDecodeError:
                print(f"Failed to parse JSON from response: {response_text}")
                return {
                    "success": False,
                    "error": "Failed to generate valid suggestions"
                }
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error generating suggestions: {error_msg}")
            return {"success": False, "error": error_msg}

if __name__ == "__main__":
    # Test data
    analyzer = WasteAnalyzer()
    test_data = {
        "description": "Old plastic bottle",
        "imageUrl": "https://example.com/image.jpg",
        "type": "Plastic bottle",
        "category": "Plastic",
        "condition": "Good",
        "quantity": 1,
        "dimensions": "20cm x 10cm",
        "weight": "50g",
        "color": "Clear",
        "material": "PET plastic",
        "location": "New York"
    }
    
    # Test analysis and suggestions
    analysis = analyzer.analyze_image(test_data["imageUrl"])
    if analysis["success"]:
        test_data["image_analysis"] = analysis["analysis"]
        suggestions = analyzer.generate_suggestions(test_data)
        print("\nSuggestions:", json.dumps(suggestions, indent=2))


def sanitize_response(response_text: str) -> str:
    """Sanitize the response text to ensure it is valid JSON"""
    # Remove any leading/trailing text before/after the JSON object
    start_idx = response_text.find('{')
    end_idx = response_text.rfind('}') + 1
    if start_idx != -1 and end_idx != -1:
        return response_text[start_idx:end_idx]
    return response_text