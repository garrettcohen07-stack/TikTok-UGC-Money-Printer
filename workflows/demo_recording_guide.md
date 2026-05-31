# Demo Recording Guide
## CreatorDraft — TikTok Content Posting API Review

**Demo URL:** `https://[your-vercel-url].vercel.app/demo`

---

## Pre-Recording Setup

- [ ] Browser: Chrome or Edge, full-screen (F11)
- [ ] Resolution: 1920×1080 minimum
- [ ] Recording tool: OBS Studio (free) or Loom
- [ ] Zoom browser to 90% (Ctrl+–) for best layout
- [ ] Close all other browser tabs and notifications
- [ ] Have your TikTok app open on your phone (for the Drafts inbox shot)
- [ ] **Keyboard shortcuts during recording:** Space = pause | ← → = navigate | R = restart

---

## 3-Minute Recording Script

**Total runtime target: 2:45 – 3:15**

### 0:00 – 0:20 | Cold Open — Compliance Overview
- Open the demo URL
- The demo starts paused on Step 1
- **Say:** "This is CreatorDraft — a creator-assistive TikTok Shop UGC tool. Before I walk through anything, I want you to notice what's always visible in this header."
- Point to the header badges: **Human Review: ON** · **Auto-Publish: OFF** · **Draft Only** · **Manual Publish** · **TikTok API Compliant**
- **Say:** "These are not just labels — they're enforced at the system level. You cannot disable human review. You cannot enable auto-publish. Every single step of this demo proves that."

### 0:20 – 0:55 | Step 1 — Product Input
- Press Space to start auto-playing OR click Next →
- Walk through the form: product name, category, audience, tone
- Point to the **Compliance Settings Panel** (dark panel on dark background)
- **Say:** "Human review is required. Auto-publish is permanently off. Upload mode is draft inbox only. And it uses TikTok OAuth 2.0 — no passwords ever stored."
- **Say:** "I'll click Generate — and notice: nothing uploads. We're just generating a draft for review."

### 0:55 – 1:20 | Step 2 — AI Generation
- Watch the generation animation play
- **Say:** "The AI writes a script, drafts a caption, picks hashtags, and renders a video preview. But it does NOT upload. Watch — it's building toward the review queue."
- Point to the amber warning box at the bottom: "This video will NOT upload until you review and approve it."

### 1:20 – 2:10 | Step 3 — Human Review Dashboard ⬅ MOST IMPORTANT
- **Say:** "This is the core of CreatorDraft. Every single video stops here. The creator watches the preview..."
- Point to the TikTok video frame playing in the left column
- **Say:** "...checks the review checklist — every item must be verified..."
- Point to the six checked items on the right
- **Say:** "...reads and edits the caption and hashtags..."
- Click the caption field, make a small edit
- **Say:** "...and then makes a decision: Reject, request edits, or Approve. Nothing goes to TikTok until this moment."
- Point to the three action buttons
- Point to the amber upload warning: "Draft upload only — not a public post"
- **Say:** "I'll click Approve — and ONLY now does an API call begin."

### 2:10 – 2:35 | Step 4 — Draft Upload
- Watch the four progress steps tick off
- **Say:** "OAuth token validated. File prepared. Uploading to the TikTok draft inbox via the official Content Posting API inbox endpoint. Not to the public feed — to the draft inbox."
- Point to the three callout boxes on the right: **DRAFT UPLOAD ONLY** · **NOT PUBLICLY POSTED** · **MANUAL PUBLISH REQUIRED**
- **Say:** "This is the video.upload scope — inbox upload only. The creator still has to manually publish inside TikTok."

### 2:35 – 3:00 | Step 5 — Compliance Summary
- **Say:** "Upload confirmed. Now look at the full compliance summary."
- Read through the 8 checklist items as they appear:
  - Human review completed ✓
  - Auto-publish permanently disabled ✓
  - Draft-only upload ✓
  - OAuth 2.0, no passwords ✓
  - No scraping ✓
  - No mass posting ✓
  - Creator manually publishes ✓
  - Single-account access ✓

### 3:00 – 3:15 | Closing — TikTok App + End Screen
- Optionally: switch to phone camera, show TikTok app → Profile → Drafts → your test video sitting as DRAFT
- Click "View End Summary →" to reach the end screen
- **Say:** "CreatorDraft is a creator productivity tool — not a bot. Human review is mandatory. Auto-publishing is impossible. The creator publishes when they're ready."

---

