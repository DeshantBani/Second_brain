# Office add-in manifest (scaffold)

This is configuration only - no app code lives here. `manifest.json` is a **unified
manifest for Microsoft 365** (not the older per-host XML manifest) covering both an
Outlook mail-read task pane and a Word task pane, both pointing at routes inside the
same Next.js app that serves the main web UI (`/addin/outlook`, `/addin/word`).

Per the build plan (Section 9 / Phase 5), this pass ships those two routes as
structural stubs - they share the web app's components and API client, but are not
wired to `Office.js` (no `Office.context.ui.displayDialogAsync` sign-in flow, no
`Office.context.ui.messageParent` token bridge, no mail-body seeding, no
insert-into-document action). `api/app/routers/addin.py`'s `/addin/session` endpoint is
the auth bridge a real integration would call from that dialog.

To sideload this manifest during development once the stub routes are built out:

1. Replace `localhost:3000` above with wherever the frontend is actually reachable
   from the Office client (a real device/VM may need a tunreled HTTPS URL - Office
   add-ins require HTTPS outside of localhost on some hosts).
2. Add real PNG icons under `assets/` (referenced above but not included in this pass).
3. In Outlook or Word: **Get Add-ins → My Add-ins → Add a Custom Add-in → Upload
   Manifest File**, and select `manifest.json`.

No AppSource listing or admin-center deployment is needed for personal/internal use at
this scale - sideloading is sufficient.
