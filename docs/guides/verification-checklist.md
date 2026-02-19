# Verification Checklist

- [ ] Restart backend (Policy Service) to apply router changes.
- [ ] Restart frontend (Next.js) to apply middleware.
- [ ] **Manual Test 1**: Visit `/admin/dash` incognito -> Redirect to `/admin`.
- [ ] **Manual Test 2**: Login with random credentials -> Error.
- [ ] **Manual Test 3**: Create admin user in DB (via script).
- [ ] **Manual Test 4**: Login with correct credentials -> Redirect to `/admin/dash`.
