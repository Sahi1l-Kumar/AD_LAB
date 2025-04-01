// State management
let state = {
  expenses: [],
  categories: [],
  currentView: "dashboard",
  selectedFile: null,
};

// DOM Elements
const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const navButtons = document.querySelectorAll(".nav-btn");
const views = document.querySelectorAll(".view");

// Charts
let pieChart, lineChart, barChart, stackedChart;

// Initialize the application
async function init() {
  setupEventListeners();
  setupCharts();
  await loadDashboardData();
  await loadTransactions();
}

// Event Listeners
function setupEventListeners() {
  // File Upload
  dropZone.addEventListener("click", () => fileInput.click());
  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
  });
  dropZone.addEventListener("dragleave", () =>
    dropZone.classList.remove("drag-over")
  );
  dropZone.addEventListener("drop", handleFileDrop);
  fileInput.addEventListener("change", handleFileSelect);

  // Navigation
  navButtons.forEach((btn) => {
    btn.addEventListener("click", () => switchView(btn.dataset.view));
  });

  // Filters
  document
    .getElementById("searchInput")
    .addEventListener("input", debounce(loadTransactions, 300));
  document
    .getElementById("categoryFilter")
    .addEventListener("change", loadTransactions);
  document
    .getElementById("startDate")
    .addEventListener("change", loadTransactions);
  document
    .getElementById("endDate")
    .addEventListener("change", loadTransactions);

  // Reports
  document
    .getElementById("generateReport")
    .addEventListener("click", generateReport);
}

// File Handling
async function handleFileDrop(e) {
  e.preventDefault();
  dropZone.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  updateFilePreview(file);
}

async function handleFileSelect(e) {
  const file = e.target.files[0];
  updateFilePreview(file);
}

function updateFilePreview(file) {
  state.selectedFile = file;
  const uploadContent = document.querySelector(".upload-content");
  const uploadBtn = uploadContent.querySelector(".upload-btn");

  // Remove existing preview if any
  const existingPreview = uploadContent.querySelector(".file-preview");
  if (existingPreview) {
    existingPreview.remove();
  }

  if (file) {
    const preview = document.createElement("div");
    preview.className = "file-preview";

    const fileName = document.createElement("span");
    fileName.className = "file-name";
    fileName.textContent = file.name;

    const clearButton = document.createElement("button");
    clearButton.className = "clear-file";
    clearButton.innerHTML = "×";
    clearButton.addEventListener("click", (e) => {
      e.stopPropagation();
      clearFileSelection();
    });

    preview.appendChild(fileName);
    preview.appendChild(clearButton);
    uploadContent.appendChild(preview);

    // Change button text to "Upload"
    uploadBtn.textContent = "Upload File";
    uploadBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      uploadFile(file);
    });
  } else {
    // Reset button text to "Choose File"
    uploadBtn.textContent = "Choose File";
  }
}

function clearFileSelection() {
  state.selectedFile = null;
  fileInput.value = "";
  const preview = document.querySelector(".file-preview");
  if (preview) {
    preview.remove();
  }
}

async function uploadFile(file) {
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/upload", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();

    if (data.success) {
      showNotification("File uploaded successfully", "success");
      clearFileSelection();
      await loadDashboardData();
      await loadTransactions();
    } else {
      showNotification(data.error, "error");
    }
  } catch (error) {
    showNotification("Error uploading file", "error");
  }
}

// View Management
function switchView(view) {
  state.currentView = view;

  navButtons.forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.view === view);
  });

  views.forEach((v) => {
    v.classList.toggle("active", v.id === `${view}-view`);
  });

  if (view === "dashboard") {
    loadDashboardData();
  } else if (view === "transactions") {
    loadTransactions();
  }
}

// Dashboard Data
async function loadDashboardData() {
  try {
    const response = await fetch("/api/dashboard-data");
    const data = await response.json();

    updateSummaryCards(data.summary);
    updateCharts(data.charts);
    updateUnusualExpenses(data.unusual_expenses);
  } catch (error) {
    showNotification("Error loading dashboard data", "error");
  }
}

function updateSummaryCards(summary) {
  document.getElementById("totalExpenses").textContent = formatCurrency(
    summary.total_expenses
  );
  document.getElementById("monthlyAverage").textContent = formatCurrency(
    summary.avg_monthly_expense
  );
  document.getElementById("topCategory").textContent = summary.top_category;
  document.getElementById("totalTransactions").textContent =
    summary.total_transactions;
}

// Charts
function setupCharts() {
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "bottom",
        labels: {
          boxWidth: 12,
          padding: 15,
        },
      },
    },
  };

  // Pie Chart
  pieChart = new Chart(document.getElementById("pieChart"), {
    type: "pie",
    options: {
      ...chartOptions,
      plugins: {
        ...chartOptions.plugins,
        legend: {
          ...chartOptions.plugins.legend,
          position: "right",
        },
      },
    },
  });

  // Line Chart
  lineChart = new Chart(document.getElementById("lineChart"), {
    type: "line",
    options: {
      ...chartOptions,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (value) => formatCurrency(value),
          },
        },
      },
    },
  });

  // Bar Chart
  barChart = new Chart(document.getElementById("barChart"), {
    type: "bar",
    options: {
      ...chartOptions,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (value) => formatCurrency(value),
          },
        },
      },
    },
  });

  // Stacked Bar Chart
  stackedChart = new Chart(document.getElementById("stackedChart"), {
    type: "bar",
    options: {
      ...chartOptions,
      scales: {
        x: {
          stacked: true,
        },
        y: {
          stacked: true,
          ticks: {
            callback: (value) => formatCurrency(value),
          },
        },
      },
    },
  });
}

