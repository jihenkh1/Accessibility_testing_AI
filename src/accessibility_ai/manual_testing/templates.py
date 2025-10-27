"""
Hardcoded manual testing checklist templates based on professional accessibility testing standards.
No AI needed - these are established testing methodologies from WCAG and professional testers.

Each test item follows the structure:
- test_item: Specific action to perform (verb-first, clear instruction)
- how_to_test: Exact steps with keyboard shortcuts and tools
- what_to_look_for: Clear pass/fail criteria
- wcag_reference: Specific WCAG guideline
- priority: high/medium/low (impact-based)
- estimated_time: Realistic time estimate in minutes
"""

from typing import Dict, List, Any

# Base checklist items that apply to all page types
BASE_CHECKLIST = [
    {
        "id": "kb-001",
        "category": "Keyboard Navigation",
        "test_item": "Press Tab - verify focus moves through all interactive elements in logical order",
        "how_to_test": "1. Click in address bar to reset focus\n2. Press Tab repeatedly\n3. Observe focus moving left→right, top→bottom through buttons, links, form controls\n4. Continue until focus cycles back to browser UI",
        "what_to_look_for": "✓ All interactive elements receive focus\n✓ Tab order matches visual layout (reading order)\n✓ No elements skipped\n✗ Focus jumps randomly or skips sections",
        "wcag_reference": "2.1.1 Keyboard (Level A)",
        "priority": "high",
        "estimated_time": 3
    },
    {
        "id": "kb-002",
        "category": "Keyboard Navigation",
        "test_item": "Press Tab - verify visible focus indicators appear on every focusable element",
        "how_to_test": "1. Press Tab to move through page\n2. Watch for outline/border/background change on each element\n3. Check focus indicators have minimum 3:1 contrast ratio\n4. Test on buttons, links, inputs, custom components",
        "what_to_look_for": "✓ Clear visible outline/border appears (not browser default only)\n✓ Focus indicator is at least 2px thick or has equivalent area\n✓ Color contrast is 3:1 or better against background\n✗ Focus indicator invisible or very faint",
        "wcag_reference": "2.4.7 Focus Visible (Level AA)",
        "priority": "high",
        "estimated_time": 2
    },
    {
        "id": "kb-003",
        "category": "Keyboard Navigation",
        "test_item": "Press Escape - verify all modals, menus, and dialogs close and release focus",
        "how_to_test": "1. Open each modal/dialog/dropdown on page\n2. Press Escape key\n3. Verify component closes\n4. Check focus returns to trigger element\n5. Press Tab to confirm focus isn't trapped",
        "what_to_look_for": "✓ Escape closes component immediately\n✓ Focus returns to element that opened it\n✓ Can Tab away freely\n✗ Component stays open or focus trapped inside",
        "wcag_reference": "2.1.2 No Keyboard Trap (Level A)",
        "priority": "high",
        "estimated_time": 2
    },
    {
        "id": "kb-004",
        "category": "Keyboard Navigation",
        "test_item": "Press Shift+Tab - verify focus moves backward through elements correctly",
        "how_to_test": "1. Tab forward to middle of page\n2. Press Shift+Tab repeatedly\n3. Verify focus moves in reverse order\n4. Check same elements are focusable in both directions",
        "what_to_look_for": "✓ Reverse tab order is exact opposite of forward\n✓ No elements appear/disappear when reversing\n✓ Focus returns to start correctly\n✗ Different elements focusable backward vs forward",
        "wcag_reference": "2.4.3 Focus Order (Level A)",
        "priority": "medium",
        "estimated_time": 2
    },
    {
        "id": "sr-001",
        "category": "Screen Reader",
        "test_item": "NVDA+Down Arrow - listen to page read in reading order from top to bottom",
        "how_to_test": "1. Start NVDA (Insert+N to verify running)\n2. Press NVDA+Down Arrow repeatedly\n3. Listen to each element announcement\n4. Verify order matches visual layout\n5. Note any missing content or redundant announcements",
        "what_to_look_for": "✓ Reading order matches visual order (left→right, top→bottom)\n✓ All visible text announced\n✓ No redundant repetition of same information\n✓ Headings, buttons, links announced with role\n✗ Reading order jumps around or content skipped",
        "wcag_reference": "4.1.2 Name, Role, Value (Level A)",
        "priority": "high",
        "estimated_time": 5
    },
    {
        "id": "sr-002",
        "category": "Screen Reader",
        "test_item": "NVDA+H - navigate through all headings and verify logical hierarchy",
        "how_to_test": "1. Press NVDA+H to open headings list\n2. Review heading levels (H1→H2→H3, etc.)\n3. Verify only one H1 per page\n4. Check no heading levels skipped (no H1→H3)\n5. Listen to heading text for clear, descriptive labels",
        "what_to_look_for": "✓ One H1 (page title)\n✓ Heading levels increase by 1 (H2→H3, not H2→H4)\n✓ Headings describe section content clearly\n✓ Logical outline structure\n✗ Multiple H1s, skipped levels, or vague headings like 'Content'",
        "wcag_reference": "2.4.6 Headings and Labels (Level AA)",
        "priority": "high",
        "estimated_time": 3
    },
    {
        "id": "sr-003",
        "category": "Screen Reader",
        "test_item": "NVDA+D - navigate through landmarks and verify semantic structure",
        "how_to_test": "1. Press NVDA+D to open landmarks list\n2. Verify these landmarks exist: banner/header, navigation, main, contentinfo/footer\n3. Press NVDA+D repeatedly to jump between landmarks\n4. Confirm each landmark contains appropriate content",
        "what_to_look_for": "✓ Landmarks present: header, nav, main, footer (at minimum)\n✓ Each landmark appears once (except nav can repeat)\n✓ Main content is inside <main> landmark\n✓ Landmarks have descriptive labels if multiple of same type\n✗ No landmarks, or entire page in single landmark",
        "wcag_reference": "1.3.1 Info and Relationships (Level A)",
        "priority": "high",
        "estimated_time": 2
    },
    {
        "id": "sr-004",
        "category": "Screen Reader",
        "test_item": "NVDA+G - navigate through all images and verify alt text appropriateness",
        "how_to_test": "1. Press NVDA+G to open graphics list\n2. Listen to alt text for each image\n3. Check informative images have descriptive alt text\n4. Verify decorative images marked as alt=\"\" or role=\"presentation\"\n5. Confirm complex images have long descriptions",
        "what_to_look_for": "✓ Informative images: alt text describes content/function\n✓ Decorative images: alt=\"\" (announced as 'graphic' with no text)\n✓ Linked images: alt describes link destination\n✓ Complex images (charts/graphs): long description available\n✗ Alt text is filename, 'image', or missing entirely",
        "wcag_reference": "1.1.1 Non-text Content (Level A)",
        "priority": "high",
        "estimated_time": 3
    },
    {
        "id": "cc-001",
        "category": "Color & Contrast",
        "test_item": "Use browser DevTools - check text contrast ratios meet WCAG minimums",
        "how_to_test": "1. Open browser DevTools (F12)\n2. Select text element with inspector\n3. View contrast ratio in Accessibility panel\n4. Verify: 4.5:1 for normal text (<24px or <19px bold)\n5. Verify: 3:1 for large text (≥24px or ≥19px bold)\n6. Test body text, headings, buttons, links",
        "what_to_look_for": "✓ Normal text: 4.5:1 or higher\n✓ Large text: 3:1 or higher\n✓ UI components/graphics: 3:1 or higher\n✗ Contrast ratios below minimums (common: light gray text)",
        "wcag_reference": "1.4.3 Contrast (Minimum) (Level AA)",
        "priority": "high",
        "estimated_time": 4
    },
    {
        "id": "cc-002",
        "category": "Color & Contrast",
        "test_item": "Inspect page - verify information not conveyed by color alone",
        "how_to_test": "1. Look for color-coded information (error messages, required fields, status indicators)\n2. Check each has non-color indicator: icon, text label, pattern, or underline\n3. Common examples: form errors (red text), required fields (red asterisk), links (blue text)\n4. Verify icons/labels accompany color coding",
        "what_to_look_for": "✓ Error text has icon + color (not just red text)\n✓ Required fields have asterisk or '(required)' text + color\n✓ Links underlined or have other visual cue beyond color\n✓ Status indicators have icon + color\n✗ Only color distinguishes meaning (red/green, pass/fail)",
        "wcag_reference": "1.4.1 Use of Color (Level A)",
        "priority": "high",
        "estimated_time": 3
    },
    {
        "id": "zm-001",
        "category": "Zoom & Reflow",
        "test_item": "Browser zoom 200% - verify page usable without horizontal scrolling",
        "how_to_test": "1. Press Ctrl+0 to reset zoom\n2. Press Ctrl+ (plus) until 200% zoom\n3. Navigate entire page with keyboard/mouse\n4. Verify no horizontal scrollbar appears\n5. Check all content readable and buttons clickable",
        "what_to_look_for": "✓ Content reflows to fit width (no horizontal scroll)\n✓ All text readable\n✓ All buttons/controls remain usable\n✓ No overlapping content\n✗ Horizontal scrollbar, text cut off, or overlapping elements",
        "wcag_reference": "1.4.4 Resize Text (Level AA)",
        "priority": "medium",
        "estimated_time": 2
    },
    {
        "id": "zm-002",
        "category": "Zoom & Reflow",
        "test_item": "Browser zoom 400% - verify content reflows at 320px viewport width (3 minutes)",
        "how_to_test": "1. Set browser window to 1280px wide\n2. Zoom to 400% (equivalent to 320px viewport)\n3. Scroll vertically through entire page\n4. Verify content stacks in single column\n5. Check all functionality remains available",
        "what_to_look_for": "✓ Content in single column (no horizontal scroll)\n✓ Two-dimensional scrolling only for images, maps, diagrams, tables, toolbars\n✓ All interactive elements accessible\n✗ Content requires horizontal scroll or is cut off",
        "wcag_reference": "1.4.10 Reflow (Level AA)",
        "priority": "medium",
        "estimated_time": 3
    },
    {
        "id": "mobile-001",
        "category": "Mobile & Touch",
        "test_item": "Inspect touch targets - verify minimum 44x44px with 8px spacing (3 minutes)",
        "how_to_test": "1. Open browser DevTools (F12)\n2. Toggle device toolbar (Ctrl+Shift+M)\n3. Select mobile device (iPhone, Android)\n4. Right-click interactive elements → Inspect\n5. Check computed width/height in Styles panel\n6. Measure spacing between adjacent targets\n7. Test buttons, links, form controls, icons",
        "what_to_look_for": "✓ All touch targets at least 44x44 CSS pixels\n✓ Minimum 8px spacing between targets\n✓ Larger targets for primary actions (48x48px+)\n✓ Small text links have padding to increase hit area\n✗ Targets <44px or crowded together <8px apart",
        "wcag_reference": "2.5.5 Target Size (Level AAA)",
        "priority": "high",
        "estimated_time": 3
    },
    {
        "id": "mobile-002",
        "category": "Mobile & Touch",
        "test_item": "Test pinch-to-zoom - verify page remains usable at 200% zoom (2 minutes)",
        "how_to_test": "1. Open page on mobile device or emulator\n2. Pinch to zoom to 200%\n3. Navigate page by swiping\n4. Test all interactive elements (tap buttons, links)\n5. Verify no content is inaccessible\n6. Check for viewport meta tag: user-scalable=yes",
        "what_to_look_for": "✓ Pinch-to-zoom enabled (not disabled)\n✓ Page usable at 200% zoom\n✓ All content accessible via panning\n✓ No maximum-scale=1.0 in viewport meta\n✗ Zoom disabled or content breaks when zoomed",
        "wcag_reference": "1.4.4 Resize Text (Level AA)",
        "priority": "high",
        "estimated_time": 2
    },
    {
        "id": "mobile-003",
        "category": "Mobile & Touch",
        "test_item": "Check swipe gestures - verify button alternatives provided (2 minutes)",
        "how_to_test": "1. Look for swipe-based interactions (carousels, cards, menus)\n2. Test if swiping works\n3. Look for button alternatives: arrows, dots, next/prev\n4. Verify buttons work with tap/keyboard\n5. Test with TalkBack/VoiceOver - confirm accessible",
        "what_to_look_for": "✓ Every swipe gesture has button alternative\n✓ Buttons clearly visible and labeled\n✓ Works with screen reader gestures\n✓ No swipe-only actions\n✗ Gestures required without button alternatives",
        "wcag_reference": "2.5.1 Pointer Gestures (Level A)",
        "priority": "medium",
        "estimated_time": 2
    }
]


