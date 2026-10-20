# The Everyday Reset • Quote Studio v6.0 — 18 Editorial Templates

**Actual upgraded v5.4 project**, not a fresh disconnected mockup. Angular interface + Node backend + Python/Pillow renderer + FFmpeg video output. Uses the same adjustable page handle and uploaded bottom-center icon from the original studio.

## What changed in v6

- **18 new editable layout presets** based on the *layout characteristics* of the 18 uploaded WhatsApp references: warm ivory/cream/beige/peach paper texture, dramatic black serif headline, vivid yellow phrase highlighting, long reflective essays, checklists, numbered wins, letters, poetry, and dialogue.
- **Auto** selects a category-appropriate template with reduced back-to-back repeats. Select any of the 18 presets manually to match a chosen design format. The original v5 dark style remains as **Original V5 Dark Mode**.
- Gemini produces **original topic/category/template-specific copy** as structured JSON with `headline`, `paragraphs`, `items`, `closing`, `highlights` (exact strings), `caption`, `hashtags`. The renderer does real word-level highlighting; no fake painted block over the entire poster. No reference watermark/text is copied. You can keep your existing brand/page handle.
- Six extra content categories: Gratitude, Maturity, Boundaries, Hard Truths, Dear Self/Affirmations, Positive Thinking.
- New **true full-frame 9:16 Reel poster** generated from the same template and text. Existing 4:5 PNG is unchanged. MP4 stays silent so you can add legally available Facebook audio after export.
- Still supports **5s and 10s**, optional effects, PNG / MP4, local history, in-app preview, Netlify/Render deployment and Gemini Lite models.
- Uploaded logo is cached in **browser localStorage** when space allows. Large files may require re-upload after a refresh. Do not use shared computers if you don't want saved branding.
- The artwork is original and inspired by design traits, **not a pixel-perfect clone** or a copy of another creator's watermark/quotes.

## Windows 10/11: run locally

Install: **Node.js 22**, **Python 3.11+**, **FFmpeg** (add ffmpeg to PATH), internet for the first dependency install. Unzip and open the **`Everyday_Reset_Quote_Studio_v6` folder containing `package.json`**.

```cmd
node -v
python --version
ffmpeg -version
npm run setup
npm run dev
```

Open **http://localhost:4200**. The existing `setup-windows.bat` and `start-windows.bat` also work. Setup uses the existing pnpm/Corepack/npm fallback installer for the known Windows `edgesOut` npm dependency issue.

## Usage

1. Select **English** and a category such as Life, Maturity, Relationships, or Self-Respect.
2. Choose **AUTO** for category-sensitive template rotation, or any of the 18 designs. A short custom topic is optional.
3. Enter **your existing page handle** in the Corner handle text field. Upload **your current page icon** once (bottom center). See optional `brand_assets/Everyday_Reset_Logo.png` only if this is the logo you're using. Do not change the icon/handle just to use templates.
4. Paste your **Gemini API key** in the UI to get newly generated original copy; without a valid key you receive **labelled, prewritten local example copy**, not a new Gemini quote. API key is not hardcoded in this project.
5. Keep **1080×1350 4:5** for Facebook image posts (square 1080×1080 also supported). Enable Reel for 720×1280 24FPS silent MP4, 5s or 10s. Use the preview/download buttons.
6. If you plan to publish, **review AI copy** for clarity and factual accuracy. Add appropriate rights-cleared audio in the Facebook Reels editor.

### Template families

01 Comeback Note; 02 Life Beauty Essay; 03 Discipline Lesson; 04 Dear Self Letter; 05 Feelings Checklist; 06 Expectations List; 07 Everyday Wins Numbered; 08 Blush Poem; 09 Honest Insight; 10 Positive Thinking Centered; 11 Heartfelt Essay; 12 Relationship Truth; 13 Little Blessings; 14 Hard Truth; 15 Never Forget; 16 Question & Answer; 17 Maturity Lesson; 18 Wake-Up Reality. Optional **classic dark** template remains.

`examples/editorial_v6` contains an **actual rendered PNG for every one of the 18 presets**. The handle/logo in samples illustrates how **your icon and handle appear**; they are not auto-forced into the app.

### Output notes

- Gemini free usage depends on your Google project/quota and availability; no guaranteed free unlimited generation.
- A very long square post may show a warning that secondary copy was shortened to avoid text clipping; for longer lists choose 4:5.
- Text fonts use **system-installed typefaces** (e.g. Windows Georgia/Times New Roman). Appearance can vary slightly across operating systems; no restricted fonts are bundled.
- Render free hosting has ephemeral file storage and may have memory/time limits. A generation-specific access key is supported on the backend (`GENERATE_ACCESS_KEY`), set its value in the UI's Deployment settings.

## Verification performed

- Original JavaScript tests: 9/9 passed. Original Python tests: 3/3 passed.
- All 18 templates rendered to actual 1080×1350 PNGs. Real Node API → Python worker → actual poster and 5-second 720×1280 MP4 succeeded; Auto selection succeeded.
- Existing FFmpeg reference effect also generated a 5-second MP4 successfully.
- **Full Angular installation/build not verified** in this sandbox because package dependencies are not installed. Run `npm run setup` and `npm --prefix frontend run build` on your computer to verify Angular before deploying.

See `DEPLOY_NETLIFY_RENDER.md` for existing instructions. Source layout: `frontend`, `backend`, `worker`, `scripts`, `examples`.
