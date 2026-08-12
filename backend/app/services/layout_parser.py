import re
from html.parser import HTMLParser
from typing import List, Dict

class LayoutHTMLParser(HTMLParser):
    """
    Parser to group layout divs with data-label and data-bbox attributes 
    hierarchically under their preceding Section-Header element.
    """
    def __init__(self):
        super().__init__()
        self.sections: List[Dict] = []
        self.current_section: Dict = None
        self.current_div: Dict = None
        self.tag_stack: List[str] = []
        self.html_accumulator: List[str] = []
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        # Check if we are opening a root layout container block
        is_layout_div = tag == 'div' and ('data-label' in attrs_dict or 'data-bbox' in attrs_dict)
        
        if is_layout_div:
            # If we were already accumulating another block, flush it first
            if self.current_div:
                self.flush_current_div()
                
            self.current_div = {
                "type": attrs_dict.get('data-label', 'Text'),
                "bbox": attrs_dict.get('data-bbox', ''),
                "content": ""
            }
            self.html_accumulator = []
            
        self.tag_stack.append(tag)
        
        if self.current_div:
            # Reconstruct tag string for inner HTML recovery
            attr_str = "".join([f' {k}="{v}"' for k, v in attrs])
            self.html_accumulator.append(f"<{tag}{attr_str}>")

    def handle_endtag(self, tag):
        if self.current_div:
            self.html_accumulator.append(f"</{tag}>")
            
        if self.tag_stack:
            self.tag_stack.pop()
            
        # If we closed the root layout div, flush its contents
        if tag == 'div' and self.current_div and len([t for t in self.tag_stack if t == 'div']) == 0:
            self.flush_current_div()
            
    def handle_data(self, data):
        if self.current_div:
            self.html_accumulator.append(data)
            
    def flush_current_div(self):
        if not self.current_div:
            return
            
        # Reconstruct inner content html
        html_content = "".join(self.html_accumulator)
        
        # Strip the outer-most wrapping div tag from the collected HTML string
        div_start_match = re.match(r"^<div[^>]*>", html_content, re.IGNORECASE)
        div_end_match = re.search(r"</div>$", html_content, re.IGNORECASE)
        
        if div_start_match and div_end_match:
            html_content = html_content[div_start_match.end():div_end_match.start()].strip()
            
        self.current_div["content"] = html_content
        label = self.current_div["type"]
        bbox = self.current_div["bbox"]
        content = self.current_div["content"]
        
        # Differentiate sections vs children
        if label == 'Section-Header':
            # Strip formatting tags for the section title representation
            clean_title = re.sub(r"<[^>]*>", "", content).strip()
            # If the clean title is empty, use a fallback name
            if not clean_title:
                clean_title = "Untitled Section"
                
            self.current_section = {
                "section_title": clean_title,
                "bbox": bbox,
                "children": []
            }
            self.sections.append(self.current_section)
        else:
            # Fallback section if document starts directly with text/tables without a header
            if not self.current_section:
                self.current_section = {
                    "section_title": "Document Overview",
                    "bbox": "",
                    "children": []
                }
                self.sections.append(self.current_section)
                
            self.current_section["children"].append({
                "type": label,
                "bbox": bbox,
                "content": content
            })
            
        self.current_div = None
        self.html_accumulator = []

def parse_layout_sections(html_content: str) -> List[Dict]:
    """
    Parses a combined layout HTML string into structured section folders.
    """
    if not html_content:
        return []
    parser = LayoutHTMLParser()
    try:
        parser.feed(html_content)
        parser.flush_current_div()
    except Exception:
        # Fallback if HTML parsing fails due to malformed XML structures
        return [{
            "section_title": "Document Overview",
            "bbox": "",
            "children": [{
                "type": "Text",
                "bbox": "",
                "content": html_content
            }]
        }]
    return parser.sections
