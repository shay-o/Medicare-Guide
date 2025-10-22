
const state = {
  intent: null, // 'do' or 'learn'
  topic: null,
  plan: "",
  zip: "",
  data: null,
  qa: [],
  last_card_id: null
};

const $ = (id) => document.getElementById(id);
const el = (tag, cls="", text="") => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text) e.textContent = text;
  return e;
};

function todayISO() {
  const d = new Date();
  return d.toISOString().slice(0,10);
}

async function loadData() {
  try {
    const res = await fetch("assets/seed.json");
    if (!res.ok) {
      throw new Error(`Failed to load data: ${res.status} ${res.statusText}`);
    }
    state.data = await res.json();
    $("last-reviewed").textContent = todayISO();
    renderSuggestions();
    console.info("Data loaded successfully");
  } catch (err) {
    console.error("Error loading data:", err);
    alert("Error loading data. If you're opening this file directly, please use a local web server instead.\n\nQuick fix:\n1. Open Terminal\n2. Navigate to the project folder\n3. Run: python3 -m http.server 8000\n4. Open http://localhost:8000 in your browser");
  }
}
loadData();

// Suggestions
function renderSuggestions() {
  const wrap = $("topicButtons");
  wrap.innerHTML = "";
  const topics = state.data.topics || [];
  // Show all topics since we no longer have intent filtering
  for (const t of topics) {
    const b = el("button", "px-3 py-2 rounded-xl border border-slate-300 hover:bg-slate-100", t.title || t.id);
    b.addEventListener("click", () => {
      // Clear text input and hide error when topic button is clicked
      $("utterance").value = "";
      $("matchError").classList.add("hidden");
      routeTo(t.id);
    });
    wrap.appendChild(b);
  }
}

// Routing
$("route").addEventListener("click", () => {
  // Check if data has loaded
  if (!state.data || !state.data.topics) {
    alert("Data is still loading. Please wait a moment and try again.");
    return;
  }

  // Hide any previous error message
  $("matchError").classList.add("hidden");

  state.plan = $("plan").value;
  state.zip = $("zip").value;
  const u = ($("utterance").value || "").toLowerCase().trim();

  // Only try to match if user entered text
  if (u) {
    console.info("Attempting to match user input:", u);
    let topicId = null;

    // Search through topics by title, summary, and id
    console.info("Searching topics for match");
    for (const topic of state.data.topics) {
      const title = (topic.title || "").toLowerCase();
      const summary = (topic.summary || "").toLowerCase();
      const id = (topic.id || "").toLowerCase();

      if (title.includes(u) || u.includes(title) ||
          summary.includes(u) || id.includes(u)) {
        topicId = topic.id;
        console.info("Match found:", topicId);
        break;
      }
    }

    if (!topicId) {
      // Show error message
      console.info("No match found");
      $("matchError").classList.remove("hidden");
      return;
    }

    console.info("Routing to topic:", topicId);
    routeTo(topicId);
  } else {
    // No text entered - show error
    $("matchError").textContent = "Please enter a topic or choose one below.";
    $("matchError").classList.remove("hidden");
  }
});

function routeTo(topicId) {
  state.topic = topicId;
  state.plan = $("plan").value;
  state.zip = $("zip").value;
  state.qa = [];
  renderCard();
  renderQA();
  console.info("route", {topic: topicId, plan: state.plan, zip: state.zip});
}

