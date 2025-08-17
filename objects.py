from enum import Enum

class LLM(Enum):
    DEFAULT = 'gpt-4o'
    CHEAP = 'gpt-4o-mini'

class MeetingTypes(Enum):
    LAW_COMMITTEE = 'law_committee'
    PLENARY = 'plenary_session'

class Page:
    def __init__(self, page_number, content):
        self.page_number = page_number
        self.content = content
        self.translated = None