# User Account & Profile page checklist
USER_ACCOUNT_CHECKLIST = [
    {
        "id": "acct-001",
        "category": "Account Settings",
        "test_item": "Tab through settings form - verify all controls keyboard accessible (3 minutes)",
        "how_to_test": "1. Navigate to account settings page\n2. Press Tab through all form controls\n3. Test toggles with Space\n4. Test dropdowns with Arrow keys\n5. Verify Save/Cancel buttons with Enter",
        "what_to_look_for": "✓ All settings reachable via Tab\n✓ Toggle switches work with Space\n✓ Dropdowns open with Space/Enter, navigate with arrows\n✓ Changes can be saved with Enter key\n✗ Any setting requires mouse interaction",
        "wcag_reference": "2.1.1 Keyboard (Level A)",
        "priority": "high",
        "estimated_time": 3
    },
    {
        "id": "acct-002",
        "category": "Account Settings",
        "test_item": "NVDA on form labels - verify all settings have clear descriptions (2 minutes)",
        "how_to_test": "1. Start NVDA\n2. Navigate through settings with Arrow keys\n3. Listen for label + current value announcements\n4. Verify toggle states announced: 'checked' or 'not checked'\n5. Check help text is announced with aria-describedby",
        "what_to_look_for": "✓ Each setting has clear label\n✓ Current value announced (on/off, selected option)\n✓ Help text provided for complex settings\n✓ NVDA announces 'checkbox checked' or 'switch on'\n✗ Settings announced without context or current state",
        "wcag_reference": "3.3.2 Labels or Instructions (Level A)",
        "priority": "high",
        "estimated_time": 2
    },
    {
        "id": "acct-003",
        "category": "Profile Data",
        "test_item": "Test password change - verify current password required and announced (2 minutes)",
        "how_to_test": "1. Navigate to password change form\n2. Try changing password without entering current one\n3. Verify error message appears and is announced\n4. Use NVDA - confirm error announced with aria-live\n5. Check error is associated with field via aria-describedby",
        "what_to_look_for": "✓ Current password required\n✓ Error message appears adjacent to field\n✓ Error announced immediately to screen readers\n✓ Clear explanation: 'Current password is required'\n✗ Silent validation or vague 'Error' message",
        "wcag_reference": "3.3.1 Error Identification (Level A)",
        "priority": "high",
        "estimated_time": 2
    },
    {
        "id": "acct-004",
        "category": "Profile Data",
        "test_item": "Check delete account - verify confirmation dialog with clear consequences (3 minutes)",
        "how_to_test": "1. Locate delete/close account option\n2. Activate delete button\n3. Verify confirmation dialog appears\n4. Read warning text - should explain data loss\n5. Test keyboard navigation in dialog\n6. Verify 'Cancel' is default action (focused first)\n7. Check Escape closes dialog",
        "what_to_look_for": "✓ Confirmation dialog appears\n✓ Clear warning about permanent data loss\n✓ Cancel button focused by default (not Delete)\n✓ Both buttons keyboard accessible\n✓ Escape closes dialog without deleting\n✗ No confirmation, or delete is too easy",
        "wcag_reference": "3.3.4 Error Prevention (Legal, Financial, Data) (Level AA)",
        "priority": "high",
        "estimated_time": 3
    }
]

