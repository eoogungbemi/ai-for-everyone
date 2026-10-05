# AI for Everyone

A friendly one-page website that explains everyday AI in plain English. It includes a 5-question quiz, simple safety tips and links to free beginner courses.

It's built with plain HTML, CSS and JavaScript, so there's nothing to install and no build step.

## Files

| File | What it does |
|---|---|
| `index.html` | The page content, from top to bottom: header, hero, "What is AI?", quiz, stay-safe tips, learn more, footer |
| `styles.css` | All the styling. Change the colours in `:root` at the top to re-theme the site, including dark mode |
| `script.js` | Part A is the quiz logic, with 5 built-in questions plus the bank. Part B is the mobile menu and the footer year |
| `questions.json` | Extra questions written by a local AI model. Each round picks 5 at random from these plus the built-in ones |
| `generator/` | The Python script that writes `questions.json` with Ollama, plus its tests |
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

## Generating new questions with AI (Ollama)

`generator/generate_questions.py` uses a small AI model running on your own computer (through [Ollama](https://ollama.com)) to write a fresh bank of questions on 10 everyday-AI topics. It saves them to `questions.json`, and the site labels them "🤖 AI-written".

GitHub Pages can't run AI models, so you generate the bank on your Mac and then publish the file.

```bash
ollama pull llama3.2:3b                         # one-time download (~2 GB)
python3 generator/generate_questions.py         # ~4 questions per topic
python3 generator/generate_questions.py --model gemma4:31b --per-topic 3   # slower, more accurate
```

Before a question is kept, it must pass two automatic checks:
1. **Rules:** exactly 5 different options, a sensible length, no "all of the above", and not a near-copy of an existing question.
2. **A blind test:** the model answers its own question with the options shuffled. If it picks a different answer, the question is thrown out.

**Always read the new bank before publishing.** Small models still write questions with wrong advice or two right answers, and the automatic checks can't catch those. In the first run, 10 of 37 questions passed a careful fact-check. Delete any bad entries from `questions.json`, then commit and push.

If no bank is available, the site falls back to the 5 built-in questions. This also happens when you open `index.html` by double-clicking, because browsers block loading a separate file from a page opened that way. Preview with the local server below to see the full bank.

Run the generator's tests with `python3 -m unittest discover generator`.

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
