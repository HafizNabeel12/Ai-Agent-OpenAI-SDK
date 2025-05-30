import asyncio
from pydantic import BaseModel, Field
from agents import Agent, Runner, function_tool
from typing import List
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Set model choice
model = os.getenv('LLM_MODEL_NAME', 'gpt-4o-mini')

# --- Structured Output Models ---
class WorkoutPlan(BaseModel):
    """Workout recommendation with exercises and details"""
    focus_area: str = Field(description="Primary focus of the workout (e.g., 'upper body', 'cardio')")
    difficulty: str = Field(description="Difficulty level (Beginner, Intermediate, Advanced)")
    exercises: List[str] = Field(description="List of recommended exercises")
    notes: str = Field(description="Additional notes or form tips")

class MealPlan(BaseModel):
    """Basic meal plan recommendation"""
    daily_calories: int = Field(description="Recommended daily calorie intake")
    protein_grams: int = Field(description="Daily protein target in grams")
    carbs_grams: int = Field(description="Daily carbohydrate target in grams") 
    fat_grams: int = Field(description="Daily fat target in grams")
    meal_suggestions: List[str] = Field(description="Simple meal ideas")
    notes: str = Field(description="Dietary advice and tips")

# --- Tools ---
@function_tool
def get_exercise_info(muscle_group: str) -> str:
    """Get a list of exercises for a specific muscle group"""
    exercise_data = {
        "chest": [
            "Push-ups: 3 sets of 10-15 reps",
            "Bench Press: 3 sets of 8-12 reps",
            "Chest Flyes: 3 sets of 12-15 reps",
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

# --- Specialized Agents ---
workout_agent = Agent(
    name="Workout Specialist",
    handoff_description="Specialist agent for creating workout plans",
    instructions="""
    You are a workout specialist who creates effective exercise routines.
    
    Use the get_exercise_info tool to find exercises for specific muscle groups.
    
    Create workouts that are appropriate for the user's level and match their goals.
    Always include form tips to prevent injury.
    """,
    model=model,
    tools=[get_exercise_info],
    output_type=WorkoutPlan
)

nutrition_agent = Agent(
    name="Nutrition Specialist",
    handoff_description="Specialist agent for nutrition advice and meal planning",
    instructions="""
    You are a nutrition specialist who helps users with meal planning and nutrition advice.
    
    Use the calculate_calories tool to determine appropriate calorie and macronutrient targets.
    
    Provide meal suggestions that support the user's fitness goals.
    Focus on practical, sustainable nutrition advice.
    """,
    model=model,
    tools=[calculate_calories],
    output_type=MealPlan
)

# --- Main Fitness Agent with Handoffs ---
fitness_agent = Agent(
    name="Fitness Coach with Specialized Agents",
    instructions="""
    You are a fitness coach who helps users achieve their health and fitness goals.
    
    You can use tools to get exercise information and calculate nutritional needs.
    You can also hand off to specialized agents for more detailed help:
    
    - When the user asks specifically about workouts or exercises, hand off to the workout specialist
    - When the user asks specifically about nutrition, diet, or meal plans, hand off to the nutrition specialist
    
    Only handle general fitness questions yourself. For specialized needs, use the appropriate handoff.
    """,
    model=model,
    tools=[get_exercise_info, calculate_calories],
    handoffs=[workout_agent, nutrition_agent]
)

async def main():
    # Example queries
    queries = [
        "I want to start working out to lose weight. What exercises should I do?",
        "How should I eat to lose 10 pounds in the next 2 months?",
        "Can you give me some general fitness tips for a beginner?"
    ]
    
    for query in queries:
        print("\n" + "="*50)
        print(f"QUERY: {query}")
        print("="*50)
        
        result = await Runner.run(fitness_agent, query)
        print("\nRESPONSE:")
        print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())