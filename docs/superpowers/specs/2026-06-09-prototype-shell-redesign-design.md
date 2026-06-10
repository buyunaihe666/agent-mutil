# Prototype Shell Redesign Design

Date: 2026-06-09

## Goal

Update the frontend application shell to follow the layout and visual structure in `doc/web.html`: a blue desktop title bar, three-column workspace, and bottom status bar. The redesign should embed the existing conversation, asset, monitor/security, and agent-management modules into one unified workspace instead of keeping the old dark vertical navigation as the primary shell.

## Chosen Approach

Use an **prototype-first refactor**.

The global shell will be rebuilt around the prototype layout while preserving current Redux-backed module behavior. This approach best matches the requested full application-shell redesign and avoids the visual mismatch that would come from wrapping the old dark module pages inside a new header/footer.

Rejected alternatives:

- **Wrapper-only adaptation:** lower risk, but keeps too much of the old dark sidebar and does not match the prototype.
- **Static pixel recreation:** fastest visual result, but drops existing module behavior and is not suitable for full module embedding.

## Layout Architecture

`frontend/src/components/layout/LayoutShell.tsx` becomes the fixed workspace shell:

- Top title bar: blue `DeepSeek V6.2.0 | NEXUS AI` header with app identity and window-control-style icons.
- Main body: three columns using the prototype proportions:
  - Left column: 24% width.
  - Center workspace: 60% width.
  - Right column: 16% width.
- Bottom status bar: API status, log export affordance, and ping/status text.

The primary workspace is not a traditional route navigation sidebar. Instead, modules are embedded into the shell:

- Left column tabs: `会话` and `资产`.
- Center column: conversation/chat workspace remains the main work surface.
- Right column tabs: `性能`, `安全`, and `Agent`.

Existing routes remain as compatibility entry points. Visiting `/assets`, `/agents`, or `/monitor` should use the same shell and activate the corresponding embedded panel where practical instead of rendering an unrelated full-page layout.

## Module Placement

### Conversation

Conversation remains the center of the app:

- Left `会话` tab shows pinned and active conversations plus the `新建对话` button.
- Center area shows messages, assistant task cards, code/action cards, and the input area.
- The visual style follows `doc/web.html`: white background, light gray message/task containers, blue active states, and compact spacing.

`ConversationUI.tsx` should be split or adjusted so reusable parts can render in the new shell without duplicating logic.

### Assets

Assets move into the left column under the `资产` tab:

- Search input.
- File list.
- Selected asset details/preview in a compact column layout.

The asset panel should stop assuming a dark sidebar background when used in the new shell.

### Monitor and Security

The right column owns monitoring:

- `性能` tab shows hardware bars and recent agent activity.
- `安全` tab shows rate limits and audit/security events.

The styling should match the light right panel in the prototype: white background, subtle borders, blue progress bars, and small text.

### Agent Management

Agent management is added to the right column as an `Agent` tab because the prototype has no separate global Agent navigation slot.

The first version should provide a compact management surface:

- Agent list with avatar/name/status/permission summary.
- Entry points for templates and new/edit actions.
- Inline or scrollable editor behavior may reuse existing component logic, but it must fit in the right column without breaking the shell.

## Visual Direction

The first implementation prioritizes the light prototype.

- Primary color: `#2563eb`.
- Success color: `#10b981`.
- Soft page/card background: `#f7f8fa`.
- Borders: light gray similar to `border-gray-200`.
- Avoid Font Awesome CDN. Use existing `lucide-react` icons for equivalent symbols.
- Keep all user-facing strings behind `t()` in `frontend/src/i18n.ts`.

Dark mode state may remain in Redux, but this redesign does not require full dark-mode parity. The new shell can render the light prototype style by default while leaving deeper dark-mode polish for a later pass.

## Responsive Behavior

Respect the project’s existing responsive constraints:

- Hide or collapse the right panel below 1280px.
- Hide or collapse the left panel below 768px.
- Keep the center conversation area usable at smaller widths.

Exact mobile behavior can be minimal for this pass, but the layout must not overflow horizontally in normal desktop widths.

## Component Strategy

Prefer splitting and reusing existing UI logic over creating one large shell file.

Expected component changes:

- `LayoutShell.tsx`: owns the top bar, shell columns, tabs, bottom status bar, and route-to-tab activation.
- `ConversationUI.tsx`: expose or separate conversation list, message area, and input area for shell embedding.
- `AssetPanel.tsx`: support compact left-column light rendering.
- `MonitorPanel.tsx`: support right-column light rendering for performance/security.
- `AgentManagerUI.tsx`: support compact right-column rendering for the `Agent` tab.
- `i18n.ts`: add new strings for prototype labels, status bar text, and tab names.

## Testing

Update frontend tests to match the new shell behavior.

Minimum verification:

- Layout renders the blue title identity text and bottom status bar.
- Left tabs include `会话` and `资产`.
- Right tabs include `性能`, `安全`, and `Agent`.
- Conversation input and new-conversation button still exist.
- Asset, monitor/security, and agent panels can be activated in the shell.
- Run frontend tests with `cd frontend && npm run test` or `make test-frontend`.

## Out of Scope

- Pixel-perfect dark mode.
- Backend/API changes.
- New external icon or CSS CDN dependencies.
- Replacing mock data with live API calls.
- Full mobile drawer behavior beyond preventing layout breakage.
