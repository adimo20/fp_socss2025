from pydantic import BaseModel

"""Definieren eines Output Schemes an das sich das Model halten soll."""

class ExtractedContent(BaseModel):
    page_id:str
    content:list[str]
