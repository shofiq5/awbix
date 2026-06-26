Enhance AWB Inventory Workbench.

Goal:
Build a highly user-friendly, fast, and production-safe AWB management workbench with powerful filtering, bulk operations, and minimal-click workflows while maintaining all existing functionality.

Core UX Principles:

* Extremely user-friendly and intuitive
* Minimal clicks for all operations
* Fast bulk processing (single/multi/range)
* Clear status visibility at all times
* Production-safe (no breaking changes)
* Maintain backward compatibility

Functional Requirements:

1. Series Selection & Loading

* User selects an AWB generated series from dropdown/search.
* System loads all AWBs belonging to the selected series.
* Support large datasets with server-side pagination/lazy loading.
* Preserve selected series context across actions.

2. AWB Listing & Visibility
   Display AWBs in a structured grid/workbench with:

* AWB Number
* Status (Available, Assigned, Withdrawn, Hold, Blacklisted, etc.)
* Assigned To
* Date Created
* Last Updated
* Optional metadata columns

Enhancements:

* Color-coded status badges
* Sortable columns
* Quick search (instant filter)
* Column show/hide preferences
* Compact / normal view toggle

3. Filtering System
   Provide fast filters:

* Status filter (multi-select)
* Series filter
* Date range
* Customer / Carrier / Branch
* Assigned user
* Free-text AWB search
* Range filter (start–end AWB)

Saved UX shortcuts:

* Recently used filters
* Favorite filters/series

4. Selection Model (Critical)
   Users can select AWBs via:

* Single selection
* Multi-selection (checkbox)
* Select all filtered results
* Range selection (start AWB → end AWB)

Validation:

* Range must belong to same series
* Only existing AWBs included
* Skip invalid/non-existent AWBs automatically (with warning summary)

5. Bulk Action System
   From selected AWBs, user can perform:

Core Actions:

* Assign
* Withdraw
* Hold
* Release Hold
* Blacklist
* Remove Blacklist
* Change Status
* Transfer ownership

Optional Actions:

* Export (CSV/Excel)
* Print AWB list
* Audit view

UX Requirements:

* Sticky bulk action toolbar
* Context menu (right-click actions)
* Keyboard-friendly shortcuts
* Confirmation modal for destructive actions
* Progress indicator for bulk operations
* Post-action success/failure summary
* Real-time UI update without reload

6. Assignment Workflow (Enhanced)
   When assigning AWBs:

* Assign to Customer / Agent / Branch / User
* Optional remarks field
* Pre-confirmation preview of selected AWBs
* Bulk assignment support with batching

7. Audit & Tracking
   Maintain full history:

* Action type
* User
* Timestamp
* Previous status → New status
* Remarks

UI Feature:

* Quick “View History” panel per AWB or bulk selection

8. Performance Requirements

* Server-side filtering & pagination
* Batch DB updates for bulk operations
* Avoid full page reloads
* Optimize for high-volume AWB datasets
* Debounced search inputs

9. Operational Safety

* No breaking changes to existing AWB logic
* All enhancements additive only
* Production-safe execution
* Proper error handling per batch item
* Partial success support with clear reporting

10. Additional UX Enhancements (Recommended)

* Dashboard counters by status
* Undo last action (safe actions only)
* Export filtered dataset
* Mobile/tablet responsive design
* Dark mode compatibility
* Permission-based action visibility
* Activity log shortcut panel

System Behavior Rules:

* Do NOT modify existing working workflows unless required
* Ensure backward compatibility
* Optimize for high-speed operations
* Assume production environment constraints

Output Constraint:

* NO CHATTY FILLER
* CODE ONLY for implementation requests
* DO NOT generate tests unless explicitly requested
* Assume standard engineering context and proceed directly
