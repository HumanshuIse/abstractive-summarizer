const input = document.querySelector("#inputText");
const summarizeButton = document.querySelector("#summarizeBtn");
const summaryText = document.querySelector("#summaryText");
const emptyState = document.querySelector("#emptyState");
const resultError = document.querySelector("#resultError");
const stats = document.querySelector("#stats");
const copyButton = document.querySelector("#copySummary");
const downloadButton = document.querySelector("#downloadSummary");
const clearResultButton = document.querySelector("#clearResult");

const sampleText = `Researchers are developing new approaches to make renewable energy more reliable and affordable. Solar and wind power have expanded rapidly, but their output changes with weather conditions. Energy storage systems can save electricity when production is high and release it when demand rises. Batteries are becoming less expensive, while pumped hydroelectric storage and green hydrogen offer alternatives for different scales. Modern forecasting tools also help grid operators plan for changing supply. Experts say that combining several technologies, improving transmission networks, and encouraging flexible electricity use will be essential. These changes could reduce emissions while creating a more resilient energy system for communities and businesses.`;

function updateCounts() {
  const words = input.value.trim() ? input.value.trim().split(/\s+/).length : 0;
  document.querySelector("#wordCount").textContent = `${words} words`;
  document.querySelector("#charCount").textContent = `${input.value.length} characters`;
  summarizeButton.disabled = words === 0;
}
function setLoading(loading) {
  summarizeButton.disabled = loading;
  document.querySelector("#buttonLabel").classList.toggle("d-none", loading);
  document.querySelector("#buttonLoading").classList.toggle("d-none", !loading);
}
function showError(message) {
  resultError.textContent = message;
  resultError.classList.remove("d-none");
}
function clearError() { resultError.textContent = ""; resultError.classList.add("d-none"); }
function clearResult() {
  summaryText.textContent = "";
  summaryText.classList.add("d-none");
  emptyState.classList.remove("d-none");
  stats.classList.add("d-none");
  copyButton.disabled = downloadButton.disabled = clearResultButton.disabled = true;
  clearError();
}
input.addEventListener("input", updateCounts);
document.querySelector("#loadSample").addEventListener("click", () => { input.value = sampleText; updateCounts(); input.focus(); });
document.querySelector("#clearInput").addEventListener("click", () => { input.value = ""; updateCounts(); input.focus(); });
clearResultButton.addEventListener("click", clearResult);

summarizeButton.addEventListener("click", async () => {
  clearError(); setLoading(true);
  try {
    const response = await fetch("/api/summarize", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({text: input.value, summary_length: document.querySelector("#summaryLength").value}) });
    const data = await response.json();
    if (!response.ok || !data.success) throw new Error(data.error || "The summary could not be generated.");
    summaryText.textContent = data.summary;
    summaryText.classList.remove("d-none"); emptyState.classList.add("d-none");
    const s = data.statistics;
    document.querySelector("#originalWords").textContent = s.original_word_count;
    document.querySelector("#summaryWords").textContent = s.summary_word_count;
    document.querySelector("#compression").textContent = `${s.compression_ratio}%`;
    document.querySelector("#processingTime").textContent = `${s.processing_time}s`;
    stats.classList.remove("d-none");
    copyButton.disabled = downloadButton.disabled = clearResultButton.disabled = false;
  } catch (error) { showError(error.message || "Network error. Please check the server and try again."); }
  finally { setLoading(false); updateCounts(); }
});
copyButton.addEventListener("click", async () => {
  try { await navigator.clipboard.writeText(summaryText.textContent); copyButton.innerHTML = '<i class="fa-solid fa-check me-1"></i> Copied'; setTimeout(() => { copyButton.innerHTML = '<i class="fa-regular fa-copy me-1"></i> Copy Summary'; }, 1600); }
  catch (_error) { showError("Clipboard access failed. Select and copy the summary manually."); }
});
downloadButton.addEventListener("click", () => {
  const blob = new Blob([summaryText.textContent], {type: "text/plain"});
  const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = "summary.txt"; link.click(); URL.revokeObjectURL(link.href);
});
updateCounts();
