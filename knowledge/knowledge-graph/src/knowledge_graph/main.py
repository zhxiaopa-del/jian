import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.knowledge_graph.config import load_config
from src.knowledge_graph.llm import call_llm, extract_json_from_text
from src.knowledge_graph.visualization import visualize_knowledge_graph, sample_data_visualization
from src.knowledge_graph.entity_standardization import standardize_entities, infer_relationships, limit_predicate_length
from src.knowledge_graph.prompts import prompt_factory

def load_qa_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("QA 文件必须是 JSON 数组")
        valid = []
        for i, item in enumerate(data):
            if "question" in item and "answer" in item:
                valid.append({
                    "question": item["question"].strip(),
                    "answer": item["answer"].strip()
                })
            else:
                print(f"跳过无效 QA 条目 index={i}")
        return valid
    except Exception as e:
        raise Exception(f"读取 QA 文件失败: {str(e)}")

def process_with_llm(config, input_text, debug=False):
    """
    Process input text with LLM to extract triples.

    Args:
        config: Configuration dictionary
        input_text: Text to analyze
        debug: If True, print detailed debug information

    Returns:
        List of extracted triples or None if processing failed
    """
    # Use prompts from the centralized prompt factory
    system_prompt = prompt_factory.get_prompt("main_system")
    user_prompt = prompt_factory.get_prompt("main_user")
    user_prompt += f"```\n{input_text}```\n"

    # LLM configuration
    model = config["llm"]["model"]
    api_key = config["llm"]["api_key"]
    max_tokens = config["llm"]["max_tokens"]
    temperature = config["llm"]["temperature"]
    base_url = config["llm"]["base_url"]

    # Process with LLM
    metadata = {}
    response = call_llm(model, user_prompt, api_key, system_prompt, max_tokens, temperature, base_url)

    # Print raw response only if debug mode is on
    if debug:
        print("Raw LLM response:")
        print(response)
        print("\n---\n")

    # Extract JSON from the response
    result = extract_json_from_text(response)

    if result:
        # Validate and filter triples to ensure they have all required fields
        valid_triples = []
        invalid_count = 0

        for item in result:
            if isinstance(item, dict) and "subject" in item and "predicate" in item and "object" in item:
                # Add metadata to valid items
                valid_triples.append(dict(item, **metadata))
            else:
                invalid_count += 1

        if invalid_count > 0:
            print(f"Warning: Filtered out {invalid_count} invalid triples missing required fields")

        if not valid_triples:
            print("Error: No valid triples found in LLM response")
            return None

        # Apply predicate length limit to all valid triples
        for triple in valid_triples:
            triple["predicate"] = limit_predicate_length(triple["predicate"])

        # Print extracted JSON only if debug mode is on
        if debug:
            print("Extracted JSON:")
            print(json.dumps(valid_triples, indent=2))  # Pretty print the JSON

        return valid_triples
    else:
        # Always print error messages even if debug is off
        print("\n\nERROR ### Could not extract valid JSON from response: ", response, "\n\n")
        return None

def qa_to_text(qa:dict)->str:
    return f"""
    问题：{qa["question"]}
    答案：{qa["answer"]}
    """

