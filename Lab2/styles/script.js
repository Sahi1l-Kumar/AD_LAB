document.addEventListener("DOMContentLoaded", () => {
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");
  const imagePreview = document.getElementById("imagePreview");
  const previewContainer = document.querySelector(".preview-container");
  const uploadContainer = document.querySelector(".upload-container");
  const classifyBtn = document.querySelector(".classify-btn");
  const result = document.querySelector(".result");
  const petType = document.querySelector(".pet-type");
  const petIcon = document.querySelector(".pet-icon");
  const resultText = document.querySelector(".result-text");
  const tryAgainBtn = document.querySelector(".try-again-btn");

  let currentFile = null;

  ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, preventDefaults);
  });

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  ["dragenter", "dragover"].forEach((eventName) => {
    dropZone.addEventListener(eventName, () => {
      dropZone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, () => {
      dropZone.classList.remove("dragover");
    });
  });

  dropZone.addEventListener("drop", (e) => {
    const items = e.dataTransfer.items;
    let file = null;

    if (items) {
      for (let i = 0; i < items.length; i++) {
        if (items[i].kind === "file" && items[i].type.startsWith("image/")) {
          file = items[i].getAsFile();
          break;
        }
      }
    } else {
      const files = e.dataTransfer.files;
      for (let i = 0; i < files.length; i++) {
        if (files[i].type.startsWith("image/")) {
          file = files[i];
          break;
        }
      }
    }

    if (file) {
      handleFile(file);
    } else {
      alert("Please drop an image file");
    }
  });

  dropZone.addEventListener("click", () => {
    fileInput.click();
  });

  fileInput.addEventListener("change", (e) => {
    if (
      e.target.files.length > 0 &&
      e.target.files[0].type.startsWith("image/")
    ) {
      handleFile(e.target.files[0]);
    } else {
      alert("Please select an image file");
    }
  });

  function handleFile(file) {
    currentFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      imagePreview.src = e.target.result;
      dropZone.style.display = "none";
      previewContainer.classList.remove("hidden");
    };
    reader.readAsDataURL(file);
  }

  classifyBtn.addEventListener("click", async () => {
    if (!currentFile) {
      alert("Please select an image first");
      return;
    }

    classifyBtn.disabled = true;
    classifyBtn.textContent = "Analyzing...";

    try {
      const formData = new FormData();
      formData.append("image", currentFile);

      const response = await fetch("http://localhost:5000/classify", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Classification failed");
      }

      const data = await response.json();

      uploadContainer.classList.add("hidden");
      previewContainer.classList.add("hidden");
      result.classList.remove("hidden");

      setTimeout(() => {
        result.classList.add("visible");
        const predictedPet = data.category.toLowerCase();
        petType.textContent = data.category;
        petIcon.className = `pet-icon ${predictedPet}`;

        setTimeout(() => {
          petIcon.classList.add("visible");
          resultText.classList.add("visible");
        }, 300);
      }, 100);
    } catch (error) {
      console.error("Error:", error);
      alert("Failed to classify image. Please try again.");
      classifyBtn.disabled = false;
      classifyBtn.textContent = "Classify Pet";
    }
  });

  tryAgainBtn.addEventListener("click", () => {
    uploadContainer.classList.remove("hidden");
    dropZone.style.display = "block";
    previewContainer.classList.add("hidden");
    result.classList.remove("visible");
    petIcon.className = "pet-icon";
    resultText.classList.remove("visible");
    currentFile = null;
    setTimeout(() => {
      result.classList.add("hidden");
      classifyBtn.disabled = false;
      classifyBtn.textContent = "Classify Pet";
      fileInput.value = "";
    }, 500);
  });
});
