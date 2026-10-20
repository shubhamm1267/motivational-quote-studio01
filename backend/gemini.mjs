
/**
 * Gemini text generation: ONLY Flash-Lite models with a bounded retry policy.
 * Free-tier access and capacity depend on the user's Google AI Studio project.
 * No automatic switch to paid/non-Lite models.
 */
export const LITE_MODELS = Object.freeze([
  'gemini-3.5-flash-lite',
  'gemini-3.1-flash-lite',
  'gemini-2.5-flash-lite', // Legacy: Google may restrict new projects.
]);
export const DEFAULT_MODEL = LITE_MODELS[0];

const TEMPORARY_STATUSES = new Set([408, 429, 500, 502, 503, 504]);
const MODEL_UNAVAILABLE_STATUSES = new Set([404]);

export function sanitizeModel(model) {
  return LITE_MODELS.includes(model) ? model : DEFAULT_MODEL;
}

export function modelOrder(requested) {
  const selected = sanitizeModel(requested);
  return [selected, ...LITE_MODELS.filter((model) => model !== selected)];
}

export class GeminiUnavailableError extends Error {
  constructor(message, attempts) {
    super(message);
    this.name = 'GeminiUnavailableError';
    this.attempts = attempts;
  }
}

function extractJSON(text) {
  const trimmed = String(text || '')
    .replace(/^```(?:json)?\s*/i, '')
    .replace(/```\s*$/, '')
    .trim();

  try {
    return JSON.parse(trimmed);
  } catch {}

  const start = trimmed.indexOf('{');
  const end = trimmed.lastIndexOf('}');

  if (start < 0 || end <= start) {
    throw new Error('Gemini returned no JSON quote.');
  }

  return JSON.parse(trimmed.slice(start, end + 1));
}

function clean(value, max = 180) {
  return typeof value === 'string' ? value.trim().slice(0, max) : '';
}

