from flask import Flask, request, jsonify, session
from flask_cors import CORS
import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv
import logging
import json
from supabase import create_client
from waste_analysis import WasteAnalyzer
from chatbot import UpcyclingChatbot

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

# Configure CORS
# CORS(app, resources={
#     r"/*": {
#         "origins": ["http://localhost:5173", "http://localhost:3000"],
#         "methods": ["GET", "POST", "OPTIONS"],
#         "allow_headers": ["Content-Type", "Authorization"]
#     }
# }, supports_credentials=True)


CORS(app, resources={r"/*": {"origins": ["*"]}}, supports_credentials=False)


# Initialize external services
try:
    # Initialize Supabase
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    supabase = create_client(supabase_url, supabase_key)
    
    # Initialize Cloudinary
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET')
    )
    
    # Initialize our services
    chatbot = UpcyclingChatbot()
    waste_analyzer = WasteAnalyzer()
    
except Exception as e:
    logger.error(f"Error initializing services: {str(e)}")
    raise

# Example hardcoded suggestions (structure matches frontend expectations)
HARDCODED_SUGGESTIONS = [
    {
        "id": "1",
        "title": "Plastic Bottle Planter",
        "description": "Turn an old plastic bottle into a beautiful planter for your home or garden.",
        "difficulty": "Easy",
        "timeRequired": "20 min",
        "tools": ["Scissors", "Marker", "Paint"],
        "materials": ["Plastic Bottle", "Soil", "Seeds"],
        "estimatedCost": "$2",
        "steps": [
            "Cut the bottle in half.",
            "Decorate the outside with paint.",
            "Fill with soil and plant seeds."
        ],
        "safetyTips": ["Be careful when cutting plastic.", "Use non-toxic paint."],
        "ecoImpact": {
            "co2Saved": 0.2,
            "wasteReduced": 0.05,
            "energySaved": 0.1
        },
        "videoSearchQuery": "Plastic Bottle Planter DIY"
    },
    {
        "id": "2",
        "title": "Tin Can Lantern",
        "description": "Create a lantern from an empty tin can for cozy lighting.",
        "difficulty": "Medium",
        "timeRequired": "40 min",
        "tools": ["Hammer", "Nail", "Paintbrush"],
        "materials": ["Tin Can", "Candle", "Wire"],
        "estimatedCost": "$3",
        "steps": [
            "Clean the tin can.",
            "Punch holes in patterns using hammer and nail.",
            "Paint and add a handle with wire.",
            "Place a candle inside."
        ],
        "safetyTips": ["Watch out for sharp edges.", "Supervise children with candles."],
        "ecoImpact": {
            "co2Saved": 0.5,
            "wasteReduced": 0.1,
            "energySaved": 0.2
        },
        "videoSearchQuery": "Tin Can Lantern DIY"
    }
]


@app.route('/')
def home():
    return jsonify({"message": "Flask API is working successfully!"})



# API Routes
@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    """Upload image to Cloudinary"""
    # Create temp directory if it doesn't exist
    if not os.path.exists('temp'):
        os.makedirs('temp')
        
    try:
        # Validate image file
        if 'image' not in request.files:
            return jsonify({
                "success": False,
                "error": "No image file provided"
            }), 400
            
        file = request.files['image']
        if not file.filename:
            return jsonify({
                "success": False,
                "error": "No file selected"
            }), 400

        # Validate file type
        filename = file.filename.lower()
        if not any(filename.endswith(ext) for ext in ['.png', '.jpg', '.jpeg']):
            return jsonify({
                "success": False,
                "error": "Invalid file type. Allowed types: .png, .jpg, .jpeg"
            }), 400

        # Save with original extension
        ext = os.path.splitext(filename)[1]
        temp_path = os.path.join('temp', f'temp_image{ext}')
            
        # Save image temporarily
        file.save(temp_path)
        logger.debug("Saved image to temporary file")
        
        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            return jsonify({
                "success": False,
                "error": "Invalid or empty image file"
            }), 400

        # Upload to Cloudinary
        try:
            upload_result = cloudinary.uploader.upload(temp_path)
            image_url = upload_result.get('secure_url')
            if not image_url:
                raise Exception("Failed to get image URL from Cloudinary")
            session['image_url'] = image_url
            logger.info("Uploaded image to Cloudinary")
            
            return jsonify({
                "success": True,
                "image_url": image_url
            })
            
        except Exception as e:
            logger.error(f"Failed to upload to Cloudinary: {str(e)}")
            return jsonify({
                "success": False,
                "error": "Failed to upload image"
            }), 500
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in image analysis: {error_msg}")
        return jsonify({
            "success": False,
            "error": error_msg
        }), 500
        
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.debug("Cleaned up temporary file")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {str(e)}")