# Search & Results page checklist
SEARCH_RESULTS_CHECKLIST = [
    {
        "id": "search-001",
        "category": "Search Interface",
        "test_item": "Tab to search input - verify label and placeholder provide clear instructions (1 minute)",
        "how_to_test": "1. Tab to search field\n2. Check for visible label (not just placeholder)\n3. Use NVDA - verify label announced\n4. Read placeholder text for search hints\n5. Right-click → Inspect for aria-label or aria-labelledby",
        "what_to_look_for": "✓ Visible label present: 'Search products', 'Search articles'\n✓ Placeholder provides hint: 'Enter keywords...'\n✓ NVDA announces label when focusing input\n✓ Search button adjacent with clear text\n✗ Only placeholder (disappears when typing)",
        "wcag_reference": "3.3.2 Labels or Instructions (Level A)",
        "priority": "high",
        "estimated_time": 1
    },
    {
        "id": "search-002",
        "category": "Search Interface",
        "test_item": "Type in search - verify autocomplete suggestions keyboard accessible (3 minutes)",
        "how_to_test": "1. Type partial query\n2. Wait for suggestions dropdown to appear\n3. Press Arrow Down to enter suggestions\n4. Press Arrow Up/Down to navigate\n5. Press Enter to select\n6. Press Escape to dismiss\n7. Verify NVDA announces: 'X suggestions available'",
        "what_to_look_for": "✓ Arrow Down moves focus into suggestions\n✓ Arrow keys navigate suggestions with visual highlight\n✓ Enter selects and submits search\n✓ Escape dismisses suggestions\n✓ NVDA announces suggestion count and current selection\n✗ Must click suggestions with mouse",
        "wcag_reference": "2.1.1 Keyboard (Level A)",
        "priority": "high",
        "estimated_time": 3
    },
    {
        "id": "search-003",
        "category": "Results Display",
        "test_item": "Submit search - verify results count announced via aria-live (2 minutes)",
        "how_to_test": "1. Start NVDA\n2. Perform search\n3. Listen for automatic announcement (don't move focus)\n4. Verify announces: '45 results found' or 'No results found'\n5. Right-click results container → Inspect for aria-live=\"polite\"\n6. Test with zero results",
        "what_to_look_for": "✓ NVDA announces results count immediately\n✓ Message is specific: 'X results found for [query]'\n✓ Zero results announced: 'No results found'\n✓ aria-live=\"polite\" or role=\"status\" present\n✗ Silent to screen readers, must manually find count",
        "wcag_reference": "4.1.3 Status Messages (Level AA)",
        "priority": "high",
        "estimated_time": 2
    },
    {
        "id": "search-004",
        "category": "Filtering",
        "test_item": "Tab to filters - verify all checkboxes/radios keyboard accessible (3 minutes)",
        "how_to_test": "1. Tab to filter section\n2. Press Space to toggle checkboxes\n3. Use Arrow keys for radio button groups\n4. Test 'Apply Filters' button with Enter\n5. Verify results update after applying\n6. Use NVDA to confirm filter states announced",
        "what_to_look_for": "✓ All filters reachable via Tab\n✓ Space toggles checkboxes\n✓ Arrow keys navigate radio groups\n✓ Filter states announced: 'checked', 'not checked'\n✓ Applied filters cause results update\n✗ Must click filters or results don't update",
        "wcag_reference": "2.1.1 Keyboard (Level A)",
        "priority": "high",
        "estimated_time": 3
    },
    {
        "id": "search-005",
        "category": "Results Display",
        "test_item": "NVDA through results - verify each result has clear structure (4 minutes)",
        "how_to_test": "1. Start NVDA\n2. Navigate through search results with Arrow keys\n3. Listen for: result title, description, metadata\n4. Check each result is contained in <article> or has role=\"article\"\n5. Verify headings used for result titles\n6. Confirm links have descriptive text",
        "what_to_look_for": "✓ Each result announced with clear structure\n✓ Headings used for result titles (H2 or H3)\n✓ Description text provided\n✓ Links are descriptive: 'View product: [name]'\n✓ Metadata announced: price, rating, date\n✗ Results read as flat text without structure",
        "wcag_reference": "1.3.1 Info and Relationships (Level A)",
        "priority": "medium",
        "estimated_time": 4
    }
]

# Content & Articles page checklist
CONTENT_ARTICLES_CHECKLIST = [
    {
        "id": "content-001",
        "category": "Reading Structure",
        "test_item": "NVDA+H through article - verify logical heading hierarchy (2 minutes)",
        "how_to_test": "1. Open article page\n2. Press NVDA+H to list headings\n3. Verify H1 for article title (only one)\n4. Check H2 for main sections\n5. Verify H3 for subsections (no level skipping)\n6. Confirm heading text is descriptive",
        "what_to_look_for": "✓ One H1 (article title)\n✓ Logical hierarchy: H1 → H2 → H3 (no H2 → H4)\n✓ Headings describe section content clearly\n✓ Can navigate article by headings alone\n✗ Multiple H1s, skipped levels, or 'Section 1' type headings",
        "wcag_reference": "2.4.6 Headings and Labels (Level AA)",
        "priority": "high",
        "estimated_time": 2
    },
    {
        "id": "content-002",
        "category": "Reading Structure",
        "test_item": "Zoom to 200% - verify text reflows without horizontal scroll (2 minutes)",
        "how_to_test": "1. Press Ctrl+0 to reset zoom\n2. Press Ctrl+ (plus) repeatedly until 200%\n3. Read through entire article\n4. Verify no horizontal scrollbar\n5. Check images scale appropriately\n6. Confirm buttons remain clickable",
        "what_to_look_for": "✓ Text reflows to fit window width\n✓ No horizontal scrolling required\n✓ Images resize or hide gracefully\n✓ All interactive elements remain usable\n✗ Horizontal scroll, text cut off, or broken layout",
        "wcag_reference": "1.4.4 Resize Text (Level AA)",
        "priority": "high",
        "estimated_time": 2
    },
    {
        "id": "content-003",
        "category": "Media Content",
        "test_item": "Play embedded video - verify captions and transcript available (5 minutes)",
        "how_to_test": "1. Locate video player\n2. Tab to player controls - verify keyboard accessible\n3. Press Space or Enter to play\n4. Look for CC button and activate\n5. Verify captions appear and are synchronized\n6. Look for transcript link near video\n7. Check transcript matches audio content",
        "what_to_look_for": "✓ Video controls keyboard accessible\n✓ CC button present and toggles captions\n✓ Captions synchronized (< 2 sec delay)\n✓ Captions include dialogue and sound effects\n✓ Transcript link provided\n✗ No captions or auto-generated only with errors",
        "wcag_reference": "1.2.2 Captions (Prerecorded) (Level A)",
        "priority": "high",
        "estimated_time": 5
    },
    {
        "id": "content-004",
        "category": "Reading Tools",
        "test_item": "Test text spacing - verify 2x line height remains readable (3 minutes)",
        "how_to_test": "1. Open browser console (F12)\n2. Paste CSS: * { line-height: 2 !important; letter-spacing: 0.12em !important; word-spacing: 0.16em !important; }\n3. Read article content\n4. Verify text doesn't overlap\n5. Check no content hidden or clipped\n6. Test interactive elements still work",
        "what_to_look_for": "✓ Text remains readable with increased spacing\n✓ No overlapping text or truncation\n✓ All content visible (nothing clipped)\n✓ Buttons and links still clickable\n✗ Text overlaps, content hidden, or layout breaks",
        "wcag_reference": "1.4.12 Text Spacing (Level AA)",
        "priority": "medium",
        "estimated_time": 3
    },
    {
        "id": "content-005",
        "category": "Navigation",
        "test_item": "Use table of contents - verify jump links work with keyboard (2 minutes)",
        "how_to_test": "1. Look for table of contents or jump links\n2. Tab to first jump link\n3. Press Enter to activate\n4. Verify page scrolls to correct section\n5. Check focus moves to target heading\n6. Test all jump links in TOC",
        "what_to_look_for": "✓ Jump links keyboard accessible\n✓ Activating link scrolls to correct section\n✓ Focus moves to target (or tab order preserved)\n✓ Back to top link present for long articles\n✗ Links don't work or focus lost after jump",
        "wcag_reference": "2.4.1 Bypass Blocks (Level A)",
        "priority": "medium",
        "estimated_time": 2
    }
]

# Form-specific checklist items (renamed for consistency)
FORMS_DATA_INPUT_CHECKLIST = [
    {
        "id": "form-001",
        "category": "Forms",
        "test_item": "Inspect form inputs - verify all have visible <label> elements programmatically associated",
        "how_to_test": "1. Right-click each input field → Inspect Element\n2. Look for <label> tag with matching 'for' attribute\n3. OR check input has aria-labelledby pointing to label ID\n4. Click label text - verify it focuses the input\n5. Use NVDA on input - verify label is announced",
        "what_to_look_for": "✓ Every input has visible label text\n✓ Clicking label focuses input (for/id association works)\n✓ NVDA announces label when focusing input\n✓ Label describes input purpose clearly\n✗ Placeholder as only label, or no label at all",
        "wcag_reference": "3.3.2 Labels or Instructions (Level A)",
        "priority": "high",
        "estimated_time": 3
    },
    {
        "id": "form-002",
        "category": "Forms",
        "test_item": "Submit form with errors - verify error messages clearly identify which fields failed",
        "how_to_test": "1. Leave required fields empty or enter invalid data\n2. Submit form\n3. Check error message appears for each problem field\n4. Verify error text describes the problem specifically\n5. Use NVDA - confirm errors announced with aria-live or focus movement",
        "what_to_look_for": "✓ Error message appears adjacent to each problem field\n✓ Error text is specific ('Email must include @' not just 'Error')\n✓ Errors announced immediately to screen reader users\n✓ Error messages persist until corrected\n✗ Generic error at top without field-specific details",
        "wcag_reference": "3.3.1 Error Identification (Level A)",
        "priority": "high",
        "estimated_time": 4
    },
    {
        "id": "form-003",
        "category": "Forms",
        "test_item": "Trigger validation errors - verify messages include suggestions for correction",
        "how_to_test": "1. Enter invalid data in fields (wrong format, out of range, etc.)\n2. Read each error message\n3. Check if message explains HOW to fix it\n4. Examples: 'Enter date as MM/DD/YYYY', 'Password must be 8+ characters'",
        "what_to_look_for": "✓ Error messages include format/requirement details\n✓ Examples provided for expected formats\n✓ Helpful suggestions, not just 'invalid'\n✓ Links to help documentation if complex\n✗ Vague errors like 'Invalid input' without guidance",
        "wcag_reference": "3.3.3 Error Suggestion (Level AA)",
        "priority": "medium",
        "estimated_time": 3
    },
    {
        "id": "form-004",
        "category": "Forms",
        "test_item": "Inspect required fields - verify marked with asterisk AND aria-required=\"true\"",
        "how_to_test": "1. Look for required field indicators (usually red asterisk *)\n2. Right-click required input → Inspect\n3. Check for aria-required=\"true\" or required attribute\n4. Use NVDA on field - listen for 'required' announcement\n5. Verify asterisk meaning explained (e.g., legend says '* = required')",
        "what_to_look_for": "✓ Visual indicator (asterisk) on required fields\n✓ aria-required=\"true\" attribute in code\n✓ NVDA announces 'required' when focusing field\n✓ Legend/instruction explains asterisk meaning\n✗ Only visual indicator OR only aria-required (need both)",
        "wcag_reference": "3.3.2 Labels or Instructions (Level A)",
        "priority": "high",
        "estimated_time": 3
    },
    {
        "id": "form-005",
        "category": "Forms",
        "test_item": "Inspect personal data fields - verify autocomplete attributes for autofill",
        "how_to_test": "1. Right-click name, email, address, phone fields → Inspect\n2. Look for autocomplete attribute (e.g., autocomplete=\"name\", autocomplete=\"email\")\n3. Test: Start typing in field - verify browser suggests saved values\n4. Check common fields: name, email, phone, address, cc-number",
        "what_to_look_for": "✓ autocomplete attribute present on personal data fields\n✓ Correct values used (see HTML spec: 'name', 'email', 'tel', 'street-address')\n✓ Browser autofill suggestions appear\n✗ No autocomplete attributes or incorrect values",
        "wcag_reference": "1.3.5 Identify Input Purpose (Level AA)",
        "priority": "low",
        "estimated_time": 2
    },
    {
        "id": "form-006",
        "category": "Forms",
        "test_item": "Press Enter in form - verify submission works via keyboard and success message appears",
        "how_to_test": "1. Fill form completely using only keyboard\n2. Press Enter (or Tab to submit button and press Space)\n3. Verify form submits\n4. Check for success message or page transition\n5. Use NVDA - confirm success message announced with aria-live",
        "what_to_look_for": "✓ Enter key submits form from text inputs\n✓ Success message appears and is announced\n✓ Message has role=\"alert\" or aria-live=\"polite\"\n✓ Clear confirmation of what happened\n✗ Must click submit button, or no feedback after submission",
        "wcag_reference": "3.2.2 On Input (Level A)",
        "priority": "medium",
        "estimated_time": 2
    }
]


