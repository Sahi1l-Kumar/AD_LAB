document.addEventListener("DOMContentLoaded", () => {
  const signupForm = document.getElementById("signupForm");
  const signinForm = document.getElementById("signinForm");
  const showSignIn = document.getElementById("showSignIn");
  const showSignUp = document.getElementById("showSignUp");

  // Toggle between forms
  const toggleForms = (hideForm, showForm) => {
    hideForm.classList.add("hidden");
    showForm.classList.remove("hidden");
  };

  // Toggle between forms
  showSignIn.addEventListener("click", (e) => {
    e.preventDefault();
    toggleForms(signupForm, signinForm);
  });

  showSignUp.addEventListener("click", (e) => {
    e.preventDefault();
    toggleForms(signinForm, signupForm);
  });

  // Handle form submissions
  const forms = document.querySelectorAll("form");
  forms.forEach((form) => {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const formData = new FormData(form);
      const data = Object.fromEntries(formData);
      console.log("Form submitted:", data);
      // Simulate successful login/signup
      window.location.href = "grades.html";
    });

    // Add keypress event listener for Enter key
    form.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        form.querySelector(".submit-btn").click();
      }
    });
  });
});
