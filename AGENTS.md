# Project notes

Streamlit (single file `app.py`) survey app that reads/writes a Supabase table
named `project` via `supabase-py`. `requirements.txt` is unpinned.

## Running here

```bash
docker compose -f docker-compose.base44.yml up -d
docker compose -f docker-compose.base44.yml ps          # everything healthy
curl http://localhost:3000/_stcore/health               # -> ok
docker compose -f docker-compose.base44.yml logs -f web
```

Web entry point: host port 3000 (`streamlit run app.py`, `--server.runOnSave`
+ polling watcher, source bind-mounted at `/app`, so edits apply without a
rebuild). Python deps are pip-installed on every container start (there is no
lockfile), which adds ~30s to the first boot.

## Non-obvious things

- **Streamlit cannot read env vars as secrets.** It only loads
  `<cwd>/.streamlit/secrets.toml`. `dev/supabase-local/write_secrets.py`
  therefore writes that file at startup into `/tmp/st/.streamlit/` (outside the
  repo) from `SUPABASE_URL` / `SUPABASE_KEY`, and the process runs with cwd
  `/tmp/st`. `app.py` uses `st.secrets[...]`, not `os.environ`.
- **Local Supabase stand-in.** A hosted Supabase project is not required to run:
  - `db` — postgres:16, seeded by `dev/supabase-local/init.sql` (roles
    `anon`/`authenticator` + the `project` table + 10 sample rows). The init
    script only runs on a **fresh** `db-data` volume.
  - `rest` — PostgREST (the engine behind Supabase's REST API). The image ships
    no shell or HTTP client, so it has no healthcheck of its own; its liveness
    is covered by the `rest-proxy` probe.
  - `rest-proxy` — nginx that rewrites `/rest/v1/<table>` → PostgREST
    `/<table>`, because `supabase-py` always prefixes `/rest/v1`. `/healthz`
    proxies through to PostgREST.
  - `.env.base44-defaults` points `SUPABASE_URL` at the proxy and holds the dev
    `PGRST_JWT_SECRET`; the startup script signs a local `anon` JWT with it when
    no `SUPABASE_KEY` is provided. Real `SUPABASE_URL`/`SUPABASE_KEY` delivered
    in `/run/base44/app.env` are read **after** the defaults and win.
- **`server.enableCORS=false`** is set in the compose command: the preview proxy
  forwards a sandbox `Host` while the browser sends the public `Origin`, which
  Streamlit's origin check would reject, killing the websocket. XSRF protection
  stays enabled. This lives only in the Base44 compose file, not in app code.
- Table shape used by `app.py` (`public.project`): `id` (text, `S_001` style),
  `grade_class`, `study_hours`, `academic_score`, `sleep_hours`, `tired_score`,
  `favorite_subject`. Next id is computed as max+1 by the app.
- `init.sql` seeds sample rows so the "데이터 분석" charts render on first boot.

## Verifying a change

Load `/`, submit the form (the "소중한 의견 감사합니다." banner should appear),
then open "데이터 분석" in the sidebar: 총 응답 should increase by one. Delete any
test row when done (the app has no delete UI):

```bash
docker compose -f docker-compose.base44.yml exec -T web python -c "
import pathlib, tomllib, urllib.request
s = tomllib.loads(pathlib.Path('/tmp/st/.streamlit/secrets.toml').read_text())
h = {'apikey': s['SUPABASE_KEY'], 'Authorization': 'Bearer ' + s['SUPABASE_KEY']}
urllib.request.urlopen(urllib.request.Request(s['SUPABASE_URL'] + '/rest/v1/project?id=eq.S_011', headers=h, method='DELETE'))
"
```

There is no test suite or linter in this repo.
