document.addEventListener("DOMContentLoaded", () => {
  // Add input animation
  const urlInput = document.getElementById("urlInput");
  urlInput.addEventListener("focus", () => {
    urlInput.parentElement.classList.add("focused");
  });
  urlInput.addEventListener("blur", () => {
    urlInput.parentElement.classList.remove("focused");
  });
});

async function scrapeWebsite() {
  const urlInput = document.getElementById("urlInput");
  const loading = document.getElementById("loading");
  const error = document.getElementById("error");
  const results = document.getElementById("results");
  const summary = document.getElementById("summary");
  const scrapedContent = document.getElementById("scraped-content");

  // Reset state
  error.style.display = "none";
  results.classList.remove("visible");
  summary.innerHTML = "";
  scrapedContent.innerHTML = "";

  // Validate URL
  const url = urlInput.value.trim();
  if (!url) {
    showError("Please enter a valid URL");
    return;
  }

  try {
    // Show loading state
    loading.style.display = "flex";

    const response = await fetch("/scrape", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url }),
    });

    const data = await response.json();

    if (response.ok) {
      // Update UI with results
      summary.innerHTML = `
                <h2 style="margin-bottom: 1rem; color: var(--text)">LLM Summary</h2>
                <pre style="white-space: pre-wrap; font-family: inherit;">${data.summary}</pre>
            `;

      scrapedContent.innerHTML = `
                <h2 style="margin-bottom: 1rem; color: var(--text)">Scraped Content Preview</h2>
                <p>${data.scraped_content}</p>
            `;

      // Show results with animation
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