// Card rendering
function renderCard() {
  // Find topic by id
  const topic = state.data.topics.find(t => t.id === state.topic);
  if (!topic) return;

  $("cardSection").classList.remove("hidden");
  const card = $("card");
  card.innerHTML = "";

  const header = el("div", "mb-2");
  const title = el("h2", "text-xl font-semibold", topic.title || state.topic);
  header.appendChild(title);
  card.appendChild(header);

  // Add summary if present
  if (topic.summary) {
    const summary = el("p", "text-sm text-slate-600 mb-2", topic.summary);
    card.appendChild(summary);
  }

  const meta = el("div", "text-sm text-slate-600 mb-4");
  meta.textContent = `ZIP: ${state.zip || "n/a"} • Plan: ${state.plan || "n/a"}`;
  if (topic.last_updated) {
    meta.textContent += ` • Updated: ${topic.last_updated}`;
  }
  card.appendChild(meta);

  // Add source link if present
  if (topic.source) {
    const sourceLink = el("a", "text-sm text-blue-600 hover:underline mb-3 block", "View official source");
    sourceLink.href = topic.source;
    sourceLink.target = "_blank";
    sourceLink.rel = "noopener";
    card.appendChild(sourceLink);
  }

  if (topic.kind === "do") {
    const stepsH = el("h3", "font-semibold mt-3 mb-1", "What to do next");
    card.appendChild(stepsH);

    const steps = el("ol", "list-decimal ml-5 space-y-1");
    (topic.steps || []).forEach(stepText => {
      const li = el("li", "leading-relaxed", stepText);
      steps.appendChild(li);
    });
    card.appendChild(steps);
  } else {
    // Learn card
    const pointsH = el("h3", "font-semibold mt-2 mb-1", "Key points");
    card.appendChild(pointsH);
    const points = el("ul", "list-disc ml-5 space-y-1");
    (topic.points || []).forEach(p => points.appendChild(el("li","",p)));
    card.appendChild(points);
  }

  // Show QA section
  renderQA();
}

// QA rendering
function renderQA() {
  $("qaSection").classList.remove("hidden");
  const topic = state.data.topics.find(t => t.id === state.topic);
  // Suggested
  const sug = $("suggestedQ");
  sug.innerHTML = "";
  (topic?.followups || []).forEach(q => {
    const b = el("button","px-3 py-2 rounded-xl border border-slate-300 hover:bg-slate-100 text-sm", q);
    b.addEventListener("click", () => answerQuestion(q));
    sug.appendChild(b);
  });

  // Thread
  const wrap = $("qaThread");
  wrap.innerHTML = "";
  state.qa.forEach(item => {
    const card = el("div","border rounded-xl p-3");
    const q = el("div","font-semibold mb-1","Q: " + item.q);
    const a = el("div","", "A: " + item.a);
    const meta = el("div","text-xs text-slate-500 mt-1", `${item.source} • ${new Date(item.ts).toLocaleString()}`);
    card.appendChild(q); card.appendChild(a); card.appendChild(meta);
    wrap.appendChild(card);
  });
}

$("askBtn").addEventListener("click", () => {
  const q = $("qaInput").value.trim();
  if (!q) return;
  $("qaInput").value = "";
  answerQuestion(q);
});

function answerQuestion(q) {
  const topic = state.data.topics.find(t => t.id === state.topic);
  // Very simple heuristic answers:
  let a = "Thanks for your question. ";
  if (/cost|price|\$0|free/i.test(q)) {
    a += "Costs vary by plan and location. Preferred pharmacies and in-network providers are usually cheaper.";
  } else if (/prior auth|authorization/i.test(q)) {
    a += "Some Medicare Advantage plans require prior authorization. Call your plan to confirm before scheduling.";
  } else if (/network|in[- ]?network|out[- ]?of[- ]?network/i.test(q)) {
    a += "Using in-network providers helps avoid extra charges. Use your plan's provider finder.";
  } else if (/codes|cpt|hcpcs/i.test(q)) {
    a += "Ask your clinician for the CPT/HCPCS codes. You can share those with your plan to estimate costs.";
  } else if (/apply|enroll|sign up/i.test(q)) {
    a += "Check the official Medicare or Social Security website for enrollment information, or call 1-800-MEDICARE.";
  } else {
    a += "For more details, please check the official source link on this card or contact your plan directly.";
  }

  state.qa.push({ q, a, source: "qa", ts: new Date().toISOString() });
  renderQA();
  console.info("ask_question", {topic: state.topic, q});
}
