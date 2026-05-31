# Deploy Legal Site — Step-by-Step

Static site at `legal-site/` containing Privacy Policy and Terms of Service.
These URLs go directly into the TikTok Developer Portal.

---

## Before You Deploy: Find & Replace

Open each HTML file and replace these 4 values:

| Placeholder | Replace with |
|-------------|-------------|
| `CreatorDraft` | Your actual app name |
| `creatordraft.app` | Your actual domain (or leave as-is for free subdomain) |
| `support@creatordraft.app` | Your real support email (garrettcohen07@gmail.com is fine for now) |
| `[YOUR STATE]` | Your state, e.g. `Florida` |

**Quick way:** Open VS Code → Ctrl+Shift+H (Find & Replace in Files) → set path to `legal-site/`

---

## Option A: Deploy to Vercel (Recommended — fastest, free, HTTPS auto)

1. **Create a GitHub repo** for the legal site:
   ```
   cd "c:\Users\Owner\OneDrive\Desktop\SKook\TIKTOK UGC _ MONEY PRINTER LLM\legal-site"
   git init
   git add .
   git commit -m "Initial legal site"
   gh repo create creatordraft-legal --public --push --source=.
   ```
   Or create the repo at github.com manually and push.

2. **Go to** [vercel.com](https://vercel.com) → Sign in with GitHub → "Add New Project"

3. **Import** your `creatordraft-legal` repo

4. **Settings** (Vercel will auto-detect):
   - Framework Preset: **Other**
   - Root Directory: `.` (leave default)
   - Build Command: (leave blank)
   - Output Directory: `.` (leave default)

5. **Click Deploy** → takes ~30 seconds

6. **Your URLs** (paste these into TikTok Developer Portal):
   ```
   Privacy Policy:    https://creatordraft-legal.vercel.app/privacy
   Terms of Service:  https://creatordraft-legal.vercel.app/terms
   ```

7. **Optional: Add a custom domain** in Vercel Dashboard → Domains → Add
   - Example: `legal.yourdomain.com` → set DNS CNAME to `cname.vercel-dns.com`
   - URLs become: `https://legal.yourdomain.com/privacy`

---

## Option B: Deploy to Netlify (Alternative, also free)

1. Go to [app.netlify.com](https://app.netlify.com) → "Add new site" → "Deploy manually"

2. **Drag and drop** the entire `legal-site/` folder onto the Netlify deploy area

3. Your site deploys instantly with a URL like `https://random-name-12345.netlify.app`

4. **Rename the site**: Site Settings → Site information → Change site name
   - Example: `creatordraft-legal` → URL becomes `https://creatordraft-legal.netlify.app`

5. **Your URLs**:
   ```
   Privacy Policy:    https://creatordraft-legal.netlify.app/privacy
   Terms of Service:  https://creatordraft-legal.netlify.app/terms
   ```

---

## Option C: GitHub Pages (Free, no account needed beyond GitHub)

1. Push `legal-site/` contents to a GitHub repo (e.g., `creatordraft-legal`)

2. Go to repo Settings → Pages → Source: **Deploy from branch** → Branch: `main` → Folder: `/ (root)`

3. Your URLs (after ~2 minutes):
   ```
   Privacy Policy:    https://yourusername.github.io/creatordraft-legal/privacy/
   Terms of Service:  https://yourusername.github.io/creatordraft-legal/terms/
   ```
   Note: GitHub Pages includes the repo name in the URL and requires trailing slash.
   For TikTok portal, paste the full URL with trailing slash.

4. **Optional: Custom domain** → repo Settings → Pages → Custom domain → add `legal.yourdomain.com`

---

## Verify Before Submitting to TikTok

Test these 5 things before pasting URLs into the developer portal:

- [ ] `https://yourdomain/privacy` loads without error (not 404)
- [ ] `https://yourdomain/terms` loads without error
- [ ] Both pages have HTTPS (padlock icon in browser)
- [ ] Both pages load on mobile (resize browser window)
- [ ] Contact email link (`mailto:`) opens email client when clicked

---

## TikTok Developer Portal — Where to Paste

| TikTok Portal Field | Value |
|---------------------|-------|
| Privacy Policy URL | `https://your-site.vercel.app/privacy` |
| Terms of Service URL | `https://your-site.vercel.app/terms` |

Both fields are in: **TikTok Developer Portal → Your App → App Details → Basic Information**

They're also required again in: **Products → Content Posting API → Application form**
