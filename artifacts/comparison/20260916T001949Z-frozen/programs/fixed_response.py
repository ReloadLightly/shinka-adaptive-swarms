"""Fixed control using the selected program's compact-swarm recovery floors.

Investigator-defined mechanism comparison, not an evolved candidate.
Chosen from source before independent outcomes; no parameter fitting.
"""

def choose_response(observation: dict) -> dict:
    return {"radius_scale": 2.0, "fraction": 0.60,
            "memory": "reevaluate", "reset_velocity": False}
