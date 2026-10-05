# AI for Everyone

A friendly one-page website that explains everyday AI in plain English. It includes a 5-question quiz, simple safety tips and links to free beginner courses.

It's built with plain HTML, CSS and JavaScript, so there's nothing to install and no build step.

## Files

| File | What it does |
|---|---|
| `index.html` | The page content, from top to bottom: header, hero, "What is AI?", quiz, stay-safe tips, learn more, footer |
| `styles.css` | All the styling. Change the colours in `:root` at the top to re-theme the site, including dark mode |
| `script.js` | Part A is the quiz logic. Part B is the mobile menu and the footer year |
| `standalone-quiz.html` | The original quiz as a single file you can open by double-clicking or attach to an email |
| `.nojekyll` | Tells GitHub Pages to serve the files exactly as they are |

## Editing the quiz questions

Open `script.js` and edit the `questions` list near the top. Each question has these fields:

```js
{
  question: "The question text?",
  options: ["Option 1", "Option 2", "Option 3", "Option 4", "Option 5"],
  answer: "Option 1",            // must match one option exactly
  explanation: "Shown after the visitor answers."
}
```

The answer order is shuffled automatically. The progress bar, question count and score all adjust if you add or remove questions.

## Preview locally

```bash
cd ai-literacy-quiz
python3 -m http.server 8000
```

Then open http://localhost:8000. You can also double-click `index.html`.

## Publish on GitHub Pages

1. Create an empty repository on GitHub, for example `ai-for-everyone`.
2. Push this folder to it:
   ```bash
   git remote add origin https://github.com/<your-username>/ai-for-everyone.git
   git push -u origin main
   ```
3. On GitHub, open the repository and go to **Settings → Pages**. Under **Build and deployment**, choose **Deploy from a branch**, then branch **main**, folder **/ (root)**, and click **Save**.
4. After a minute or two the site is live at `https://<your-username>.github.io/ai-for-everyone/`.

Any later changes go live automatically after you `git push`.
