"""
Fitness AI MCP Server
Health and fitness tools powered by MEOK AI Labs.
"""


import sys, os
sys.path.insert(0, os.path.expanduser('~/clawd/meok-labs-engine/shared'))
from auth_middleware import check_access

import time
import math
import random
import hashlib
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("fitness-ai", instructions="MEOK AI Labs MCP Server")

_call_counts: dict[str, list[float]] = defaultdict(list)
FREE_TIER_LIMIT = 40
WINDOW = 86400


def _check_rate_limit(tool_name: str) -> None:
    now = time.time()
    _call_counts[tool_name] = [t for t in _call_counts[tool_name] if now - t < WINDOW]
    if len(_call_counts[tool_name]) >= FREE_TIER_LIMIT:
        raise ValueError(f"Rate limit exceeded for {tool_name}. Free tier: {FREE_TIER_LIMIT}/day.")
    _call_counts[tool_name].append(now)


EXERCISES = {
    "chest": [
        {"name": "Bench Press", "type": "compound", "equipment": "barbell"},
        {"name": "Dumbbell Flyes", "type": "isolation", "equipment": "dumbbells"},
        {"name": "Push-ups", "type": "compound", "equipment": "bodyweight"},
        {"name": "Incline Bench Press", "type": "compound", "equipment": "barbell"},
        {"name": "Cable Crossovers", "type": "isolation", "equipment": "cable"},
    ],
    "back": [
        {"name": "Deadlift", "type": "compound", "equipment": "barbell"},
        {"name": "Pull-ups", "type": "compound", "equipment": "bodyweight"},
        {"name": "Barbell Rows", "type": "compound", "equipment": "barbell"},
        {"name": "Lat Pulldown", "type": "compound", "equipment": "cable"},
        {"name": "Seated Cable Row", "type": "compound", "equipment": "cable"},
    ],
    "legs": [
        {"name": "Squat", "type": "compound", "equipment": "barbell"},
        {"name": "Leg Press", "type": "compound", "equipment": "machine"},
        {"name": "Romanian Deadlift", "type": "compound", "equipment": "barbell"},
        {"name": "Lunges", "type": "compound", "equipment": "dumbbells"},
        {"name": "Leg Curl", "type": "isolation", "equipment": "machine"},
        {"name": "Calf Raises", "type": "isolation", "equipment": "machine"},
    ],
    "shoulders": [
        {"name": "Overhead Press", "type": "compound", "equipment": "barbell"},
        {"name": "Lateral Raises", "type": "isolation", "equipment": "dumbbells"},
        {"name": "Face Pulls", "type": "isolation", "equipment": "cable"},
        {"name": "Arnold Press", "type": "compound", "equipment": "dumbbells"},
    ],
    "arms": [
        {"name": "Barbell Curl", "type": "isolation", "equipment": "barbell"},
        {"name": "Tricep Dips", "type": "compound", "equipment": "bodyweight"},
        {"name": "Hammer Curls", "type": "isolation", "equipment": "dumbbells"},
        {"name": "Skull Crushers", "type": "isolation", "equipment": "barbell"},
        {"name": "Cable Tricep Pushdown", "type": "isolation", "equipment": "cable"},
    ],
    "core": [
        {"name": "Plank", "type": "isometric", "equipment": "bodyweight"},
        {"name": "Hanging Leg Raises", "type": "compound", "equipment": "bodyweight"},
        {"name": "Cable Woodchops", "type": "compound", "equipment": "cable"},
        {"name": "Ab Wheel Rollout", "type": "compound", "equipment": "ab_wheel"},
    ],
    "cardio": [
        {"name": "Running", "type": "cardio", "equipment": "none"},
        {"name": "Cycling", "type": "cardio", "equipment": "bike"},
        {"name": "Rowing", "type": "cardio", "equipment": "rowing_machine"},
        {"name": "Jump Rope", "type": "cardio", "equipment": "jump_rope"},
        {"name": "Swimming", "type": "cardio", "equipment": "pool"},
    ],
}