function updateCharts(chartData) {
  // Update Pie Chart
  pieChart.data = {
    labels: Object.keys(chartData.category_distribution),
    datasets: [
      {
        data: Object.values(chartData.category_distribution),
        backgroundColor: generateColors(
          Object.keys(chartData.category_distribution).length
        ),
      },
    ],
  };
  pieChart.update();

  // Update Line Chart
  lineChart.data = {
    labels: chartData.monthly_trend.map((item) => item.month),
    datasets: [
      {
        label: "Monthly Expenses",
        data: chartData.monthly_trend.map((item) => item.amount),
        borderColor: "#2563eb",
        tension: 0.1,
      },
    ],
  };
  lineChart.update();

  // Update Bar Chart
  barChart.data = {
    labels: chartData.category_breakdown.map((item) => item.category),
    datasets: [
      {
        label: "Category Expenses",
        data: chartData.category_breakdown.map((item) => item.amount),
        backgroundColor: "#3b82f6",
      },
    ],
  };
  barChart.update();

  // Update Stacked Bar Chart
  const categories = [
    ...new Set(chartData.stacked_bar_data.flatMap(Object.keys)),
  ].filter((key) => key !== "month");
  stackedChart.data = {
    labels: chartData.stacked_bar_data.map((item) => item.month),
    datasets: categories.map((category, index) => ({
      label: category,
      data: chartData.stacked_bar_data.map((item) => item[category] || 0),
      backgroundColor: generateColors(categories.length)[index],
    })),
  };
  stackedChart.update();
}

// Transactions
async function loadTransactions() {
  const search = document.getElementById("searchInput").value;
  const category = document.getElementById("categoryFilter").value;
  const startDate = document.getElementById("startDate").value;
  const endDate = document.getElementById("endDate").value;

  try {
    const response = await fetch(
      `/api/expenses?search=${search}&category=${category}&start_date=${startDate}&end_date=${endDate}`
    );
    const data = await response.json();

    renderTransactions(data.expenses);
    updateCategoryFilter(data.expenses);
  } catch (error) {
    showNotification("Error loading transactions", "error");
  }
}

function renderTransactions(expenses) {
  const tbody = document.getElementById("transactionsBody");
  tbody.innerHTML = "";

  expenses.forEach((expense) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
            <td>${formatDate(expense.date)}</td>
            <td>${expense.description}</td>
            <td>${formatCurrency(expense.amount)}</td>
            <td>
                <select class="category-select" data-id="${expense.id}">
                    ${state.categories
                      .map(
                        (cat) => `
                        <option value="${cat}" ${
                          cat === expense.category ? "selected" : ""
                        }>
                            ${cat}
                        </option>
                    `
                      )
                      .join("")}
                </select>
            </td>
            <td>
                <button class="btn-edit" data-id="${expense.id}">Edit</button>
            </td>
        `;
    tbody.appendChild(tr);
  });

  // Add event listeners for category changes
  document.querySelectorAll(".category-select").forEach((select) => {
    select.addEventListener("change", async (e) => {
      const expenseId = e.target.dataset.id;
      const newCategory = e.target.value;
      await updateExpenseCategory(expenseId, newCategory);
    });
  });
}

// Reports
async function generateReport() {
  const type = document.getElementById("reportType").value;
  const date = document.getElementById("reportDate").value;

  try {
    const response = await fetch(
      `/api/generate-report?type=${type}&month_year=${date}`
    );
    const data = await response.json();

    renderReport(data);
  } catch (error) {
    showNotification("Error generating report", "error");
  }
}

function renderReport(data) {
  const reportContent = document.getElementById("reportContent");
  reportContent.innerHTML = `
        <h2>${
          data.report_type.charAt(0).toUpperCase() + data.report_type.slice(1)
        } Report - ${data.period}</h2>
        <div class="report-summary">
            <p>Total Amount: ${formatCurrency(data.total_amount)}</p>
            <p>Total Transactions: ${data.total_transactions}</p>
        </div>
        <div class="category-breakdown">
            <h3>Category Breakdown</h3>
            <ul>
                ${data.category_breakdown
                  .map(
                    (cat) => `
                    <li>
                        <span>${cat.category}</span>
                        <span>${formatCurrency(cat.amount)}</span>
                    </li>
                `
                  )
                  .join("")}
            </ul>
        </div>
    `;
}

// Utility Functions
function formatCurrency(amount) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
  }).format(amount);
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString("en-IN");
}

function generateColors(count) {
  const colors = [
    "#3b82f6",
    "#ef4444",
    "#10b981",
    "#f59e0b",
    "#6366f1",
    "#ec4899",
    "#8b5cf6",
    "#14b8a6",
    "#f97316",
    "#06b6d4",
  ];
  return Array(count)
    .fill(0)
    .map((_, i) => colors[i % colors.length]);
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

function showNotification(message, type) {
  // Implementation of notification system
  console.log(`${type}: ${message}`);
}

// Initialize the application
init();
