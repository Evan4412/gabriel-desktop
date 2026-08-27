# gabriel-desktop — Code Audit Summary

**Net result: −1,304 lines / +61 lines across 73 files** (3 local commits on `main`, nothing pushed).
All verified: `tsc --noEmit --noUnusedLocals` clean, `next build` succeeds, `next lint` clean,
`knip` reports zero dead code, gateway `pytest` 13/13 pass.

## Deleted files (23)

| Category | Files |
|---|---|
| Unused React components | `common/sparkline.tsx`, `common/stat-card.tsx`, `ui/tabs.tsx`, `ui/tag.tsx`, `ui/tooltip.tsx` |
| Dead realtime layer (never imported by any feature) | `services/realtime/` — index, types, mock-transport, mock-scripts, sse-transport, websocket-transport (6 files, ~430 lines) |
| Dead service | `services/events.ts` (only consumer of the realtime layer) |
| Dead hook | none deleted whole; `useNotifications` export removed from `hooks/use-notifications.ts` |
| Build artifact tracked in git | `apps/web/tsconfig.tsbuildinfo` (untracked + added `*.tsbuildinfo` to `.gitignore`) |
| Redundant doc formats | `docs/*.docx`, `docs/*.pdf` (kept the canonical `.md` sources) |
| Unused public assets | `placeholder-logo.png/.svg`, `placeholder-user.jpg`, `placeholder.jpg/.svg`, `apple-icon.png`, `icon-dark-32x32.png`, `icon-light-32x32.png` (only `/icon.svg` is referenced) |

## Web app (`apps/web`) — dead code removal

- **Unused exported functions removed** (knip-verified, none had any caller):
  `auth.listDevPrincipals`, `auth.loginWithDevPrincipal`, `chat.updateConversation`,
  `chat.deleteConversation`, `documents.getDocument`, `knowledge.deleteKnowledgeSource`,
  `knowledge.attachDocument`, `memory.getMemory`, `organizations.getOrganization`,
  `resources.getResource`, `tools.getTool`, `agents.updateAgentConfig`,
  `notifications.listNotifications`, `useUpdateAgentConfig`, `useDeleteConversation`,
  `useNotifications`, `navigation.getWorkspace`.
- **gateway-client.ts**: removed deprecated `GATEWAY_URL` alias, dead `isMock()`/`LiveDomain`,
  legacy `NEXT_PUBLIC_GATEWAY_URL` fallback; un-exported internals (`API_URL`,
  `refreshAccessToken`, `SSEFrame`).
- **Services barrel** (`services/index.ts`): dropped dead re-exports (`events`, `GATEWAY_URL`,
  `API_URL`, `USE_MOCK`, dashboard types).
- **Mock seed data** (`services/mock/data.ts`): removed unused `organizations`, `devPrincipals`,
  `messagesByConversation`, `notifications` datasets (~120 lines).
- **Types**: deleted fully-unused types (`AgentRun`, `ConversationCreateDto`, `ChatStreamEventDto`,
  `Page`, `LoadState`, `NotificationChannel`, `DevPrincipalOption`); un-exported ~15 types only
  used within their own module (`MessageRole`, `Role`, `User`, `SafetyLevel`, `Theme`, …).
- **UI primitives**: removed unused `CardDescription`/`CardFooter`, `DropdownMenuCheckboxItem`/
  `DropdownMenuGroup`, `DialogTrigger`/`DialogClose`; un-exported internal-only
  `badgeVariants`/`buttonVariants`/`Command`/`DialogPortal`/`DialogOverlay`.
- **Unused imports** stripped everywhere (verified with `--noUnusedLocals`).
- **Dependencies removed**: `@radix-ui/react-tabs`, `@radix-ui/react-tooltip`.

## Python gateway (`apps/gateway`)

- **core_specs.py** (152 → 88 lines): dropped unused `CoreSpecService` back-compat alias,
  unused context-manager/`close()` lifecycle (client lives for the process), `__all__`,
  and section-divider comment noise; module-level route prefix constant.
- **main.py**: replaced the hand-rolled 15-line `to_payload()` field loop with pydantic's
  built-in `model_dump(by_alias=True, exclude_none=True)` — identical output, 1 line.
- **settings.py**: removed the never-read `environment` setting.
- **`__init__.py`**: fixed stale docstring (claimed the gateway *imports* gabriel-core; it's HTTP-only).
- **pyproject.toml**: removed unused deps `pydantic-settings` and `asgi-lifespan`; relaxed the
  stale `fastapi<0.116` pin — it made the test suite un-runnable because gabriel-core's routers
  require a newer FastAPI (`204 must not have a response body` assert, fixed upstream in FastAPI).
  With the pin relaxed, all 13 tests pass.

## Kept deliberately

- `eslint`/`eslint-config-next` (knip false positive — used by `next lint`).
- `USE_MOCK` mock mode + remaining mock datasets (live dev feature for dashboard/memory/resources/search).
- `SpecificationNotFoundError` (exercised by tests, meaningful 404 mapping).
- Feature views (tools/agents/chat) are large but live — no dead branches found; not rewritten
  to avoid behavioral risk without a UI test suite.

## Note for gabriel-core

Two pre-existing issues surfaced while running the gateway tests against gabriel-core:
its routers crash on FastAPI <0.116x-era asserts only when *old* fastapi is installed (fine), and
`jsonschema` + `pyjwt` + `aiosqlite` are imported but not declared in gabriel-core's dependencies.
To address in the gabriel-core audit.