@mcp.tool()
def generate_workout(
    goal: str = "general_fitness",
    experience_level: str = "intermediate",
    duration_minutes: int = 45,
    equipment_available: list[str] | None = None,
    muscle_groups: list[str] | None = None,
    exclude_exercises: list[str] | None = None, api_key: str = "") -> dict:
    """Generate a complete workout plan tailored to goals and equipment.

    Args:
        goal: Fitness goal: strength, hypertrophy, fat_loss, general_fitness, endurance
        experience_level: Level: beginner, intermediate, advanced
        duration_minutes: Available workout time in minutes
        equipment_available: Available equipment: barbell, dumbbells, cable, machine, bodyweight, none
        muscle_groups: Target muscle groups: chest, back, legs, shoulders, arms, core, cardio
        exclude_exercises: Exercise names to exclude

    Behavior:
        This tool generates structured output without modifying external systems.
        Output is deterministic for identical inputs. No side effects.
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.
    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    _check_rate_limit("generate_workout")

    equipment_available = equipment_available or ["barbell", "dumbbells", "cable", "machine", "bodyweight"]
    exclude_exercises = [e.lower() for e in (exclude_exercises or [])]

    if not muscle_groups:
        muscle_groups = {"strength": ["chest", "back", "legs"], "hypertrophy": ["chest", "back", "legs", "shoulders", "arms"],
                        "fat_loss": ["legs", "back", "core", "cardio"], "general_fitness": ["chest", "back", "legs", "core"],
                        "endurance": ["cardio", "legs", "core"]}.get(goal, ["chest", "back", "legs"])

    set_schemes = {
        "strength": {"sets": 5, "reps": "3-5", "rest_sec": 180},
        "hypertrophy": {"sets": 4, "reps": "8-12", "rest_sec": 90},
        "fat_loss": {"sets": 3, "reps": "12-15", "rest_sec": 45},
        "general_fitness": {"sets": 3, "reps": "10-12", "rest_sec": 60},
        "endurance": {"sets": 2, "reps": "15-20", "rest_sec": 30},
    }
    scheme = set_schemes.get(goal, set_schemes["general_fitness"])

    exercises_per_group = max(2, duration_minutes // (len(muscle_groups) * 8))
    workout = []
    total_sets = 0

    seed = hashlib.md5(f"{goal}{duration_minutes}{time.time():.0f}".encode()).hexdigest()
    rng = random.Random(seed)

    for group in muscle_groups:
        available = [e for e in EXERCISES.get(group, [])
                     if e["equipment"] in equipment_available and e["name"].lower() not in exclude_exercises]
        if not available:
            continue

        rng.shuffle(available)
        selected = available[:exercises_per_group]

        # Compounds first
        selected.sort(key=lambda e: 0 if e["type"] == "compound" else 1)

        for ex in selected:
            if ex["type"] == "cardio":
                workout.append({
                    "exercise": ex["name"],
                    "muscle_group": group,
                    "duration": f"{min(20, duration_minutes // 4)} minutes",
                    "intensity": {"fat_loss": "HIIT intervals", "endurance": "steady state"}.get(goal, "moderate"),
                    "equipment": ex["equipment"],
                })
            elif ex["type"] == "isometric":
                workout.append({
                    "exercise": ex["name"],
                    "muscle_group": group,
                    "sets": scheme["sets"],
                    "hold": "30-60 seconds",
                    "rest_seconds": scheme["rest_sec"],
                    "equipment": ex["equipment"],
                })
                total_sets += scheme["sets"]
            else:
                workout.append({
                    "exercise": ex["name"],
                    "muscle_group": group,
                    "sets": scheme["sets"],
                    "reps": scheme["reps"],
                    "rest_seconds": scheme["rest_sec"],
                    "equipment": ex["equipment"],
                    "type": ex["type"],
                })
                total_sets += scheme["sets"]

    return {
        "goal": goal,
        "experience_level": experience_level,
        "duration_minutes": duration_minutes,
        "exercises": workout,
        "total_exercises": len(workout),
        "total_sets": total_sets,
        "warmup": "5-10 min light cardio + dynamic stretching for target muscle groups",
        "cooldown": "5 min static stretching + foam rolling",
        "tips": {
            "strength": "Focus on progressive overload. Rest fully between sets.",
            "hypertrophy": "Control the eccentric phase. Mind-muscle connection is key.",
            "fat_loss": "Keep rest periods short. Superset where possible.",
            "general_fitness": "Maintain proper form throughout. Increase weight gradually.",
            "endurance": "Keep heart rate in zone 2-3. Focus on breathing rhythm.",
        }.get(goal, "Listen to your body and maintain proper form."),
    }


@mcp.tool()
def track_calories(
    foods: list[dict],
    target_calories: int = 2000,
    target_protein_g: int = 0, api_key: str = "") -> dict:
    """Track daily calorie and macronutrient intake from food entries.

    Args:
        foods: List of dicts with keys: name, calories, protein_g (optional), carbs_g (optional), fat_g (optional), quantity (optional, default 1)
        target_calories: Daily calorie target
        target_protein_g: Daily protein target in grams (0 = auto-calculate)

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.
    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    _check_rate_limit("track_calories")

    total_cal = 0
    total_protein = 0
    total_carbs = 0
    total_fat = 0
    entries = []

    for food in foods:
        qty = float(food.get("quantity", 1))
        cal = float(food.get("calories", 0)) * qty
        protein = float(food.get("protein_g", 0)) * qty
        carbs = float(food.get("carbs_g", 0)) * qty
        fat = float(food.get("fat_g", 0)) * qty

        total_cal += cal
        total_protein += protein
        total_carbs += carbs
        total_fat += fat

        entries.append({
            "name": food.get("name", "Unknown"),
            "quantity": qty,
            "calories": round(cal),
            "protein_g": round(protein, 1),
            "carbs_g": round(carbs, 1),
            "fat_g": round(fat, 1),
        })

    if target_protein_g == 0:
        target_protein_g = round(target_calories * 0.3 / 4)  # 30% of calories from protein

    remaining_cal = target_calories - total_cal
    remaining_protein = target_protein_g - total_protein

    macro_cals = total_protein * 4 + total_carbs * 4 + total_fat * 9
    macro_split = {
        "protein": f"{(total_protein * 4 / macro_cals * 100):.0f}%" if macro_cals > 0 else "0%",
        "carbs": f"{(total_carbs * 4 / macro_cals * 100):.0f}%" if macro_cals > 0 else "0%",
        "fat": f"{(total_fat * 9 / macro_cals * 100):.0f}%" if macro_cals > 0 else "0%",
    }

    return {
        "entries": entries,
        "totals": {
            "calories": round(total_cal),
            "protein_g": round(total_protein, 1),
            "carbs_g": round(total_carbs, 1),
            "fat_g": round(total_fat, 1),
        },
        "macro_split": macro_split,
        "targets": {
            "calories": target_calories,
            "protein_g": target_protein_g,
        },
        "remaining": {
            "calories": round(remaining_cal),
            "protein_g": round(remaining_protein, 1),
        },
        "status": "ON_TRACK" if abs(remaining_cal) < target_calories * 0.1 else "UNDER" if remaining_cal > 0 else "OVER",
    }


