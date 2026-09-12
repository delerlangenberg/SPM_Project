# SPM Prusa Local Construction Handbook

This is an unprotected, local-only handbook for the SPM Prusa project. It does
not use ChatGPT sign-in, workspace identity, accounts, a database or remote
storage.

## Run locally

Requirements: Node.js 22.13 or newer.

The easiest option is to double-click `OPEN HANDBOOK.bat`. It starts the local
handbook server when required and opens the correct page automatically.

`index.html` is a readable offline index and safe fallback that can also be
opened directly.

```powershell
Set-Location C:\SPM_Prusa_Project\web\project_handbook
npm run dev
```

Open the local URL printed by the development server. To verify a production
build locally:

```powershell
npm test
```

## Maintained content

- `app/page.tsx` contains the handbook structure and construction sequence.
- `app/globals.css` contains the responsive presentation.
- `public/project/` contains selected project evidence images.
- `public/source/` contains copies of the maintained wiring and commissioning
  references used by the handbook.

The authoritative editable engineering sources remain under
`C:\SPM_Prusa_Project\docs` and
`C:\SPM_Prusa_Project\firmware\crtouch_edge_controller\docs`.

This interface is intended for trusted internal networks. It has no access
control; do not expose it directly to the public internet.
