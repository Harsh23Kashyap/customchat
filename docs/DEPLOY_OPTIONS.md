# Ways to put CustomChat online: pick one

Written comparison only. Nothing here was deployed. Prices and free tiers change, so check each provider's pricing page before choosing.

| | A. "Just give this prompt" | B. One-liner (`python3 setup_and_run.py`) | C. Render blueprint | D. EC2 on their own AWS | E. EC2 + S3 frontend |
|---|---|---|---|---|---|
| Who does the work | The client pastes a prompt into their own coding agent | The client runs one command on any machine | The client clicks through Render | A technical person follows the guide | Same, plus two code changes |
| Time to live | 5-15 min, depends on the agent | 2-5 min, local only (not public) | ~10 min | 1-2 h first time | half a day |
| Public URL | Depends on the prompt | No (localhost) unless tunnelled | Yes, automatic HTTPS | Yes, needs nginx + certificate | Yes |
| Data survives restarts | Depends | Yes (local file) | Yes with the disk in `render.yaml` | Yes (MySQL or SQLite on the box) | Yes |
| Client owns the infrastructure | Yes | Yes | Their Render account | Their AWS account | Their AWS account |
| Ongoing care | Low | None | Low | Patching, backups, certificate | Same as D |
| Status in this repo | Prompt below, untested with real agents | Built and tested (95+ tests, `--check`, `--lock-config`) | `render.yaml` written, never deployed | `docs/DEPLOY_AWS.md` + `deploy/` written, never run on AWS | Not built, see below |

## Recommendation
- Client wants it on their laptop or office machine: **B**. It already handles Python checks, a private virtual environment, retries, and a key prompt.
- Client wants a public link with the least work and no server skills: **C**. Configure the app provider first, then use the blueprint and paste the key in Render. The default minimal app is offline Demo (mock); a key alone does not switch it to AI. It needs a paid instance because of the disk; check the current price.
- Client insists on their own AWS: **D**. It is one box, which is the simplest AWS story. Skip E unless they need the static files served from S3.

## E: why the S3 frontend is not the easy path
The web files call the API with relative paths (`/api/...`) and the server sends no CORS headers. A pure S3 frontend on a different address would fail until two things change: an API base address setting in the web code, and CORS headers on the server. Both are small, neither is built. A simpler option with the same result is CloudFront in front of S3 and EC2 with `/api/*` routed to the box, which needs no code change but more console setup. For a chat-only app one nginx box (D) is easier.

## A: the "just give this prompt" option
Idea: the client's own coding agent does B or D for them. Untested, so treat it as a draft.

```
Set up CustomChat for me.
1. Clone https://github.com/Harsh23Kashyap/customchat and open the folder.
2. Run: python3 setup_and_run.py --no-key-prompt --no-browser (first start creates the environment). Check /api/health, then stop it. Run python3 setup_and_run.py --check.
3. Ask whether I want offline Demo or an AI provider. For AI, configure the app provider before --lock-config and ask me to enter any key privately. A key alone does not change the default mock provider. Do not print keys or store them in the repo.
4. Start it in chat-only mode: python3 setup_and_run.py --port 8080 --lock-config
5. Open http://localhost:8080 and tell me when the chat answers.
Do not create cloud accounts, buy anything, or open ports to the internet unless I say so.
```
Limits: it depends on the agent, it cannot produce a public URL without more steps, and the client must trust the agent with a shell.
