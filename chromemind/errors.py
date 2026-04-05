class SkillError(Exception):
    """Raised by skill functions."""
    pass

class GuardrailViolation(Exception):
    """Raised by guardrail checks."""
    def __init__(self, rule_id: str, message: str):
        self.rule_id = rule_id
        super().__init__(f"[GUARDRAIL {rule_id}] {message}")

class ChromeNotFoundError(Exception):
    """Raised when Chrome or a necessary Chrome file is not found."""
    pass

class NotionWriteError(Exception):
    """Raised on Notion API failures."""
    pass
