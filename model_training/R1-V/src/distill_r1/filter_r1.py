import json
import re
from pathlib import Path



def extract_answer_from_query(query_results: str) -> str | None:
    """
    Extract answer from query results, specifically looking for:
    - Numbers within asterisks
    - Yes/No answers in various formats

    Args:
        query_results: String containing the query response

    Returns:
        Extracted answer string or None if no answer found
    """
    # First try to find answers in the standard format with labels
    # Split the text into segments (trying to get the last conclusion)
    if "<think>" not in query_results or "</think>" not in query_results:
        return None
    segments = query_results.split("\n")

    # First try to find final conclusion in the last few segments
    conclusion_patterns = [
        r"(?:so|therefore|thus|hence),?\s*(?:the answer is\s+)?\*\*\s*(no|yes|[0-9]+)\s*\*\*",
        r"(?:so|therefore|thus|hence),?\s*(?:the answer is\s+)?(no|yes|[0-9]+)\b",
        r"the answer is\s+\*\*\s*(no|yes|[0-9]+)\s*\*\*",
        r"(?:final|conclusive) answer(?:\s+is)?\s*\*\*\s*(no|yes|[0-9]+)\s*\*\*",
    ]

    # Try to find conclusion in last 3 segments
    for segment in reversed(segments[-3:]):
        for pattern in conclusion_patterns:
            match = re.search(pattern, segment, re.IGNORECASE)
            if match:
                return match.group(1).strip().lower()

    # If no conclusion found, try other patterns on the full text
    labeled_patterns = [
        r"\*\*The answer is:\s*\*\*\s*([0-9]+|yes|no)\b",
        r"\*\*Answer:\s*\*\*\s*([0-9]+|yes|no)\b",
        r"\*\*Answer\*\*:\s*([0-9]+|yes|no)\b",
        r"\*\*Answer:?\s*\*\*\s*There (?:is|are)\s+([0-9]+)",
        r"\*\*Final Count:\s*\*\*\s*([0-9]+)",
        r"\*\*Final Count:\s*\*\*\s*([0-9]+)\s+(?:items?|objects?|spheres?|cubes?|boxes?)",
        r"\*\*Total:\s*\*\*\s*([0-9]+)",
        r"The answer is:\s*([0-9]+|yes|no)\b",
        r"Answer:\s*([0-9]+|yes|no)\b",
        r"should be\s+([0-9]+)[.\s]",
    ]

    direct_patterns = [
        r"\*\*\s*([0-9]+)\s*\*\*",
        r"\*\*\s*([0-9]+)\s+(?:items?|objects?|cubes?|boxes?|spheres?)?\s*\*\*",
        r"\*\*\s*([0-9]+)\s+[^*]+\*\*",
    ]

    latex_patterns = [
        r"\$\\boxed{([0-9]+)}\$",
        r"\\boxed{([0-9]+)}",
    ]

    count_patterns = [
        r"There (?:is|are)\s+([0-9]+)\s+(?:items?|objects?|spheres?|cubes?|boxes?)",
    ]

    # Try all patterns in sequence on full text
    all_patterns = labeled_patterns + direct_patterns + latex_patterns + count_patterns

    for pattern in all_patterns:
        match = re.search(pattern, query_results, re.IGNORECASE)
        if match:
            return match.group(1).strip().lower()

    return None


def validate_qa_pairs(input_file: str, output_dir: str, verbose: bool = True):
    """
    Process QA pairs and save them to separate files.
    Only saves pairs where parsed answer matches ground truth.

    Args:
        input_file: Path to input JSONL file
        output_dir: Directory to save output files
        verbose: If True, print examples of mismatched or unparseable responses
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    valid_pairs = []
    invalid_pairs = []
    stats = {"total": 0, "unparseable": 0, "mismatch": 0, "valid": 0}

    with open(input_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            stats["total"] += 1
            qa_pair = json.loads(line.strip())
            ground_truth = str(qa_pair.get("a", "")).lower().strip()
            parsed_answer = extract_answer_from_query(qa_pair["r1_response"])

            if parsed_answer is None:
                stats["unparseable"] += 1
                qa_pair["error"] = "unparseable"
                invalid_pairs.append(qa_pair)
                if verbose:
                    print(f"\nLine {line_num}: Could not parse answer")
                    print(f"Ground truth: {ground_truth}")
                    print(f"Query results: {qa_pair['r1_response'][-200:]}...")
            elif parsed_answer != ground_truth:
                stats["mismatch"] += 1
                qa_pair["error"] = "mismatch"
                qa_pair["parsed_answer"] = parsed_answer
                invalid_pairs.append(qa_pair)
                if verbose:
                    print(f"\nLine {line_num}: Answer mismatch")
                    print(f"Ground truth: {ground_truth}")
                    print(f"Parsed answer: {parsed_answer}")
                    print(f"Query results: {qa_pair['r1_response'][-200:]}...")
            else:
                stats["valid"] += 1
                valid_pairs.append(qa_pair)

    # Save valid pairs (where parsed answer matches ground truth)
    valid_file = output_dir / "valid_pairs.jsonl"
    with open(valid_file, "w", encoding="utf-8") as f:
        for pair in valid_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    # Save invalid pairs (unparseable or mismatched)
    invalid_file = output_dir / "invalid_pairs.jsonl"
    with open(invalid_file, "w", encoding="utf-8") as f:
        for pair in invalid_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    # Print statistics
    print(f"\nProcessing Summary:")
    print(f"Total pairs processed: {stats['total']}")
    print(f"Valid pairs (matching ground truth): {stats['valid']}")
    print(f"Invalid pairs: {stats['unparseable'] + stats['mismatch']}")
    print(f"  - Unparseable: {stats['unparseable']}")
    print(f"  - Answer mismatch: {stats['mismatch']}")
    print(f"\nOutput files:")
    print(f"Valid pairs saved to: {valid_file}")
    print(f"Invalid pairs saved to: {invalid_file}")


if __name__ == "__main__":
    validate_qa_pairs(
        "r1_results_clevr_cogent_v1.0_trainA_v2.jsonl", "filter_results_v2"
    )  # "filtered_output_tmp_v1.jsonl")
