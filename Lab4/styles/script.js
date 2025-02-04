let fileContent = "";

async function uploadFile() {
  const fileInput = document.getElementById("fileInput");
  const file = fileInput.files[0];

  if (!file) {
    alert("Please select a file first");
    return;
  }

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
      alert("File uploaded successfully!");
    } else {
      alert("Error: " + data.error);
    }
  } catch (error) {
    alert("Error uploading file: " + error);
  }
}

async function askQuestion() {
  if (!fileContent) {
    alert("Please upload a file first");
    return;
  }

  const question = document.getElementById("questionInput").value;
  const model = document.getElementById("modelSelect").value;
  const loadingDiv = document.getElementById("loading");
  const responseDiv = document.getElementById("response");

  if (!question) {
    alert("Please enter a question");
    return;
  }

  loadingDiv.style.display = "block";
  responseDiv.innerHTML = "";

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
  }
}
