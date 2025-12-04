"""
Script to generate Excel-based WCAG 2.1 AA checklists for manual testing.
Run this once to create the Excel files that testers can edit.
"""
import pandas as pd
from pathlib import Path

# Create checklists directory
checklists_dir = Path("static/checklists")
checklists_dir.mkdir(parents=True, exist_ok=True)

# NVDA Screen Reader Checklist
nvda_data = [
    {
        "wcag_criterion": "1.1.1",
        "level": "A",
        "item_title": "Images have meaningful alt text",
        "instructions": "Navigate to images using G key. NVDA should announce descriptive alt text for informative images, or mark decorative images as such.",
        "expected_result": "Informative images: Alt text describes content/function. Decorative images: Announced as 'graphic' with no description or skipped entirely.",
        "common_failures": "Missing alt text, generic alt text like 'image.jpg', decorative images with alt text, complex images without detailed description",
        "tool": "NVDA",
        "priority": "Critical",
        "reference_url": "https://www.w3.org/WAI/WCAG21/Understanding/non-text-content.html"
    },
    {
        "wcag_criterion": "1.3.1",
        "level": "A",
        "item_title": "Headings are properly structured",
        "instructions": "Use H key to navigate through headings. Verify heading levels (H1, H2, H3) follow logical hierarchy without skipping levels.",
        "expected_result": "NVDA announces heading level (e.g., 'Heading level 2'). Heading structure reflects page organization.",
        "common_failures": "Skipping heading levels, using headings for styling, multiple H1s, non-semantic heading markup",
        "tool": "NVDA",
        "priority": "High",
        "reference_url": "https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html"
    },
    {
        "wcag_criterion": "1.3.1",
        "level": "A",
        "item_title": "Form labels are associated with inputs",
        "instructions": "Navigate to form fields using F key. NVDA should announce label, field type, and current value for each form control.",
        "expected_result": "Each input announces its label clearly (e.g., 'Email, edit, blank').",
        "common_failures": "Missing labels, placeholder as label, label not programmatically associated, aria-label conflicts",
        "tool": "NVDA",
        "priority": "Critical",
        "reference_url": "https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html"
    },
    {
        "wcag_criterion": "2.1.1",
        "level": "A",
        "item_title": "All functionality available via keyboard",
        "instructions": "Using NVDA, navigate through all interactive elements (links, buttons, form fields) using Tab/Shift+Tab. Activate with Enter/Space.",
        "expected_result": "All interactive elements are reachable and operable. NVDA announces element type and label clearly.",
        "common_failures": "Click handlers on divs without keyboard support, missing tabindex, JavaScript-only interactions",
        "tool": "NVDA",
        "priority": "Critical",
        "reference_url": "https://www.w3.org/WAI/WCAG21/Understanding/keyboard.html"
    },
    {
        "wcag_criterion": "2.4.1",
        "level": "A",
        "item_title": "Skip navigation links work",
        "instructions": "When page loads, check if first interactive element is a 'Skip to main content' or similar link. Activate it and verify focus moves to main content.",
        "expected_result": "NVDA announces skip link. Activating it moves focus past navigation.",
        "common_failures": "Skip link missing, skip link not visible on focus, skip link doesn't move focus correctly",
        "tool": "NVDA",
        "priority": "High",
        "reference_url": "https://www.w3.org/WAI/WCAG21/Understanding/bypass-blocks.html"
    },
    {
        "wcag_criterion": "2.4.3",
        "level": "A",
        "item_title": "Focus order is logical",
        "instructions": "Tab through the page. Verify focus order matches visual/logical reading order.",
        "expected_result": "NVDA announces elements in an order that makes sense.",
        "common_failures": "CSS positioning breaks tab order, modals don't trap focus, focus jumps unpredictably",
        "tool": "NVDA",
        "priority": "High",
        "reference_url": "https://www.w3.org/WAI/WCAG21/Understanding/focus-order.html"
    },
    {
        "wcag_criterion": "2.4.4",
        "level": "A",
        "item_title": "Link text is descriptive",
        "instructions": "Use K key to navigate links. Each link should clearly describe its destination or purpose.",
        "expected_result": "Links have meaningful text (avoid 'click here', 'read more' without context).",
        "common_failures": "Generic link text, links with same text going to different places, URLs as link text",
        "tool": "NVDA",
        "priority": "Medium",
        "reference_url": "https://www.w3.org/WAI/WCAG21/Understanding/link-purpose-in-context.html"
    },
    {
        "wcag_criterion": "3.3.1",
        "level": "A",
        "item_title": "Form errors are announced",
        "instructions": "Submit form with errors. NVDA should announce error messages and identify which fields have errors.",
        "expected_result": "Errors are announced clearly with field identification.",
        "common_failures": "Error messages not in live region, errors only shown visually, error not associated with field",
        "tool": "NVDA",
        "priority": "Critical",
        "reference_url": "https://www.w3.org/WAI/WCAG21/Understanding/error-identification.html"
    },
    {
        "wcag_criterion": "4.1.2",
        "level": "A",
        "item_title": "Custom controls announce role and state",
        "instructions": "Navigate to custom interactive elements (custom dropdowns, sliders, tabs). NVDA should announce role (button, tab, slider) and state (expanded, selected, value).",
        "expected_result": "Custom controls announce: name, role, and current state/value.",
        "common_failures": "Missing ARIA roles, incorrect ARIA states, role conflicts, undiscoverable controls",
        "tool": "NVDA",
        "priority": "Critical",
        "reference_url": "https://www.w3.org/WAI/WCAG21/Understanding/name-role-value.html"
    },
    {
        "wcag_criterion": "4.1.3",
        "level": "AA",
        "item_title": "Status messages are announced",
        "instructions": "Trigger status messages (success confirmations, loading states, search results count). NVDA should announce them without moving focus.",
        "expected_result": "Status updates are announced via ARIA live regions.",
        "common_failures": "Status not in live region, wrong live region politeness, status messages missed",
        "tool": "NVDA",
        "priority": "High",
        "reference_url": "https://www.w3.org/WAI/WCAG21/Understanding/status-messages.html"
    }
]

