document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("analysis-form");
  const loadingElement = document.getElementById("loading");
  const resultsElement = document.getElementById("results");
  const commentsListElement = document.getElementById("comments-list");
  const videoPreviewElement = document.getElementById("video-preview");
  const sentimentStatsElement = document.getElementById("sentiment-stats");
  const chartContainer = document.getElementById("chart-container");
  const analyzeBtn = document.getElementById("analyze-btn");

  let sentimentChart;

  form.addEventListener("submit", async function (event) {
    event.preventDefault();

    loadingElement.style.display = "flex";
    resultsElement.style.display = "none";

    analyzeBtn.disabled = true;
    analyzeBtn.textContent = "Processing...";

    try {
      const formData = new FormData(form);

      const response = await fetch("/analyze", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "An error occurred");
      }

      const data = await response.json();
      displayResults(data);

      document
        .querySelector(".loading-container")
        .scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) {
      alert("Error: " + error.message);
    } finally {
      loadingElement.style.display = "none";

      analyzeBtn.disabled = false;
      analyzeBtn.textContent = "Analyze Comments";
    }
  });

  document.querySelectorAll(".filter-btn").forEach((button) => {
    button.addEventListener("click", function () {
      document
        .querySelectorAll(".filter-btn")
        .forEach((btn) => btn.classList.remove("active"));
      this.classList.add("active");

      const sentiment = this.dataset.sentiment;
      filterComments(sentiment);
    });
  });

  function displayResults(data) {
    resultsElement.style.display = "block";

    embedVideo(data.video_id);

    displaySentimentStats(data.stats);

    renderSentimentChart(data.stats);

    displayComments(data.comments);

    document
      .querySelector(".loading-container")
      .scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function embedVideo(videoId) {
    videoPreviewElement.innerHTML = `
            <iframe 
                src="https://www.youtube.com/embed/${videoId}" 
                allowfullscreen
                title="YouTube video player"
            ></iframe>
        `;
  }

  function displaySentimentStats(stats) {
    const total = stats.positive + stats.neutral + stats.negative;
    const positivePercent = ((stats.positive / total) * 100).toFixed(1);
    const neutralPercent = ((stats.neutral / total) * 100).toFixed(1);
    const negativePercent = ((stats.negative / total) * 100).toFixed(1);

    sentimentStatsElement.innerHTML = `
      <div class="stat-item">
        <div class="stat-color positive-bg"></div>
        <div>
          <strong>Positive:</strong> ${stats.positive} comments 
          <span>(${positivePercent}%)</span>
        </div>
      </div>
      <div class="stat-item">
        <div class="stat-color neutral-bg"></div>
        <div>
          <strong>Neutral:</strong> ${stats.neutral} comments
          <span>(${neutralPercent}%)</span>
        </div>
      </div>
      <div class="stat-item">
        <div class="stat-color negative-bg"></div>
        <div>
          <strong>Negative:</strong> ${stats.negative} comments
          <span>(${negativePercent}%)</span>
        </div>
      </div>
      <div class="stat-item" style="background-color: #f0f4f8;">
        <div style="margin-left: 34px;">
          <strong>Total analyzed:</strong> ${total} comments
        </div>
      </div>
    `;
  }

  function renderSentimentChart(stats) {
    if (sentimentChart) {
      sentimentChart.destroy();
    }

    chartContainer.innerHTML = '<canvas id="sentiment-chart"></canvas>';
    const ctx = document.getElementById("sentiment-chart").getContext("2d");

    sentimentChart = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["Positive", "Neutral", "Negative"],
        datasets: [
          {
            data: [stats.positive, stats.neutral, stats.negative],
            backgroundColor: ["#4cc9f0", "#f72585", "#7209b7"],
            borderWidth: 0,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "70%",
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              padding: 20,
              usePointStyle: true,
              font: {
                size: 12,
              },
            },
          },
          tooltip: {
            backgroundColor: "rgba(0, 0, 0, 0.8)",
            padding: 12,
            cornerRadius: 8,
            titleFont: {
              size: 14,
              weight: "bold",
            },
            bodyFont: {
              size: 13,
            },
            displayColors: true,
            callbacks: {
              label: function (context) {
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const percentage = Math.round((context.raw / total) * 100);
                return `${context.raw} comments (${percentage}%)`;
              },
            },
          },
        },
        animation: {
          animateScale: true,
          animateRotate: true,
          duration: 800,
        },
      },
    });
  }

  function displayComments(comments) {
    commentsListElement.innerHTML = "";

    comments.forEach((comment) => {
      const commentCard = createCommentCard(comment);
      commentsListElement.appendChild(commentCard);
    });
  }

  function createCommentCard(comment) {
    const date = new Date(comment.published_at);
    const formattedDate = date.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });

    const card = document.createElement("div");
    card.className = `comment-card ${comment.sentiment.toLowerCase()}`;
    card.dataset.sentiment = comment.sentiment.toLowerCase();

    card.innerHTML = `
      <div class="comment-header">
        <div class="comment-author">${escapeHTML(comment.author)}</div>
        <span class="comment-sentiment sentiment-${comment.sentiment.toLowerCase()}">${
      comment.sentiment
    }</span>
      </div>
      <div class="comment-content">${escapeHTML(comment.text)}</div>
      <div class="comment-metadata">
        <div class="comment-date">${formattedDate}</div>
        <div class="comment-likes">${comment.likes}</div>
      </div>
    `;

    return card;
  }

  function escapeHTML(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function filterComments(sentiment) {
    const comments = document.querySelectorAll(".comment-card");
    const filterAnimation = [
      { opacity: 0.5, transform: "scale(0.98)" },
      { opacity: 1, transform: "scale(1)" },
    ];

    const filterTiming = {
      duration: 300,
      easing: "ease-out",
    };

    comments.forEach((comment) => {
      if (sentiment === "all" || comment.dataset.sentiment === sentiment) {
        comment.style.display = "flex";
        comment.animate(filterAnimation, filterTiming);
      } else {
        comment.style.display = "none";
      }
    });
  }
});
