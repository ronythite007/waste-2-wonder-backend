from crewai import Agent, Task, Crew
from crewai.llm import LLM
from crewai_tools import TavilySearchTool
import logging

# Configure logging
logger = logging.getLogger(__name__)

class UpcyclingChatbot:
    def __init__(self):
        """Initialize the chatbot with LLM and response patterns"""
        self.llm = LLM(
            model="gemini/gemini-2.0-flash",
            temperature=0.1
        )
        
        self.response_patterns = {
            'greetings': ['hi', 'hello', 'hey', 'hola'],
            'identity': ['name', 'who are you', 'what are you','what is waste2wonder'],
            'capabilities': ['can you do', 'help', 'what do you do', 'how can you help']
        }

    def create_upcycling_crew(self, items):
        """Create a CrewAI setup for generating upcycling suggestions"""
        
        # Research Agent
        research_agent = Agent(
            role="Upcycling Research Specialist",
            goal=f"Research creative and practical upcycling ideas specifically for: {items}. Focus on DIY-friendly, safe, and impactful projects.",
            backstory="""You are an expert at finding creative and practical upcycling solutions. 
            You focus on projects that are feasible for home crafters and have meaningful environmental impact.
            You always consider safety and practicality in your suggestions.""",
            tools=[TavilySearchTool()],
            verbose=True,
            llm=self.llm
        )

        # Writer Agent
        writer_agent = Agent(
            role="Upcycling Idea Writer",
            goal="Create a detailed, step-by-step guide for the most practical and impactful upcycling idea",
            backstory="""You are a DIY expert who excels at explaining upcycling projects clearly.
            You break down complex ideas into simple steps and always include safety precautions.
            You focus on making instructions accessible to everyone.""",
            llm=self.llm,
            verbose=True
        )

        # Tasks
        task1 = Task(
            description=f"Find 3-5 recent or practical upcycling ideas for the materials: {items}. Focus on sustainability, feasibility, and creativity.",
            expected_output="A list of 3-5 potential upcycling ideas or inspirations",
            agent=research_agent
        )

        task2 = Task(
            description=(
                "Using the research results from task1, provide one unique and creative upcycling idea. "
                "Include materials, steps, and safety tips. Format it neatly as a single actionable idea."
            ),
            expected_output="A single, actionable upcycling idea formatted with Materials, Steps, Safety Tips",
            agent=writer_agent,
            context=[task1]
        )

        return Crew(
            agents=[research_agent, writer_agent],
            tasks=[task1, task2],
            verbose=True
        )

    def get_fallback_response(self, message):
        """Get a fallback response when AI service is unavailable"""
        message = message.lower()
        
        if any(greeting in message for greeting in self.response_patterns['greetings']):
            return "Hi! I'm Wonder, your Waste2Wonder assistant. I'm here to help with waste management and upcycling!"
        elif any(word in message for word in self.response_patterns['identity']):
            return "I'm Wonder, the AI assistant for Waste2Wonder. I focus on helping with waste management and upcycling ideas!"
        elif any(word in message for word in self.response_patterns['capabilities']):
            return "I can help you with waste management tips, upcycling ideas, and sustainability advice. Just ask me anything about reducing waste or reusing materials!"
        return "I'd love to help you upcycle your items! Could you tell me what materials you'd like to repurpose?"

    def is_upcycling_query(self, message):
        """Determine if the message is asking for upcycling suggestions"""
        message = message.lower()
        
        # Keywords that indicate upcycling intent
        upcycling_keywords = [
            'upcycling', 'upcycle', 'reuse', 'repurpose', 'make from', 'create with',
            'what can i do with', 'how to reuse', 'ideas for', 'craft from', 'tell me',
            'using', 'ideas', 'old', 'waste', 'recycle'
        ]
        
        # Material keywords that often indicate upcycling queries
        material_keywords = [
            'plastic', 'paper', 'bottle', 'box', 'container', 'cardboard',
            'glass', 'metal', 'wood', 'cloth', 'fabric', 'materials'
        ]
        
        # Check for upcycling intent
        has_upcycling_term = any(keyword in message for keyword in upcycling_keywords)
        has_material_term = any(keyword in message for keyword in material_keywords)
        
        # If message contains both upcycling intent and mentions materials, it's likely an upcycling query
        return has_upcycling_term and has_material_term

    def handle_message(self, message):
        """Process user message and return appropriate response"""
        try:
            # Log the message type for debugging
            is_upcycling = self.is_upcycling_query(message)
            logger.info(f"Message: '{message}' - Is upcycling query: {is_upcycling}")
            
            # For casual conversations, use Gemini directly
            if not is_upcycling:
                response = self.llm.generate(f"""
                You are Wonder, a friendly AI assistant for Waste2Wonder. 
                Respond to this casual conversation: "{message}"
                Keep the response concise and friendly, but don't give any upcycling suggestions unless specifically asked.
                """)
                return str(response)
            
            # For upcycling queries, use CrewAI workflow
            crew = self.create_upcycling_crew(message)
            result = crew.kickoff()
            return str(result)
            
        except Exception as e:
            logger.warning(f"AI service error, using fallback: {str(e)}")
            return self.get_fallback_response(message)