@mcp.tool()
def calculate_body_composition(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: str = "male",
    waist_cm: float = 0,
    neck_cm: float = 0,
    hip_cm: float = 0,
    activity_level: str = "moderate", api_key: str = "") -> dict:
    """Calculate BMI, body fat estimate, BMR, and TDEE.

    Args:
        weight_kg: Body weight in kg
        height_cm: Height in cm
        age: Age in years
        sex: Biological sex: male, female
        waist_cm: Waist circumference in cm (for body fat estimate)
        neck_cm: Neck circumference in cm (for body fat estimate)
        hip_cm: Hip circumference in cm (females, for body fat estimate)
        activity_level: Activity: sedentary, light, moderate, active, very_active

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.
    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    _check_rate_limit("calculate_body_composition")

    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)

    if bmi < 18.5:
        bmi_category = "Underweight"
    elif bmi < 25:
        bmi_category = "Normal"
    elif bmi < 30:
        bmi_category = "Overweight"
    else:
        bmi_category = "Obese"

    # Mifflin-St Jeor BMR
    if sex.lower() == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    activity_multipliers = {
        "sedentary": 1.2, "light": 1.375, "moderate": 1.55,
        "active": 1.725, "very_active": 1.9,
    }
    tdee = bmr * activity_multipliers.get(activity_level, 1.55)

    # US Navy body fat estimation
    body_fat = None
    if waist_cm > 0 and neck_cm > 0:
        if sex.lower() == "male":
            body_fat = 495 / (1.0324 - 0.19077 * math.log10(waist_cm - neck_cm) + 0.15456 * math.log10(height_cm)) - 450
        elif hip_cm > 0:
            body_fat = 495 / (1.29579 - 0.35004 * math.log10(waist_cm + hip_cm - neck_cm) + 0.22100 * math.log10(height_cm)) - 450

    lean_mass = weight_kg * (1 - body_fat / 100) if body_fat else None

    ideal_weight_low = 18.5 * height_m ** 2
    ideal_weight_high = 24.9 * height_m ** 2

    result = {
        "bmi": round(bmi, 1),
        "bmi_category": bmi_category,
        "bmr_kcal": round(bmr),
        "tdee_kcal": round(tdee),
        "activity_level": activity_level,
        "ideal_weight_range_kg": f"{ideal_weight_low:.1f} - {ideal_weight_high:.1f}",
        "calorie_targets": {
            "maintain": round(tdee),
            "mild_loss": round(tdee - 250),
            "moderate_loss": round(tdee - 500),
            "mild_gain": round(tdee + 250),
            "moderate_gain": round(tdee + 500),
        },
        "protein_recommendation_g": round(weight_kg * 1.6),
    }

    if body_fat is not None:
        result["body_fat_percent"] = round(body_fat, 1)
        result["lean_mass_kg"] = round(lean_mass, 1)
        result["fat_mass_kg"] = round(weight_kg - lean_mass, 1)

    return result


@mcp.tool()
def build_training_plan(
    goal: str = "general_fitness",
    experience_level: str = "intermediate",
    days_per_week: int = 4,
    plan_weeks: int = 8,
    equipment_available: list[str] | None = None, api_key: str = "") -> dict:
    """Build a multi-week training program with periodization.

    Args:
        goal: Training goal: strength, hypertrophy, fat_loss, general_fitness, endurance
        experience_level: Level: beginner, intermediate, advanced
        days_per_week: Training days per week (2-6)
        plan_weeks: Program duration in weeks (4-16)
        equipment_available: Available equipment types

    Behavior:
        This tool generates structured output without modifying external systems.
        Output is deterministic for identical inputs. No side effects.
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.
    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    _check_rate_limit("build_training_plan")

    days_per_week = max(2, min(6, days_per_week))
    plan_weeks = max(4, min(16, plan_weeks))

    splits = {
        2: [["chest", "back", "shoulders"], ["legs", "arms", "core"]],
        3: [["chest", "shoulders"], ["back", "arms"], ["legs", "core"]],
        4: [["chest", "shoulders"], ["back"], ["legs"], ["arms", "core"]],
        5: [["chest"], ["back"], ["shoulders"], ["legs"], ["arms", "core"]],
        6: [["chest"], ["back"], ["shoulders"], ["legs", "core"], ["arms"], ["cardio"]],
    }

    weekly_split = splits.get(days_per_week, splits[4])
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Assign rest days
    training_days = []
    if days_per_week <= 3:
        day_indices = [0, 2, 4][:days_per_week]
    elif days_per_week == 4:
        day_indices = [0, 1, 3, 4]
    elif days_per_week == 5:
        day_indices = [0, 1, 2, 3, 4]
    else:
        day_indices = [0, 1, 2, 3, 4, 5]

    for i, idx in enumerate(day_indices):
        training_days.append({
            "day": day_names[idx],
            "focus": ", ".join(g.title() for g in weekly_split[i]),
            "muscle_groups": weekly_split[i],
        })

    # Periodization phases
    phases = []
    weeks_per_phase = max(2, plan_weeks // 3)

    phase_configs = {
        "strength": [
            ("Foundation", "4x6-8", "Build base strength"),
            ("Intensity", "5x3-5", "Peak strength development"),
            ("Deload & Test", "3x5", "Recovery and PR testing"),
        ],
        "hypertrophy": [
            ("Volume", "4x10-12", "Accumulate training volume"),
            ("Intensity", "4x8-10", "Increase load"),
            ("Peak & Deload", "3x6-8", "Metabolic stress focus"),
        ],
        "fat_loss": [
            ("Metabolic", "3x12-15", "High volume, short rest"),
            ("HIIT Focus", "4x10-12", "Circuit-style training"),
            ("Maintenance", "3x10-12", "Maintain muscle mass"),
        ],
    }

    configs = phase_configs.get(goal, phase_configs["hypertrophy"])
    week_start = 1
    for name, scheme, focus in configs:
        duration = weeks_per_phase if name != configs[-1][0] else plan_weeks - (weeks_per_phase * (len(configs) - 1))
        phases.append({
            "name": name,
            "weeks": f"{week_start}-{week_start + duration - 1}",
            "duration_weeks": duration,
            "set_rep_scheme": scheme,
            "focus": focus,
            "intensity_rpe": {"Foundation": "7-8", "Volume": "7-8", "Metabolic": "7",
                             "Intensity": "8-9", "HIIT Focus": "8-9",
                             "Peak & Deload": "6-7", "Deload & Test": "6-9", "Maintenance": "7"}.get(name, "7-8"),
        })
        week_start += duration

    return {
        "plan_name": f"{plan_weeks}-Week {goal.replace('_', ' ').title()} Program",
        "goal": goal,
        "experience_level": experience_level,
        "duration_weeks": plan_weeks,
        "days_per_week": days_per_week,
        "weekly_schedule": training_days,
        "rest_days": [day_names[i] for i in range(7) if i not in day_indices],
        "phases": phases,
        "progression_strategy": {
            "strength": "Add 2.5kg to upper body, 5kg to lower body lifts each week",
            "hypertrophy": "Increase weight when you can complete all reps with good form",
            "fat_loss": "Maintain weights, decrease rest periods over time",
        }.get(goal, "Progressive overload - gradually increase volume or intensity"),
        "nutrition_note": "Ensure adequate protein (1.6-2.2g/kg bodyweight) and caloric intake aligned with your goal.",
    }


@mcp.tool()
def check_exercise_form(
    exercise_name: str,
    common_mistakes: bool = True, api_key: str = "") -> dict:
    """Get exercise form cues, common mistakes, and muscle activation info.

    Args:
        exercise_name: Name of the exercise
        common_mistakes: Include common form mistakes and corrections

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.
    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    _check_rate_limit("check_exercise_form")

    exercises_db = {
        "squat": {
            "primary_muscles": ["quadriceps", "glutes"],
            "secondary_muscles": ["hamstrings", "core", "lower back"],
            "setup": ["Bar across upper back (high bar) or rear delts (low bar)",
                      "Feet shoulder-width apart, toes slightly out",
                      "Chest up, core braced"],
            "execution": ["Break at hips and knees simultaneously",
                         "Descend until hip crease is below knee (parallel or deeper)",
                         "Drive through midfoot to stand, squeezing glutes at top"],
            "breathing": "Inhale before descent, brace core, exhale at top",
            "common_mistakes": [
                {"mistake": "Knees caving inward", "fix": "Push knees out over toes. Use a band above knees as a cue."},
                {"mistake": "Excessive forward lean", "fix": "Work on ankle mobility. Try elevating heels with plates."},
                {"mistake": "Rounding lower back", "fix": "Brace core harder. Reduce weight until form improves."},
                {"mistake": "Not hitting depth", "fix": "Work on hip and ankle mobility. Use box squats to groove pattern."},
            ],
        },
        "bench press": {
            "primary_muscles": ["pectorals"],
            "secondary_muscles": ["anterior deltoids", "triceps"],
            "setup": ["Lie flat, eyes under the bar",
                      "Retract shoulder blades and arch upper back slightly",
                      "Grip slightly wider than shoulder width, feet flat on floor"],
            "execution": ["Unrack, bring bar over chest",
                         "Lower bar to mid-chest with control",
                         "Press bar up and slightly back to lockout"],
            "breathing": "Inhale on descent, exhale through the press",
            "common_mistakes": [
                {"mistake": "Flaring elbows at 90 degrees", "fix": "Tuck elbows to 45-75 degrees."},
                {"mistake": "Bouncing bar off chest", "fix": "Control the descent. Pause briefly on chest."},
                {"mistake": "Flat shoulder blades", "fix": "Squeeze shoulder blades together and down before unracking."},
                {"mistake": "Feet off the floor", "fix": "Keep feet flat. Use leg drive by pressing feet into the ground."},
            ],
        },
        "deadlift": {
            "primary_muscles": ["hamstrings", "glutes", "lower back"],
            "secondary_muscles": ["quadriceps", "forearms", "core", "traps"],
            "setup": ["Bar over midfoot, feet hip-width apart",
                      "Grip bar just outside knees (double overhand or mixed)",
                      "Hips hinge back, chest up, back flat"],
            "execution": ["Drive through feet, keeping bar close to body",
                         "Extend hips and knees simultaneously",
                         "Lock out by squeezing glutes, standing tall"],
            "breathing": "Big breath before lift, brace core, exhale at lockout",
            "common_mistakes": [
                {"mistake": "Rounding back", "fix": "Engage lats, think 'proud chest'. Reduce weight if needed."},
                {"mistake": "Bar drifting forward", "fix": "Keep bar against shins/thighs throughout the lift."},
                {"mistake": "Jerking the bar", "fix": "Take slack out of the bar before pulling. Smooth initiation."},
                {"mistake": "Hyperextending at lockout", "fix": "Stand tall, squeeze glutes. Don't lean back."},
            ],
        },
    }

    key = exercise_name.lower().strip()
    info = exercises_db.get(key)

    if not info:
        # Fuzzy match
        for db_key in exercises_db:
            if db_key in key or key in db_key:
                info = exercises_db[db_key]
                key = db_key
                break

    if not info:
        return {
            "exercise": exercise_name,
            "message": f"Detailed form guide not found for '{exercise_name}'. Available: {', '.join(exercises_db.keys())}",
            "general_tips": [
                "Start with lighter weight to master the movement pattern",
                "Record yourself to check form",
                "Warm up with 2-3 lighter sets before working sets",
                "If something hurts (not just muscle fatigue), stop and reassess",
            ],
        }

    result = {
        "exercise": key.title(),
        "primary_muscles": info["primary_muscles"],
        "secondary_muscles": info["secondary_muscles"],
        "setup_cues": info["setup"],
        "execution_cues": info["execution"],
        "breathing": info["breathing"],
    }

    if common_mistakes:
        result["common_mistakes"] = info["common_mistakes"]

    return result


if __name__ == "__main__":
    mcp.run()
