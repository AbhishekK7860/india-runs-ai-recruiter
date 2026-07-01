import json
from typing import Any, Type
from pydantic import BaseModel

def _generate_field_descriptions(schema: dict[str, Any], defs: dict[str, Any], prefix: str = "") -> list[str]:
    lines = []
    if "properties" not in schema:
        return lines
    
    required_fields = set(schema.get("required", []))
    
    for field_name, field_info in schema["properties"].items():
        # Handle $ref
        if "$ref" in field_info:
            ref_name = field_info["$ref"].split("/")[-1]
            ref_schema = defs.get(ref_name, {})
            # merge
            field_info = {**ref_schema, **field_info}
            
        field_type = field_info.get("type", "any")
        
        # Handle arrays
        if field_type == "array" and "items" in field_info:
            item_info = field_info["items"]
            if "$ref" in item_info:
                ref_name = item_info["$ref"].split("/")[-1]
                item_info = {**defs.get(ref_name, {}), **item_info}
            item_type = item_info.get("type", "object")
            field_type = f"array of {item_type}s"
            
        is_required = "required" if field_name in required_fields else "optional"
        desc = field_info.get("description", "").strip()
        desc_str = f" - {desc}" if desc else ""
        
        lines.append(f"{prefix}{field_name} : {field_type} ({is_required}){desc_str}")
        
        # Recursively handle nested objects
        if field_type == "object" or "properties" in field_info:
            lines.extend(_generate_field_descriptions(field_info, defs, prefix + "  "))
        elif field_type.startswith("array of object"):
             if "items" in field_info and ("properties" in field_info["items"] or "$ref" in field_info["items"]):
                 item_info = field_info["items"]
                 if "$ref" in item_info:
                     ref_name = item_info["$ref"].split("/")[-1]
                     item_info = defs.get(ref_name, {})
                 lines.extend(_generate_field_descriptions(item_info, defs, prefix + "  "))
                 
    return lines

def _generate_example(schema: dict[str, Any], defs: dict[str, Any]) -> Any:
    if "properties" in schema:
        obj = {}
        for k, v in schema["properties"].items():
            if "$ref" in v:
                ref_name = v["$ref"].split("/")[-1]
                v = {**defs.get(ref_name, {}), **v}
            obj[k] = _generate_example(v, defs)
        return obj
    
    t = schema.get("type", "string")
    if t == "string":
        return "example_string"
    elif t == "integer":
        return 0
    elif t == "number":
        return 0.0
    elif t == "boolean":
        return True
    elif t == "array":
        items = schema.get("items", {})
        if "$ref" in items:
            ref_name = items["$ref"].split("/")[-1]
            items = {**defs.get(ref_name, {}), **items}
        return [_generate_example(items, defs)]
    return None

def simplify_schema(model: Type[BaseModel]) -> tuple[str, str, set[str]]:
    """
    Returns:
        (field_descriptions_string, json_example_string, expected_root_keys)
    """
    schema = model.model_json_schema()
    defs = schema.get("$defs", {})
    
    lines = _generate_field_descriptions(schema, defs)
    fields_str = "\n".join(lines)
    
    example_obj = _generate_example(schema, defs)
    example_str = json.dumps(example_obj, indent=2)
    
    expected_root = set(schema.get("properties", {}).keys())
    
    return fields_str, example_str, expected_root

def parse_and_recover(response_text: str, expected_root: set[str], schema_cls: Type[BaseModel]) -> BaseModel:
    """Strips markdown, parses JSON, and detects if a schema was returned."""
    from backend.llm.providers.base import StructuredOutputError, StructuredOutputSchemaError
    
    clean_text = response_text.strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    elif clean_text.startswith("```"):
        clean_text = clean_text[3:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
    clean_text = clean_text.strip()
    
    try:
        data = json.loads(clean_text)
    except Exception as e:
        raise StructuredOutputError(f"Failed to parse JSON: {e}")
        
    if isinstance(data, dict):
        keys = set(data.keys())
        schema_keywords = {"properties", "required", "definitions", "$schema", "type", "title", "description"}
        
        has_schema_keys = bool(keys.intersection(schema_keywords))
        has_business_keys = bool(keys.intersection(expected_root))
        
        if has_schema_keys and not has_business_keys:
            raise StructuredOutputSchemaError("Model returned a JSON Schema instead of data object.")
            
    try:
        return schema_cls.model_validate(data)
    except Exception as e:
        raise StructuredOutputError(f"Failed to validate Pydantic schema: {e}")
