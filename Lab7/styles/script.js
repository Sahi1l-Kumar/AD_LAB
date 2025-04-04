document.addEventListener("DOMContentLoaded", () => {
  // Form elements
  const signupForm = document.querySelector("#signupForm form");
  const signinForm = document.querySelector("#signinForm form");
  const showSignIn = document.getElementById("showSignIn");
  const showSignUp = document.getElementById("showSignUp");

  // Toggle between forms
  const toggleForms = () => {
    document.getElementById("signupForm").classList.toggle("hidden");
    document.getElementById("signinForm").classList.toggle("hidden");
  };

  if (showSignIn) {
    showSignIn.addEventListener("click", (e) => {
      e.preventDefault();
      toggleForms();
    });
  }

  if (showSignUp) {
    showSignUp.addEventListener("click", (e) => {
      e.preventDefault();
      toggleForms();
    });
  }

  // Function to handle form submission
  const handleFormSubmit = async (endpoint, data) => {
    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      const result = await response.json();

      if (result.success) {
        if (result.redirect) {
          window.location.href = result.redirect;
        } else {
          alert(result.message || "Operation successful!");
        }
      } else {
        alert(result.message || "An error occurred. Please try again.");
      }
    } catch (error) {
      console.error("Error:", error);
      alert("An error occurred. Please try again.");
    }
  };

  // Signup form submission
  if (signupForm) {
    signupForm.addEventListener("submit", (e) => {
      e.preventDefault();

      const inputs = signupForm.querySelectorAll("input");
      const username = inputs[0].value.trim();
      const fullname = inputs[1].value.trim();
      const email = inputs[2].value.trim();
      const password = inputs[3].value.trim();

      if (!username || !fullname || !email || !password) {
        alert("Please fill in all fields");
        return;
      }

      handleFormSubmit("/signup", { username, fullname, email, password });
    });
  }

  // Signin form submission
  if (signinForm) {
    signinForm.addEventListener("submit", (e) => {
      e.preventDefault();

      const username = signinForm.querySelector('input[type="text"]').value.trim();
      const password = signinForm.querySelector('input[type="password"]').value.trim();

      if (!username || !password) {
        alert("Please fill in all fields");
        return;
      }

      handleFormSubmit("/login", { username, password });
    });
  }

  // Navbar toggle for mobile view
  const hamburger = document.querySelector(".hamburger");
  const navLinks = document.querySelector(".nav-links");

  if (hamburger && navLinks) {
    hamburger.addEventListener("click", () => {
      navLinks.classList.toggle("show");
    });
  }
});