def process_QA_json(config, valid, debug=False):
    print("=" * 50)
    print("PHASE 1: INITIAL TRIPLE EXTRACTION")
    print("=" * 50)
    all_results = []
    for i, qa in enumerate(valid):
        print(f"Processing QA {i+1}/{len(valid)}")
        qa_text=qa_to_text(qa)
        qa_results = process_with_llm(config, qa_text, debug)
        if qa_results:
            all_results.extend(qa_results)
        else:
            print(f"Warning: Failed to extract triples from QA {i+1}")

    print(f"\nExtracted a total of {len(all_results)} triples from all QAs")
    print(all_results)

    # Apply entity standardization if enabled
    if config.get("standardization", {}).get("enabled", False):
        print("\n" + "="*50)
        print("PHASE 2: ENTITY STANDARDIZATION")
        print("="*50)
        print(f"Starting with {len(all_results)} triples and {len(get_unique_entities(all_results))} unique entities")

        all_results = standardize_entities(all_results, config)

        print(f"After standardization: {len(all_results)} triples and {len(get_unique_entities(all_results))} unique entities")

    # Apply relationship inference if enabled
    if config.get("inference", {}).get("enabled", False):
        print("\n" + "="*50)
        print("PHASE 3: RELATIONSHIP INFERENCE")
        print("="*50)
        print(f"Starting with {len(all_results)} triples")

        # Count existing relationships
        relationship_counts = {}
        for triple in all_results:
            relationship_counts[triple["predicate"]] = relationship_counts.get(triple["predicate"], 0) + 1

        print("Top 5 relationship types before inference:")
        for pred, count in sorted(relationship_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  - {pred}: {count} occurrences")

        all_results = infer_relationships(all_results, config)

        # Count relationships after inference
        relationship_counts_after = {}
        for triple in all_results:
            relationship_counts_after[triple["predicate"]] = relationship_counts_after.get(triple["predicate"], 0) + 1

        print("\nTop 5 relationship types after inference:")
        for pred, count in sorted(relationship_counts_after.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  - {pred}: {count} occurrences")

        # Count inferred relationships
        inferred_count = sum(1 for triple in all_results if triple.get("inferred", False))
        print(f"\nAdded {inferred_count} inferred relationships")
        print(f"Final knowledge graph: {len(all_results)} triples")

    return all_results

def get_unique_entities(triples):
    entities = set()
    for triple in triples:
        if not isinstance(triple, dict):
            continue
        if "subject" in triple:
            entities.add(triple["subject"])
        if "object" in triple:
            entities.add(triple["object"])
    return entities

def main():
    """Main entry point for the knowledge graph generator."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Knowledge Graph Generator and Visualizer')
    parser.add_argument('--test', action='store_true', help='Generate a test visualization with sample data')
    parser.add_argument('--config', type=str, default='config.toml', help='Path to configuration file')
    parser.add_argument('--output', type=str, default='knowledge_graph.html', help='Output HTML file path')
    parser.add_argument('--input', type=str, required=False, help='Path to input text file (required unless --test is used)')
    parser.add_argument('--debug', action='store_true', help='Enable debug output (raw LLM responses and extracted JSON)')
    parser.add_argument('--no-standardize', action='store_true', help='Disable entity standardization')
    parser.add_argument('--no-inference', action='store_true', help='Disable relationship inference')

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)
    if not config:
        print(f"Failed to load configuration from {args.config}. Exiting.")
        return

    # If test flag is provided, generate a sample visualization
    if args.test:
        print("Generating sample data visualization...")
        sample_data_visualization(args.output, config=config)
        print(f"\nSample visualization saved to {args.output}")
        print(f"To view the visualization, open the following file in your browser:")
        print(f"file://{os.path.abspath(args.output)}")
        return

    # For normal processing, input file is required
    if not args.input:
        print("Error: --input is required unless --test is used")
        parser.print_help()
        return

    # Override configuration settings with command line arguments
    if args.no_standardize:
        config.setdefault("standardization", {})["enabled"] = False
    if args.no_inference:
        config.setdefault("inference", {})["enabled"] = False

    try:
        input_text = load_qa_file(args.input)
        print(f"Using input text from file: {args.input}")
    except Exception as e:
        print(f"Error reading input file {args.input}: {e}")
        return

    result = process_QA_json(config, input_text, args.debug)

    print(result)

    if result:
        json_output = args.output.replace('.html', '.json')
        try:
            with open(json_output, 'w', encoding='utf-8-sig') as f:
                json.dump(result, f, indent=2)
            print(f"Saved raw knowledge graph data to {json_output}")
        except Exception as e:
            print(f"Warning: Could not save raw data to {json_output}: {e}")

    else:
        print("Knowledge graph generation failed due to errors in LLM processing.")

if __name__ == "__main__":
    main()