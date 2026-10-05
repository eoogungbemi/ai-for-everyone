// =========================================================
// AI for Everyone: site script
// Part A: the quiz. Each round draws 5 random questions from the built-in
//         ones plus the AI-generated bank in questions.json
// Part B: small site behaviours (mobile menu, footer year)
// =========================================================

// ======================= Part A: Quiz =======================

// ---- 1. The built-in questions (always available) ---------------------
// To add or change a question, edit this list.
// "answer" is the exact text of the correct option.
const builtInQuestions = [
  {
    question: "What is AI (Artificial Intelligence)?",
    options: [
      "Computer programs that learn from lots of examples to do tasks like recognising voices or suggesting things",
      "A robot that thinks and feels like a person",
      "A website that stores your photos",
      "A type of computer virus",
      "A super-fast internet connection"
    ],
    answer: "Computer programs that learn from lots of examples to do tasks like recognising voices or suggesting things",
    explanation: "AI is software that spots patterns in huge amounts of examples. It doesn't think or feel like a human. It's very good at guessing what usually comes next."
  },
  {
    question: "Where might you already be using AI without realising?",
    options: [
      "Your phone suggesting the next word as you type",
      "Flicking a light switch",
      "Writing on a paper calendar",
      "Reading a printed newspaper",
      "Winding up an old wristwatch"
    ],
    answer: "Your phone suggesting the next word as you type",
    explanation: "Predictive text, voice assistants, spam filters and 'you might also like' suggestions all use AI behind the scenes."
  },
  {
    question: "An AI chatbot tells you a 'fact' that sounds very convincing. What should you do?",
    options: [
      "Double-check it with a trusted source",
      "Believe it, because AI is never wrong",
      "Share it with friends straight away",
      "Never use AI for anything again",
      "Ask the same chatbot if it's sure, and trust that answer"
    ],
    answer: "Double-check it with a trusted source",
    explanation: "AI chatbots can sound confident even when they're wrong (sometimes called 'hallucinating'). Asking the same chatbot again isn't a real check. Use a trusted website, book or expert."
  },
  {
    question: "Which of these should you NOT type into a public AI chatbot?",
    options: [
      "Your bank password or card details",
      "A question about a recipe",
      "A request for a birthday poem",
      "Asking what a word means",
      "Asking for tips to plan a holiday"
    ],
    answer: "Your bank password or card details",
    explanation: "What you type into a chatbot may be stored or reviewed. Treat it like a public place, so never share passwords, bank details or other private information."
  },
  {
    question: "You see a video of a celebrity saying something shocking online. What's a smart thought?",
    options: [
      "It could be a 'deepfake' (a fake video made with AI), so check reliable news first",
      "Videos are always real",
      "If lots of people shared it, it must be true",
      "Only photos can be faked, not videos",
      "If it looks clear and high quality, it must be genuine"
    ],
    answer: "It could be a 'deepfake' (a fake video made with AI), so check reliable news first",
    explanation: "AI can now make realistic fake videos and voices. Before you believe or share something surprising, see if trusted news outlets are reporting it too."
  }
];

// ---- 1b. The AI-generated question bank -------------------------------
// questions.json is made by generator/generate_questions.py with a local AI
// model (Ollama). If it can't load (e.g. the page was opened by
// double-clicking the file), the quiz simply uses the built-in questions.
const ROUND_SIZE = 5;
let questionPool = builtInQuestions;
let questions = builtInQuestions;   // the questions in the current round

// Skip any bank entry that's malformed, so one bad question can't break the quiz
function isValidQuestion(q) {
  return q && typeof q.question === "string" && typeof q.explanation === "string" &&
    Array.isArray(q.options) && q.options.length >= 2 &&
    q.options.every(o => typeof o === "string") && q.options.includes(q.answer);
}

async function loadQuestionBank() {
  try {
    const res = await fetch("questions.json", { cache: "no-cache" });
    if (!res.ok) return;
    const data = await res.json();
    const extra = (data.questions || []).filter(isValidQuestion);
    questionPool = [...builtInQuestions, ...extra];
  } catch (err) {
    // No bank available: the built-in questions still work.
  }
  updatePoolNote();
}

// Tell visitors where the questions come from
function updatePoolNote() {
  const aiCount = questionPool.filter(q => q.source === "ai").length;
  $("pool-note").textContent = aiCount
    ? `Each round picks ${ROUND_SIZE} at random from ${questionPool.length} questions. ` +
      `${aiCount} of them were written by a small AI model and are marked "🤖 AI-written".`
    : "";
}

// ---- 2. Grab the page elements we need --------------------------------
const $ = (id) => document.getElementById(id);
const startScreen  = $("start-screen");
const quizScreen   = $("quiz-screen");
const resultScreen = $("result-screen");
const questionText = $("question-text");
const optionsBox   = $("options");
const feedbackBox  = $("feedback");
const nextBtn      = $("next-btn");
const progressLbl  = $("progress-label");
const progressFill = $("progress-fill");
const aiBadge      = $("ai-badge");

// ---- 3. Quiz state: where we are and how we're doing ------------------
let state = { index: 0, score: 0, answers: [] };

