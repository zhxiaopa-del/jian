"""Phase 2: Entity standardization prompts."""

ENTITY_RESOLUTION_SYSTEM_PROMPT = """
You are an expert in entity resolution and knowledge representation.
Your task is to standardize entity names from a knowledge graph to ensure consistency.

Core Rules for Standardization (MUST FOLLOW):
1. Include all key details
2. Only group entities into the same standard name if they refer to the exact same real-world entity (including all key details).
3. Do NOT over-standardize: If two entities differ in any key detail, they must have separate standardized names.
4. The standardized name must include all key details from the variants (use the most complete and clear wording as the standard).
5.The name of the entity can not be standardized as it relates to differences in position and number.
"""


def get_entity_resolution_user_prompt(entity_list):
    return f"""
Below is a list of entity names extracted from a knowledge graph. 
Some refer to the same real-world entities but with different wording.

Please：
1.identify groups of entities that refer to the definitely same concept.
2.for each group,provide a standardized name for each group.
3.Return your answer as a JSON object where the keys are the standardized names and the values are arrays of all variant names that should map to that standard name.
4.Only include entities that have multiple variants or need standardization.

Entity list:
{entity_list}

Format your response as valid JSON like this:
{{
  \"standardized name 1\": [\"variant 1\", \"variant 2\"],
  \"standardized name 2\": [\"variant 3\", \"variant 4\", \"variant 5\"]
}}
"""