# Dashboard-specific checklist items
DASHBOARD_CHECKLIST = [
    {
        "id": "dash-001",
        "category": "Data Visualization",
        "test_item": "Inspect charts/graphs - verify text alternative or accessible data table provided",
        "how_to_test": "1. Locate all charts, graphs, infographics on page\n2. Right-click each → Inspect\n3. Look for aria-label or aria-labelledby describing the data\n4. OR check for accompanying data table with same information\n5. Use NVDA - verify meaningful description announced",
        "what_to_look_for": "✓ Chart has aria-label summarizing key data points\n✓ OR accessible data table presents same data\n✓ Description includes: chart type, data ranges, trends\n✓ Complex charts have detailed long description\n✗ Chart is just image with alt=\"chart\" or no description",
        "wcag_reference": "1.1.1 Non-text Content (Level A)",
        "priority": "high",
        "estimated_time": 4
    },
    {
        "id": "dash-002",
        "category": "Data Visualization",
        "test_item": "Trigger live updates - verify screen reader announces changes via aria-live",
        "how_to_test": "1. Start NVDA screen reader\n2. Wait for or trigger dynamic content updates (new notifications, data refresh, status changes)\n3. Listen for automatic announcements without moving focus\n4. Right-click updated region → Inspect for aria-live attribute\n5. Test multiple update types: polite, assertive",
        "what_to_look_for": "✓ NVDA announces updates automatically\n✓ aria-live=\"polite\" for non-critical updates\n✓ aria-live=\"assertive\" for important alerts\n✓ Updates don't interrupt current reading\n✗ Dynamic changes silent to screen reader users",
        "wcag_reference": "4.1.3 Status Messages (Level AA)",
        "priority": "high",
        "estimated_time": 3
    },
    {
        "id": "dash-003",
        "category": "Data Visualization",
        "test_item": "Inspect data tables - verify proper <th> headers with scope attributes",
        "how_to_test": "1. Right-click table → Inspect Element\n2. Check <th> elements exist for all column/row headers\n3. Verify scope=\"col\" on column headers, scope=\"row\" on row headers\n4. Look for <caption> describing table purpose\n5. Use NVDA+T to navigate table - listen for header announcements",
        "what_to_look_for": "✓ <th> elements (not <td>) for all headers\n✓ scope=\"col\" or scope=\"row\" attributes present\n✓ <caption> describes table content\n✓ NVDA announces headers when navigating cells\n✗ All cells are <td>, or no scope attributes",
        "wcag_reference": "1.3.1 Info and Relationships (Level A)",
        "priority": "high",
        "estimated_time": 3
    },
    {
        "id": "dash-004",
        "category": "Navigation",
        "test_item": "Press Tab from page load - verify skip link appears as first focusable element",
        "how_to_test": "1. Reload page (Ctrl+R)\n2. Press Tab once\n3. Look for 'Skip to main content' link appearing\n4. Press Enter to activate skip link\n5. Press Tab - verify focus moves to main content area (bypassing navigation)\n6. Check skip link works with keyboard only",
        "what_to_look_for": "✓ Skip link is first Tab stop on page\n✓ Link is visible when focused (or becomes visible)\n✓ Activating link moves focus past navigation\n✓ Multiple skip links if page has multiple sections\n✗ No skip link, or skip link doesn't actually skip content",
        "wcag_reference": "2.4.1 Bypass Blocks (Level A)",
        "priority": "high",
        "estimated_time": 2
    },
    {
        "id": "dash-005",
        "category": "Interaction",
        "test_item": "Tab to elements with tooltips - verify tooltips appear on focus, not just hover",
        "how_to_test": "1. Tab through page to elements with info icons or tooltips\n2. Verify tooltip appears when element receives focus\n3. Don't use mouse - keyboard only\n4. Press Escape - verify tooltip dismisses\n5. Move focus away - verify tooltip disappears\n6. Hover without focus - verify tooltip can be dismissed with Escape",
        "what_to_look_for": "✓ Tooltip appears on keyboard focus (not just mouse hover)\n✓ Escape key dismisses tooltip\n✓ Moving focus away dismisses tooltip\n✓ Tooltip content readable with screen reader\n✗ Tooltip only appears on hover, or can't be dismissed",
        "wcag_reference": "1.4.13 Content on Hover or Focus (Level AA)",
        "priority": "medium",
        "estimated_time": 3
    }
]


