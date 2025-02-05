let chart = null;

const stockData = {
  RELIANCE: { name: "Reliance Industries", basePrice: 2856.75 },
  TCS: { name: "Tata Consultancy Services", basePrice: 3945.2 },
  HDFCBANK: { name: "HDFC Bank", basePrice: 1678.45 },
  INFY: { name: "Infosys", basePrice: 1456.3 },
  TATAMOTORS: { name: "Tata Motors", basePrice: 876.25 },
};

function generateDummyData(days, stockSymbol, model) {
  const stock = stockData[stockSymbol.toUpperCase()] || { basePrice: 1000 };
  const basePrice = stock.basePrice;
  const historicalData = [];
  const predictions = [];

  // Generate more realistic historical data with smaller variations
  let currentPrice = basePrice;
  for (let i = 0; i < 30; i++) {
    currentPrice += (Math.random() - 0.5) * (basePrice * 0.02); // Reduced variation
    historicalData.push(parseFloat(currentPrice.toFixed(2)));
  }

  // Generate predictions that follow the historical trend more closely
  const lastPrice = historicalData[historicalData.length - 1];
  const recentTrend =
    historicalData[historicalData.length - 1] -
    historicalData[historicalData.length - 5];
  const trend = recentTrend > 0 ? 1 : -1;

  let predictedPrice = lastPrice;
  for (let i = 0; i < days; i++) {
    // Use smaller variations and follow the recent trend
    const variation = Math.random() * 0.015 * basePrice; // Reduced variation
    predictedPrice += trend * variation;
    predictions.push(parseFloat(predictedPrice.toFixed(2)));
  }

  const finalPredictedPrice = predictions[predictions.length - 1];

  return {
    historical_data: historicalData,
    predictions: predictions,
    technical_indicators: {
      rsi: (Math.random() * 40 + 30).toFixed(2),
      macd: ((Math.random() - 0.5) * 10).toFixed(2),
    },
    ai_metrics: {
      accuracy: (Math.random() * 5 + 85).toFixed(2) + "%",
      confidence: (Math.random() * 5 + 85).toFixed(2) + "%",
    },
    trend_direction: trend,
    model_prediction: {
      days: parseInt(days),
      predicted_price: parseFloat(finalPredictedPrice.toFixed(2)),
      symbol: stockSymbol.toUpperCase(),
      model: model,
    },
  };
}

function renderChart(historicalData, predictions, stockSymbol) {
  const ctx = document.getElementById("predictionChart");

  if (chart) {
    chart.destroy();
  }

  const labels = [
    ...Array(historicalData.length + predictions.length).keys(),
  ].map((i) => `Day ${i + 1}`);

  // Create connected datasets by including the last historical point in predictions
  const connectingPoint = historicalData[historicalData.length - 1];
  const connectedPredictions = [connectingPoint, ...predictions];

  chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Historical Data",
          data: historicalData,
          borderColor: "#26A69A",
          backgroundColor: "rgba(38, 166, 154, 0.1)",
          borderWidth: 2,
          tension: 0.4,
          fill: true,
        },
        {
          label: "Predictions",
          data: [
            ...Array(historicalData.length - 1).fill(null),
            ...connectedPredictions,
          ],
          borderColor: "#387ED1",
          backgroundColor: "rgba(56, 126, 209, 0.1)",
          borderWidth: 2,
          borderDash: [5, 5],
          tension: 0.4,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      interaction: {
        intersect: false,
        mode: "index",
      },
      plugins: {
        legend: {
          position: "top",
          labels: {
            color: "#1F2937",
            font: {
              family: "Inter",
            },
          },
        },
        title: {
          display: true,
          text: `Price Prediction Analysis for ${stockSymbol.toUpperCase()}`,
          color: "#1F2937",
          font: {
            family: "Inter",
            size: 16,
            weight: 600,
          },
        },
      },
      scales: {
        y: {
          grid: {
            color: "rgba(0, 0, 0, 0.1)",
          },
          ticks: {
            color: "#6B7280",
            callback: function (value) {
              return "₹" + value.toLocaleString();
            },
          },
        },
        x: {
          grid: {
            color: "rgba(0, 0, 0, 0.1)",
          },
          ticks: {
            color: "#6B7280",
          },
        },
      },
    },
  });
}

function setLoading(loading) {
  const submitBtn = document.getElementById("submitBtn");
  const btnText = submitBtn.querySelector(".btn-text");
  const spinner = submitBtn.querySelector(".spinner");

  submitBtn.disabled = loading;
  btnText.classList.toggle("hidden", loading);
  spinner.classList.toggle("hidden", !loading);
}

function updateMetrics(predictions) {
  document.getElementById("rsiValue").textContent =
    predictions.technical_indicators.rsi;
  document.getElementById("macdValue").textContent =
    predictions.technical_indicators.macd;
  document.getElementById("accuracyValue").textContent =
    predictions.ai_metrics.accuracy;
  document.getElementById("confidenceValue").textContent =
    predictions.ai_metrics.confidence;

  const trendIndicator = document.getElementById("trendIndicator");
  const modelPrediction = predictions.model_prediction;
  const trend = predictions.trend_direction > 0;
  const trendClass = trend ? "up" : "down";

  trendIndicator.innerHTML = `
    <div class="model-prediction">
      <div class="prediction-header">
        <h3>${modelPrediction.model.toUpperCase()} Model Prediction</h3>
        <span class="prediction-days">${
          modelPrediction.days
        } days forecast</span>
      </div>
      <div class="prediction-price ${trendClass}">
        <span class="price-label">Target Price:</span>
        <span class="price-value">₹${modelPrediction.predicted_price.toLocaleString()}</span>
      </div>
      <div class="trend-signal ${trendClass}">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          ${
            trend
              ? '<line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline>'
              : '<line x1="7" y1="7" x2="17" y2="17"></line><polyline points="17 7 17 17 7 17"></polyline>'
          }
        </svg>
        <span>${trend ? "Bullish Signal" : "Bearish Signal"}</span>
      </div>
    </div>
  `;
}

function animateCards() {
  const cards = document.querySelectorAll(".metrics-card, .trend-card");
  cards.forEach((card, index) => {
    card.style.animationDelay = `${index * 0.1}s`;
  });
}

document.querySelectorAll(".stock-pill").forEach((pill) => {
  pill.addEventListener("click", () => {
    const stockSymbol = pill.dataset.stock;
    document.getElementById("stockSymbol").value = stockSymbol;
    document
      .getElementById("predictionForm")
      .dispatchEvent(new Event("submit"));
  });
});

document
  .getElementById("predictionForm")
  .addEventListener("submit", async (e) => {
    e.preventDefault();
    setLoading(true);
    document.getElementById("results").classList.add("hidden");

    const stockSymbol = document.getElementById("stockSymbol").value;
    const predictionDays = parseInt(
      document.getElementById("predictionDays").value
    );
    const selectedModel = document.getElementById("modelSelect").value;

    setTimeout(() => {
      const data = generateDummyData(
        predictionDays,
        stockSymbol,
        selectedModel
      );
      renderChart(data.historical_data, data.predictions, stockSymbol);
      updateMetrics(data);

      document.getElementById("results").classList.remove("hidden");
      animateCards();
      setLoading(false);
    }, 1500);
  });
