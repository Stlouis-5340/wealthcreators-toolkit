# Reels — 26 Oct 2026

Three vertical cuts from real footage. Nothing here was generated as a talking head, and nothing was posted.

Comment keyword for every reel: **CLASS**.
CTA: comment CLASS for the free Wealth Creation Class.
These clips are education, not a recommendation to buy, borrow, or file anything a particular way.

Durations below are the encoded files. In/out times are on the source clock.

## reel1_yield_real.mp4

- **Source:** Wealth Creators Webinar, Vimeo. Page `https://vimeo.com/1233097501/da48e7b9b4`. Player URL used by yt-dlp: `https://player.vimeo.com/video/1233097501?h=da48e7b9b4` with referer `https://vimeo.com/`.
- **Search window:** about 0:34:45–0:36:05 (yield-sign hook).
- **In:** 0:34:48.84
- **Out:** 0:35:58.55
- **Encoded duration:** 69.71s
- **Why this cut:** The kept take starts on “What color is a yield sign?” — the repeat — so the line “when would you want to know about it?” still fits under 70 seconds. The first ask and “let me know in the chat” sit just before this in-point. The shout-outs after 0:36:05 are out.
- **Spoken gist:** He asks what color a yield sign is. Most of the room says yellow. He says it is not yellow anymore — it used to be, and a yield sign is red and white. People drive past them over and over and still have the color wrong. Then he turns it: if you can be wrong about a sign you see every drive, you can also be pre-programmed with ideas about money that are not true. If what you thought was true about money turned out not to be, when would you want to know?
- **On-screen text:** No captions burned by this pipeline. The webinar slide stays mostly outside the speaker crop.
- **Suggested IG caption:** What color is a yield sign? Most people say yellow. They’re sure. And they’re wrong. A yield sign is red and white — and you’ll pass a handful of them every drive without noticing. So here’s the real question: if something you believed about money turned out not to be true, when would you want to know? Comment **CLASS** and I’ll send the free Wealth Creation Class. Education only.
- **Hashtags:** #yieldsign #moneymindset #wealthcreators #financialeducation #moneytalk #learnmoney

## reel2_money_babies_real.mp4

- **Source:** `Money Babies_ Your Guide to Buying Assets.mp4` inside the public Dropbox folder `https://www.dropbox.com/scl/fo/gzh9f50in6rt1qo7a9c1e/AIJVAce-yL93Rvjyv5c_A-I/27?rlkey=607fyy3m97653udbpdy33xce7&dl=0`.
- **In:** 0:00.00
- **Out:** end of file (the file is already one vertical piece, and the whole thing is the money-babies / pregnant-money point).
- **Encoded duration:** 58.58s
- **Spoken gist:** Your job is to make money babies. You can’t make a money baby if the parents aren’t there — the parents are the capital you build, the babies are the cash flow, and then you want money grandbabies. A lot of people buy stuff instead of assets. From here, the job is to buy assets. Some people are far enough along that the next move is paying the debt down, but until then you build, and any debt you use should produce an asset, not something you consume.
- **On-screen text:** The Dropbox master already has burned-in kinetic words (“money babies”, “pregnant money”, and the asset lines). There is no clean plate, so this pipeline does not invent a `_clean` file and does not add a second caption layer.
- **Suggested IG caption:** Money babies need parents. The parents are the capital. The babies are the cash flow. Then come the grandbabies. Buying stuff doesn’t do that. Buying assets does. Comment **CLASS** and I’ll send the free Wealth Creation Class. Education only.
- **Hashtags:** #moneybabies #cashflow #buyassets #wealthcreators #realestate #financialeducation

## reel3_loan_tax_real.mp4

- **Requested source:** YouTube `https://www.youtube.com/watch?v=Erb1J65ozQ4` (“How to Become Your Own Bank | Marvin Mitchell Interview with Myron Golden Part 1”), for the “interest rate later” / tax-deferred loan analogy.
- **Fallback used:** same Vimeo webinar as reel 1. yt-dlp on this machine gets “Sign in to confirm you’re not a bot” for that YouTube URL (no captions, no formats), and public front-ends tried from here failed the same way. This cut is the fallback the brief named: tax-deferred is not tax-free, inside about 0:30:33–0:33:00. It is **not** the YouTube loan-analogy line.
- **In:** 0:32:03.40
- **Out:** 0:32:59.85
- **Encoded duration:** 56.47s
- **Spoken gist:** Most of us were handed one path, and it works for the IRS more than it works for you. The problem isn’t effort, it’s the order: school, a job, trade hours for pay, buy a house, pay interest, max the 401(k), defer the taxes until later, retire, and hope the market and the tax rates cooperate. A plan built on hope isn’t a plan. Tax-deferred is not tax-free. Deferring the bill just hands the IRS a bigger slice later, when required minimum distributions turn it into taxable income at rates that may already be higher.
- **On-screen text:** No captions burned by this pipeline. The slide “TAX-DEFERRED ≠ TAX-FREE” is on the left of the webinar frame and is mostly outside the speaker crop.
- **Not tax advice:** This is education about how tax-deferral is described in the webinar. It is not tax advice, not a filing recommendation, and not a suggestion to change a retirement account.
- **Suggested IG caption:** Tax-deferred is not tax-free. The usual path — job, house, max the 401(k), defer the taxes until later, then hope — can hand the IRS a bigger slice when the bill comes due. A real plan isn’t built on hope. Comment **CLASS** and I’ll send the free Wealth Creation Class. Education only. This is not tax advice.
- **Hashtags:** #taxdeferred #financialeducation #wealthcreators #moneymindset #401k #learnmoney

## Pipeline

`scripts/reels-oct26/run.sh` downloads the windows and encodes `output/reel1_yield_real.mp4`, `output/reel2_money_babies_real.mp4`, and `output/reel3_loan_tax_real.mp4`. Large masters stay in `work/` and `output/`, which are gitignored.
