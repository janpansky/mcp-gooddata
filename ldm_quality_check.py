from gooddata_sdk import CatalogDeclarativeAttribute, CatalogDeclarativeFact
from dataclasses import dataclass
import re
from difflib import SequenceMatcher

@dataclass
class ObfuscatedTitle:
    is_obfuscated: bool
    reason: str = ""


@dataclass
class SemanticallySimilar:
    semantically_similar_pairs: list[tuple[str, str]]

def has_no_description(item: CatalogDeclarativeAttribute | CatalogDeclarativeFact) -> bool:
    match item:
        case CatalogDeclarativeAttribute():
            return item.description is None or item.description == item.title
        case CatalogDeclarativeFact():
            return item.description is None or item.description == item.title
        case _:
            return False

def check_semantic_similarity(text1: str, text2: str, threshold: float = 0.8) -> bool:
    """
    Check if two texts are semantically similar using sequence matching.
    
    Args:
        text1: First text to compare
        text2: Second text to compare
        threshold: Similarity threshold (0.0 to 1.0)
        
    Returns:
        bool: True if texts are similar above threshold, False otherwise
    """
    if not text1 or not text2:
        return False
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio() > threshold

def obfuscated_title_check(item: CatalogDeclarativeAttribute | CatalogDeclarativeFact) -> ObfuscatedTitle:
    """
    Check if the title of an attribute or fact appears to be obfuscated.
    
    Args:
        item: A CatalogDeclarativeAttribute or CatalogDeclarativeFact object
        
    Returns:
        bool: True if the title appears to be obfuscated, False otherwise
    """
    if not hasattr(item, 'title') or not item.title:
        return ObfuscatedTitle(is_obfuscated=False)
        
    title = item.title
    
    # Check if title is too short (less than 3 characters)
    if len(title) < 3:
        return ObfuscatedTitle(is_obfuscated=True, reason=f"Title is too short ({len(title)} characters)")
        
    # Check if title is all uppercase (common in technical names)
    if title.isupper():
        return ObfuscatedTitle(is_obfuscated=True, reason=f"Title is all uppercase")
        
    # Check if title contains only numbers and special characters
    if not any(c.isalpha() for c in title):
        return ObfuscatedTitle(is_obfuscated=True, reason=f"Title contains only numbers and special characters")
        
    # Check if title is too long without spaces (more than 30 characters)
    if len(title) > 30 and not re.search(r'[\s_-]', title):
        return ObfuscatedTitle(is_obfuscated=True, reason=f"Title is too long without spaces")
        
    return ObfuscatedTitle(is_obfuscated=False)

def semantic_similarity_check(items: list[CatalogDeclarativeAttribute] | list[CatalogDeclarativeFact]) -> SemanticallySimilar:
    """
    Check if the titles of attributes or facts are semantically similar.
    
    Args:
        items: A list of CatalogDeclarativeAttribute or CatalogDeclarativeFact objects
        
    Returns:
        bool: True if titles are similar, False otherwise
    """        
    similar = []
    for i, item1 in enumerate(items):            
        for item2 in items[i + 1:]:
            if check_semantic_similarity(item1.title, item2.title):
                similar.append((item1.title, item2.title))
    return SemanticallySimilar(similar)

    