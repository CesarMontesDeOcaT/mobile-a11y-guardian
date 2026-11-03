# Mobile Accessibility - WCAG 2.2 AA (Focus & Traversal)

This document defines the normative mobile accessibility rules applicable to screen reader orchestration (TalkBack/VoiceOver).

## WCAG 2.4.3: Focus Order
**Official Definition:** If a web page or screen can be navigated sequentially and the navigation sequences affect meaning or operation, focusable components receive focus in an order that preserves meaning and operability.

**Application in Jetpack Compose (Layout Traversal):**
*   **The Problem (Fragmentation):** Mobile screen readers navigate the screen via swipe gestures. If a logical container (such as a product card, a list item, or a user profile row) is composed of multiple texts and icons, TalkBack traps the user by forcing them to make multiple swipes to read information that should be presented as a single block. This violates the logical focus order and frustrates the user.
*   **The Solution (Merge Semantics):** Visual components that act as a single semantic or interactive unit **MUST** group their semantic children. In Compose, this is achieved by applying `Modifier.semantics(mergeDescendants = true)` to the parent container (`Card`, `Row`, `Column`).

## Evaluation Rules for the AI
1.  **Logical Unit:** If the texts within a layout do not make sense on their own in isolation, or if they force an excessive cognitive and physical effort (too many swipes), they must be merged.
2.  **Clickability:** If a parent container is interactive (`clickable`, `combinedClickable`, `toggleable`), its readable inner children must be merged so that the action announcement encompasses the content's context.
3.  **Findings Justification:** Whenever you detect a fragmented container, classify it as a violation of **WCAG criteria 2.4.3 (Focus Order)** in your report.