# TikTok Developer API Application Guide
## Content Posting API — Draft Upload Approval Path

**Scope of this document:** Everything needed to submit and pass TikTok's Content Posting API review for the `video.upload` (draft-only) scope. Written for a **creator-assistive TikTok Shop UGC workflow** — human review is required before any draft goes live.

---

## 1. App Description

> Copy-paste this into the "App Description" field on the TikTok Developer portal.

**Short version (≤200 chars for portal summary):**
> AI-assisted UGC draft tool for TikTok Shop creators. Generates video scripts and captions, then uploads drafts for human review — creators publish manually.

**Long version (for the detailed description field):**
> [App Name] is a creator productivity tool for TikTok Shop affiliate marketers. It uses AI to generate short-form video scripts, product captions, and hashtag sets based on trending TikTok Shop products. Once a video is generated, it is queued in a human review dashboard where the creator watches the draft, edits the caption, and approves it for upload. The approved draft is then uploaded to TikTok via the API as an unposted draft — the creator reviews it one final time inside TikTok's native app and publishes it manually. No video is ever posted publicly without the creator's explicit action inside TikTok. The tool is designed to help solo creators produce consistent, on-brand TikTok Shop content without sacrificing authenticity or oversight.

---

## 2. Use-Case Explanation

> For the "Use Case" field or any supplementary text box.

**Primary use case:** TikTok Shop affiliate content creation for individual creators and small creator teams.

**Detailed breakdown:**

| Step | Who acts | What happens |
|------|----------|-------------|
| 1. Product research | AI agent | Scans TikTok Shop trending products in creator's niche |
| 2. Script generation | Claude AI | Writes a short UGC-style script (hook + demo + CTA) |
| 3. Caption + hashtags | Claude AI | Generates caption with affiliate links and relevant hashtags |
| 4. Video render | MoneyPrinterTurbo | Assembles B-roll, voiceover, captions into MP4 |
| 5. Human review queue | Creator (human) | Watches the draft, edits script/caption, approves or rejects |
| 6. Draft upload | API (`video.upload`) | Approved video is uploaded as a TikTok draft (NOT published) |
| 7. Final publish | Creator (human) | Opens TikTok app, reviews the draft, hits Publish manually |

**What this tool does NOT do:**
- Does not auto-publish any video
- Does not post without a human approving each video individually
- Does not use third-party scheduling or posting tools
- Does not manage other creators' accounts — one OAuth token per creator

**Volume:** Designed for 1–3 videos per day per creator account, well within TikTok's rate limits.

---

## 3. OAuth Redirect / Callback Plan

### Flow

```
Creator clicks "Connect TikTok" in the app
  → App redirects to TikTok OAuth authorization URL
  → Creator logs in and approves the requested scopes
  → TikTok redirects to: https://[yourdomain.com]/auth/tiktok/callback
  → App exchanges code for access_token + refresh_token
  → Tokens stored securely (encrypted at rest, never logged)
  → Creator is now connected — their TikTok draft inbox is the target
```

### Callback URL to register in developer portal
```
https://[yourdomain.com]/auth/tiktok/callback
```

For local dev/testing (add as a second redirect URI):
```
http://localhost:3000/auth/tiktok/callback
```

### Token handling rules
- `access_token`: stored encrypted in SQLite (Phase 1-2) → Supabase (Phase 2+)
- `refresh_token`: auto-refreshed before expiry; rotated on each use
- Tokens scoped to ONE creator account per installation
- No token sharing across accounts
- Token revocation: creator can disconnect inside the app at any time; app immediately deletes stored tokens

### What to say in the portal
> Our OAuth callback is `https://[yourdomain.com]/auth/tiktok/callback`. After authorization, we exchange the code for an access token, which is stored encrypted and used exclusively to upload video drafts to the authorizing creator's own account. We never use tokens to read or post on behalf of users without their explicit per-video approval.

---

## 4. Required Scopes

Request **only these scopes** — do not over-request:

| Scope | Why needed | Notes |
|-------|-----------|-------|
| `user.info.basic` | Display creator's username/avatar in the review UI | Read-only |
| `video.upload` | Upload video file as a draft | Draft only — does NOT auto-publish |

**Do NOT request at this stage:**
- `video.publish` — this auto-publishes; avoid until Phase 6 with proven track record
- `video.list` — not needed for draft-only workflow
- `user.info.profile` — not needed
- Any `commerce` or `shop` scopes — handled via TikTok Shop Affiliate separately

