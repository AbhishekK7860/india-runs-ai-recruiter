import os
import sys
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field

# Ensure project root is in pythonpath
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.llm.client import LLMClient

class JobType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"

class SimpleObject(BaseModel):
    name: str
    age: int
    is_active: bool
    score: float

class NestedObject(BaseModel):
    id: str
    details: SimpleObject
    tags: list[str]

class ComprehensiveSchema(BaseModel):
    job_type: JobType
    title: str
    salary: Optional[float] = None
    requirements: list[str] = Field(default_factory=list)
    empty_list: list[str]
    metadata: Optional[dict[str, str]] = None
    
def test_providers():
    client = LLMClient()
    
    print("\n--- Test 1: Plain Text ---")
    text_res = client.generate_text("You are a helpful assistant.", "Say 'hello world'.")
    print(f"Result: {text_res}")
    
    print("\n--- Test 2: Simple Object ---")
    sys_prompt = "You are a helpful assistant. Provide data about a user named Alice."
    user_prompt = "Alice is 30, active, and has a score of 95.5."
    res2 = client.generate_structured(sys_prompt, user_prompt, SimpleObject)
    print(f"Result: {res2}")
    
    print("\n--- Test 3: Nested Object & Arrays ---")
    sys_prompt = "Provide data about an entity."
    user_prompt = "ID is E123. It contains details for Bob who is 25, inactive, score 80.0. Tags: new, test."
    res3 = client.generate_structured(sys_prompt, user_prompt, NestedObject)
    print(f"Result: {res3}")
    
    print("\n--- Test 4: Comprehensive Schema (Enum, Optional, Float, Empty arrays) ---")
    sys_prompt = "Provide data about a job."
    user_prompt = "It is a part_time role for 'Data Entry'. Salary is unknown. There are no requirements and empty list should be empty. metadata is null."
    res4 = client.generate_structured(sys_prompt, user_prompt, ComprehensiveSchema)
    print(f"Result: {res4}")
    
    print("\nAll tests completed successfully.")

if __name__ == "__main__":
    test_providers()