@app.route('/api/generate-suggestions', methods=['POST'])
def generate_suggestions():
    """Generate upcycling suggestions based on form data, including image analysis"""
    try:
        # Get JSON data
        data = request.json
        if not data or 'formData' not in data:
            return jsonify({
                "success": False,
                "error": "Invalid request format. formData is required."
            }), 400

        form_data = data['formData']

        # Validate required fields
        if not form_data.get('description'):
            return jsonify({
                "success": False,
                "error": "Description is required"
            }), 400

        if not form_data.get('imageUrl'):
            return jsonify({
                "success": False,
                "error": "Image URL is required"
            }), 400

        # First analyze the image
        try:
            analysis_result = waste_analyzer.analyze_image(form_data['imageUrl'])
            if not analysis_result["success"]:
                return jsonify({
                    "success": False,
                    "error": "Failed to analyze image"
                }), 400
            image_analysis = analysis_result["analysis"]
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return jsonify({
                "success": False,
                "error": "Failed to analyze image"
            }), 500
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return jsonify({
                "success": False,
                "error": "Failed to analyze image"
            }), 500

        # Generate suggestions with both analysis and form data
        suggestion_data = {
            "description": form_data['description'],
            "type": form_data['type'],
            "category": form_data['category'],
            "condition": form_data['condition'],
            "quantity": form_data['quantity'],
            "dimensions": form_data['dimensions'],
            "weight": form_data['weight'],
            "color": form_data['color'],
            "material": form_data['material'],
            "location": form_data['location'],
            "image_analysis": image_analysis,
            "image_url": form_data['imageUrl']
        }
        
        result = waste_analyzer.generate_suggestions(
            analysis_data=suggestion_data
        )

        if not result["success"]:
            return jsonify(result), 400

        return jsonify({
            "success": True,
            "suggestions": result["suggestions"]
        })

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error generating suggestions: {error_msg}")
        return jsonify({
            "success": False,
            "error": error_msg
        }), 500

@app.route('/api/suggestions', methods=['GET'])
def get_suggestions():
    """Get all saved suggestions for a user"""
    try:
        # Get the authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                "success": False,
                "error": "Missing or invalid authorization token"
            }), 401

        # Extract the JWT token and user ID
        jwt_token = auth_header.split(' ')[1]
        user_id = request.args.get('userId')
        
        if not user_id:
            return jsonify({
                "success": False,
                "error": "User ID is required"
            }), 400

        # Query Supabase for saved suggestions
        try:
            result = supabase.table('saved_suggestions').select('*').eq('user_id', user_id).execute()
            
            if not result.data:
                return jsonify({
                    "success": True,
                    "suggestions": []
                })

            return jsonify({
                "success": True,
                "suggestions": result.data
            })

        except Exception as e:
            logger.error(f"Error fetching from Supabase: {str(e)}")
            return jsonify({
                "success": False,
                "error": "Failed to fetch suggestions"
            }), 500

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in get_suggestions: {error_msg}")
        return jsonify({
            "success": False,
            "error": error_msg
        }), 500

@app.route('/api/save-suggestion', methods=['POST'])
def save_suggestion():
    """Save a suggestion to user's collection"""
    try:
        data = request.json
        if not data or 'suggestion' not in data or 'userId' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required data"
            }), 400

        # Get the authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                "success": False,
                "error": "Missing or invalid authorization token"
            }), 401

        # Extract the JWT token
        jwt_token = auth_header.split(' ')[1]

        suggestion = data['suggestion']
        user_id = data['userId']

        # Insert into Supabase with auth context
        try:
            # Convert the data to match our table structure
            suggestion_data = {
                'user_id': user_id,
                'title': suggestion['title'],
                'description': suggestion['description'],
                'difficulty': suggestion['difficulty'],
                'time_required': suggestion['timeRequired'],
                'tools': suggestion['tools'],
                'materials': suggestion['materials'],
                'estimated_cost': suggestion['estimatedCost'],
                'steps': suggestion['steps'],
                'safety_tips': suggestion['safetyTips'],
                'eco_impact': suggestion['ecoImpact'],
                'video_search_query': suggestion['videoSearchQuery']
            }

            # Create a new Supabase client with the user's JWT
            result = supabase.table('saved_suggestions').insert(suggestion_data).execute(
                
            )
            
            if not result.data:
                raise Exception("Failed to insert data into Supabase")

            return jsonify({
                "success": True,
                "message": "Suggestion saved successfully",
                "data": result.data[0]
            })

        except Exception as e:
            logger.error(f"Error saving to Supabase: {str(e)}")
            return jsonify({
                "success": False,
                "error": "Failed to save suggestion"
            }), 500

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in save_suggestion: {error_msg}")
        return jsonify({
            "success": False,
            "error": error_msg
        }), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat requests and generate responses"""
    try:
        # Log incoming request
        logger.info("Received chat request")
        
        # Validate request data
        data = request.json
        if not data or 'items' not in data:
            logger.warning("Invalid request: missing 'items' field")
            return jsonify({'error': 'No message provided'}), 400

        user_message = data['items']
        if not isinstance(user_message, str):
            logger.warning("Invalid request: 'items' is not a string")
            return jsonify({'error': 'Message must be a text string'}), 400

        logger.info(f"Processing message: {user_message[:50]}...")  # Log first 50 chars
        
        try:
            # Use the global chatbot instance
            response = chatbot.handle_message(user_message)
            logger.info("Successfully processed message")
            return jsonify({'response': response})
            
        except Exception as ai_error:
            logger.warning(f"AI service error: {str(ai_error)}")
            # Fall back to basic responses
            response = chatbot.get_fallback_response(user_message)
            return jsonify({'response': response})
            
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        return jsonify({
            'error': 'Sorry, I encountered a technical issue. Please try again in a moment.',
            'details': str(e) if os.getenv('DEBUG') == 'true' else None
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