# Keyboard Navigation Checklist
keyboard_data = [
    {
        "wcag_criterion": "2.1.1",
        "level": "A",
        "item_title": "All links are keyboard accessible",
        "instructions": "Tab through the page. Verify all links can be reached and activated with Enter key.",
        "expected_result": "All links receive focus and activate on Enter press.",
        "common_failures": "Links missing href, onclick on span/div without tabindex, disabled links",
        "tool": "Keyboard",
        "priority": "Critical",
        "reference_url": "https://www.w3.org/WAI/WCAG21/Understanding/keyboard.html"
    },
    {
        "wcag_criterion": "2.1.1",
        "level": "A",
        "item_title": "All buttons are keyboard accessible",
        "instructions": "Tab to all buttons. Activate with Enter or Space bar.",
        "expected_result": "All buttons can be focused and activated via keyboard.",
        "common_failures": "Div with onclick instead of button, missing button type, JavaScript-only buttons",
        "tool": "Keyboard",
        "priority": "Critical",
        "reference_url": "https://www.w3.org/WAI/WCAG21/Understanding/keyboard.html"
    },
    {
        "wcag_criterion": "2.1.1",
        "level": "A",
        "item_title": "All form controls are keyboard accessible",
        "instructions": "Tab through form. Test text inputs (type text), checkboxes (Space to toggle), radio buttons (Arrow keys), dropdowns (Space to open, Arrow keys to select).",
        "expected_result": "All form controls operable via keyboard only.",
        "common_failures": "Custom controls without keyboard support, missing keyboard patterns for complex widgets",
        "tool": "Keyboard",
        "priority": "Critical",
        "reference_url": "https://www.w3.org/WAI/WCAG21/Understanding/keyboard.html"
    },
    {
        "wcag_criterion": "2.1.2",
        "level": "A",
        "item_title": "No keyboard traps exist",
        "instructions": "Tab through entire page including modals, popups, and embedded content. Verify you can always Tab/Shift+Tab out of components.",
        "expected_result": "Focus never gets stuck. You can always navigate forward/backward.",
        "common_failures": "Modal traps focus with no way out, embedded content traps keyboard, infinite Tab loops",
        "tool": "Keyboard",
        "priority": "Critical",
        "reference_url": "https://www.w3.org/WAI/WCAG21/Understanding/no-keyboard-trap.html"
    },
    {
        "wcag_criterion": "2.4.3",
        "level": "A",
        "item_title": "Tab order is logical and intuitive",
        "instructions": "Tab through entire page. Verify tab order matches visual layout and reading order (left-to-right, top-to-bottom in most cases).",
        "expected_result": "Focus moves in logical sequence that matches page structure.",
        "common_failures": "Tab order jumps around, CSS positioning breaks order, hidden elements in tab order",
        "tool": "Keyboard",
        "priority": "High",
        "reference_url": "https://www.w3.org/WAI/WCAG21/Understanding/focus-order.html"
    },
    {
        "wcag_criterion": "2.4.7",
        "level": "AA",
        "item_title": "All interactive elements show focus indicator",
        "instructions": "Tab through all interactive elements. Each should show a clear visual focus indicator (outline, border, background color change).",
        "expected_result": "Focus indicator is visible, has sufficient contrast, and clearly shows which element is focused.",
        "common_failures": "Focus outline removed with CSS, insufficient contrast, focus indicator too subtle",
        "tool": "Keyboard",
        "priority": "Critical",
        "reference_url": "https://www.w3.org/WAI/WCAG21/Understanding/focus-visible.html"
    },
    {
        "wcag_criterion": "3.2.1",
        "level": "A",
        "item_title": "Focus doesn't trigger unexpected changes",
        "instructions": "Tab through form fields and controls. Verify that simply focusing an element doesn't cause navigation, form submission, or significant context changes.",
        "expected_result": "Focus alone doesn't trigger actions. Context changes only occur on activation (Enter/Space).",
        "common_failures": "Dropdown auto-submits on focus, modals open on focus, navigation changes on focus",
        "tool": "Keyboard",
        "priority": "High",
        "reference_url": "https://www.w3.org/WAI/WCAG21/Understanding/on-focus.html"
    }
]

