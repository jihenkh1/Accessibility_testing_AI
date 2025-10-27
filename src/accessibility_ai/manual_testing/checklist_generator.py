"""
Checklist generator for manual accessibility testing.
Combines page-type and component checklists into a complete testing plan.
"""

from typing import List, Dict, Any
from .templates import (
    get_page_type_checklist,
    get_component_checklist,
    get_all_page_types,
    get_all_components
)


def generate_checklist(page_type: str, components: List[str]) -> Dict[str, Any]:
    """
    Generate a complete manual testing checklist based on page type and components.
    
    Args:
        page_type: Type of page (landing, form, dashboard, ecommerce)
        components: List of component names present on the page
    
    Returns:
        Dictionary containing checklist metadata and items
    """
    # Start with page-type specific checklist
    checklist_items = get_page_type_checklist(page_type)
    
    # Add component-specific items
    for component in components:
        component_items = get_component_checklist(component)
        checklist_items.extend(component_items)
    
    # Build summary statistics
    categories = set(item["category"] for item in checklist_items)
    priority_counts = {
        "critical": len([item for item in checklist_items if item["priority"] == "critical"]),
        "high": len([item for item in checklist_items if item["priority"] == "high"]),
        "medium": len([item for item in checklist_items if item["priority"] == "medium"]),
        "low": len([item for item in checklist_items if item["priority"] == "low"])
    }
    
    # Estimate testing time (rough estimate: 2 min per item)
    estimated_minutes = len(checklist_items) * 2
    
    return {
        "page_type": page_type,
        "components": components,
        "total_items": len(checklist_items),
        "categories": sorted(list(categories)),
        "priority_counts": priority_counts,
        "estimated_minutes": estimated_minutes,
        "items": checklist_items
    }


def get_supported_page_types() -> List[str]:
    """Get list of all supported page types."""
    return get_all_page_types()


def get_supported_components() -> List[str]:
    """Get list of all supported component types."""
    return get_all_components()


def detect_components_from_report(issues: List[Dict[str, Any]]) -> List[str]:
    """
    Detect likely components present based on automated scan issues.
    This is a simple heuristic - looks for common patterns in rule IDs and selectors.
    
    Args:
        issues: List of issues from automated scan
    
    Returns:
        List of detected component names
    """
    detected = set()
    
    for issue in issues:
        rule_id = issue.get("rule_id", "").lower()
        selector = issue.get("selector", "").lower()
        
        # Modal detection
        if "dialog" in rule_id or "modal" in rule_id or "role=\"dialog\"" in selector:
            detected.add("modal")
        
        # Dropdown detection
        if "select" in selector or "dropdown" in rule_id or "combobox" in selector:
            detected.add("dropdown")
        
        # Tabs detection
        if "tab" in rule_id or "tablist" in selector or "role=\"tab\"" in selector:
            detected.add("tabs")
        
        # Carousel detection
        if "carousel" in rule_id or "slider" in rule_id or "slide" in selector:
            detected.add("carousel")
        
        # Accordion detection
        if "accordion" in rule_id or "aria-expanded" in selector:
            detected.add("accordion")
        
        # Date picker detection
        if "date" in rule_id or "datepicker" in selector or "calendar" in selector:
            detected.add("datepicker")
        
        # Menu detection
        if "menu" in rule_id or "navigation" in rule_id or "nav" in selector:
            detected.add("menu")
        
        # Search detection
        if "search" in rule_id or "search" in selector:
            detected.add("search")
        
        # Pagination detection
        if "pagination" in rule_id or "pager" in selector:
            detected.add("pagination")
        
        # Tooltip detection
        if "tooltip" in rule_id or "title" in rule_id:
            detected.add("tooltip")
    
    return sorted(list(detected))