function toPost(json, usedModel) {
  const text =
    json?.candidates?.[0]?.content?.parts?.map((p) => p.text || '').join('') || '';

  const obj = extractJSON(text);

  const post = {
    headline: clean(obj.headline, 200),
    detail: clean(obj.detail, 230),
    paragraphs: (Array.isArray(obj.paragraphs)?obj.paragraphs:[]).slice(0,5).map(p=>({
      text:clean(p?.text,460),
      highlights:(Array.isArray(p?.highlights)?p.highlights:[]).slice(0,3).map(s=>clean(s,100))
    })).filter(p=>p.text),
    items:(Array.isArray(obj.items)?obj.items:[]).slice(0,10).map(t=>clean(t,150)).filter(Boolean),
    closing:clean(obj.closing,225),
    highlights:(Array.isArray(obj.highlights)?obj.highlights:[]).slice(0,6).map(t=>clean(t,110)).filter(Boolean),
    template:clean(obj.template,40),
    eyebrow: clean(obj.eyebrow, 45),
    seoTitle: clean(obj.seoTitle, 180),
    caption: clean(obj.caption, 400),
    hashtags: (Array.isArray(obj.hashtags) ? obj.hashtags : [])
      .map((tag) => clean(tag, 40))
      .filter((tag) => /^#[\p{L}\p{N}_]+$/u.test(tag))
      .slice(0, 3),
    imageQuery: '',
    sourceUrl: '',
    sourceName: `Original Gemini quote draft (${usedModel})`,
    verification: 'ai_original_quote_review_required',
    aiModel: usedModel,
  };

  if (!post.headline) {
    throw new Error('Gemini returned an empty quote.');
  }

  if (!post.hashtags.length) {
    post.hashtags = ['#MotivationalQuotes'];
  }

  return post;
}

function errorMessage(status, text) {
  let message = '';

  try {
    message = JSON.parse(text)?.error?.message || '';
  } catch {}

  return clean(message || text || `HTTP ${status}`, 220);
}

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Attempts each Lite model up to twice on transient 408/429/5xx errors.
 * Non-retryable 400/401/403 errors are surfaced rather than hidden.
 * Pass fetchImpl/sleepImpl in automated tests; production uses native fetch.
 */
export async function writePost({
  key,
  model,
  topic,
  category = 'life',
  template = 'comeback',
  language = 'en',
  fetchImpl = fetch,
  sleepImpl = wait
}) {
  if (!key?.trim()) {
    throw new Error('Gemini API key required for AI quote generation.');
  }

  const format = {
    comeback:'statement',beauty:'essay',discipline:'essay',dear_self:'letter',emotions:'list',expectations:'list',underrated:'numbered',book_quote:'poem',truth_teller:'essay',thinking:'center',heart:'essay',ghosted:'essay',blessings:'essay',hard_truth:'essay',remember:'essay',dialogue:'dialogue',maturity:'essay',wake_up:'list'
  }[template] || 'essay';
  const prompt = `You are the original copywriter of a modern American-English motivational quote page (USA readers).
Write ONE completely original, emotionally believable, thoughtfully written social-media TEXT DESIGN, in ${language === 'en' ? 'natural American English' : 'Hindi (Devanagari)'}.
TOPIC: ${String(topic || 'motivation').slice(0,145)}.
CATEGORY: ${String(category).slice(0,35)}.
FORMAT: ${format}. SELECTED DESIGN TEMPLATE: ${template} (must stay unchanged).
The style is like a minimal editorial quote journal: short bold headline, then tightly written meaningful paragraphs, lists or reflective letter below. Not a one-line motivational slogan. Make it sound human, specific, relatable, fresh. Be sensitive in relationship/healing posts, not manipulative, not defamatory.
For essay/center/poem/dialogue/statement: use 1 to 3 paragraphs, each 70-220 characters. For statement: can include a little conclusion. For poem: 2-3 short airy paragraphs. For dialogue: make first line a surprising question and include a thoughtful answer. For numbered: write 9-10 short items. For letter: 7-8 short items. For list: write 6-8 short items (not empty generic cliches), with a meaningful 1-2 sentence closing.
Do NOT reproduce, paraphrase, closely imitate or attribute any real creator's example posts. No emojis in the quote graphic, no quotes attributed to famous people.
HIGHLIGHTING: Give 1-3 exact meaningful phrases in "highlights" (each copied verbatim from your headline/paragraphs/closing) for neon-yellow marker emphasis. On paragraph-level "highlights", phrases must be exact substrings of that paragraph. Do not highlight every sentence or the full paragraph. Emphasize memorable words that express the core idea.
LIMITS: headline 6-70 characters; paragraph total max 440 characters across all paragraphs; max 10 items of up to 70 characters; closing up to 110 characters. Minimize repeated information. Avoid line breaks inside any string.
SEO: caption 1 or 2 natural sentences, 3 relevant topic hashtags. Do not insert a fake page handle/logo or another creator watermark.
Return one JSON object and NOTHING else with exact fields:
{"headline":"...","detail":"short optional","paragraphs":[{"text":"...","highlights":["exact emphasized words"]}],"items":["..."],"closing":"...","highlights":["exact phrase from title or content"],"template":"${template}","seoTitle":"...","caption":"...","hashtags":["#Topic","#Theme","#Thought"]}.`;

  const attempts = [];
  const requested = sanitizeModel(model);

  for (const candidateModel of modelOrder(requested)) {
    const endpoint =
      `https://generativelanguage.googleapis.com/v1beta/models/${candidateModel}:generateContent`;

    for (let retry = 0; retry < 2; retry++) {
      let response;

      try {
        response = await fetchImpl(endpoint, {
          method: 'POST',
          headers: {
            'x-goog-api-key': key,
            'content-type': 'application/json'
          },
          body: JSON.stringify({
            contents: [{
              role: 'user',
              parts: [{ text: prompt }]
            }],
            generationConfig: {
              responseMimeType: 'application/json',
              temperature: 0.8,
              maxOutputTokens: 2400
            }
          }),
          signal: AbortSignal.timeout(12000)
        });
      } catch (error) {
        attempts.push(`${candidateModel}: temporary network error`);

        if (retry === 0) {
          await sleepImpl(700);
        }

        continue;
      }

      if (!response.ok) {
        const detail = errorMessage(
          response.status,
          await response.text().catch(() => '')
        );

        if (
          !TEMPORARY_STATUSES.has(response.status) &&
          !MODEL_UNAVAILABLE_STATUSES.has(response.status)
        ) {
          if (response.status === 400) {
            throw new Error(
              `Gemini 400: ${detail}. Check API request/model settings.`
            );
          }

          if (response.status === 401 || response.status === 403) {
            throw new Error(
              `Gemini ${response.status}: API key or project access denied. Check your AI Studio API key and permissions.`
            );
          }

          throw new Error(`Gemini ${response.status}: ${detail}`);
        }

        attempts.push(`${candidateModel}: HTTP ${response.status}`);

        // A model not offered to this project cannot be rescued by retrying.
        if (MODEL_UNAVAILABLE_STATUSES.has(response.status)) {
          break;
        }

        if (retry === 0) {
          const retryAfter = Number(response.headers?.get?.('retry-after'));

          const backoff =
            Number.isFinite(retryAfter) && retryAfter > 0
              ? Math.min(3000, Math.round(retryAfter * 1000))
              : 750 + Math.floor(Math.random() * 250);

          await sleepImpl(backoff);
        }

        continue;
      }

      try {
        const post = toPost(await response.json(), candidateModel);

        if (candidateModel !== requested) {
          post.aiNotice =
            `Selected ${requested} was unavailable; generated successfully with ${candidateModel}.`;
        }

        return post;
      } catch {
        attempts.push(`${candidateModel}: incomplete AI response`);

        if (retry === 0) {
          await sleepImpl(700);
        }
      }
    }
  }

  throw new GeminiUnavailableError(
    'All available Flash-Lite models failed temporarily or are inaccessible. A local original quote will be used instead.',
    attempts
  );
}
