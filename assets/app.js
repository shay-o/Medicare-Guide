
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
  const res = await fetch("assets/seed.json");
  state.data = await res.json();
  $("last-reviewed").textContent = todayISO();
  renderSuggestions();
}
loadData();

// Intent handlers
$("btnDo").addEventListener("click", () => { state.intent = "do"; highlightIntent(); });
$("btnLearn").addEventListener("click", () => { state.intent = "learn"; highlightIntent(); });

function highlightIntent() {
  $("btnDo").classList.toggle("bg-blue-50", state.intent === "do");
  $("btnLearn").classList.toggle("bg-blue-50", state.intent === "learn");
}

// Suggestions
function renderSuggestions() {
  const wrap = $("topicButtons");
  wrap.innerHTML = "";
  const entries = Object.entries(state.data.topics);
  const visible = entries.filter(([key, t]) => !state.intent || t.type === state.intent);
  for (const [key, t] of visible) {
    const b = el("button", "px-3 py-2 rounded-xl border border-slate-300 hover:bg-slate-100", t.label || key);
    b.addEventListener("click", () => routeTo(key));
    wrap.appendChild(b);
  }
}

// Routing
$("route").addEventListener("click", () => {
  state.plan = $("plan").value;
  state.zip = $("zip").value;
  const u = ($("utterance").value || "").toLowerCase().trim();
  const table = state.data.routing_table || {};
  let topic = null;
  for (const [k, v] of Object.entries(table)) {
    if (u.includes(k)) { topic = v; break; }
  }
  if (!topic && state.intent) {
    // fallback: first topic that matches intent
    topic = Object.entries(state.data.topics).find(([id, t]) => t.type === state.intent)?.[0] || null;
  }
  if (!topic) {
    alert("I could not figure that out. Pick a topic below.");
    return;
  }
  routeTo(topic);
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
  const topic = state.data.topics[state.topic];
  if (!topic) return;

  $("cardSection").classList.remove("hidden");
  const card = $("card");
  card.innerHTML = "";

  const header = el("div", "mb-2");
  const title = el("h2", "text-xl font-semibold", topic.label || state.topic);
  header.appendChild(title);
  card.appendChild(header);

  const meta = el("div", "text-sm text-slate-600 mb-4");
  meta.textContent = `Intent: ${topic.type.toUpperCase()} • ZIP: ${state.zip || "n/a"} • Plan: ${state.plan || "n/a"}`;
  card.appendChild(meta);

  if (topic.type === "do") {
    const what = el("p", "mb-2");
    what.innerHTML = `<span class="font-semibold">What you get:</span> ${topic.what_you_get}`;
    card.appendChild(what);

    const cost = el("p", "mb-3");
    cost.innerHTML = `<span class="font-semibold">What it costs:</span> ${topic.cost_band} <span class="text-xs text-slate-500">(estimate)</span>`;
    card.appendChild(cost);

    const stepsH = el("h3", "font-semibold mt-3 mb-1", "What to do next");
    card.appendChild(stepsH);

    const steps = el("ol", "list-decimal ml-5 space-y-1");
    topic.steps.forEach(s => {
      const li = el("li", "leading-relaxed");
      const explainBtn = el("button", "ml-2 text-xs px-2 py-0.5 rounded border border-slate-300 hover:bg-slate-100", "Explain this step");
      explainBtn.addEventListener("click", () => showExplanation(s.id, topic));
      li.textContent = s.text;
      li.appendChild(explainBtn);
      steps.appendChild(li);
    });
    card.appendChild(steps);

    if (topic.heads_up?.length) {
      const huH = el("h3", "font-semibold mt-4 mb-1", "Heads up");
      const hu = el("ul", "list-disc ml-5 space-y-1");
      topic.heads_up.forEach(h => hu.appendChild(el("li", "", h)));
      card.appendChild(huH);
      card.appendChild(hu);
    }
  } else {
    // Learn card
    const whatH = el("h3", "font-semibold mt-2 mb-1", "What this means");
    card.appendChild(whatH);
    const what = el("ul", "list-disc ml-5 space-y-1");
    topic.what_this_means?.forEach(t => what.appendChild(el("li","",t)));
    card.appendChild(what);

    const whyH = el("h3", "font-semibold mt-3 mb-1", "Why it matters");
    card.appendChild(whyH);
    const why = el("ul", "list-disc ml-5 space-y-1");
    topic.why_it_matters?.forEach(t => why.appendChild(el("li","",t)));
    card.appendChild(why);

    if (topic.example) {
      const exH = el("h3", "font-semibold mt-3 mb-1", "Example");
      const ex = el("p", "mb-2", topic.example);
      card.appendChild(exH);
      card.appendChild(ex);
    }

    if (topic.key_terms?.length) {
      const ktH = el("h3", "font-semibold mt-3 mb-1", "Key terms");
      const kt = el("div", "flex flex-wrap gap-2");
      topic.key_terms.forEach(k => {
        const tag = el("span", "text-xs px-2 py-1 rounded-full border border-slate-300", k);
        kt.appendChild(tag);
      });
      card.appendChild(ktH);
      card.appendChild(kt);
    }

    if (topic.link_do?.length) {
      const linkWrap = el("div", "mt-3");
      const btn = el("button", "px-3 py-2 rounded-xl bg-blue-600 text-white", "Now help me do this");
      btn.addEventListener("click", () => routeTo(topic.link_do[0]));
      linkWrap.appendChild(btn);
      card.appendChild(linkWrap);
    }
  }

  // Show QA section
  renderQA();
}

function showExplanation(stepId, topic) {
  const text = topic.followups?.explanations?.[stepId] || "No details available.";
  // append to QA thread as an 'Explain' event
  state.qa.push({
    q: `Explain step ${stepId}`,
    a: text,
    source: "explain",
    ts: new Date().toISOString()
  });
  renderQA();
  console.info("expand_explanation", { topic: state.topic, stepId });
}

// QA rendering
function renderQA() {
  $("qaSection").classList.remove("hidden");
  const topic = state.data.topics[state.topic];
  // Suggested
  const sug = $("suggestedQ");
  sug.innerHTML = "";
  (topic.followups?.suggested || []).forEach(q => {
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
  const topic = state.data.topics[state.topic];
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
  } else {
    a += "Here are details related to this card. ";
  }
  // add topic-specific hint
  if (topic.type === "do" && topic.followups?.explanations) {
    a += " You can also tap 'Explain this step' for details on each action.";
  }

  state.qa.push({ q, a, source: "qa", ts: new Date().toISOString() });
  renderQA();
  console.info("ask_question", {topic: state.topic, q});
}
