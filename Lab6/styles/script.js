document.addEventListener("DOMContentLoaded", () => {
  // Form elements
  const signupForm = document.querySelector("#signupForm form");
  const signinForm = document.querySelector("#signinForm form");
  const showSignIn = document.getElementById("showSignIn");
  const showSignUp = document.getElementById("showSignUp");
  const profileForm = document.getElementById("profileForm");

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
  const handleFormSubmit = async (form, endpoint, data) => {
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
          // Display success message if there's no redirect
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

      const username = signupForm.querySelector('input[type="text"]').value;
      const fullname = signupForm.querySelector('input[type="text"]').value;
      const email = signupForm.querySelector('input[type="email"]').value;
      const password = signupForm.querySelector('input[type="password"]').value;

      if (!username || !fullname || !email || !password) {
        alert("Please fill in all fields");
        return;
      }

      handleFormSubmit(signupForm, "/signup", {
        username: username,
        fullname: fullname,
        email: email,
        password: password,
      });
    });
  }

  // Signin form submission
  if (signinForm) {
    signinForm.addEventListener("submit", (e) => {
      e.preventDefault();

      const username = signinForm.querySelector('input[type="text"]').value;
      const password = signinForm.querySelector('input[type="password"]').value;

      if (!username || !password) {
        alert("Please fill in all fields");
        return;
      }

      handleFormSubmit(signinForm, "/login", {
        username: username,
        password: password,
      });
    });
  }

  // Profile form submission
  if (profileForm) {
    profileForm.addEventListener("submit", (e) => {
      e.preventDefault();

      const email = profileForm.querySelector('input[type="email"]').value;
      const full_name = profileForm.querySelector(
        'input[value="John Doe"]'
      ).value;

      handleFormSubmit(profileForm, "/profile", {
        email: email,
        full_name: full_name,
      });
    });

    // Password reset functionality
    const currentPassword = profileForm.querySelector(
      'input[placeholder="Enter current password"]'
    );
    const newPassword = profileForm.querySelector(
      'input[placeholder="Enter new password"]'
    );

    if (currentPassword && newPassword) {
      profileForm.addEventListener("submit", (e) => {
        e.preventDefault();

        if (currentPassword.value && newPassword.value) {
          handleFormSubmit(profileForm, "/reset_password", {
            current_password: currentPassword.value,
            new_password: newPassword.value,
          });
        }
      });
    }
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
