import asyncio
import json
from pydantic import BaseModel, Field
from agents import Agent, Runner, function_tool
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Set model choice
model = os.getenv('LLM_MODEL_NAME', 'gpt-4o-mini')

# --- Structured Output Model ---
class WorkoutPlan(BaseModel):
    """Workout recommendation with exercises and details"""
    focus_area: str = Field(description="Primary focus of the workout (e.g., 'upper body', 'cardio')")
    difficulty: str = Field(description="Difficulty level (Beginner, Intermediate, Advanced)")
    exercises: list[str] = Field(description="List of recommended exercises")
    notes: str = Field(description="Additional notes or form tips")

# --- Tools ---
@function_tool
def get_exercise_info(muscle_group: str) -> str:
    """Get a list of exercises for a specific muscle group"""
    exercise_data = {
        "chest": [
            "Push-ups: 3 sets of 10-15 reps",
            "Bench Press: 3 sets of 8-12 reps",
            "Chest Flyes: 4 sets of 12-15 reps",
            "Incline Push-ups: 3 sets of 10-15 reps"
        ],
        "back": [
            "Pull-ups: 3 sets of 6-10 reps",
            "Bent-over Rows: 3 sets of 8-12 reps",
            "Lat Pulldowns: 3 sets of 10-12 reps",
            "Superman Holds: 3 sets of 30 seconds"
        ],
        "legs": [
            "Squats: 3 sets of 10-15 reps",
            "Lunges: 3 sets of 10 per leg",
            "Calf Raises: 3 sets of 15-20 reps",
            "Glute Bridges: 3 sets of 15 reps"
        ],
        "arms": [
            "Bicep Curls: 3 sets of 10-12 reps",
            "Tricep Dips: 3 sets of 10-15 reps",
            "Hammer Curls: 3 sets of 10-12 reps",
            "Overhead Tricep Extensions: 3 sets of 10-12 reps"
        ],
        "core": [
            "Planks: 3 sets of 30-60 seconds",
            "Crunches: 3 sets of 15-20 reps",
            "Russian Twists: 3 sets of 20 total reps",
            "Mountain Climbers: 3 sets of 20 total reps"
        ]
    }
    
    muscle_group = muscle_group.lower()
    if muscle_group in exercise_data:
        exercises = exercise_data[muscle_group]
        return json.dumps({
            "muscle_group": muscle_group,
            "exercises": exercises,
            "recommendation": f"For {muscle_group} training, complete all exercises with 60-90 seconds rest between sets."
        })
    else:
        return f"Exercise information for {muscle_group} is not available."

@function_tool
def calculate_calories(goal: str, weight_kg: float, height_cm: float, age: int, gender: str) -> str:
    """Calculate daily calorie needs and macronutrient breakdown based on user stats and goals"""
    
    # Calculate BMR (Basal Metabolic Rate) using Mifflin-St Jeor Equation
    if gender.lower() in ['male', 'm']:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:  # female
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    
    # Use a moderate activity level for this example
    tdee = bmr * 1.55
    
    # Adjust based on goal
    if goal.lower() == "weight loss":
        calorie_target = tdee - 500  # 500 calorie deficit
    elif goal.lower() == "muscle gain":
        calorie_target = tdee + 300  # 300 calorie surplus
    else:  # maintenance
        calorie_target = tdee
    
    # Calculate macros (simplified)
    if goal.lower() == "weight loss":
        protein_pct = 0.40  # 40% protein
        fat_pct = 0.30      # 30% fat
        carb_pct = 0.30     # 30% carbs
    elif goal.lower() == "muscle gain":
        protein_pct = 0.30  # 30% protein
        fat_pct = 0.25      # 25% fat
        carb_pct = 0.45     # 45% carbs
    else:  # maintenance or general fitness
        protein_pct = 0.30  # 30% protein
        fat_pct = 0.30      # 30% fat
        carb_pct = 0.40     # 40% carbs
    
    # Convert percentages to grams
    protein_calories = calorie_target * protein_pct
    fat_calories = calorie_target * fat_pct
    carb_calories = calorie_target * carb_pct
    
    # Protein and carbs have 4 calories per gram, fat has 9 calories per gram
    protein_grams = round(protein_calories / 4)
    fat_grams = round(fat_calories / 9)
    carb_grams = round(carb_calories / 4)
    
    result = {
        "goal": goal,
        "daily_calories": round(calorie_target),
        "macros": {
            "protein": protein_grams,
            "fat": fat_grams,
            "carbs": carb_grams
        }
    }
    
    return json.dumps(result)

# --- Fitness Agent with Tools ---
fitness_agent = Agent(
    name="Fitness Coach with Tools",
    instructions="""
    You are a fitness coach who creates workout plans and provides nutrition advice.
    
    Use the get_exercise_info tool to find exercises for specific muscle groups.
    Use the calculate_calories tool to provide nutrition guidance.
    
    When a user asks for workout recommendations:
    1. Determine their fitness goal
    2. Use the get_exercise_info tool to find appropriate exercises
    3. Create a workout plan that matches their goals
    
    When a user asks for nutrition advice:
    1. Ask for their stats if not provided (weight, height, age, gender)
    2. Use the calculate_calories tool to determine their needs
    3. Provide practical nutrition guidance based on the calculations
    
    Your responses should be practical, safe, and tailored to the user's needs.
    """,
    model=model,
    tools=[get_exercise_info, calculate_calories],
    output_type=WorkoutPlan
)

async def main():
    # Example queries
    queries = [
        "What are some good chest exercises I can do at home?",
        "I'm 30 years old, male, 175cm tall, and weigh 80kg. How many calories should I eat to lose weight?"
    ]
    
    for query in queries:
        print("\n" + "#"*50)
        print(f"QUERY: {query}")
        print("="*50)
        
        result = await Runner.run(fitness_agent, query)
        print("\nRESPONSE:")
        print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())