### How to frame scope justification in the portal

**`user.info.basic`:**
> We display the connected creator's TikTok username and profile photo in our review dashboard so they can confirm they are connected to the correct account before approving any content.

**`video.upload`:**
> We upload creator-approved video drafts to TikTok using the draft upload endpoint (`/v2/post/publish/inbox/video/init/`). These drafts are NOT published automatically. The creator reviews and publishes them manually inside the TikTok app. Our human review step is mandatory — no video can be uploaded without creator approval in our dashboard.

---

## 5. Privacy Policy Outline

> Host this at: `https://[yourdomain.com]/privacy`  
> Must be live and accessible before submitting the developer application.

### Required sections

**1. Data We Collect**
- TikTok OAuth access token and refresh token (encrypted, not logged)
- TikTok username and profile photo (for display only)
- Video files generated by the tool (stored temporarily for upload, deleted after 24 hours)
- Creator-entered captions and hashtags

**2. How We Use Data**
- Tokens: used solely to upload draft videos to the authorizing creator's own TikTok account
- Username/photo: displayed in the review UI to confirm correct account connection
- Video files: uploaded as drafts via TikTok API; local copies deleted after successful upload or within 24 hours
- We do not sell, share, or transfer any data to third parties

**3. Data Storage and Security**
- Tokens encrypted at rest using AES-256
- No plaintext credentials stored anywhere
- Local SQLite database in Phase 1; migrated to Supabase with row-level security in Phase 2
- HTTPS enforced on all endpoints

**4. Data Retention**
- OAuth tokens: retained until creator disconnects; immediately deleted on revocation
- Video files: deleted within 24 hours of upload or rejection
- No long-term storage of TikTok content

**5. TikTok Platform Data**
- We comply with TikTok's Developer Terms of Service and Data Portability requirements
- We do not scrape TikTok; all data is obtained via official API endpoints
- Creators can request deletion of all stored data by disconnecting their account and emailing [support@yourdomain.com]

**6. Contact**
- Email: [support@yourdomain.com]
- Last updated: [date]

---

## 6. Terms of Service Outline

> Host this at: `https://[yourdomain.com]/terms`  
> Must be live and accessible before submitting.

### Required sections

**1. Acceptance**
By connecting your TikTok account, you agree to these terms and TikTok's own Terms of Service.

**2. Permitted Use**
- Tool is for individual creators managing their own TikTok account
- One TikTok account per installation
- Creator must be the authorized account holder

**3. Prohibited Use**
- Do not use this tool to post spam, misleading content, or content that violates TikTok's Community Guidelines
- Do not share OAuth credentials or tokens with third parties
- Do not attempt to automate publishing (all publishing is manual inside TikTok)
- Do not use the tool to manage accounts you do not own

**4. Human Review Requirement**
Every video must be reviewed and approved by the creator before it is uploaded as a draft. The tool does not auto-publish. The creator is fully responsible for the content they choose to publish.

**5. Content Responsibility**
You are responsible for ensuring all content complies with TikTok's Community Guidelines, advertising policies, and TikTok Shop affiliate program rules.

**6. Account Disconnection**
You may disconnect your TikTok account at any time. Disconnection immediately revokes our access and deletes your stored tokens.

**7. Limitation of Liability**
We are not responsible for TikTok account actions, violations, or bans resulting from content the creator publishes.

**8. Changes**
We may update these terms; continued use constitutes acceptance.

---

## 7. Demo Flow Checklist

> This is what TikTok reviewers will look for. Walk through this EXACTLY in your demo video.

### Pre-demo setup
- [ ] Test account connected via OAuth (use a personal/alt TikTok account)
- [ ] At least 1 complete video ready in the review queue
- [ ] Review dashboard visible and functional
- [ ] TikTok app open on phone to show the draft inbox after upload

### Demo script (in order)

1. **Show the product input screen**
   - Enter a sample TikTok Shop product URL or name
   - Show that a script + caption is generated by AI

2. **Show the human review dashboard**
   - Video plays in the review panel
   - Caption and hashtags are editable
   - Two buttons visible: "Approve" and "Reject"
   - Approve the video

3. **Show the upload trigger**
   - After approval, show the "Upload as Draft" button being clicked
   - Show a loading/progress indicator
   - Show a success confirmation with the TikTok draft link