# Ecommerce-specific checklist items
ECOMMERCE_CHECKLIST = [
    {
        "id": "ecom-001",
        "category": "Product Browsing",
        "test_item": "Tab to filter controls - verify checkboxes, dropdowns accessible via keyboard",
        "how_to_test": "1. Tab to product filter section\n2. Press Space on checkboxes to toggle\n3. Arrow keys to navigate dropdown options\n4. Enter to select dropdown items\n5. Verify filters apply without mouse\n6. Use NVDA - confirm filter labels and states announced",
        "what_to_look_for": "✓ All filter controls reachable via Tab\n✓ Space toggles checkboxes\n✓ Arrow keys work in dropdowns\n✓ NVDA announces filter name, type, and state (checked/unchecked)\n✗ Filters require mouse clicks or lack keyboard support",
        "wcag_reference": "4.1.2 Name, Role, Value (Level A)",
        "priority": "high",
        "estimated_time": 3
    },
    {
        "id": "ecom-002",
        "category": "Product Browsing",
        "test_item": "NVDA+G on product images - verify alt text describes product clearly",
        "how_to_test": "1. Press NVDA+G to list all graphics\n2. Listen to alt text for each product image\n3. Check alt text includes: product name, key features, color/style\n4. Verify decorative images (background patterns) have alt=\"\"\n5. Linked product images should describe destination (product name)",
        "what_to_look_for": "✓ Alt text identifies product clearly (not 'product123.jpg')\n✓ Includes distinguishing features (color, size, style)\n✓ Linked images describe where link goes\n✓ Concise but descriptive (not marketing copy)\n✗ Generic alt like 'product image' or missing entirely",
        "wcag_reference": "1.1.1 Non-text Content (Level A)",
        "priority": "high",
        "estimated_time": 3
    },
    {
        "id": "ecom-003",
        "category": "Shopping Cart",
        "test_item": "Click 'Add to Cart' - verify confirmation announced to screen reader via aria-live",
        "how_to_test": "1. Start NVDA\n2. Add item to cart (click button or press Enter/Space)\n3. Listen for automatic announcement (don't move focus)\n4. Right-click notification area → Inspect for aria-live\n5. Verify message is clear: 'Item added to cart' not just 'Success'\n6. Test with multiple items",
        "what_to_look_for": "✓ NVDA announces 'X added to cart' immediately\n✓ Notification has aria-live=\"polite\" or role=\"status\"\n✓ Message is specific (item name included)\n✓ Visual confirmation also appears\n✗ Silent to screen readers, or vague message like 'Done'",
        "wcag_reference": "4.1.3 Status Messages (Level AA)",
        "priority": "high",
        "estimated_time": 2
    },
    {
        "id": "ecom-004",
        "category": "Shopping Cart",
        "test_item": "Tab to quantity controls - verify keyboard can increase/decrease values",
        "how_to_test": "1. Tab to quantity input field or spinner\n2. Try: Arrow Up/Down keys to change value\n3. Try: Type number directly\n4. Try: +/- buttons with Space/Enter\n5. Verify updated quantity works with screen reader\n6. Check min/max values enforced",
        "what_to_look_for": "✓ Arrow keys increase/decrease quantity OR\n✓ Type number directly in field OR\n✓ +/- buttons work with Space/Enter\n✓ NVDA announces new quantity value\n✓ Min (usually 1) and max enforced\n✗ Must use mouse to click tiny +/- buttons",
        "wcag_reference": "2.1.1 Keyboard (Level A)",
        "priority": "high",
        "estimated_time": 2
    },
    {
        "id": "ecom-005",
        "category": "Checkout",
        "test_item": "Navigate checkout flow - verify entire process completable without mouse",
        "how_to_test": "1. Start checkout using keyboard only (Enter on checkout button)\n2. Tab through all fields: shipping, billing, payment\n3. Use Space/Enter to select radio buttons and dropdowns\n4. Arrow keys for dropdown navigation\n5. Enter to submit forms and proceed\n6. Complete purchase using only keyboard",
        "what_to_look_for": "✓ All checkout steps keyboard accessible\n✓ Can fill all forms with Tab/Shift+Tab\n✓ Radio buttons work with Space\n✓ Dropdowns work with Arrow keys\n✓ Submit buttons work with Enter\n✗ Any step requires mouse (e.g., payment iframe issues)",
        "wcag_reference": "2.1.1 Keyboard (Level A)",
        "priority": "high",
        "estimated_time": 5
    },
    {
        "id": "ecom-006",
        "category": "Checkout",
        "test_item": "Inspect secure payment indicators - verify SSL icons and text are screen reader accessible",
        "how_to_test": "1. Look for security badges (lock icon, 'Secure Checkout', SSL certificates)\n2. Right-click icons → Inspect\n3. Check for aria-label or visually hidden text explaining security\n4. Use NVDA on payment area - listen for security assurances\n5. Verify not just decorative images",
        "what_to_look_for": "✓ Lock icons have aria-label='Secure connection' or similar\n✓ Security text is readable (not just icon)\n✓ NVDA announces security information\n✓ SSL/secure checkout badges have alt text\n✗ Security communicated only through visual icons",
        "wcag_reference": "1.3.1 Info and Relationships (Level A)",
        "priority": "medium",
        "estimated_time": 2
    }
]

# E-commerce: Checkout Flow specific checklist
ECOMMERCE_CHECKOUT_CHECKLIST = [
    {
        "id": "checkout-001",
        "category": "Checkout Flow",
        "test_item": "Navigate entire checkout - verify completable with keyboard only (8 minutes)",
        "how_to_test": "1. Add item to cart and proceed to checkout\n2. Complete all steps using ONLY keyboard:\n   - Tab through shipping form\n   - Space to select shipping method radio buttons\n   - Tab through billing form\n   - Arrow keys in state/country dropdowns\n   - Tab to payment iframe (if applicable)\n   - Space on terms checkbox\n   - Enter to place order\n3. Verify each step transitions to next\n4. Check confirmation page appears",
        "what_to_look_for": "✓ All form fields keyboard accessible\n✓ Radio buttons selectable with Space\n✓ Dropdowns navigable with Arrow keys\n✓ Checkboxes toggle with Space\n✓ Submit button works with Enter\n✓ No step requires mouse\n✗ Any step blocks keyboard-only completion",
        "wcag_reference": "2.1.1 Keyboard (Level A)",
        "priority": "high",
        "estimated_time": 8
    },
    {
        "id": "checkout-002",
        "category": "Form Validation",
        "test_item": "Submit with errors - verify messages announced within 2 seconds (3 minutes)",
        "how_to_test": "1. Start NVDA\n2. Leave required fields empty or enter invalid data\n3. Click/press Enter to submit\n4. Start timer - listen for announcement\n5. Verify error announced within 2 seconds\n6. Check error summary at top of form\n7. Verify focus moves to first error or summary\n8. Test aria-live on error container",
        "what_to_look_for": "✓ Errors announced immediately (<2 sec)\n✓ Error summary appears at top: '3 errors found'\n✓ Focus moves to error summary or first error\n✓ Each error linked to specific field\n✓ aria-live=\"assertive\" on error container\n✗ Silent errors or delayed announcement >2 sec",
        "wcag_reference": "3.3.1 Error Identification (Level A)",
        "priority": "high",
        "estimated_time": 3
    },
    {
        "id": "checkout-003",
        "category": "Payment Security",
        "test_item": "Inspect payment form - verify autocomplete attributes on all fields (2 minutes)",
        "how_to_test": "1. Right-click each payment field → Inspect\n2. Check for autocomplete attributes:\n   - Card number: autocomplete=\"cc-number\"\n   - Exp date: autocomplete=\"cc-exp\"\n   - CVV: autocomplete=\"cc-csc\"\n   - Name: autocomplete=\"cc-name\"\n3. Test browser autofill suggestions appear\n4. Verify PCI compliance indicators",
        "what_to_look_for": "✓ All payment fields have autocomplete\n✓ Correct values used (cc-number, cc-exp, cc-csc)\n✓ Browser shows autofill suggestions\n✓ Sensitive fields marked with appropriate type\n✗ No autocomplete or incorrect values",
        "wcag_reference": "1.3.5 Identify Input Purpose (Level AA)",
        "priority": "medium",
        "estimated_time": 2
    },
    {
        "id": "checkout-004",
        "category": "Order Review",
        "test_item": "Review order - verify all costs clearly labeled and announced (3 minutes)",
        "how_to_test": "1. Navigate to order review/summary section\n2. Use NVDA to read through all line items\n3. Verify announces:\n   - Item name + price\n   - Subtotal label + amount\n   - Shipping label + amount\n   - Tax label + amount\n   - Total label + amount\n4. Check visual labels match announced text\n5. Verify currency symbols announced correctly",
        "what_to_look_for": "✓ Each cost has clear label\n✓ NVDA announces label + amount together\n✓ Total clearly distinguished (bold, larger)\n✓ Currency symbols properly announced\n✓ No confusion about what each charge is\n✗ Amounts without labels or labels without amounts",
        "wcag_reference": "1.3.1 Info and Relationships (Level A)",
        "priority": "high",
        "estimated_time": 3
    },
    {
        "id": "checkout-005",
        "category": "Error Prevention",
        "test_item": "Before final submit - verify confirmation dialog or review step (2 minutes)",
        "how_to_test": "1. Complete checkout form\n2. Press submit/place order button\n3. Look for one of:\n   - Confirmation dialog: 'Place order for $XX.XX?'\n   - Review page showing all order details\n   - Checkbox: 'I confirm the order details'\n4. Verify can cancel/go back\n5. Check confirmation is keyboard accessible",
        "what_to_look_for": "✓ Confirmation step before final submission\n✓ Shows order total clearly: '$XX.XX'\n✓ Option to cancel/go back\n✓ Dialog/checkbox keyboard accessible\n✓ Clear button labels: 'Confirm Order' vs 'Cancel'\n✗ No confirmation, order submitted immediately",
        "wcag_reference": "3.3.4 Error Prevention (Legal, Financial, Data) (Level AA)",
        "priority": "high",
        "estimated_time": 2
    },
    {
        "id": "checkout-006",
        "category": "Progress Indication",
        "test_item": "Multi-step checkout - verify current step clearly indicated (2 minutes)",
        "how_to_test": "1. Start checkout process\n2. Look for step indicator (1/3, 2/3, 3/3)\n3. Check current step visually distinguished\n4. Use NVDA on step indicator\n5. Verify announces: 'Step 2 of 3: Shipping'\n6. Right-click → Inspect for aria-current=\"step\"\n7. Test on each step of checkout",
        "what_to_look_for": "✓ Step indicator visible: '2 of 3' or progress bar\n✓ Current step highlighted differently\n✓ NVDA announces current step + label\n✓ aria-current=\"step\" on current step\n✓ Completed steps marked (checkmark icon)\n✗ No indication of progress or current step",
        "wcag_reference": "2.4.8 Location (Level AAA)",
        "priority": "medium",
        "estimated_time": 2
    }
]


