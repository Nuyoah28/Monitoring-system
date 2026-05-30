# Agent Deployment

The repo includes `agent-api.service` as a systemd template for server
deployment.

Default runtime limits for the 8G server:

- `MemoryMax=1536M`
- `TasksMax=256`
- `AGENT_MAX_WORKERS=4`

Install example:

```bash
sudo cp ReAct_agent/agent-api.service /etc/systemd/system/agent-api.service
sudo systemctl daemon-reload
sudo systemctl enable --now agent-api.service
```

Before enabling it, adjust these fields in the service file to match the server:

- `WorkingDirectory`
- `ExecStart`
- `User`
