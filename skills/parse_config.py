import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from chromemind.schemas import RunConfig
from chromemind.errors import SkillError
import re

def parse_config(filepath: str | Path = "chromemind-config.yaml") -> RunConfig:
    """Loads YAML, resolves env vars, and validates to RunConfig."""
    load_dotenv()
    
    path = Path(filepath)
    if not path.exists():
        raise SkillError(f"Config file not found at {path}")
        
    content = path.read_text("utf-8")
    
    # Resolve env vars pattern ${ENV_VAR}
    def replace_env(match):
        var = match.group(1)
        val = os.environ.get(var)
        if val is None:
            raise SkillError(f"Environment variable '{var}' not found.")
        return val
        
    content = re.sub(r"\$\{([A-Za-z0-9_]+)\}", replace_env, content)
    
    try:
        data = yaml.safe_load(content)
        return RunConfig(**data)
    except Exception as e:
        raise SkillError(f"Failed to parse or validate config: {e}")