# Landing page-specific checklist items (renamed for consistency)
MARKETING_LANDING_CHECKLIST = [
    {
        "id": "land-001",
        "category": "Hero Section",
        "test_item": "Inspect hero image - verify alt text for foreground images OR accessible text over background",
        "how_to_test": "1. Right-click hero image → Inspect\n2. If <img>: Check alt attribute has meaningful description\n3. If background-image: Verify text overlay is real HTML text (not image text)\n4. Use NVDA - confirm content is announced\n5. Test with images disabled - verify content still makes sense",
        "what_to_look_for": "✓ Foreground <img> has descriptive alt text\n✓ Background images have HTML text overlay (not text-in-image)\n✓ Hero message readable with NVDA\n✓ Page makes sense with images off\n✗ Hero is pure image with text baked in (no alt, no HTML text)",
        "wcag_reference": "1.1.1 Non-text Content (Level A)",
        "priority": "high",
        "estimated_time": 2
    },
    {
        "id": "land-002",
        "category": "Call to Action",
        "test_item": "NVDA on CTA buttons - verify descriptive accessible names announced (not just 'Click here')",
        "how_to_test": "1. Use NVDA to navigate to all CTA buttons\n2. Listen to button announcement\n3. Check button text is descriptive (tells you where it goes/what it does)\n4. Right-click → Inspect for aria-label if visual text is vague\n5. Verify 'Learn more' buttons have context (aria-labelledby to heading)",
        "what_to_look_for": "✓ Button text describes action: 'Start free trial', 'Download guide', 'Sign up now'\n✓ Generic text like 'Learn more' has aria-label adding context\n✓ NVDA announces full, clear button purpose\n✓ No 'Click here' or 'Read more' without context\n✗ Buttons say 'Click here', 'Learn more' with no additional label",
        "wcag_reference": "2.4.4 Link Purpose (In Context) (Level A)",
        "priority": "high",
        "estimated_time": 3
    },
    {
        "id": "land-003",
        "category": "Media",
        "test_item": "Play video - verify closed captions available and transcript link present",
        "how_to_test": "1. Play video\n2. Look for CC button - click to enable captions\n3. Verify captions are synchronized with audio\n4. Check captions include: dialogue, speaker identification, important sounds\n5. Look for 'Transcript' link near video\n6. Verify transcript includes all spoken content",
        "what_to_look_for": "✓ CC button present in video player\n✓ Captions synchronized (not 2+ seconds delay)\n✓ Captions include speaker names and sound effects [applause]\n✓ Transcript link available for full text version\n✗ No captions, or auto-generated captions with major errors",
        "wcag_reference": "1.2.2 Captions (Prerecorded) (Level A)",
        "priority": "high",
        "estimated_time": 4
    },
    {
        "id": "land-004",
        "category": "Media",
        "test_item": "Test autoplay - verify audio/video can be paused within 3 seconds or doesn't autoplay",
        "how_to_test": "1. Load page (or reload with Ctrl+R)\n2. Listen for autoplaying audio/video\n3. If autoplay detected: Look for pause button\n4. Press pause button within 3 seconds\n5. Verify pause button is keyboard accessible (Tab + Space/Enter)\n6. Check pause button is visible and obvious",
        "what_to_look_for": "✓ No autoplay (best option) OR\n✓ Pause button visible and reachable within 3 seconds OR\n✓ Audio auto-stops after 3 seconds OR\n✓ Autoplay respects user's OS 'prefers-reduced-motion' setting\n✗ Audio/video autoplays without easy way to pause",
        "wcag_reference": "1.4.2 Audio Control (Level A)",
        "priority": "high",
        "estimated_time": 2
    },
    {
        "id": "land-005",
        "category": "Animation",
        "test_item": "Enable prefers-reduced-motion - verify animations pause or reduce intensity",
        "how_to_test": "1. Open browser DevTools → Settings → Emulate CSS media feature prefers-reduced-motion: reduce\n2. Reload page\n3. Check all animations, parallax scrolling, auto-playing carousels\n4. Verify motion stops or becomes subtle\n5. OR look for pause/stop animation button on page",
        "what_to_look_for": "✓ Animations stop or reduce to simple fades when prefers-reduced-motion enabled\n✓ Parallax effects become static\n✓ Auto-advancing carousels pause\n✓ Page remains functional without animations\n✗ Animations ignore prefers-reduced-motion setting",
        "wcag_reference": "2.3.3 Animation from Interactions (Level AAA)",
        "priority": "low",
        "estimated_time": 3
    }
]


