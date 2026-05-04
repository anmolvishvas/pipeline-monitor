# Technical Decisions — Pipeline Monitor

## 1. N+1 Query Optimization

The `/jobs/:id/stages/` endpoint was optimized to avoid N+1 queries.

Instead of querying logs per stage (which would result in multiple DB hits),
I used:

- `prefetch_related('logs')` to fetch all logs in a single query
- `select_related('job')` where needed

This ensures:
- predictable query count
- better performance as data scales

---

## 2. Single Active Poller Design

The frontend implements a strict **single-active-poller pattern**.

Key design:
- A `ref` (`activeStageId`) tracks the currently expanded stage
- A `stopFn` ref stores the cleanup function of the active poll
- A `watch` on `activeStageId`:
  - always calls previous `stopFn()` before starting a new poll
  - starts a new interval only for the selected stage

Polling rules:
- Poll every 5 seconds
- Only poll if stage status is `running`
- Automatically stop when status becomes `done` or `failed`

This prevents:
- memory leaks
- duplicate polling
- unnecessary API calls

---

## 3. Tradeoff: Polling vs WebSockets

I chose **polling** over WebSockets due to simplicity and time constraints.

Advantages:
- easier to implement and debug
- no additional infrastructure required

Tradeoffs:
- slight delay (up to polling interval)
- less efficient than real-time push

With more time, I would replace polling with WebSockets to:
- achieve real-time updates
- reduce redundant network requests