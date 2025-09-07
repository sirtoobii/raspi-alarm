from dataclasses import dataclass
from typing import ClassVar

from numpy import ndarray
from ultralytics import YOLO
from ultralytics.engine.model import Model
from ultralytics.engine.results import Results


@dataclass
class PersonDetectionResult:
    confidence_scores: list[float]
    annotated_frame: ndarray
    _raw_result: Results

    @property
    def max_confidence_score(self) -> float:
        return max(self.confidence_scores)


class Yolo11Engine:
    model: ClassVar[Model] = YOLO("yolo11n.pt")

    @classmethod
    def detect_person(cls, frame: ndarray) -> PersonDetectionResult:
        results = cls.model.predict(source=frame, classes=[0], verbose=False)
        _r = results[0]
        return PersonDetectionResult(
            confidence_scores=[b.conf[0] for b in _r.boxes],
            annotated_frame=_r.plot(),
            _raw_result=_r
        )