# Component-specific checklist items
COMPONENT_CHECKLISTS: Dict[str, List[Dict[str, Any]]] = {
    "modal": [
        {
            "id": "comp-modal-001",
            "category": "Modal Dialog",
            "test_item": "Open modal, press Tab repeatedly - verify focus stays trapped inside modal",
            "how_to_test": "1. Click button to open modal\n2. Press Tab repeatedly through all focusable elements in modal\n3. After last element, verify Tab cycles back to first element in modal\n4. Try Shift+Tab from first element - verify goes to last element in modal\n5. Attempt to Tab to page content behind modal - verify impossible",
            "what_to_look_for": "✓ Focus cycles within modal only (first → last → first)\n✓ Cannot Tab to page content behind modal\n✓ Shift+Tab also trapped in modal\n✓ Modal has at least one focusable element\n✗ Tab escapes modal and reaches page content",
            "wcag_reference": "2.4.3 Focus Order (Level A)",
            "priority": "high",
            "estimated_time": 2
        },
        {
            "id": "comp-modal-002",
            "category": "Modal Dialog",
            "test_item": "Press Escape key - verify modal closes and focus returns to trigger button",
            "how_to_test": "1. Open modal by clicking or pressing Enter on trigger button\n2. Press Escape key\n3. Verify modal closes immediately\n4. Check focus returns to button that opened modal\n5. Test from different focus positions within modal",
            "what_to_look_for": "✓ Escape immediately closes modal\n✓ Focus automatically returns to trigger button\n✓ Works from any focusable element inside modal\n✓ No JavaScript errors\n✗ Escape doesn't work, or focus lost after close",
            "wcag_reference": "2.1.1 Keyboard (Level A)",
            "priority": "high",
            "estimated_time": 1
        },
        {
            "id": "comp-modal-003",
            "category": "Modal Dialog",
            "test_item": "Close modal - verify focus automatically returns to element that opened it",
            "how_to_test": "1. Tab to trigger button and press Enter to open modal\n2. Close modal using close button (Tab to it, press Enter)\n3. Verify focus returns to original trigger button\n4. Try all close methods: X button, Cancel button, Escape, click overlay\n5. Confirm focus management works for all methods",
            "what_to_look_for": "✓ Focus returns to trigger button after close\n✓ Works for all close methods (X, Cancel, Escape, overlay click)\n✓ Focus not lost to top of page\n✓ Consistent behavior\n✗ Focus lost, or goes to wrong element",
            "wcag_reference": "2.4.3 Focus Order (Level A)",
            "priority": "high",
            "estimated_time": 2
        }
    ],
    "dropdown": [
        {
            "id": "comp-dd-001",
            "category": "Dropdown",
            "test_item": "Tab to dropdown, press Arrow Down/Up - verify items selectable via keyboard",
            "how_to_test": "1. Tab to dropdown trigger\n2. Press Space or Enter to open dropdown\n3. Press Arrow Down to move to next item\n4. Press Arrow Up to move to previous item\n5. Press Enter to select highlighted item\n6. Verify dropdown closes and selection applied",
            "what_to_look_for": "✓ Space/Enter opens dropdown\n✓ Arrow keys navigate items (highlight moves visibly)\n✓ Home/End jump to first/last item (bonus)\n✓ Enter selects item and closes dropdown\n✓ Escape closes without selection\n✗ Must use mouse to select items",
            "wcag_reference": "2.1.1 Keyboard (Level A)",
            "priority": "high",
            "estimated_time": 2
        },
        {
            "id": "comp-dd-002",
            "category": "Dropdown",
            "test_item": "Inspect dropdown with DevTools - verify aria-expanded and aria-haspopup attributes",
            "how_to_test": "1. Right-click dropdown button → Inspect Element\n2. Look for aria-haspopup=\"true\" or aria-haspopup=\"menu\"/\"listbox\"\n3. Check aria-expanded=\"false\" when closed\n4. Open dropdown, inspect again - verify aria-expanded=\"true\"\n5. Use NVDA - listen for 'collapsed'/'expanded' announcements",
            "what_to_look_for": "✓ aria-haspopup present (value: true, menu, or listbox)\n✓ aria-expanded toggles false → true when opening\n✓ NVDA announces state: 'collapsed' or 'expanded'\n✓ Button has accessible name\n✗ Missing ARIA attributes, or states don't toggle",
            "wcag_reference": "4.1.2 Name, Role, Value (Level A)",
            "priority": "high",
            "estimated_time": 2
        }
    ],
    "tabs": [
        {
            "id": "comp-tabs-001",
            "category": "Tabs",
            "test_item": "Tab to tab list, press Arrow Left/Right - verify tabs switch via arrow keys",
            "how_to_test": "1. Tab to first tab button\n2. Press Arrow Right to move to next tab\n3. Press Arrow Left to move to previous tab\n4. Verify tab panel content updates as you arrow between tabs\n5. Check Home/End keys jump to first/last tab (bonus)\n6. Confirm visual focus indicator on active tab",
            "what_to_look_for": "✓ Arrow Left/Right navigate between tabs\n✓ Tab panel updates automatically as you arrow\n✓ Focus stays in tab list (doesn't move to panel)\n✓ Visual focus indicator clearly visible\n✓ Home/End work (nice to have)\n✗ Must click tabs, or arrow keys don't work",
            "wcag_reference": "2.1.1 Keyboard (Level A)",
            "priority": "high",
            "estimated_time": 2
        },
        {
            "id": "comp-tabs-002",
            "category": "Tabs",
            "test_item": "Inspect tabs with DevTools - verify role=\"tablist\", role=\"tab\", role=\"tabpanel\"",
            "how_to_test": "1. Right-click tab button → Inspect\n2. Verify parent container has role=\"tablist\"\n3. Verify each tab has role=\"tab\"\n4. Check aria-selected=\"true\" on active tab, \"false\" on others\n5. Verify each panel has role=\"tabpanel\"\n6. Check aria-labelledby linking panel to tab",
            "what_to_look_for": "✓ Container: role=\"tablist\"\n✓ Buttons: role=\"tab\"\n✓ Content: role=\"tabpanel\"\n✓ Active tab has aria-selected=\"true\"\n✓ Panels linked to tabs via aria-labelledby\n✗ Missing roles or incorrect ARIA attributes",
            "wcag_reference": "4.1.2 Name, Role, Value (Level A)",
            "priority": "high",
            "estimated_time": 2
        }
    ],
    "carousel": [
        {
            "id": "comp-car-001",
            "category": "Carousel",
            "test_item": "Tab to carousel controls - verify Previous/Next buttons work with Space/Enter",
            "how_to_test": "1. Tab to Previous button\n2. Press Enter or Space\n3. Verify slide changes backward\n4. Tab to Next button\n5. Press Enter or Space\n6. Verify slide changes forward\n7. Test all carousel navigation (dots, arrows, thumbnails)",
            "what_to_look_for": "✓ All carousel controls keyboard accessible\n✓ Space and Enter both work on buttons\n✓ Visual focus indicators on all controls\n✓ Slide transitions work correctly\n✗ Must use mouse to navigate slides",
            "wcag_reference": "2.1.1 Keyboard (Level A)",
            "priority": "high",
            "estimated_time": 2
        },
        {
            "id": "comp-car-002",
            "category": "Carousel",
            "test_item": "Check for autoplay - verify pause button present and accessible via keyboard",
            "how_to_test": "1. Load page with carousel\n2. Observe if slides auto-advance\n3. If yes: Look for Play/Pause button\n4. Tab to pause button\n5. Press Space/Enter to pause\n6. Verify carousel stops auto-rotating\n7. Check button toggles to Play state",
            "what_to_look_for": "✓ Pause button visible and easy to find\n✓ Button keyboard accessible\n✓ Pausing stops auto-rotation immediately\n✓ Button clearly labeled 'Pause' or has pause icon with aria-label\n✓ Respects prefers-reduced-motion (auto-pauses)\n✗ Autoplay with no pause control",
            "wcag_reference": "2.2.2 Pause, Stop, Hide (Level A)",
            "priority": "high",
            "estimated_time": 2
        },
        {
            "id": "comp-car-003",
            "category": "Carousel",
            "test_item": "Use NVDA while advancing slides - verify slide changes announced",
            "how_to_test": "1. Start NVDA\n2. Navigate to carousel\n3. Click Next button (or wait for auto-advance)\n4. Listen for announcement of slide change\n5. Verify announcement includes: slide number, total slides, content summary\n6. Check for aria-live region on slide container",
            "what_to_look_for": "✓ Slide changes announced automatically\n✓ Announcement includes useful info: 'Slide 2 of 5'\n✓ Content summary provided (heading or key text)\n✓ Announcements not overly verbose or repetitive\n✗ Slide changes silent to screen reader users",
            "wcag_reference": "4.1.3 Status Messages (Level AA)",
            "priority": "medium",
            "estimated_time": 2
        }
    ],
    "accordion": [
        {
            "id": "comp-acc-001",
            "category": "Accordion",
            "test_item": "Tab to accordion headers, press Enter/Space - verify panels expand/collapse",
            "how_to_test": "1. Tab to first accordion header button\n2. Press Enter (or Space)\n3. Verify panel expands and content visible\n4. Press Enter again\n5. Verify panel collapses and content hidden\n6. Repeat for all accordion items\n7. Test Shift+Tab moves backward correctly",
            "what_to_look_for": "✓ Enter and Space both toggle panels\n✓ Visual expansion/collapse animation\n✓ Only one panel open at a time (OR multiple allowed - check pattern)\n✓ Focus stays on header button during toggle\n✗ Must click to expand, or keyboard doesn't work",
            "wcag_reference": "2.1.1 Keyboard (Level A)",
            "priority": "high",
            "estimated_time": 2
        },
        {
            "id": "comp-acc-002",
            "category": "Accordion",
            "test_item": "Inspect accordion with DevTools - verify aria-expanded toggles on headers",
            "how_to_test": "1. Right-click accordion header → Inspect\n2. Verify element is <button> (not <div> with click handler)\n3. Check aria-expanded=\"false\" when collapsed\n4. Expand accordion, inspect again\n5. Verify aria-expanded=\"true\" when expanded\n6. Check aria-controls points to panel ID\n7. Use NVDA - listen for 'collapsed'/'expanded' announcements",
            "what_to_look_for": "✓ Headers are <button> elements\n✓ aria-expanded present and toggles false/true\n✓ aria-controls references panel ID\n✓ NVDA announces state changes\n✓ Panel has matching ID\n✗ Missing ARIA, or headers aren't buttons",
            "wcag_reference": "4.1.2 Name, Role, Value (Level A)",
            "priority": "high",
            "estimated_time": 2
        }
    ],
    "datepicker": [
        {
            "id": "comp-date-001",
            "category": "Date Picker",
            "test_item": "Open datepicker, press Arrow keys - verify navigation through calendar dates",
            "how_to_test": "1. Tab to date input field\n2. Press Space or click calendar icon to open picker\n3. Press Arrow Right/Left to move between days\n4. Press Arrow Up/Down to move between weeks\n5. Press Page Up/Down to change months\n6. Press Home/End for start/end of week\n7. Press Enter to select date\n8. Verify date populates input field",
            "what_to_look_for": "✓ Arrow keys navigate dates (visual focus moves)\n✓ Page Up/Down change months\n✓ Home/End jump within week\n✓ Enter selects date and closes picker\n✓ Escape closes without selecting\n✗ Must click dates with mouse",
            "wcag_reference": "2.1.1 Keyboard (Level A)",
            "priority": "high",
            "estimated_time": 3
        },
        {
            "id": "comp-date-002",
            "category": "Date Picker",
            "test_item": "Inspect date input - verify instructions for expected format (MM/DD/YYYY)",
            "how_to_test": "1. Look for visible format hint near input field (e.g., 'MM/DD/YYYY')\n2. Right-click input → Inspect\n3. Check for aria-describedby pointing to format instructions\n4. Use NVDA on input - verify format announced\n5. Try typing date manually - verify it works (picker is optional)",
            "what_to_look_for": "✓ Visual format hint visible (placeholder or label)\n✓ aria-describedby links to format instructions\n✓ NVDA announces expected format when focusing input\n✓ Manual typing works (not forced to use picker)\n✗ No format guidance, or picker is only option",
            "wcag_reference": "3.3.2 Labels or Instructions (Level A)",
            "priority": "high",
            "estimated_time": 2
        }
    ],
    "menu": [
        {
            "id": "comp-menu-001",
            "category": "Navigation Menu",
            "test_item": "Tab to menu, press Arrow keys - verify navigation between menu items",
            "how_to_test": "1. Tab to first menu item\n2. Press Arrow Right (horizontal menus) or Arrow Down (vertical menus)\n3. Verify focus moves to next menu item\n4. Press Enter to activate menu item or open submenu\n5. If submenu: Press Arrow Right/Down to enter submenu\n6. Press Escape or Arrow Left/Up to close submenu\n7. Test Home/End for first/last item",
            "what_to_look_for": "✓ Arrow keys navigate menu items\n✓ Enter activates links or opens submenus\n✓ Escape closes submenus\n✓ Focus visible on current item\n✓ Home/End work (bonus)\n✗ Must Tab through all items, or arrow keys don't work",
            "wcag_reference": "2.1.1 Keyboard (Level A)",
            "priority": "high",
            "estimated_time": 3
        },
        {
            "id": "comp-menu-002",
            "category": "Navigation Menu",
            "test_item": "Use NVDA on menu items - verify submenus announced clearly",
            "how_to_test": "1. Start NVDA\n2. Navigate to menu items with submenus\n3. Listen for indicators: 'has submenu', 'collapsed', 'submenu'\n4. Right-click menu item → Inspect\n5. Check for aria-haspopup=\"true\" or aria-haspopup=\"menu\"\n6. Verify aria-expanded toggles when opening/closing submenu",
            "what_to_look_for": "✓ NVDA announces 'has submenu' or similar\n✓ aria-haspopup present on items with submenus\n✓ aria-expanded toggles false/true\n✓ Visual indicator for submenus (arrow icon)\n✗ No indication that submenu exists",
            "wcag_reference": "4.1.2 Name, Role, Value (Level A)",
            "priority": "medium",
            "estimated_time": 2
        }
    ],
    "search": [
        {
            "id": "comp-search-001",
            "category": "Search",
            "test_item": "Type in search field - verify autocomplete suggestions keyboard accessible",
            "how_to_test": "1. Tab to search input\n2. Type partial query (e.g., 'acc')\n3. Wait for autocomplete suggestions to appear\n4. Press Arrow Down to move into suggestions list\n5. Press Arrow Up/Down to navigate suggestions\n6. Press Enter to select highlighted suggestion\n7. Verify search executes or input populates",
            "what_to_look_for": "✓ Suggestions appear while typing\n✓ Arrow Down moves focus into suggestions\n✓ Arrow Up/Down navigate suggestions\n✓ Enter selects suggestion\n✓ Escape closes suggestions\n✗ Must click suggestions with mouse",
            "wcag_reference": "2.1.1 Keyboard (Level A)",
            "priority": "high",
            "estimated_time": 2
        },
        {
            "id": "comp-search-002",
            "category": "Search",
            "test_item": "Submit search, use NVDA - verify results count announced automatically",
            "how_to_test": "1. Start NVDA\n2. Perform search\n3. Listen for automatic announcement (don't move focus)\n4. Verify announcement includes results count: '23 results found'\n5. Right-click results area → Inspect\n6. Check for aria-live region or role=\"status\"\n7. Test with zero results - confirm announcement",
            "what_to_look_for": "✓ Results count announced automatically: 'X results found'\n✓ aria-live=\"polite\" or role=\"status\" on results container\n✓ Zero results also announced: 'No results found'\n✓ Announcement happens without moving focus\n✗ Silent to screen readers, must manually find results count",
            "wcag_reference": "4.1.3 Status Messages (Level AA)",
            "priority": "medium",
            "estimated_time": 2
        }
    ],
    "pagination": [
        {
            "id": "comp-page-001",
            "category": "Pagination",
            "test_item": "Tab through pagination controls - verify all page links keyboard accessible",
            "how_to_test": "1. Tab to pagination controls\n2. Press Tab through: Previous, page numbers, Next\n3. Press Enter on page number link\n4. Verify page changes\n5. Check Previous/Next buttons with Enter/Space\n6. Confirm disabled states (e.g., Previous on page 1) skip focus",
            "what_to_look_for": "✓ All pagination controls keyboard accessible\n✓ Enter activates page links\n✓ Disabled Previous/Next not focusable\n✓ Focus visible on all controls\n✗ Must click to change pages",
            "wcag_reference": "2.1.1 Keyboard (Level A)",
            "priority": "high",
            "estimated_time": 2
        },
        {
            "id": "comp-page-002",
            "category": "Pagination",
            "test_item": "Use NVDA on pagination - verify current page clearly marked and announced",
            "how_to_test": "1. Start NVDA\n2. Navigate to pagination controls\n3. Listen to each page link announcement\n4. Verify current page announced differently: 'Page 2, current page'\n5. Right-click current page → Inspect\n6. Check for aria-current=\"page\" attribute\n7. Verify visual styling differs (color, bold, etc.)",
            "what_to_look_for": "✓ Current page has aria-current=\"page\"\n✓ NVDA announces 'current page'\n✓ Visual styling clearly distinguishes current page\n✓ Current page may be non-interactive (not a link)\n✗ No indication of current page, or only visual (no aria-current)",
            "wcag_reference": "1.3.1 Info and Relationships (Level A)",
            "priority": "medium",
            "estimated_time": 2
        }
    ],
    "tooltip": [
        {
            "id": "comp-tip-001",
            "category": "Tooltip",
            "test_item": "Tab to elements with tooltips - verify tooltip appears on focus, not just hover",
            "how_to_test": "1. Tab to element with tooltip (info icon, button, link)\n2. Verify tooltip appears when element receives keyboard focus\n3. Don't use mouse - keyboard only\n4. Read tooltip content\n5. Tab to next element - verify tooltip disappears\n6. Test: Hover with mouse (no focus) - tooltip should still appear",
            "what_to_look_for": "✓ Tooltip appears on keyboard focus\n✓ Tooltip also appears on hover\n✓ Tooltip disappears when focus moves away\n✓ Tooltip content readable and logical\n✗ Tooltip only on hover, not on keyboard focus",
            "wcag_reference": "1.4.13 Content on Hover or Focus (Level AA)",
            "priority": "high",
            "estimated_time": 2
        },
        {
            "id": "comp-tip-002",
            "category": "Tooltip",
            "test_item": "Show tooltip, press Escape - verify tooltip dismisses without losing focus",
            "how_to_test": "1. Tab to element to show tooltip\n2. Press Escape\n3. Verify tooltip closes\n4. Verify focus stays on trigger element (doesn't move)\n5. Test with hover: Hover to show tooltip, press Escape\n6. Verify tooltip closes while pointer still hovering",
            "what_to_look_for": "✓ Escape dismisses tooltip\n✓ Focus remains on trigger element\n✓ Works for both keyboard focus and mouse hover\n✓ Tooltip can be re-opened after dismissing\n✗ Escape doesn't work, or dismissing loses focus",
            "wcag_reference": "1.4.13 Content on Hover or Focus (Level AA)",
            "priority": "medium",
            "estimated_time": 1
        }
    ]
}