4. **Show TikTok's draft inbox on a phone**
   - Open TikTok app → Creator tools → Drafts
   - Show the uploaded video sitting as an unposted draft
   - Optionally show tapping "Post" — this is the final human step

5. **Show what does NOT happen automatically**
   - Briefly show settings panel: "Auto-publish: OFF", "Human review required: ON"
   - Highlight that no video posts without creator action

### Common reviewer questions to preempt
- "Does this auto-post?" → No, draft upload only; creator publishes manually
- "Can it post on behalf of others?" → No, one account per OAuth token
- "What's the posting volume?" → Max 3 drafts/day by design; 1-3 typical

---

## 8. Screenshots / Videos to Prepare

### Screenshots (static, for portal submission)

| # | What to capture | Tool |
|---|----------------|------|
| 1 | OAuth connection screen — "Connect your TikTok account" button | Browser screenshot |
| 2 | TikTok OAuth consent screen showing requested scopes | Browser screenshot |
| 3 | Human review dashboard with video player, caption editor, Approve/Reject buttons | Browser screenshot |
| 4 | Post-approval "Upload as Draft" button and progress indicator | Browser screenshot |
| 5 | TikTok draft inbox (mobile) showing the uploaded draft | Phone screenshot |
| 6 | App settings showing "Auto-publish: OFF" and "Human review required: ON" | Browser screenshot |

### Demo video (2-3 minutes, required for most API tiers)

**Format:** Screen recording (desktop) + phone camera (for TikTok draft inbox)  
**Tool:** OBS Studio (free) or Loom  
**Resolution:** 1080p minimum  

**Script outline:**
```
0:00-0:20  Intro — "This is [App Name], a draft-upload tool for TikTok Shop creators"
0:20-0:50  Show product input and AI script/caption generation
0:50-1:30  Walk through human review dashboard — approve a video
1:30-2:00  Show draft upload to TikTok (API call + success response)
2:00-2:30  Show TikTok draft inbox on phone — video is there, NOT posted
2:30-3:00  Show settings — auto-publish off, human review enforced
```

**DO include in video:**
- The word "DRAFT" clearly visible in TikTok's UI
- The creator manually clicking "Approve" before anything uploads
- Settings panel showing safety controls

**DO NOT include:**
- Any video publishing automatically
- Bulk upload of multiple videos in rapid succession
- Any reference to competitor tools or API workarounds

---

## 9. Things to Avoid Saying in the Application

These phrases raise red flags with TikTok reviewers and trigger rejections or additional scrutiny.

### Never write these

| Phrase | Why it's a problem | What to say instead |
|--------|-------------------|---------------------|
| "auto-post" / "automatic posting" | Implies no human in the loop | "creator-approved draft upload" |
| "schedule posts" | Sounds like a scheduling/automation tool | "upload drafts for human review" |
| "mass upload" / "bulk post" | Implies spam at scale | "1-3 drafts per day, individually approved" |
| "post on behalf of" | Implies agency over accounts | "the creator connects their own account" |
| "monetize" (in scope justification) | Sounds like extracting value from the API | "help creators produce authentic Shop content" |
| "hourly" / "24/7" / "always-on" | Implies fully autonomous bot | "runs when the creator initiates" |
| "bypass" / "workaround" | Obvious | Never use these words |
| "unlimited" posts/videos | Implies no rate limits | "1-3 drafts per day maximum" |
| "competitor" tool names | Implies replicating unapproved tools | Don't name-drop |
| "scrape" / "scraping" | Implies ToS violation | "uses TikTok Shop's official affiliate data" |

### Tone to avoid

- Do not sound like a SaaS agency tool managing multiple creator accounts
- Do not emphasize volume, speed, or scale
- Do not describe the AI as "replacing" the creator's judgment
- Do not frame this as a revenue-maximization bot

### Tone to use

- Single creator, their own account
- Human is always in control
- AI assists with ideation, not execution
- Drafts, not posts
- Authentic UGC, not production automation

---

## 10. Step-by-Step TikTok Developer Submission Instructions

### Phase A: Setup (before submitting)

**Step 1: Create a TikTok Developer account**
1. Go to `developers.tiktok.com`
2. Log in with a TikTok account (use your primary or a dedicated business account)
3. Complete email verification

