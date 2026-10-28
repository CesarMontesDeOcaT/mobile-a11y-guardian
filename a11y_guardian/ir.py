from typing import List, Optional
from pydantic import BaseModel, Field

class UINode(BaseModel):
    id: str
    component_type: str
    line_number: int
    is_interactive: bool = False
    content_description: Optional[str] = None
    text_content: Optional[str] = None
    role: Optional[str] = None
    merged_descendants: bool = False
    children: List["UINode"] = Field(default_factory=list)

class ScreenSemanticTree(BaseModel):
    file_path: str
    composable_name: str
    root_nodes: List[UINode]
