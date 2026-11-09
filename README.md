# SmartTime — SQLite-backed staff attendance and IT admin console

- `index.html` is the staff attendance home page.
- `admin.html` is the IT administrator console. Its dashboard is hidden until the admin login succeeds and hidden again after sign-out.
- `server.py` serves the pages and the `/api/db` endpoints.
- `smarttime.sqlite3` is created automatically in this folder when the server first starts. Users, attendance records, and workplace settings are stored in SQLite tables; browser `localStorage` is no longer used.

## Start SmartTime

Requires Python 3.9+; no third-party Python packages are required.

1. Extract the ZIP file.
2. Open a terminal in the `SmartTime_separated` folder.
3. Run:

   ```bash
   python server.py
   ```

4. Open `http://localhost:8000/` for staff attendance.
5. Open `http://localhost:8000/admin.html` for the IT console. Demo credentials: **Admin User** / **demo123**.
6. In **Workplace Settings**, configure the actual latitude, longitude and allowed radius in metres. Staff devices must allow location access. For deployment on other devices, host this app behind HTTPS.

Keep `server.py` running while using the system. Back up `smarttime.sqlite3` to back up the stored records and settings.

## Responsive layout and GPS geofencing notes

- The staff page and admin console adapt to phone, tablet, and desktop widths. On phones/tablets, the admin sidebar opens from the menu button and closes after a page is selected or the backdrop is tapped.
- Workplace coordinates must be decimal degrees: latitude first (−90 to 90), longitude second (−180 to 180). Do not swap the two values. Copy coordinates for the actual building/entrance from a reliable map source; use the same datum (WGS84, used by GPS).
- Geolocation requests a fresh, high-accuracy device fix. The UI reports the estimated distance and the GPS uncertainty in metres. If the GPS uncertainty is very large, staff are asked to improve the fix rather than receiving a misleading distance result.
- To reduce false rejections near the boundary, access is accepted when the GPS uncertainty circle overlaps the configured radius (`estimated distance − reported accuracy <= radius`). This is intentionally more tolerant at the edge; use a sensible radius and server-side verification for production.
- Browser geolocation requires HTTPS on deployed sites (or localhost during local testing). Staff should grant location permission and enable precise location/GPS in their device settings. Indoor GPS can be inaccurate; test near a window or outdoors when setting up the workplace coordinates.

## Important prototype/security note

This is a local demonstration, not a production-ready attendance system. The demo administrator password is not secure server-side authentication, and the API currently accepts state updates from clients. Do not expose it to the public internet or use it for real employee records until server-side authentication/authorization, audit logging, and server-verified geofencing are implemented. Browser location checks alone can be spoofed. Camera capture, QR token entry and fingerprint options are still demonstration flows rather than production-grade identity verification.