**Step 2: Create your app**
1. Dashboard → "Manage Apps" → "Create App"
2. Select **"Web"** as platform (even if you also have mobile later)
3. App name: Use your brand name (not "TikTok Bot" or similar)
4. Category: **"Productivity"** or **"Entertainment"** (Productivity is safer)

**Step 3: Get your credentials**
- Note your `Client Key` and `Client Secret`
- Add these to your `.env` file:
  ```
  TIKTOK_CLIENT_KEY=your_key_here
  TIKTOK_CLIENT_SECRET=your_secret_here
  TIKTOK_REDIRECT_URI=https://yourdomain.com/auth/tiktok/callback
  ```

**Step 4: Configure redirect URIs**
- App settings → "Login Kit" → Add redirect URI
- Add: `https://yourdomain.com/auth/tiktok/callback`
- Add (for dev): `http://localhost:3000/auth/tiktok/callback`

**Step 5: Deploy your Privacy Policy and Terms of Service**
- Both must be live HTTPS URLs before submitting
- Test that they load from an incognito window

---

### Phase B: Request API Access

**Step 6: Navigate to "Add Products" → "Content Posting API"**
- In your app dashboard: Products → Content Posting API → Apply

**Step 7: Fill in the application form**

| Field | What to enter |
|-------|--------------|
| App Name | Your brand name |
| App Description | Use the long version from Section 1 |
| Use Case | Use the breakdown from Section 2 |
| Target Audience | "Individual TikTok Shop affiliate creators" |
| Redirect URI | `https://yourdomain.com/auth/tiktok/callback` |
| Privacy Policy URL | `https://yourdomain.com/privacy` |
| Terms of Service URL | `https://yourdomain.com/terms` |
| Scopes requested | `user.info.basic`, `video.upload` ONLY |
| Expected daily API calls | 3–10 (conservative and honest) |
| Demo video | Upload your 2-3 minute walkthrough |
| Screenshots | Upload all 6 screenshots from Section 8 |

**Step 8: Scope justification fields**
- For `video.upload`: Use the exact language from Section 4
- For `user.info.basic`: Use the exact language from Section 4
- Keep justifications short (2-4 sentences each) and factual

**Step 9: Submit**
- Review everything one more time against the "avoid saying" list in Section 9
- Submit and note the submission date
- TikTok review takes **1–4 weeks** (typically 2 weeks for draft-only scope)

---

### Phase C: While You Wait

**Step 10: Use Sandbox mode during review**
- TikTok provides a sandbox environment for `video.upload` testing
- In your developer portal: enable Sandbox
- Your app gets a test user with draft upload permissions
- Build and test `tools/tiktok_upload_draft.py` against the sandbox endpoint

**Step 11: Add a test user (for sandbox)**
- App dashboard → "Sandbox" → "Add Test User"
- Use your personal TikTok account as the test user
- This lets you test the full OAuth + draft upload flow without approval

**Sandbox endpoint to test:**
```
POST https://open.tiktokapis.com/v2/post/publish/inbox/video/init/
```

**Step 12: Prepare for reviewer questions**
TikTok may email you asking for:
- Clarification on how you prevent auto-publishing
- A live demo (screen share or video call)
- Proof that Human Review is enforced (show the code or UI)

Keep Section 7's demo checklist ready for this.

---

### Phase D: After Approval

**Step 13: Move from Sandbox to Production**
- Dashboard → toggle from Sandbox to Production
- Replace sandbox credentials with production `Client Key` + `Client Secret` in `.env`
- Run one end-to-end test with a real draft upload to your TikTok account

**Step 14: Set `POSTING_ENABLED=true` only in `.env`**
- Keep `HUMAN_REVIEW_REQUIRED=true` — always
- Keep `MAX_DRAFTS_PER_DAY=3` — always

**Step 15: Log your first production draft upload**
- Screenshot or screen-record as evidence the integration works
- Useful if TikTok ever audits your usage

---

## Quick Reference Card

```
Scopes to request:    user.info.basic, video.upload
Scopes to skip:       video.publish (for now)
Upload endpoint:      /v2/post/publish/inbox/video/init/
Callback URL:         https://yourdomain.com/auth/tiktok/callback
Daily volume:         1-3 drafts (say this explicitly)
Key phrase:           "creator-approved draft upload, manually published by the creator"
Review timeline:      1-4 weeks
Sandbox:              Available immediately after app creation
```
