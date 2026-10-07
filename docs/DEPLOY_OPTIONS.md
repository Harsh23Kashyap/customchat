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
| Status in this repo | Demo path validated by a fresh agent at c261a1b; revised instructions below | Built and tested (95+ tests, `--check`, `--lock-config`) | `render.yaml` written, never deployed | `docs/DEPLOY_AWS.md` + `deploy/` written, never run on AWS | Not built, see below |

## Recommendation
- Client wants it on their laptop or office machine: **B**. It already handles Python checks, a private virtual environment, retries, and a key prompt.
- Client wants a public link with the least work and no server skills: **C**. Configure the app provider first, then use the blueprint and paste the key in Render. The default minimal app is offline Demo (mock); a key alone does not switch it to AI. It needs a paid instance because of the disk; check the current price.
- Client insists on their own AWS: **D**. It is one box, which is the simplest AWS story. Skip E unless they need the static files served from S3.

## E: why the S3 frontend is not the easy path
The web files call the API with relative paths (`/api/...`) and the server sends no CORS headers. A pure S3 frontend on a different address would fail until two things change: an API base address setting in the web code, and CORS headers on the server. Both are small, neither is built. A simpler option with the same result is CloudFront in front of S3 and EC2 with `/api/*` routed to the box, which needs no code change but more console setup. For a chat-only app one nginx box (D) is easier.

## A: the "just give this prompt" option
The client's coding agent runs the local Demo path below. A fresh agent validated the core setup, health, Demo answer and configuration lock at commit c261a1b. The instructions below clarify the gaps found in that run. This is local-only, not public deployment.

```
Set up CustomChat locally in offline Demo, using no API keys.

1. Pick a new writable destination folder. Clone the main branch:
   git clone --branch main https://github.com/Harsh23Kashyap/customchat.git <destination>
   cd <destination>
   Report the checked-out commit. Do not overwrite an existing folder.

2. Start initial setup from that folder:
   python3 setup_and_run.py --no-key-prompt --no-browser --port 8080
   Wait for environment creation and pip installation to finish. This command then
   keeps the server running and blocks the terminal. Use a second terminal or a
   managed background process, retaining its logs and process ID.
   If your shell times out, inspect the process, logs and health first. A timeout
   does not prove setup failed. If still running, keep using it; if stopped, rerun
   the same command to reuse finished setup. Do not start duplicate servers.

3. Read the exact URL printed after "Starting CustomChat at". Do not assume 8080:
   the launcher tries up to 20 ports and may print 8081 or another free port.
   While that server is running, require GET <printed-URL>/api/health to return 200.
   Stop this initial server cleanly with Ctrl+C (or SIGINT to its managed process)
   and confirm it has exited before starting another.
   Run python3 setup_and_run.py --check. This checks installation diagnostics only;
   it does not verify chat or the browser interface.

4. Demo is the default for this quickstart; do not change provider or ask for keys.
   Start the final local chat-only server:
   python3 setup_and_run.py --no-key-prompt --no-browser --port 8080 --lock-config
   Read its newly printed URL. --lock-config hides Configuration, but creates no
   public deployment. To unlock later, stop it and restart without --lock-config
   (and without CUSTOMCHAT_CONFIG=off in the environment).

5. At that exact printed URL, check health 200 and confirm the provider is mock
   using /api/config. Ask "What is CustomChat?" in the chat. Require a nonempty
   answer that uses the local Demo passages and numbered source citations.
   Confirm /settings.html and /api/settings return 404 while chat remains usable.
   Open the printed URL and inspect the chat in a browser if you can. If you only
   checked the API, report "API-verified; browser UI not inspected", not UI success.

6. Leave the final server running for me only if your environment can keep it
   alive after your work ends. Report the exact URL, process ID, checked-out
   commit, completed checks and any missing checks. Tell me how to stop it:
   Ctrl+C in its terminal or SIGINT to the managed process. If you cannot keep it
   running, stop it cleanly and say so; give the command above to restart it.

If I later want AI instead of Demo, stop and ask which provider and model I want.
Before locking, either edit apps/minimal/app.yaml's provider block following
README.md's "Pick a model", or run unlocked, configure on the Model tab, then
stop and restart locked. Keys belong in the named environment variable or private
local secret store, never YAML, git, logs or chat. Do not solicit a key in chat;
let me enter it privately on my own machine. A key alone does not change mock.

Do not create cloud accounts, buy anything, expose ports to the internet or deploy
publicly. Do not claim success for any check you could not perform.
```
Limits: it depends on the agent, it cannot produce a public URL without more steps, and the client must trust the agent with a shell.


## Validation boundary
The fresh-agent test at c261a1b verified the local Linux Demo core path through API checks. It did not establish browser UI verification or test the revised wording above in another fresh run. Docker, real Render/AWS deployment, HTTPS provisioning and real Windows/WSL behavior remain unverified here. Written templates and unit tests do not replace those external checks. Timing estimates in the table are estimates, not tested guarantees.
