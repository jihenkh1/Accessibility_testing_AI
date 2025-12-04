"""
Excel checklist parser with caching for manual testing checklists.
Reads .xlsx files and caches parsed results to avoid repeated file I/O.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

# In-memory cache: {file_path: (modification_time, parsed_data)}
_checklist_cache: Dict[str, tuple[float, Dict[str, Any]]] = {}


def parse_checklist_excel(file_path: Path) -> Dict[str, Any]:
    """
    Parse Excel checklist file and return structured data with caching.
    
    Args:
        file_path: Path to .xlsx checklist file
        
    Returns:
        Dictionary with checklist metadata and items
        
    Raises:
        FileNotFoundError: If Excel file doesn't exist
        ValueError: If Excel file has invalid structure
    """
    file_str = str(file_path)
    
    # Check if file exists
    if not file_path.exists():
        raise FileNotFoundError(f"Checklist file not found: {file_path}")
    
    # Get file modification time
    current_mtime = file_path.stat().st_mtime
    
    # Check cache
    if file_str in _checklist_cache:
        cached_mtime, cached_data = _checklist_cache[file_str]
        if cached_mtime == current_mtime:
            logger.debug(f"Using cached data for {file_path.name}")
            return cached_data
    
    # Parse Excel file
    logger.info(f"Parsing Excel checklist: {file_path.name}")
    
    try:
        # Read Excel file
        df = pd.read_excel(file_path, sheet_name="Checklist")
        
        # Validate required columns
        required_columns = [
            "wcag_criterion", "level", "item_title", "instructions",
            "expected_result", "common_failures", "tool", "priority", "reference_url"
        ]
        
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Convert DataFrame to list of dictionaries
        checklist_items = []
        for _, row in df.iterrows():
            item = {
                "wcag_criterion": str(row["wcag_criterion"]),
                "level": str(row["level"]),
                "item_title": str(row["item_title"]),
                "instructions": str(row["instructions"]),
                "expected_result": str(row["expected_result"]),
                "common_failures": str(row["common_failures"]),
                "tool": str(row["tool"]),
                "priority": str(row["priority"]),
                "reference_url": str(row["reference_url"])
            }
            checklist_items.append(item)
        
        # Extract metadata from filename and content
        tool_name = file_path.stem.split("-")[0].upper()  # Extract "NVDA" from "nvda-wcag21aa-checklist"
        
        # Build structured response
        result = {
            "name": f"{tool_name} WCAG 2.1 AA Checklist",
            "tool": tool_name,
            "description": f"Manual testing checklist for {tool_name} covering WCAG 2.1 Level A and AA criteria",
            "total_items": len(checklist_items),
            "checklist_items": checklist_items,
            "file_info": {
                "filename": file_path.name,
                "last_modified": datetime.fromtimestamp(current_mtime).isoformat(),
                "format": "Excel (.xlsx)"
            }
        }
        
        # Cache the result
        _checklist_cache[file_str] = (current_mtime, result)
        logger.info(f"Cached {len(checklist_items)} items from {file_path.name}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error parsing Excel file {file_path}: {e}")
        raise ValueError(f"Failed to parse Excel checklist: {e}")


def get_checklist_by_tool(tool: str, checklists_dir: Path) -> Dict[str, Any]:
    """
    Get checklist for a specific testing tool.
    
    Args:
        tool: Testing tool name (nvda, keyboard, zoom)
        checklists_dir: Directory containing checklist Excel files
        
    Returns:
        Parsed checklist data
        
    Raises:
        FileNotFoundError: If checklist for tool doesn't exist
        ValueError: If tool name is invalid or file is corrupted
    """
    # Normalize tool name
    tool_lower = tool.lower()
    valid_tools = ["nvda", "keyboard", "zoom"]
    
    if tool_lower not in valid_tools:
        raise ValueError(f"Invalid tool '{tool}'. Must be one of: {valid_tools}")
    
    # Build expected filename
    checklist_filename = f"{tool_lower}-wcag21aa-checklist.xlsx"
    checklist_path = checklists_dir / checklist_filename
    
    # Parse and return
    return parse_checklist_excel(checklist_path)


def clear_cache():
    """Clear the checklist cache. Useful for testing or forced refresh."""
    global _checklist_cache
    _checklist_cache.clear()
    logger.info("Checklist cache cleared")


def save_checklist_to_excel(tool: str, checklist_items: List[Dict[str, Any]], checklists_dir: Path) -> bool:
    """
    Save updated checklist items back to Excel file.
    
    Args:
        tool: Testing tool name (nvda, keyboard, zoom)
        checklist_items: List of checklist item dictionaries with all 9 columns
        checklists_dir: Directory containing checklist Excel files
        
    Returns:
        True if save successful
        
    Raises:
        ValueError: If tool name is invalid or data is malformed
        Exception: If file write fails
    """
    # Normalize tool name
    tool_lower = tool.lower()
    valid_tools = ["nvda", "keyboard", "zoom"]
    
    if tool_lower not in valid_tools:
        raise ValueError(f"Invalid tool '{tool}'. Must be one of: {valid_tools}")
    
    # Build filename
    checklist_filename = f"{tool_lower}-wcag21aa-checklist.xlsx"
    checklist_path = checklists_dir / checklist_filename
    
    # Validate required columns
    required_columns = [
        "wcag_criterion", "level", "item_title", "instructions",
        "expected_result", "common_failures", "tool", "priority", "reference_url"
    ]
    
    # Validate data
    if not checklist_items:
        raise ValueError("Checklist items cannot be empty")
    
    for item in checklist_items:
        missing = [col for col in required_columns if col not in item]
        if missing:
            raise ValueError(f"Missing required columns in item: {missing}")
    
    try:
        # Convert to DataFrame
        df = pd.DataFrame(checklist_items)
        
        # Ensure column order matches specification
        df = df[required_columns]
        
        # Write to Excel
        df.to_excel(checklist_path, index=False, sheet_name="Checklist")
        
        # Clear cache for this file so it gets re-read with new data
        file_str = str(checklist_path)
        if file_str in _checklist_cache:
            del _checklist_cache[file_str]
        
        logger.info(f"Saved {len(checklist_items)} items to {checklist_filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving Excel file {checklist_path}: {e}")
        raise Exception(f"Failed to save checklist: {e}")


def get_cache_stats() -> Dict[str, Any]:
    """Get statistics about the current cache state."""
    return {
        "cached_files": len(_checklist_cache),
        "files": [Path(path).name for path in _checklist_cache.keys()]
    }


# Example usage
if __name__ == "__main__":
    # Test the parser
    checklists_dir = Path(__file__).parent.parent.parent / "static" / "checklists"
    
    print("Testing Excel Checklist Parser")
    print("=" * 60)
    
    for tool in ["nvda", "keyboard", "zoom"]:
        try:
            checklist = get_checklist_by_tool(tool, checklists_dir)
            print(f"\n✓ {checklist['name']}")
            print(f"  Items: {checklist['total_items']}")
            print(f"  File: {checklist['file_info']['filename']}")
            print(f"  Last modified: {checklist['file_info']['last_modified']}")
        except Exception as e:
            print(f"\n✗ Failed to load {tool}: {e}")
    
    print("\n" + "=" * 60)
    print(f"Cache stats: {get_cache_stats()}")
