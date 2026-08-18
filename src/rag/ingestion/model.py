from dataclasses import dataclass

@dataclass
class Document:
    
    text: str
    source: str
    file_type: str