def get_page_type_checklist(page_type: str) -> List[Dict[str, Any]]:
    """
    Get the checklist for a specific page type.
    
    Args:
        page_type: Type of page - supports both legacy and new naming:
            Legacy: landing, form, dashboard, ecommerce
            New: marketing, forms_data_input, data_display, ecommerce_product, 
                 ecommerce_checkout, user_account, search_results, content_articles
    
    Returns:
        List of checklist items combining base + page-specific items
    """
    checklist = BASE_CHECKLIST.copy()
    
    # Legacy mappings (backward compatibility)
    if page_type == "form" or page_type == "forms_data_input":
        checklist.extend(FORMS_DATA_INPUT_CHECKLIST)
    elif page_type == "dashboard" or page_type == "data_display":
        checklist.extend(DASHBOARD_CHECKLIST)
    elif page_type == "ecommerce" or page_type == "ecommerce_product":
        checklist.extend(ECOMMERCE_CHECKLIST)
    elif page_type == "landing" or page_type == "marketing":
        checklist.extend(MARKETING_LANDING_CHECKLIST)
    # New page types
    elif page_type == "ecommerce_checkout":
        checklist.extend(ECOMMERCE_CHECKOUT_CHECKLIST)
    elif page_type == "user_account":
        checklist.extend(USER_ACCOUNT_CHECKLIST)
    elif page_type == "search_results":
        checklist.extend(SEARCH_RESULTS_CHECKLIST)
    elif page_type == "content_articles":
        checklist.extend(CONTENT_ARTICLES_CHECKLIST)
    
    return checklist


def get_component_checklist(component: str) -> List[Dict[str, Any]]:
    """
    Get checklist items for a specific component.
    
    Args:
        component: Component name (modal, dropdown, tabs, etc.)
    
    Returns:
        List of component-specific checklist items
    """
    return COMPONENT_CHECKLISTS.get(component, [])


def get_all_page_types() -> List[str]:
    """
    Get list of all supported page types.
    Returns both legacy and new page type identifiers.
    """
    return [
        # Legacy types (for backward compatibility)
        "landing", "form", "dashboard", "ecommerce",
        # New professional categories
        "marketing", "forms_data_input", "data_display", 
        "ecommerce_product", "ecommerce_checkout", 
        "user_account", "search_results", "content_articles"
    ]


def get_page_type_display_names() -> Dict[str, str]:
    """
    Get mapping of page type IDs to display names for UI.
    """
    return {
        # Legacy types
        "landing": "Landing Page",
        "form": "Form Page",
        "dashboard": "Dashboard",
        "ecommerce": "E-commerce",
        # New professional categories
        "marketing": "Marketing/Landing Pages",
        "forms_data_input": "Forms & Data Input",
        "data_display": "Data Display & Dashboards",
        "ecommerce_product": "E-commerce: Product Pages",
        "ecommerce_checkout": "E-commerce: Checkout Flow",
        "user_account": "User Account & Profile",
        "search_results": "Search & Results",
        "content_articles": "Content & Articles"
    }


def get_all_components() -> List[str]:
    """Get list of all supported component types."""
    return list(COMPONENT_CHECKLISTS.keys())
