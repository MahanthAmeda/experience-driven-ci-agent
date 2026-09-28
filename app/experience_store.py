import json
import os
from typing import Dict, List, Optional
from app.models import Experience, OutcomeUpdateRequest

class ExperienceStore:
    def __init__(self, storage_path: str = "data/experiences.json"):
        self.storage_path = storage_path
        self._experiences: Dict[str, Experience] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    for item in raw:
                        exp = Experience(**item)
                        self._experiences[exp.experience_id] = exp
            except Exception as e:
                print(f"Warning: Failed to load experiences from {self.storage_path}: {e}")

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump([exp.model_dump() for exp in self._experiences.values()], f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save experiences to {self.storage_path}: {e}")

    def add(self, exp: Experience) -> Experience:
        self._experiences[exp.experience_id] = exp
        self._save()
        return exp

    def get(self, experience_id: str) -> Optional[Experience]:
        return self._experiences.get(experience_id)

    def list_all(self) -> List[Experience]:
        return list(self._experiences.values())

    def update_outcome(self, experience_id: str, outcome: OutcomeUpdateRequest) -> Optional[Experience]:
        exp = self._experiences.get(experience_id)
        if not exp:
            return None
        updated_dict = exp.model_dump()
        updated_dict["action_taken"] = outcome.action_taken
        updated_dict["action_result"] = outcome.action_result.lower()
        updated_dict["resolution"] = outcome.resolution
        updated_dict["lesson_learned"] = outcome.lesson_learned

        updated_exp = Experience(**updated_dict)
        self._experiences[experience_id] = updated_exp
        self._save()
        return updated_exp
