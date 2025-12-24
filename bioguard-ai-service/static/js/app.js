const form = document.getElementById("uploadForm");
const fileInput = document.getElementById("imageFile");

const loading = document.getElementById("loading");
const results = document.getElementById("results");
const errorAlert = document.getElementById("errorAlert");
const errorMessage = document.getElementById("errorMessage");

const originalImage = document.getElementById("originalImage");
const bboxImage = document.getElementById("bboxImage");

const resultCard = document.getElementById("resultCard");
const resultIcon = document.getElementById("resultIcon");
const resultText = document.getElementById("resultText");
const confidenceBar = document.getElementById("confidenceBar");
const confidenceText = document.getElementById("confidenceText");
const probReal = document.getElementById("probReal");
const probFake = document.getElementById("probFake");
const probUnknown = document.getElementById("probUnknown");

function showError(msg) {
  errorMessage.textContent = msg;
  errorAlert.style.display = "block";
}

function hideError() {
  errorAlert.style.display = "none";
  errorMessage.textContent = "";
}

function setLoading(isLoading) {
  loading.style.display = isLoading ? "block" : "none";
}

function setResultsVisible(visible) {
  results.style.display = visible ? "block" : "none";
}

function pct(x) {
  return `${Math.round(x * 10000) / 100}%`;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideError();
  setResultsVisible(false);
  setLoading(true);

  const file = fileInput.files?.[0];
  if (!file) {
    setLoading(false);
    showError("Please select an image.");
    return;
  }

  try {
    const fd = new FormData();
    fd.append("file", file);

    const res = await fetch("/api/predict", { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data?.detail || "Prediction failed");
    }

    originalImage.src = `data:image/jpeg;base64,${data.image_data}`;
    bboxImage.src = `data:image/jpeg;base64,${data.bbox_image_data}`;

    const r = data.result;
    const isReal = !!r.is_real;
    const conf = r.confidence ?? 0;

    resultCard.classList.remove("real", "fake");
    resultCard.classList.add(isReal ? "real" : "fake");
    resultIcon.innerHTML = isReal
      ? '<i class="fas fa-check-circle fa-3x text-success"></i>'
      : '<i class="fas fa-times-circle fa-3x text-danger"></i>';
    resultText.textContent = isReal ? "REAL FACE" : "FAKE FACE";

    confidenceBar.style.width = `${Math.min(100, Math.max(0, conf * 100))}%`;
    confidenceBar.className = `progress-bar ${isReal ? "bg-success" : "bg-danger"}`;
    confidenceText.textContent = `Confidence: ${pct(conf)}`;

    probReal.textContent = pct(r.probabilities?.real ?? 0);
    probFake.textContent = pct(r.probabilities?.fake ?? 0);
    probUnknown.textContent = pct(r.probabilities?.unknown ?? 0);

    setResultsVisible(true);
  } catch (err) {
    showError(err.message || String(err));
  } finally {
    setLoading(false);
  }
});


