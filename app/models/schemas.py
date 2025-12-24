from pydantic import BaseModel
from typing import List, Optional

class Word(BaseModel):
    text: str
    start: float
    end: float

class Chord(BaseModel):
    label: str
    timestamp: float

class AlignedWord(BaseModel):
    word: str
    chord: str
    is_new_chord: bool
    start: float
    end: float

class TaskResponse(BaseModel):
    task_id: str
    status: str

class ResultResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[str] = None