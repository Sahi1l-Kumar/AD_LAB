document.addEventListener("DOMContentLoaded", function () {
  // DOM elements
  const form = document.getElementById("analysis-form");
  const loadingElement = document.getElementById("loading");
  const resultsElement = document.getElementById("results");
  const commentsListElement = document.getElementById("comments-list");
  const videoPreviewElement = document.getElementById("video-preview");
  const sentimentStatsElement = document.getElementById("sentiment-stats");
  const chartContainer = document.getElementById("chart-container");

  // Chart instance
  let sentimentChart;

  // Form submission handler
  form.addEventListener("submit", async function (event) {
    event.preventDefault();

    // Show loading indicator
    loadingElement.style.display = "flex";
    resultsElement.style.display = "none";

    try {
      // Create FormData from form
      const formData = new FormData(form);

      // Send request to the server
      const response = await fetch("/analyze", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "An error occurred");
      }

      // Process results
      const data = await response.json();
      displayResults(data);
    } catch (error) {
      alert("Error: " + error.message);
    } finally {
      // Hide loading indicator
      loadingElement.style.display = "none";
    }
  });

  // Filter buttons functionality
  document.querySelectorAll(".filter-btn").forEach((button) => {
    button.addEventListener("click", function () {
      // Update active button
      document
        .querySelectorAll(".filter-btn")
        .forEach((btn) => btn.classList.remove("active"));
      this.classList.add("active");

      // Apply filter
      const sentiment = this.dataset.sentiment;
      filterComments(sentiment);
    });
  });

  // Display analysis results
  function displayResults(data) {
    // Show results container
    resultsElement.style.display = "block";

    // Embed video preview
    embedVideo(data.video_id);

    // Display sentiment statistics
    displaySentimentStats(data.stats);

    // Render sentiment chart
    renderSentimentChart(data.stats);

    // Display comments
    displayComments(data.comments);
  }

  // Embed YouTube video preview
  function embedVideo(videoId) {
    videoPreviewElement.innerHTML = `
            <iframe 
                src="https://www.youtube.com/embed/${videoId}" 
                allowfullscreen
                title="YouTube video player"
            ></iframe>
        `;
  }

  // Display sentiment statistics
  function displaySentimentStats(stats) {
    const total = stats.positive + stats.neutral + stats.negative;

    sentimentStatsElement.innerHTML = `
            <div class="stat-item">
                <div class="stat-color positive-bg"></div>
                <div>
                    <strong>Positive:</strong> ${stats.positive} comments 
                    (${((stats.positive / total) * 100).toFixed(1)}%)
                </div>
            </div>
            <div class="stat-item">
                <div class="stat-color neutral-bg"></div>
                <div>
                    <strong>Neutral:</strong> ${stats.neutral} comments
                    (${((stats.neutral / total) * 100).toFixed(1)}%)
                </div>
            </div>
            <div class="stat-item">
                <div class="stat-color negative-bg"></div>
                <div>
                    <strong>Negative:</strong> ${stats.negative} comments
                    (${((stats.negative / total) * 100).toFixed(1)}%)
                </div>
            </div>
            <div>
                <strong>Total analyzed:</strong> ${total} comments
            </div>
        `;
  }

  // Render sentiment chart
  function renderSentimentChart(stats) {
    // Destroy previous chart if it exists
    if (sentimentChart) {
      sentimentChart.destroy();
    }

    // Create canvas element
    chartContainer.innerHTML = '<canvas id="sentiment-chart"></canvas>';
    const ctx = document.getElementById("sentiment-chart").getContext("2d");

    // Create new chart
    sentimentChart = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["Positive", "Neutral", "Negative"],
        datasets: [
          {
            data: [stats.positive, stats.neutral, stats.negative],
            backgroundColor: [
              "#2ecc71", // Positive - green
              "#f39c12", // Neutral - orange
              "#e74c3c", // Negative - red
            ],
            borderWidth: 0,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
          },
        },
      },
    });
  }

  // Display comments list
  function displayComments(comments) {
    commentsListElement.innerHTML = "";

    comments.forEach((comment) => {
      const date = new Date(comment.published_at);
      const formattedDate = date.toLocaleDateString();

      const commentElement = document.createElement("div");
      commentElement.className = `comment-card ${comment.sentiment}`;
      commentElement.dataset.sentiment = comment.sentiment;

      commentElement.innerHTML = `
                <div class="comment-header">
                    <span class="comment-author">${comment.author}</span>
                    <span class="comment-sentiment sentiment-${comment.sentiment}">${comment.sentiment}</span>
                </div>
                <div class="comment-text">${comment.text}</div>
                <div class="comment-metadata">
                    <span>Published: ${formattedDate}</span>
                    <span>Likes: ${comment.likes}</span>
                </div>
            `;

      commentsListElement.appendChild(commentElement);
    });
  }

  // Filter comments by sentiment
  function filterComments(sentiment) {
    const comments = document.querySelectorAll(".comment-card");

    comments.forEach((comment) => {
      if (sentiment === "all" || comment.dataset.sentiment === sentiment) {
        comment.style.display = "block";
      } else {
        comment.style.display = "none";
      }
    });
  }
});
