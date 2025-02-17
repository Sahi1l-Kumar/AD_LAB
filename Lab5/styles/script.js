document.addEventListener("DOMContentLoaded", () => {
  const inputs = ["urlInput", "topicInput"];

  inputs.forEach((inputId) => {
    const input = document.getElementById(inputId);
    input.addEventListener("focus", () => {
      input.parentElement.classList.add("focused");
    });
    input.addEventListener("blur", () => {
      input.parentElement.classList.remove("focused");
    });

    input.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        scrapeWebsite();
      }
    });
  });
});

function parseMarkdown(text) {
  text = text.replace(/```([^`]+)```/g, "<pre><code>$1</code></pre>");

  text = text.replace(/`([^`]+)`/g, "<code>$1</code>");

  text = text.replace(/^### (.*$)/gm, "<h3>$1</h3>");
  text = text.replace(/^## (.*$)/gm, "<h2>$1</h2>");
  text = text.replace(/^# (.*$)/gm, "<h1>$1</h1>");

  text = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  text = text.replace(/\*(.*?)\*/g, "<em>$1</em>");

  text = text.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    '<a href="$2" target="_blank">$1</a>'
  );

  text = text.replace(/^\s*-\s(.+)/gm, "<li>$1</li>");
  text = text.replace(/(<li>.*<\/li>)/s, "<ul>$1</ul>");

  text = text.replace(/\n\n/g, "</p><p>");
  text = "<p>" + text + "</p>";

  return text;
}

async function scrapeWebsite() {
  const urlInput = document.getElementById("urlInput");
  const topicInput = document.getElementById("topicInput");
  const modelSelect = document.getElementById("modelSelect");
  const loading = document.getElementById("loading");
  const error = document.getElementById("error");
  const results = document.getElementById("results");
  const summary = document.getElementById("summary");

  error.style.display = "none";
  results.classList.remove("visible");
  summary.innerHTML = "";

  const url = urlInput.value.trim();
  if (!url) {
    showError("Please enter a valid URL");
    return;
  }

  const topic = topicInput.value.trim();
  const model = modelSelect.value;

  try {
    loading.style.display = "flex";

    const response = await fetch("/scrape", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url, topic, model }),
    });

    const data = await response.json();

    if (response.ok) {
      const headerText = topic
        ? `Analysis of "${topic}" from the webpage using ${model}`
        : `Website Analysis using ${model}`;

      summary.innerHTML = `
                <h2 style="margin-bottom: 1.5rem; color: var(--text); font-size: 1.5rem; font-weight: 700;">${headerText}</h2>
                <div class="markdown-content">${parseMarkdown(
                  data.summary
                )}</div>
            `;

      results.classList.add("visible");
    } else {
      showError(data.error || "Failed to analyze the website");
    }
  } catch (err) {
    showError("Error processing request. Please try again.");
  } finally {
    loading.style.display = "none";
  }
}

function showError(message) {
  const error = document.getElementById("error");
  error.textContent = message;
  error.style.display = "block";
}