# Zoom/Low Vision Checklist
zoom_data = [
    {
        "wcag_criterion": "1.4.4",
        "level": "AA",
        "item_title": "Text can be resized to 200% without loss of content",
        "instructions": "Zoom browser to 200% (Ctrl/Cmd + Plus). Verify all text is readable and no content is cut off or hidden.",
        "expected_result": "All content remains visible and readable at 200% zoom. No horizontal scrolling required.",
        "common_failures": "Text cut off by containers, content overlapping, horizontal scrolling required, fixed pixel sizes",
        "tool": "Zoom",
        "priority": "Critical",
        "reference_url": "https://www.w3.org/WAI/WCAG21/Understanding/resize-text.html"
    },
    {
        "wcag_criterion": "1.4.10",
        "level": "AA",
        "item_title": "Content reflows at 400% zoom without horizontal scrolling",
        "instructions": "Zoom to 400% in browser set to 1280px width. Verify no horizontal scrolling is needed for main content.",
        "expected_result": "Content reflows to single column. No horizontal scrolling (vertical scrolling is fine).",
        "common_failures": "Fixed width containers, content requires horizontal scroll, layout breaks completely",
        "tool": "Zoom",
        "priority": "Critical",
        "reference_url": "https://www.w3.org/WAI/WCAG21/Understanding/reflow.html"
    },
    {
        "wcag_criterion": "1.4.11",
        "level": "AA",
        "item_title": "Interactive controls have 3:1 contrast against background",
        "instructions": "Zoom to 200%. Visually inspect button borders, form field boundaries, focus indicators. Verify they're clearly visible.",
        "expected_result": "All interactive control boundaries are visible with 3:1 contrast minimum.",
        "common_failures": "Light gray borders on white, insufficient button outline contrast, invisible focus states",
        "tool": "Zoom",
        "priority": "High",
        "reference_url": "https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast.html"
    },
    {
        "wcag_criterion": "1.4.12",
        "level": "AA",
        "item_title": "Content adapts to increased text spacing",
        "instructions": "Apply text spacing overrides: line height 1.5x, paragraph spacing 2x font size, letter spacing 0.12x, word spacing 0.16x. Verify no text is cut off.",
        "expected_result": "All text remains visible. No clipping or overlap occurs with increased spacing.",
        "common_failures": "Text cut off by fixed height containers, overlapping text, layout breaks",
        "tool": "Zoom",
        "priority": "High",
        "reference_url": "https://www.w3.org/WAI/WCAG21/Understanding/text-spacing.html"
    },
    {
        "wcag_criterion": "1.4.3",
        "level": "AA",
        "item_title": "Text contrast is 4.5:1 for normal text",
        "instructions": "Zoom to 200% and visually inspect all text. Use contrast checker on suspicious low-contrast text.",
        "expected_result": "All normal-sized text (under 18pt/24px) has 4.5:1 contrast ratio minimum.",
        "common_failures": "Gray text on light background, colored text insufficient contrast, transparent overlays",
        "tool": "Zoom",
        "priority": "Critical",
        "reference_url": "https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html"
    },
    {
        "wcag_criterion": "1.4.13",
        "level": "AA",
        "item_title": "Tooltips remain visible when zoomed",
        "instructions": "Zoom to 200%. Hover over elements with tooltips. Verify tooltips don't disappear or move off-screen.",
        "expected_result": "Tooltips appear fully on screen and remain visible while hovering.",
        "common_failures": "Tooltips positioned off-screen, tooltips disappear too quickly, tooltips not responsive",
        "tool": "Zoom",
        "priority": "Medium",
        "reference_url": "https://www.w3.org/WAI/WCAG21/Understanding/content-on-hover-or-focus.html"
    },
    {
        "wcag_criterion": "2.4.7",
        "level": "AA",
        "item_title": "Focus indicators scale with zoom",
        "instructions": "Zoom to 200%. Tab through interactive elements. Verify focus indicators are proportionally visible.",
        "expected_result": "Focus indicators scale with zoom and remain clearly visible.",
        "common_failures": "Fixed pixel outlines become too small, focus indicators disappear at high zoom",
        "tool": "Zoom",
        "priority": "High",
        "reference_url": "https://www.w3.org/WAI/WCAG21/Understanding/focus-visible.html"
    }
]

