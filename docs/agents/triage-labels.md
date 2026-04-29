# Triage Labels

The skills speak in terms of five canonical triage roles. This file maps those roles to the local markdown status strings used in this repo.

| Label in mattpocock/skills | Status in this repo | Meaning |
| --- | --- | --- |
| `needs-triage` | `待评估` | Maintainer needs to evaluate this issue |
| `needs-info` | `待补充` | Waiting on reporter for more information |
| `ready-for-agent` | `Agent可做` | Fully specified, ready for an AFK agent |
| `ready-for-human` | `人工处理` | Requires human implementation |
| `wontfix` | `不处理` | Will not be actioned |

When a skill mentions a role, use the corresponding `Status:` value from this table.

Example issue header:

```markdown
# Example issue title

Status: 待评估
```
