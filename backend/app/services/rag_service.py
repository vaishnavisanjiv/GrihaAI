from __future__ import annotations

from typing import Any, Dict, List


KNOWLEDGE_BASE: List[Dict[str, Any]] = [
    {
        "title": "Residential room area guidance",
        "source": "Local design guidance",
        "keywords": ["room", "area", "living", "bedroom", "minimum"],
        "text": "Main living rooms are typically reviewed against a minimum habitable area benchmark, while bedrooms should provide adequate clear floor area for circulation and furniture placement.",
    },
    {
        "title": "Bathroom and circulation clearance",
        "source": "Local accessibility guidance",
        "keywords": ["bathroom", "toilet", "circulation", "clearance", "accessibility"],
        "text": "Bathrooms and sanitary spaces should maintain clear floor area around fixtures and ensure door swing and route movement do not obstruct a safe circulation path.",
    },
    {
        "title": "Exit width and emergency flow",
        "source": "Emergency access guidance",
        "keywords": ["exit", "door", "stair", "fire", "emergency"],
        "text": "Emergency routes and stair widths should remain unobstructed and dimensioned for safe evacuation, with clear door and stair widths meeting the reviewed minimum standards.",
    },
    {
        "title": "Ventilation and daylight",
        "source": "Habitable space guidance",
        "keywords": ["ventilation", "window", "daylight", "light", "air"],
        "text": "Habitable spaces generally benefit from operable openings and daylight access; incomplete opening data should trigger a review for ventilation adequacy.",
    },
]


def retrieve_knowledge(question: str) -> List[Dict[str, Any]]:
    normalized = (question or "").strip().lower()
    if not normalized:
        return []

    results: List[Dict[str, Any]] = []
    for item in KNOWLEDGE_BASE:
        score = sum(1 for keyword in item["keywords"] if keyword in normalized)
        if score:
            results.append({
                "title": item["title"],
                "source": item["source"],
                "text": item["text"],
                "score": score,
            })

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:3]
