from fastapi import FastAPI
from pydantic import BaseModel
import pyphen
import re
import html

app = FastAPI()

dic = pyphen.Pyphen(lang="nl_NL")
SOFT_HYPHEN = "\u00ad"

class TextRequest(BaseModel):
    text: str

class SlaRequest(BaseModel):
    sla: str

def xml_escape_attr(value: str) -> str:
    return (
        value
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

def should_skip_word(word: str) -> bool:
    if len(word) < 6:
        return True
    if SOFT_HYPHEN in word:
        return True
    if any(char.isdigit() for char in word):
        return True
    if word.isupper():
        return True
    if "@" in word:
        return True
    if word.startswith(("http", "www")):
        return True
    return False

def hyphenate_word(word: str) -> str:
    if should_skip_word(word):
        return word
    return dic.inserted(word, hyphen=SOFT_HYPHEN)

def hyphenate_text(text: str) -> str:
    return re.sub(
        r"\b[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'-]{5,}\b",
        lambda match: hyphenate_word(match.group(0)),
        text
    )

def hyphenate_ch_attribute(match):
    original = match.group(1)

    decoded = html.unescape(original)
    hyphenated = hyphenate_text(decoded)
    escaped = xml_escape_attr(hyphenated)

    return f'CH="{escaped}"'

@app.get("/")
def healthcheck():
    return {"status": "ok"}

@app.post("/hyphenate")
def hyphenate(request: TextRequest):
    return {
        "text": hyphenate_text(request.text)
    }

@app.post("/hyphenate-sla")
def hyphenate_sla(request: SlaRequest):
    new_sla = re.sub(
        r'CH="([^"]*)"',
        hyphenate_ch_attribute,
        request.sla
    )

    return {
        "sla": new_sla
    }
