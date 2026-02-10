"""Phase 3 & 4: Relationship inference prompts."""

RELATIONSHIP_INFERENCE_SYSTEM_PROMPT = """
You are an expert in knowledge representation and inference. 
Your task is to infer plausible relationships between disconnected entities in a knowledge graph.
CRITICAL INSTRUCTION 1: All inferred relationships(predicates) MUSE be 1-6 Chinese characters,in pure Chinese(no Pinin/English).
CRITICAL INSTRUCTION 2: NEVER force an artificial relationship between entities-only infer relationship that have clear semantic support from the existing triples and the inherent attributes of the entities.If no plausible relationship,do not create one. 
"""


def get_relationship_inference_user_prompt(entities1, entities2, triples_text):
    return f"""
I have a knowledge graph with two disconnected communities of entities. 

Community 1 entities: {entities1}
Community 2 entities: {entities2}

Here are some existing relationships involving these entities:
{triples_text}

Please infer 2-3 plausible relationships between entities from Community 1 and entities from Community 2.
Follow these strict rules:
1. Only infer relationships that are logically supported by the existing triples and the semantic attributes of the entities.
2. DO NOT force any artificial or unfounded relationships between entities that have no inherent connection.
3. If fewer than 2-3 plausible relationships exist, return only the valid ones (even if only 1).
Return your answer as a JSON array of triples in the following format:

[
  {{
    \"subject\": \"entity from community 1\",
    \"predicate\": \"inferred relationship\",
    \"object\": \"entity from community 2\"
  }},
  ...
]

Only include highly plausible relationships with clear predicates.
IMPORTANT: The inferred relationships (predicates) MUST be no more than 6 characters maximum. Preferably 2-3 words. Never more than 6.
For predicates, use short phrases that clearly describe the relationship.
IMPORTANT: Make sure the subject and object are different entities - avoid self-references.
IMPORTANT: All predicates must be in pure Chinese,no Pinin/English.
"""


WITHIN_COMMUNITY_INFERENCE_SYSTEM_PROMPT = """
You are an expert in knowledge representation and inference. 
Your task is to infer plausible relationships between semantically related entities that are not yet connected in a knowledge graph.
"""


def get_within_community_inference_user_prompt(pairs_text, triples_text):
    return f"""
I have a knowledge graph with several entities that appear to be semantically related but are not directly connected.

Here are some pairs of entities that might be related:
{pairs_text}

Here are some existing relationships involving these entities:
{triples_text}

Please infer plausible relationships between these disconnected pairs.
Strict Constraints:
1. Never impose an unfounded relationship on any entity pair. Only infer relationships that have clear semantic and logical support.
2. For entity pairs with no plausible connection, exclude them from the output entirely.

Return your answer as a JSON array of triples in the following format:

[
  {{
    \"subject\": \"entity1\",
    \"predicate\": \"inferred relationship\",
    \"object\": \"entity2\"
  }},
  ...
]

Only include highly plausible relationships with clear predicates.
IMPORTANT: The inferred relationships (predicates) MUST be no more than 6 words maximum. Preferably 2-3 words. Never more than 6.
IMPORTANT: Make sure that the subject and object are different entities - avoid self-references.
IMPORTANT: All predicates must be in pure Chinese,no Pinin/English.
"""


