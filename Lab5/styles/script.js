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

function parseMarkdown(text) {
  // Handle code blocks
  text = text.replace(/```([^`]+)```/g, "<pre><code>$1</code></pre>");

  // Handle inline code
  text = text.replace(/`([^`]+)`/g, "<code>$1</code>");

  // Handle headers
  text = text.replace(/^### (.*$)/gm, "<h3>$1</h3>");
  text = text.replace(/^## (.*$)/gm, "<h2>$1</h2>");
  text = text.replace(/^# (.*$)/gm, "<h1>$1</h1>");

  // Handle bold
  text = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  // Handle italic
  text = text.replace(/\*(.*?)\*/g, "<em>$1</em>");

  // Handle links
  text = text.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    '<a href="$2" target="_blank">$1</a>'
  );

  // Handle lists
  text = text.replace(/^\s*-\s(.+)/gm, "<li>$1</li>");
  text = text.replace(/(<li>.*<\/li>)/s, "<ul>$1</ul>");

  // Handle paragraphs
  text = text.replace(/\n\n/g, "</p><p>");
  text = "<p>" + text + "</p>";

  return text;
}

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
      // Update UI with results and parse markdown
      summary.innerHTML = `
                <h2 style="margin-bottom: 1rem; color: var(--text)">LLM Summary</h2>
                <div class="markdown-content">${parseMarkdown(
                  data.summary
                )}</div>
            `;

      scrapedContent.innerHTML = `
                <h2 style="margin-bottom: 1rem; color: var(--text)">Scraped Content Preview</h2>
                <div class="markdown-content">${parseMarkdown(
                  data.scraped_content
                )}</div>
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
