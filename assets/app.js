// Medicare LLM Evaluation System - Frontend

const API_BASE = "http://localhost:8000/api";

const state = {
  models: [],
  selectedModels: [],
  currentRunId: null,
  pollInterval: null
};

const $ = (id) => document.getElementById(id);

// Helper to create elements
const el = (tag, cls = "", text = "") => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text) e.textContent = text;
  return e;
};

// Initialize app
async function init() {
  await loadModels();
  setupEventListeners();
}

// Load available models from API
async function loadModels() {
  try {
    const res = await fetch(`${API_BASE}/models`);
    const data = await res.json();
    state.models = data.models;
    renderModelCheckboxes();
  } catch (err) {
    console.error("Error loading models:", err);
    alert("Failed to load models. Make sure the backend server is running on port 8000.");
  }
}

// Render model checkboxes
function renderModelCheckboxes() {
  const container = $("modelCheckboxes");
  container.innerHTML = "";

  state.models.forEach(model => {
    const wrapper = el("label", "flex items-center gap-2 cursor-pointer");

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = model.id;
    checkbox.className = "w-4 h-4";
    checkbox.addEventListener("change", (e) => {
      if (e.target.checked) {
        state.selectedModels.push(model.id);
      } else {
        state.selectedModels = state.selectedModels.filter(id => id !== model.id);
      }
      updateRunButton();
    });

    const label = el("span", "", `${model.name} (${model.id})`);

    wrapper.appendChild(checkbox);
    wrapper.appendChild(label);
    container.appendChild(wrapper);
  });
}

// Update run button state
function updateRunButton() {
  const btn = $("runTestBtn");
  btn.disabled = state.selectedModels.length === 0;
}

// Setup event listeners
function setupEventListeners() {
  $("runTestBtn").addEventListener("click", runTest);
  $("cancelTestBtn").addEventListener("click", cancelTest);
  $("loadHistoryBtn").addEventListener("click", loadTestHistory);
}

