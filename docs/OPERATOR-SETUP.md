# Operator Setup — Credentials & One-Time Configuration

Two secrets are needed that this repo deliberately does NOT contain.
Do these once; everything else is committed and reproducible.

## 1. Model provider

Verified catalog (no native OpenRouter): `openai`, `anthropic`, `google-gemini`,
`fireworks`, `zai`, `moonshot`, `alibaba`, `together`, `custom`.

**Option A — OpenRouter via Custom Provider:** Settings → Models →
**Add Custom Provider** → name `openrouter`, type OpenAI-compatible,
base URL `https://openrouter.ai/api/v1`, paste your
[OpenRouter key](https://openrouter.ai/settings/integrations).

**Option B — native key:** Configure any listed provider directly if you hold
its key.

Recommended default: a strong tool-calling model (`anthropic/claude-sonnet-4`
class via either route). Free models tend to fail multi-hop MCP tool loops.

## 2. Sandbox provider (Daytona)

1. Create account + API key at https://daytona.io
2. TrueForge → **Settings → Sandbox providers** → select Daytona → paste key → Save
3. Sanity test in chat: ask the agent to run `print("sandbox ok")`.

## 3. Compose & save the agent (no code, all UI)

New Chat → configure:
- Model: your OpenRouter model
- Tools/connectors: enable `kubernetes`
- Skills: import `skills/incident-triage/SKILL.md` from this repo
  (Settings → Skills → import from GitHub/local path)
- Capabilities: enable sandbox + dynamic sub-agents
- System instructions: paste the snippet at the bottom of
  [docs/findings-schema.md](findings-schema.md)

Click **Save Agent** → name it `K8s Sentinel`. It now lives in the Agents Library.

## Local services started during the build (on-demand, not auto-start)

| Service | Command | Port |
|---|---|---|
| TrueForge | `npx @truefoundry/trueforge` | 8790 |
| Kubernetes MCP | `kubernetes-mcp-server --port 9236 --bind-address 127.0.0.1 --kubeconfig ~/.kube/config --disable-destructive` | 9236 |
| kind cluster | `kind create cluster --name sentinel-demo --config infra/kind-config.yaml` | — |

All are manual-start/manual-stop. Nothing here runs at boot.
