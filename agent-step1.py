import asyncio
from pydantic import BaseModel, Field
from agents import Agent, Runner
from dotenv import load_dotenv
import os

# Load environment variables FIRST
load_dotenv()

#  Force-set OPENAI_API_KEY into os.environ
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


# Set model choice
model = os.getenv('LLM_MODEL_NAME', 'gpt-4o-mini')

# --- Structured Output Model ---
class WorkoutPlan(BaseModel):
    """Workout recommendation with exercises and details"""
    focus_area: str = Field(description="Primary focus of the workout (e.g., 'upper body', 'cardio')")
    difficulty: str = Field(description="Difficulty level (Beginner, Intermediate, Advanced)")
    exercises: list[str] = Field(description="List of recommended exercises")
    notes: str = Field(description="Additional notes or form tips")

# --- Simple Fitness Agent ---
fitness_agent = Agent(
    name="Basic Fitness Coach",
    instructions="""
    You are a fitness coach who creates workout plans for users based on their goals.

    When a user asks for workout recommendations:
    1. Determine their fitness goal (weight loss, muscle gain, endurance, etc.)
    2. Consider any information they provide about their fitness level
    3. Create an appropriate workout plan with exercises that match their goal
    4. Include form tips and safety notes

    Your responses should be practical, safe, and tailored to the user's needs.
    """,
    model=model,
    output_type=WorkoutPlan  # This enforces the structured output
)

async def main():
    query = "I want to build some muscle in my upper body. I'm a beginner and don't have much equipment."
    
    print("\n" + "*"*50)
    print(f"QUERY: {query}")
    print("="*50)
    
    result = await Runner.run(fitness_agent, query)
    print("\nSTRUCTURED RESPONSE:")
    print(result.final_output)

    print("\n" + "#"*50)
    print("\nNOTES:")
    print(result.final_output.notes)

if __name__ == "__main__":
    asyncio.run(main())