// Run test
async function runTest() {
  if (state.selectedModels.length === 0) {
    alert("Please select at least one model");
    return;
  }

  try {
    // Disable button
    $("runTestBtn").disabled = true;
    $("runTestBtn").textContent = "Starting...";

    // Check if quick test is enabled
    const quickTest = $("quickTestCheckbox").checked;

    // Start test
    const res = await fetch(`${API_BASE}/test-runs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        models: state.selectedModels,
        quick_test: quickTest
      })
    });

    const data = await res.json();
    state.currentRunId = data.run_id;

    // Show status section and cancel button
    $("statusSection").classList.remove("hidden");
    $("cancelTestBtn").classList.remove("hidden");
    showStatus("running", "Test is running...");

    // Start polling for updates
    startPolling();

  } catch (err) {
    console.error("Error starting test:", err);
    alert("Failed to start test: " + err.message);
    $("cancelTestBtn").classList.add("hidden");
    $("runTestBtn").disabled = false;
    $("runTestBtn").textContent = "Run Test";
  }
}

// Show status
function showStatus(status, message) {
  const indicator = $("statusIndicator");
  indicator.innerHTML = "";

  let icon, color, text;
  if (status === "running") {
    icon = "⏳";
    color = "text-blue-600";
    text = "Running";
  } else if (status === "completed") {
    icon = "✓";
    color = "text-green-600";
    text = "Completed";
  } else if (status === "failed") {
    icon = "✗";
    color = "text-red-600";
    text = "Failed";
  }

  const statusEl = el("div", `flex items-center gap-2 ${color} font-semibold`);
  statusEl.innerHTML = `<span class="text-2xl">${icon}</span> <span>${text}</span>`;
  indicator.appendChild(statusEl);

  const messageEl = el("div", "text-slate-600", message);
  $("progressInfo").innerHTML = "";
  $("progressInfo").appendChild(messageEl);
}

// Start polling for test run updates
function startPolling() {
  if (state.pollInterval) {
    clearInterval(state.pollInterval);
  }

  // Poll every 2 seconds
  state.pollInterval = setInterval(async () => {
    await updateTestRun();
  }, 2000);

  // Also update immediately
  updateTestRun();
}

// Stop polling
function stopPolling() {
  if (state.pollInterval) {
    clearInterval(state.pollInterval);
    state.pollInterval = null;
  }
}

// Cancel test
function cancelTest() {
  // Stop polling
  stopPolling();

  // Clear current run
  state.currentRunId = null;

  // Hide sections
  $("statusSection").classList.add("hidden");
  $("resultsSection").classList.add("hidden");
  $("logsSection").classList.add("hidden");
  $("cancelTestBtn").classList.add("hidden");

  // Re-enable run button
  $("runTestBtn").disabled = false;
  $("runTestBtn").textContent = "Run Test";

  console.log("Test cancelled by user");
}

// Update test run status
async function updateTestRun() {
  if (!state.currentRunId) return;

  try {
    const res = await fetch(`${API_BASE}/test-runs/${state.currentRunId}`);
    const data = await res.json();

    const { test_run, responses, aggregates } = data;

    // Update status
    if (test_run.status === "completed") {
      showStatus("completed", `Test completed at ${new Date(test_run.created_at).toLocaleString()}`);
      stopPolling();
      displayResults(data);
      loadLogs();

      // Hide cancel button and re-enable run button
      $("cancelTestBtn").classList.add("hidden");
      $("runTestBtn").disabled = false;
      $("runTestBtn").textContent = "Run Test";
    } else if (test_run.status === "failed") {
      showStatus("failed", `Test failed: ${test_run.error_message || "Unknown error"}`);
      stopPolling();
      loadLogs();

      // Hide cancel button and re-enable run button
      $("cancelTestBtn").classList.add("hidden");
      $("runTestBtn").disabled = false;
      $("runTestBtn").textContent = "Run Test";
    } else {
      // Still running - show progress
      const progress = `${responses.length} responses collected...`;
      $("progressInfo").textContent = progress;
    }

  } catch (err) {
    console.error("Error updating test run:", err);
  }
}

// Display results
function displayResults(data) {
  const { responses, aggregates } = data;

  $("resultsSection").classList.remove("hidden");

  // Aggregate scores
  $("overallAvg").textContent = aggregates.overall_average?.toFixed(2) || "-";
  $("totalResponses").textContent = aggregates.total_responses || "0";
  $("scoredResponses").textContent = aggregates.scored_responses || "0";

  // Per-model averages
  const perModelContainer = $("perModelScores");
  perModelContainer.innerHTML = "";

  for (const [modelId, avg] of Object.entries(aggregates.per_model_average || {})) {
    const modelName = state.models.find(m => m.id === modelId)?.name || modelId;
    const bar = el("div", "flex items-center gap-3");
    const label = el("div", "w-32 text-sm font-medium", modelName);
    const scoreBar = el("div", "flex-1 bg-slate-200 rounded-full h-6 relative");
    const fill = el("div", "bg-blue-600 h-6 rounded-full flex items-center justify-center text-white text-xs font-semibold");
    fill.style.width = `${(avg / 10) * 100}%`;
    fill.textContent = avg.toFixed(2);
    scoreBar.appendChild(fill);
    bar.appendChild(label);
    bar.appendChild(scoreBar);
    perModelContainer.appendChild(bar);
  }

  // Score grid
  renderScoreGrid(responses);

  // Detailed responses
  renderDetailedResponses(responses);
}

// Render score grid
function renderScoreGrid(responses) {
  const table = $("scoreGrid");
  const thead = table.querySelector("thead tr");
  const tbody = table.querySelector("tbody");

  // Clear existing
  thead.innerHTML = "<th class='border p-2 text-left'>Question</th>";
  tbody.innerHTML = "";

  // Get unique models and questions
  const models = [...new Set(responses.map(r => r.model_id))];
  const questions = [...new Set(responses.map(r => r.question_id))];

  // Add model headers
  models.forEach(modelId => {
    const modelName = state.models.find(m => m.id === modelId)?.name || modelId;
    const th = el("th", "border p-2 text-center", modelName);
    thead.appendChild(th);
  });

  // Add rows for each question
  questions.forEach(questionId => {
    const row = el("tr", "hover:bg-slate-50");

    // Question cell
    const questionCell = el("td", "border p-2 font-medium", questionId);
    row.appendChild(questionCell);

    // Score cells for each model
    models.forEach(modelId => {
      const response = responses.find(r => r.question_id === questionId && r.model_id === modelId);
      const score = response?.score || 0;

      // Color code by score
      let bgColor = "bg-red-100";
      if (score >= 8) bgColor = "bg-green-100";
      else if (score >= 6) bgColor = "bg-yellow-100";
      else if (score >= 4) bgColor = "bg-orange-100";

      const cell = el("td", `border p-2 text-center ${bgColor} font-semibold`, score > 0 ? score.toFixed(1) : "-");
      row.appendChild(cell);
    });

    tbody.appendChild(row);
  });
}

// Render detailed responses
function renderDetailedResponses(responses) {
  const container = $("detailedResponses");
  container.innerHTML = "";

  // Group by question
  const byQuestion = {};
  responses.forEach(r => {
    if (!byQuestion[r.question_id]) {
      byQuestion[r.question_id] = [];
    }
    byQuestion[r.question_id].push(r);
  });

  // Render each question's responses
  for (const [questionId, questionResponses] of Object.entries(byQuestion)) {
    const questionBlock = el("div", "border rounded-lg p-4 bg-slate-50");

    const header = el("div", "font-bold text-lg mb-2", `${questionId}: ${questionResponses[0].question_text}`);
    questionBlock.appendChild(header);

    const groundTruth = el("div", "mb-3 p-3 bg-blue-50 rounded border-l-4 border-blue-600");
    const gtLabel = el("div", "font-semibold text-sm text-blue-800 mb-1", "Ground Truth:");
    const gtText = el("div", "text-sm", questionResponses[0].ground_truth);
    groundTruth.appendChild(gtLabel);
    groundTruth.appendChild(gtText);
    questionBlock.appendChild(groundTruth);

    // Model responses
    questionResponses.forEach(response => {
      const modelName = state.models.find(m => m.id === response.model_id)?.name || response.model_id;

      const responseBlock = el("div", "mb-2 p-3 bg-white rounded border");
      const responseHeader = el("div", "flex justify-between items-center mb-2");
      const modelLabel = el("div", "font-semibold", modelName);
      const score = el("div", "text-lg font-bold text-blue-600", `${response.score}/10`);
      responseHeader.appendChild(modelLabel);
      responseHeader.appendChild(score);

      const responseText = el("div", "text-sm text-slate-700", response.model_response);

      const metadata = el("div", "text-xs text-slate-500 mt-2");
      const similarity = response.scoring_metadata?.cosine_similarity;
      metadata.textContent = `Response time: ${response.response_time_ms}ms | Similarity: ${similarity ? similarity.toFixed(3) : 'N/A'}`;

      responseBlock.appendChild(responseHeader);
      responseBlock.appendChild(responseText);
      responseBlock.appendChild(metadata);
      questionBlock.appendChild(responseBlock);
    });

    container.appendChild(questionBlock);
  }
}

// Load logs
async function loadLogs() {
  if (!state.currentRunId) return;

  try {
    const res = await fetch(`${API_BASE}/test-runs/${state.currentRunId}/logs`);
    const data = await res.json();

    $("logsSection").classList.remove("hidden");

    const logEntries = $("logEntries");
    logEntries.innerHTML = "";

    data.logs.forEach(log => {
      const entry = el("div", "text-xs");

      let levelColor = "text-slate-600";
      if (log.level === "ERROR") levelColor = "text-red-600";
      else if (log.level === "WARNING") levelColor = "text-yellow-600";
      else if (log.level === "INFO") levelColor = "text-blue-600";

      const timestamp = new Date(log.timestamp).toLocaleTimeString();
      entry.innerHTML = `<span class="text-slate-400">${timestamp}</span> <span class="${levelColor} font-semibold">[${log.level}]</span> ${log.message}`;

      logEntries.appendChild(entry);
    });

  } catch (err) {
    console.error("Error loading logs:", err);
  }
}

// Load test history
async function loadTestHistory() {
  try {
    const res = await fetch(`${API_BASE}/test-runs?limit=10`);
    const data = await res.json();

    const container = $("testHistory");
    container.innerHTML = "";

    if (data.test_runs.length === 0) {
      container.innerHTML = "<p class='text-slate-500'>No test runs yet</p>";
      return;
    }

    data.test_runs.forEach(run => {
      const runEl = el("div", "border rounded-lg p-3 hover:bg-slate-50 cursor-pointer");
      runEl.addEventListener("click", () => loadTestRun(run.run_id));

      const header = el("div", "flex justify-between items-center");
      const runId = el("div", "font-mono text-sm", run.run_id.slice(0, 8));
      const status = el("div", `text-sm font-semibold ${run.status === 'completed' ? 'text-green-600' : run.status === 'failed' ? 'text-red-600' : 'text-blue-600'}`, run.status);
      header.appendChild(runId);
      header.appendChild(status);

      const details = el("div", "text-xs text-slate-600 mt-1");
      const date = new Date(run.created_at).toLocaleString();
      const models = run.models_tested.length;
      details.textContent = `${date} | ${models} models`;

      runEl.appendChild(header);
      runEl.appendChild(details);
      container.appendChild(runEl);
    });

  } catch (err) {
    console.error("Error loading test history:", err);
    alert("Failed to load test history");
  }
}

// Load a specific test run
async function loadTestRun(runId) {
  state.currentRunId = runId;

  try {
    const res = await fetch(`${API_BASE}/test-runs/${runId}`);
    const data = await res.json();

    const { test_run } = data;

    $("statusSection").classList.remove("hidden");
    showStatus(test_run.status, `Test from ${new Date(test_run.created_at).toLocaleString()}`);

    if (test_run.status === "completed") {
      displayResults(data);
    }

    loadLogs();

  } catch (err) {
    console.error("Error loading test run:", err);
    alert("Failed to load test run");
  }
}

// Initialize on page load
init();
