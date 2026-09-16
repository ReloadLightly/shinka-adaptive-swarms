"""Count-four recovery policy; memory reevaluation is fixed by the adapter."""

# EVOLVE-BLOCK-START
def choose_recovery(observation: dict) -> dict:
    compactness = observation["swarm_diameter"] / max(
        observation["default_radius"], 1e-12
    )
    radius_scale = 1.25 if compactness < 2.0 else 1.2
    return {"radius_scale": radius_scale, "reset_velocity": False}
# EVOLVE-BLOCK-END