# Create Excel files
def create_excel_checklist(data, filename):
    df = pd.DataFrame(data)
    # Reorder columns to match specification
    column_order = [
        "wcag_criterion", "level", "item_title", "instructions", 
        "expected_result", "common_failures", "tool", "priority", "reference_url"
    ]
    df = df[column_order]
    
    filepath = checklists_dir / filename
    df.to_excel(filepath, index=False, sheet_name="Checklist")
    
    print(f"✓ Created {filename}")
    print(f"  - {len(data)} checklist items")
    print(f"  - Location: {filepath}")
    return filepath

# Generate all checklists
print("Generating Excel-based WCAG 2.1 AA Checklists...")
print("=" * 60)

nvda_file = create_excel_checklist(nvda_data, "nvda-wcag21aa-checklist.xlsx")
keyboard_file = create_excel_checklist(keyboard_data, "keyboard-wcag21aa-checklist.xlsx")
zoom_file = create_excel_checklist(zoom_data, "zoom-wcag21aa-checklist.xlsx")

print("=" * 60)
print("\n✅ All checklists generated successfully!")
print("\nNext steps:")
print("1. Review Excel files in static/checklists/")
print("2. Edit Excel files to add more items or customize")
print("3. Backend will automatically read these files")
print("\nTo add items: Open Excel file, add new row with all columns filled")
print("To edit items: Modify any cell directly in Excel")
print("To delete items: Delete entire row in Excel")
