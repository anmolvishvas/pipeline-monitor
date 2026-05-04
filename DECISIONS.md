# Pipeline Monitor — Technical Decisions

## 1. System Design

The system models a pipeline as:

- Job → contains multiple ordered Stages
- Stage → contains Logs (events)
- Logs → drive state transitions

This ensures a clear separation between:
- orchestration (Job)
- execution steps (Stage)
- runtime events (LogEvent)

---

## 2. State Management

A strict state machine is enforced:

queued → running → (completed | failed)

Key rules:
- A job can only be triggered if it is `queued` or retried if `failed`
- A stage moves from `pending → running → done/failed`
- Any error log immediately marks the stage as `failed`
- Job status is derived using `compute_status()` from its stages

---

## 3. Transactions

Critical operations use `@transaction.atomic`:

- Job trigger
- Log creation

This prevents:
- race conditions
- partial updates
- inconsistent state transitions

---

## 4. N+1 Query Optimization

The `/jobs/:id/stages/` endpoint avoids N+1 queries by using:

- `select_related`
- `prefetch_related`

This ensures:
- constant query count
- efficient log retrieval per stage

---

## 5. Log-Driven Architecture

Logs are the source of truth for runtime behavior:

- `info` log → starts stage (pending → running)
- `error` log → fails stage → propagates to job

This simulates real-world pipeline systems where logs drive execution flow.

---

## 6. Polling Strategy (Frontend)

Implemented a **single active poller**:

- Only one stage is actively polled at a time
- Polling stops when stage reaches `done` or `failed`
- Prevents memory leaks and redundant API calls

Tradeoff:
- Simpler than WebSockets
- Slight delay vs real-time push systems

---

## 7. Retry Mechanism

Added `retry_count` to Job:

- Incremented when a failed job is retriggered
- Retry allowed only from `failed` state
- Displayed in UI for observability

---

## 8. Error Handling

System enforces:

- Jobs without stages cannot be triggered
- Invalid state transitions are blocked
- API returns appropriate HTTP status codes

---

## 9. Frontend Design

- Card-based job layout
- Expandable stage view
- Status badges for quick visual feedback
- Optimistic UI update on trigger

---

## 10. Tradeoffs

Due to time constraints:

- Used polling instead of WebSockets
- Simulated pipeline execution using backend logic
- Focused more on correctness and architecture than UI polish

---

## 11. Future Improvements

- Replace polling with WebSockets
- Add real-time log streaming
- Add role-based UI restrictions
- Improve retry visualization and history