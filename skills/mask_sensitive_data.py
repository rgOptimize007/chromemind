"""
Skill: mask_sensitive_data
Role: Generic utility to mask sensitive tokens inside a file using regex, generating a safe version.
Input: input file path, output file path, dictionary of redactions
"""
import re

def mask_file(input_path: str, output_path: str, mask_rules: dict[str, str]):
    """
    Reads the input file, applies regex substitutions based on mask_rules, 
    and writes to the output path, perfectly preserving all structural comments.
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    for pattern, replacement in mask_rules.items():
        # Match lines like: key: "value" or key: value
        regex = re.compile(rf'^(\s*{pattern}\s*:\s*)([^\r\n]+)$', re.MULTILINE)
        content = regex.sub(rf'\g<1>{replacement}', content)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    # If run generically to generate the chrome example config:
    mask_rules = {
        "profile": '"<YOUR_CHROME_PROFILE_HERE>"',
        "model": '"<YOUR_GEMINI_MODEL_HERE>"',
        "max_items_per_source": "500",
        "max_items_per_run": "1000",
        "batch_size": "5",
        "max_tokens": "4096"
    }
    mask_file("chromemind-config.yaml", "chromemind-config.example.yaml", mask_rules)
    print("Generated safe chromemind-config.example.yaml")
