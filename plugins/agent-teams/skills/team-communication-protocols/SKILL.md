---
name: team-communication-protocols
description: >
  Structured messaging protocols for agent team communication including message
  type selection, plan approval, shutdown procedures, and anti-patterns to avoid.
  Use this skill when establishing communication norms for a newly spawned team,
  when deciding which message type to use (broadcast was removed; address
  recipients individually), when a team-lead needs to review and approve an
  implementer's plan before work begins, when
  orchestrating a graceful team shutdown after all tasks are complete, or when
  debugging why teammates are not coordinating correctly at integration points.
version: 1.1.1
---

# Team Communication Protocols

Protocols for effective communication between agent teammates, including message type selection, plan approval workflows, shutdown procedures, and common anti-patterns to avoid.

## When to Use This Skill

- Establishing communication norms for a new team
- Choosing between message types (message, shutdown_request; broadcast was removed in 2026)
- Handling plan approval workflows
- Managing graceful team shutdown
- Discovering teammate identities and capabilities

## Message Type Selection

### `message` (Direct Message) -- Default Choice

Send to a single specific teammate:

```json
{
  "type": "message",
  "recipient": "implementer-1",
  "content": "Your API endpoint is ready. You can now build the frontend form.",
  "summary": "API endpoint ready for frontend"
}
```

**Use for**: Task updates, coordination, questions, integration notifications.

### `broadcast` -- Removed in 2026

Broadcast was removed from `SendMessageTool` in 2026. There is no built-in fan-out anymore.

**To reach multiple teammates**, send one `message` per recipient by name. For critical shared-resource changes affecting everyone (e.g., updated interface contract), iterate the team config in `~/.claude/teams/{team-name}/config.json` and emit one targeted message per teammate name.

This is the same network cost as the old broadcast (broadcasts already expanded to N messages internally), but it is now explicit, which makes coordination logic auditable.

### `shutdown_request` -- Graceful Termination

Request a teammate to shut down:

```json
{
  "type": "shutdown_request",
  "recipient": "reviewer-1",
  "content": "Review complete, shutting down team."
}
```

The teammate responds with `shutdown_response` (approve or reject with reason).

## Communication Anti-Patterns

| Anti-Pattern                            | Problem                                  | Better Approach                        |
| --------------------------------------- | ---------------------------------------- | -------------------------------------- |
| Trying to use the removed `broadcast`   | Tool returns an error in 2026+           | Send one `message` per recipient       |
| Sending JSON status messages            | Not designed for structured data         | Use TaskUpdate to update task status   |
| Not communicating at integration points | Teammates build against stale interfaces | Message when your interface is ready   |
| Micromanaging via messages              | Overwhelms teammates, slows work         | Check in at milestones, not every step |
| Using UUIDs instead of names            | Hard to read, error-prone                | Always use teammate names              |
| Ignoring idle teammates                 | Wasted capacity                          | Assign new work or shut down           |

## Plan Approval Workflow

When a teammate is spawned with `plan_mode_required`:

1. Teammate creates a plan using read-only exploration tools
2. Teammate calls `ExitPlanMode` which sends a `plan_approval_request` to the lead
3. Lead reviews the plan
4. Lead responds with `plan_approval_response`:

**Approve**:

```json
{
  "type": "plan_approval_response",
  "request_id": "abc-123",
  "recipient": "implementer-1",
  "approve": true
}
```

**Reject with feedback**:

```json
{
  "type": "plan_approval_response",
  "request_id": "abc-123",
  "recipient": "implementer-1",
  "approve": false,
  "content": "Please add error handling for the API calls"
}
```

## Shutdown Protocol

### Graceful Shutdown Sequence

1. **Lead sends shutdown_request** to each teammate
2. **Teammate receives request** as a JSON message with `type: "shutdown_request"`
3. **Teammate responds** with `shutdown_response`:
   - `approve: true` -- Teammate saves state and exits
   - `approve: false` + reason -- Teammate continues working
4. **Lead handles rejections** -- Wait for teammate to finish, then retry
5. **After all teammates shut down** -- Call `TeamDelete` to remove team resources

### Handling Rejections

If a teammate rejects shutdown:

- Check their reason (usually "still working on task")
- Wait for their current task to complete
- Retry shutdown request
- If urgent, user can force shutdown

## Teammate Discovery

Find team members by reading the config file:

**Location**: `~/.claude/teams/{team-name}/config.json`

**Structure**:

```json
{
  "members": [
    {
      "name": "security-reviewer",
      "agentId": "uuid-here",
      "agentType": "team-reviewer"
    },
    {
      "name": "perf-reviewer",
      "agentId": "uuid-here",
      "agentType": "team-reviewer"
    }
  ]
}
```

**Always use `name`** for messaging and task assignment. Never use `agentId`, role names, or unsuffixed aliases directly. If a teammate was spawned as `team-lead-2`, send to `team-lead-2`, not `team-lead`.

## Troubleshooting

**A teammate is not responding to messages.**
Check the teammate's task status. If it is idle, it may have completed its task and is waiting to be assigned new work or shut down. If it is still active, it may be mid-execution and will process messages once the current operation finishes.

**A teammate says it cannot see SendMessage.**
Check the teammate agent's `tools:` frontmatter. Agent Teams communication tools such as `SendMessage`, `TaskList`, `TaskGet`, and `TaskUpdate` must be listed explicitly when an agent uses a restricted tool allowlist.

**The lead is trying to use `broadcast` and getting tool errors.**
Broadcast was removed from `SendMessageTool` in 2026. Update the lead's instructions to address recipients individually. For shared-resource updates, iterate the team config and emit one `message` per teammate name.

**A teammate rejected a shutdown request unexpectedly.**
The teammate is still working. Check the rejection reason in the `shutdown_response` content field, wait for the work to finish, then retry. Never force-terminate a teammate that has unsaved work.

**A plan_approval_request arrived but the request_id is missing.**
The teammate called `ExitPlanMode` without the required request context. Have the teammate re-enter plan mode, complete exploration, and call `ExitPlanMode` again. The `request_id` is generated automatically by the plan mode system.

**Two teammates are waiting on each other and neither is making progress.**
This is a deadlock: both are blocked waiting for the other to finish first. The lead should send a direct message to one teammate with a stub or partial result so it can unblock and proceed.

## Related Skills

- [team-composition-patterns](../team-composition-patterns/SKILL.md) -- Select agent types and team size before establishing communication norms
- [parallel-feature-development](../parallel-feature-development/SKILL.md) -- Use communication protocols to coordinate integration handoffs between parallel implementers
