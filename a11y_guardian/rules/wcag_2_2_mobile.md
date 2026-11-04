# Mobile Accessibility - WCAG 2.2 AA (Jetpack Compose Edition)

This document defines the normative mobile accessibility rules applicable to screen reader orchestration (TalkBack/VoiceOver) and visual accessibility in Jetpack Compose applications.

## Principle 1: Perceivable
Information and user interface components must be presentable to users in ways they can perceive.

### WCAG 1.1.1: Non-text Content (Text Alternatives)
**Official Definition:** All non-text content that is presented to the user has a text alternative that serves the equivalent purpose.
**Compose Application (Meaningful Descriptions):**
*   **The Problem:** Screen readers cannot interpret images or icons visually. If an `Icon` or `Image` lacks a description, TalkBack will announce it as "Unlabelled" or ignore it entirely, hiding functionality from the user.
*   **The Solution:** Every `Icon` and `Image` MUST have a `contentDescription`.
    *   If the image conveys information or indicates an action (e.g., a "Save" icon), `contentDescription` must be a localized string (e.g., `stringResource(...)`).
    *   If the image is purely decorative and offers no semantic value, it MUST explicitly define `contentDescription = null` so TalkBack skips it.

### WCAG 1.3.1: Info and Relationships
**Official Definition:** Information, structure, and relationships conveyed through presentation can be programmatically determined.
**Compose Application (Semantic Headings):**
*   **The Problem:** Visual users can identify sections of a screen by looking at large, bold text. Blind users rely on TalkBack's "Heading" navigation mode to jump between sections. If visual headings aren't programmatically marked, this navigation breaks.
*   **The Solution:** Any `Text` composable that acts as a title for a section or screen must include `Modifier.semantics { heading() }`.

[//]: # (### WCAG 1.4.4: Resize text)

[//]: # (**Official Definition:** Text can be resized without assistive technology up to 200 percent without loss of content or functionality.)

[//]: # (**Compose Application &#40;Scalable Pixels&#41;:**)

[//]: # (*   **The Problem:** Hardcoding text sizes prevents the OS-level font scaling features from working, severely impacting users with low vision.)

[//]: # (*   **The Solution:** Font sizes in `Text` components or `TextStyle` definitions MUST always use `.sp` &#40;scalable pixels&#41;. Using `.dp` for `fontSize` or `lineHeight` is a direct violation.)

---

## Principle 2: Operable
User interface components and navigation must be operable.

### WCAG 2.4.3: Focus Order
**Official Definition:** If a Web page [or screen] can be navigated sequentially and the navigation sequences affect meaning or operation, focusable components receive focus in an order that preserves meaning and operability.
**Compose Application (Layout Traversal & Merge Semantics):**
*   **The Problem (Fragmentation):** Mobile screen readers read the screen via linear swipes. If a logical container (like a product card, a list item, or a user profile row) is built using multiple texts and icons, TalkBack traps the user, forcing them to swipe multiple times to read information that should belong to a single block.
*   **The Solution:** Visual components that act as a single semantic or interactive unit MUST group their semantic children. Apply `Modifier.semantics(mergeDescendants = true)` to the parent container (`Card`, `Row`, `Column`) so TalkBack announces the entire group in a single swipe.

[//]: # (### WCAG 2.5.8: Target Size &#40;Minimum&#41;)

[//]: # (**Official Definition:** The size of the target for pointer inputs is at least 24 by 24 CSS pixels. *&#40;Note: Android's Material Design strictly requires a minimum of 48x48 dp for interactive elements&#41;.*)

[//]: # (**Compose Application &#40;Touch Targets&#41;:**)

[//]: # (*   **The Problem:** Tiny clickable elements are difficult to activate for users with motor disabilities.)

[//]: # (*   **The Solution:** Custom clickable composables &#40;e.g., a `Box` or `Icon` with `.clickable`&#41; must ensure they meet the minimum touch target size. This is usually enforced by wrapping them in standard components &#40;like `IconButton`&#41; or explicitly applying `Modifier.minimumInteractiveComponentSize&#40;&#41;`.)

---

## AI Evaluation Rules
1.  **Rule Mapping:** Whenever you detect an accessibility gap in the code, you MUST explicitly cite the specific WCAG rule (e.g., "WCAG 1.1.1 (Non-text Content)", "WCAG 2.4.3 (Focus Order)") in your `issue` description.
2.  **Surgical Fixes:** Provide the exact, minimal `suggested_code` required to fix the violation without altering surrounding logic or duplicating existing modifiers.
3.  **Prioritization:** Ensure interactive elements (clickable items) are properly labeled (1.1.1), adequately sized (2.5.8), and syntactically grouped (2.4.3).