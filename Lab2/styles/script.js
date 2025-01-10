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
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("image/")) {
      handleFile(file);
    }
  });

  dropZone.addEventListener("click", () => {
    fileInput.click();
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  });

  function handleFile(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      imagePreview.src = e.target.result;
      dropZone.style.display = "none";
      previewContainer.classList.remove("hidden");
    };
    reader.readAsDataURL(file);
  }

  classifyBtn.addEventListener("click", async () => {
    classifyBtn.disabled = true;
    classifyBtn.textContent = "Analyzing...";

    const file = fileInput.files[0];
    if (!file) {
      alert("No image selected!");
      classifyBtn.disabled = false;
      classifyBtn.textContent = "Classify Pet";
      return;
    }

    const formData = new FormData();
    formData.append("image", file);

    try {
      const response = await fetch("/classify", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to classify the image. Please try again.");
      }

      const data = await response.json();

      const pet = data.category.toLowerCase();

      uploadContainer.classList.add("hidden");
      previewContainer.classList.add("hidden");
      result.classList.remove("hidden");

      setTimeout(() => {
        result.classList.add("visible");
        petType.textContent = pet;
        petIcon.className = `pet-icon ${pet}`;

        setTimeout(() => {
          petIcon.classList.add("visible");
          resultText.classList.add("visible");
        }, 300);
      }, 100);
    } catch (error) {
      alert(error.message);
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
    setTimeout(() => {
      result.classList.add("hidden");
      classifyBtn.disabled = false;
      classifyBtn.textContent = "Classify Pet";
      fileInput.value = "";
    }, 500);
  });
});