## 60-Second Express Recording Script

**Use this for a shorter supplemental demo**

```
0:00–0:10  Header badges: "Human Review ON, Auto-Publish OFF, Draft Only — these are enforced."

0:10–0:20  Step 1: Show the locked compliance settings panel. "Human review required,
           auto-publish permanently off, draft inbox only."

0:20–0:30  Step 2→3: Skip to Human Review dashboard. "Every video stops here.
           Creator watches it, checks the compliance list, then approves or rejects."

0:30–0:45  Point to the action buttons. "Reject, Request Edits, or Approve. Only on
           Approve does an API call happen — and it goes to the draft inbox, not the feed."

0:45–0:55  Step 4: Watch OAuth → upload → "Draft inbox only. Not posted publicly.
           Creator still has to publish manually inside TikTok."

0:55–1:00  Step 5 compliance checklist: "8 compliance checks. Human review done.
           Auto-publish off. Draft only. This is creator-assistive, not a bot."
```

---

## Screen Recording Checklist

### Before you hit Record
- [ ] Browser full screen, zoom at 90%
- [ ] Demo URL open and loaded
- [ ] No notifications, no other apps visible
- [ ] OBS/Loom ready, audio check done

### Must capture in the recording
- [ ] Header compliance badges clearly visible
- [ ] Step 1: The dark compliance settings panel with "REQUIRED" and "PERMANENTLY OFF" labels
- [ ] Step 2: Generation animation playing, amber warning box visible
- [ ] Step 3: Video frame, review checklist, amber upload warning, three action buttons
- [ ] Step 3: Caption field being clicked/edited
- [ ] Step 3: "Approve Draft — Upload to Inbox" button click
- [ ] Step 4: All four upload steps ticking off, three callout boxes visible
- [ ] Step 4: API endpoint `POST /v2/post/publish/inbox/video/init/` visible
- [ ] Step 5: Compliance checklist appearing item by item
- [ ] Step 5: "DRAFT" status badge in the inbox card
- [ ] End screen: Four pillars, "Ready for TikTok Content Posting API Review" badge

### Bonus (if possible)
- [ ] Switch to phone camera briefly to show TikTok app → Profile → Drafts → video sitting as unposted draft
- [ ] Show Settings panel with auto-publish locked off

---

## TikTok App Review — 1000-Character Explanation

**Paste this verbatim into the "App Use Case Description" field in TikTok Developer Portal.**

```
CreatorDraft is a creator productivity tool for individual TikTok Shop affiliate 
marketers. It uses AI to generate video scripts, captions, and hashtags from product 
inputs provided by the creator. Every generated video is queued in a mandatory human 
review dashboard where the creator watches the full preview, edits the caption, and 
clicks "Approve" individually before any API call is made. Upon approval, the app uses 
the video.upload endpoint to place the video in the creator's TikTok draft inbox only — 
not to publish it publicly. The creator must then open the TikTok app and manually 
publish each draft at their discretion. No auto-publishing occurs at any stage. 
Auto-publish is permanently disabled and cannot be enabled. The app enforces a maximum 
of 3 draft uploads per day per account, requires TikTok OAuth 2.0 authorization, stores 
no passwords, and accesses no TikTok data beyond user.info.basic. Each upload requires 
individual human approval.
```

*(~950 characters — fits in 1000-char limit)*

---

## URL List for TikTok Developer Portal

Paste these exact URLs into the fields indicated:

| TikTok Portal Field | URL |
|---------------------|-----|
| **App URL / Website** | `https://[your-vercel-url].vercel.app/` |
| **Privacy Policy URL** | `https://[your-vercel-url].vercel.app/privacy` |
| **Terms of Service URL** | `https://[your-vercel-url].vercel.app/terms` |
| **Demo Video / App URL** | `https://[your-vercel-url].vercel.app/demo` |
| **OAuth Callback URL** | `https://[your-vercel-url].vercel.app/auth/tiktok/callback` |

**Where to find your Vercel URL:**
1. Log in to vercel.com
2. Go to your `TikTok-UGC-Money-Printer` project
3. Click "Domains" — your URL is shown there
4. Replace `[your-vercel-url]` above with the actual subdomain

**Example:**
```
https://tiktok-ugc-money-printer-garrettcohen07-stack.vercel.app/privacy
https://tiktok-ugc-money-printer-garrettcohen07-stack.vercel.app/terms
https://tiktok-ugc-money-printer-garrettcohen07-stack.vercel.app/demo
```
