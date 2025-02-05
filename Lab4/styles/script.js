let fileContent = "";

const uploadArea = document.getElementById("uploadArea");
const filePreview = document.getElementById("filePreview");
const fileNameElement = document.getElementById("fileName");
const fileContentElement = document.getElementById("fileContent");
const preUploadPreview = document.getElementById("preUploadPreview");
const preUploadFileName = document.getElementById("preUploadFileName");
const fileTypeIcon = document.getElementById("fileTypeIcon");

document
  .getElementById("fileInput")
  .addEventListener("change", handleFileSelect);

function handleFileSelect(e) {
  const file = e.target.files[0];
  if (file) {
    showPreUploadPreview(file);
  }
}

function getFileIcon(fileType) {
  const icons = {
    "text/plain": "📝",
    "application/pdf": "📄",
    "text/csv": "📊",
    default: "📄",
  };
  return icons[fileType] || icons["default"];
}

function showPreUploadPreview(file) {
  const icon = getFileIcon(file.type);
  fileTypeIcon.textContent = icon;
  preUploadFileName.textContent = file.name;
  preUploadPreview.classList.add("show");
}

function removePreUploadFile() {
  document.getElementById("fileInput").value = "";
  preUploadPreview.classList.remove("show");
}

["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
  uploadArea.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}

["dragenter", "dragover"].forEach((eventName) => {
  uploadArea.addEventListener(eventName, highlight, false);
});

["dragleave", "drop"].forEach((eventName) => {
  uploadArea.addEventListener(eventName, unhighlight, false);
});

function highlight(e) {
  uploadArea.classList.add("highlight");
}

function unhighlight(e) {
  uploadArea.classList.remove("highlight");
}

uploadArea.addEventListener("drop", handleDrop, false);

function handleDrop(e) {
  const dt = e.dataTransfer;
  const files = dt.files;

  if (files.length > 0) {
    document.getElementById("fileInput").files = files;
    showPreUploadPreview(files[0]);
  }
}

function showFilePreview(file) {
  fileNameElement.textContent = file.name;

  const reader = new FileReader();
  reader.onload = function (e) {
    const content = e.target.result;
    fileContentElement.textContent =
      content.slice(0, 500) + (content.length > 500 ? "..." : "");
    filePreview.classList.add("show");
  };
  reader.readAsText(file);
}

function removeFile() {
  document.getElementById("fileInput").value = "";
  fileContent = "";
  filePreview.classList.remove("show");
  preUploadPreview.classList.remove("show");
  showNotification("File removed successfully", "success");
}

async function uploadFile() {
  const fileInput = document.getElementById("fileInput");
  const file = fileInput.files[0];
  const button = event.target;

  if (!file) {
    showNotification("Please select a file first", "error");
    return;
  }

  button.disabled = true;
  button.innerHTML = "Uploading...";

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/upload", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (data.success) {
      fileContent = data.text;
      showFilePreview(file);
      preUploadPreview.classList.remove("show");
      showNotification("File uploaded successfully!", "success");
    } else {
      showNotification("Error: " + data.error, "error");
    }
  } catch (error) {
    showNotification("Error uploading file: " + error, "error");
  } finally {
    button.disabled = false;
    button.innerHTML = "Upload";
  }
}

async function askQuestion() {
  if (!fileContent) {
    showNotification("Please upload a file first", "error");
    return;
  }

  const question = document.getElementById("questionInput").value;
  const model = document.getElementById("modelSelect").value;
  const loadingDiv = document.getElementById("loading");
  const responseDiv = document.getElementById("response");
  const button = event.target;

  if (!question) {
    showNotification("Please enter a question", "error");
    return;
  }

  loadingDiv.style.display = "flex";
  responseDiv.innerHTML = "";
  button.disabled = true;

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question: question,
        context: fileContent,
        model: model,
      }),
    });

    const data = await response.json();
    if (data.response) {
      responseDiv.innerHTML = data.response;
    } else {
      responseDiv.innerHTML = "Error: " + data.error;
    }
  } catch (error) {
    responseDiv.innerHTML = "Error: " + error;
  } finally {
    loadingDiv.style.display = "none";
    button.disabled = false;
  }
}

function showNotification(message, type) {
  const notification = document.createElement("div");
  notification.className = `notification ${type}`;
  notification.textContent = message;

  document.body.appendChild(notification);

  setTimeout(() => {
    notification.classList.add("show");
  }, 10);

  setTimeout(() => {
    notification.classList.remove("show");
    setTimeout(() => {
      notification.remove();
    }, 300);
  }, 3000);
}

document.querySelectorAll("button").forEach((button) => {
  button.addEventListener("click", function (e) {
    const ripple = document.createElement("span");
    const rect = button.getBoundingClientRect();

    ripple.className = "ripple";
    ripple.style.left = `${e.clientX - rect.left}px`;
    ripple.style.top = `${e.clientY - rect.top}px`;

    button.appendChild(ripple);

    setTimeout(() => ripple.remove(), 600);
  });
});