// Fisher–Yates shuffle (returns a new array) so the right answer moves around
function shuffle(list) {
  const copy = [...list];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

// Show one screen, hide the others
function showScreen(screen) {
  [startScreen, quizScreen, resultScreen].forEach(s => s.classList.add("hidden"));
  screen.classList.remove("hidden");
}

// ---- 4. Draw the current question -------------------------------------
function showQuestion() {
  const q = questions[state.index];

  progressLbl.textContent = `Question ${state.index + 1} of ${questions.length}`;
  progressFill.style.width = `${(state.index / questions.length) * 100}%`;
  questionText.textContent = q.question;
  aiBadge.classList.toggle("hidden", q.source !== "ai");

  // Reset feedback, the Next button and the old options
  feedbackBox.className = "feedback hidden";
  feedbackBox.innerHTML = "";
  nextBtn.classList.add("hidden");
  optionsBox.innerHTML = "";

  // Make one button per (shuffled) option
  shuffle(q.options).forEach(text => {
    const btn = document.createElement("button");
    btn.className = "option";
    btn.innerHTML = `<span class="label"></span><span class="mark" aria-hidden="true"></span>`;
    btn.querySelector(".label").textContent = text;
    btn.addEventListener("click", () => selectAnswer(btn, text));
    optionsBox.appendChild(btn);
  });
}

// ---- 5. Handle a click on an answer -----------------------------------
function selectAnswer(chosenBtn, chosenText) {
  const q = questions[state.index];
  const isCorrect = chosenText === q.answer;

  if (isCorrect) state.score++;
  state.answers.push({ question: q.question, chosen: chosenText, correct: isCorrect, answer: q.answer });

  // Lock all options and show which was right and which was wrong
  optionsBox.querySelectorAll(".option").forEach(btn => {
    btn.disabled = true;
    const text = btn.querySelector(".label").textContent;
    if (text === q.answer) {
      btn.classList.add("correct");
      btn.querySelector(".mark").textContent = "✓";
    } else if (btn === chosenBtn) {
      btn.classList.add("wrong");
      btn.querySelector(".mark").textContent = "✗";
    }
  });

  // Explain why
  feedbackBox.className = `feedback ${isCorrect ? "correct" : "wrong"}`;
  feedbackBox.innerHTML = `<strong>${isCorrect ? "✓ Correct!" : "✗ Not quite."}</strong><span></span>`;
  feedbackBox.querySelector("span").textContent = q.explanation;

  progressFill.style.width = `${((state.index + 1) / questions.length) * 100}%`;
  nextBtn.textContent = state.index === questions.length - 1 ? "See my result →" : "Next question →";
  nextBtn.classList.remove("hidden");
  nextBtn.focus();
}

// ---- 6. Move on: next question, or results ----------------------------
function next() {
  state.index++;
  if (state.index < questions.length) {
    showQuestion();
  } else {
    showResults();
  }
}

// ---- 7. The results screen --------------------------------------------
function showResults() {
  const total = questions.length;
  $("score-text").textContent = `${state.score} / ${total}`;

  let message;
  if (state.score === total)    message = "Brilliant! You're an AI-savvy pro. Share what you know with friends and family.";
  else if (state.score >= 3)    message = "Nice work! You've got a solid grasp of everyday AI. Check the answers below to fill any gaps.";
  else                          message = "Good start! AI is new for lots of people. Read the answers below. You'll be spotting AI everywhere soon.";
  $("score-message").textContent = message;

  // Recap each question
  const list = $("review-list");
  list.innerHTML = "";
  state.answers.forEach((a, i) => {
    const li = document.createElement("li");
    li.innerHTML = `<span class="q"></span><span class="${a.correct ? "ok" : "bad"}"></span>`;
    li.querySelector(".q").textContent = `${i + 1}. ${a.question}`;
    li.querySelector(a.correct ? ".ok" : ".bad").textContent = a.correct
      ? `✓ ${a.chosen}`
      : `✗ You said: ${a.chosen}. Correct answer: ${a.answer}`;
    list.appendChild(li);
  });

  showScreen(resultScreen);
  $("restart-btn").focus();
}

// ---- 8. Start / restart ------------------------------------------------
function start() {
  questions = shuffle(questionPool).slice(0, ROUND_SIZE);   // a fresh random round
  state = { index: 0, score: 0, answers: [] };
  showScreen(quizScreen);
  showQuestion();
}

$("start-btn").addEventListener("click", start);
$("restart-btn").addEventListener("click", start);
nextBtn.addEventListener("click", next);
loadQuestionBank();

// ======================= Part B: Site =======================

// ---- 9. Mobile menu: the ☰ button opens and closes the nav ---------------
const menuToggle = $("menu-toggle");
const navLinks   = $("nav-links");

function setMenu(open) {
  navLinks.classList.toggle("open", open);
  menuToggle.setAttribute("aria-expanded", String(open));
  menuToggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
  menuToggle.textContent = open ? "✕" : "☰";
}

menuToggle.addEventListener("click", () => setMenu(!navLinks.classList.contains("open")));

// Close the menu after a link is tapped, or when Escape is pressed
navLinks.querySelectorAll("a").forEach(link => link.addEventListener("click", () => setMenu(false)));
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && navLinks.classList.contains("open")) {
    setMenu(false);
    menuToggle.focus();
  }
});

// ---- 10. Footer year stays current automatically --------------------------
$("year").textContent = new Date().getFullYear();
