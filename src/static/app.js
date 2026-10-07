document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupContainer = document.getElementById("signup-container");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  const authButton = document.getElementById("auth-button");
  const loginDialog = document.getElementById("login-dialog");
  const loginForm = document.getElementById("login-form");
  const loginError = document.getElementById("login-error");
  const closeLoginButton = document.getElementById("close-login");
  let currentTeacher = null;

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function showMessage(message, type) {
    messageDiv.textContent = message;
    messageDiv.className = `message ${type}`;
    setTimeout(() => messageDiv.classList.add("hidden"), 5000);
  }

  function renderAuthentication() {
    if (currentTeacher) {
      authButton.textContent = `${currentTeacher} - Log out`;
      signupContainer.classList.remove("hidden");
    } else {
      authButton.innerHTML = "&#128100; Teacher login";
      signupContainer.classList.add("hidden");
    }
  }

  async function fetchSession() {
    const response = await fetch("/auth/session");
    const session = await response.json();
    currentTeacher = session.authenticated ? session.username : null;
    renderAuthentication();
  }

  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      if (!response.ok) {
        throw new Error(`Activities request failed with ${response.status}`);
      }
      const activities = await response.json();

      activitiesList.innerHTML = "";
      activitySelect.innerHTML =
        '<option value="">-- Select an activity --</option>';

      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";
        const safeName = escapeHtml(name);
        const spotsLeft =
          details.max_participants - details.participants.length;
        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map((email) => {
                    const safeEmail = escapeHtml(email);
                    const removeButton = currentTeacher
                      ? `<button class="delete-btn" data-activity="${safeName}" data-email="${safeEmail}" aria-label="Unregister ${safeEmail}">Remove</button>`
                      : "";
                    return `<li><span class="participant-email">${safeEmail}</span>${removeButton}</li>`;
                  })
                  .join("")}
              </ul>
            </div>`
            : "<p><em>No participants yet</em></p>";

        activityCard.innerHTML = `
          <h4>${safeName}</h4>
          <p>${escapeHtml(details.description)}</p>
          <p><strong>Schedule:</strong> ${escapeHtml(details.schedule)}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">${participantsHTML}</div>
        `;
        activitiesList.appendChild(activityCard);

        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  async function handleUnauthorized(response) {
    if (response.status !== 401) {
      return false;
    }
    currentTeacher = null;
    renderAuthentication();
    await fetchActivities();
    showMessage("Your teacher session ended. Please log in again.", "error");
    return true;
  }

  async function handleUnregister(event) {
    const button = event.currentTarget;
    const activity = button.dataset.activity;
    const email = button.dataset.email;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/unregister?email=${encodeURIComponent(email)}`,
        { method: "DELETE" }
      );
      const result = await response.json();
      if (await handleUnauthorized(response)) {
        return;
      }
      if (!response.ok) {
        showMessage(result.detail || "An error occurred", "error");
        return;
      }
      showMessage(result.message, "success");
      await fetchActivities();
    } catch (error) {
      showMessage("Failed to unregister. Please try again.", "error");
      console.error("Error unregistering:", error);
    }
  }

  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const email = document.getElementById("email").value;
    const activity = activitySelect.value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        { method: "POST" }
      );
      const result = await response.json();
      if (await handleUnauthorized(response)) {
        return;
      }
      if (!response.ok) {
        showMessage(result.detail || "An error occurred", "error");
        return;
      }
      showMessage(result.message, "success");
      signupForm.reset();
      await fetchActivities();
    } catch (error) {
      showMessage("Failed to sign up. Please try again.", "error");
      console.error("Error signing up:", error);
    }
  });

  authButton.addEventListener("click", async () => {
    if (!currentTeacher) {
      loginError.classList.add("hidden");
      loginDialog.showModal();
      return;
    }
    try {
      const response = await fetch("/auth/logout", { method: "POST" });
      if (!response.ok) {
        showMessage("Failed to log out. Please try again.", "error");
        return;
      }
      currentTeacher = null;
      renderAuthentication();
      await fetchActivities();
      showMessage("Logged out successfully.", "success");
    } catch (error) {
      showMessage("Failed to log out. Please try again.", "error");
      console.error("Error logging out:", error);
    }
  });

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: document.getElementById("username").value,
          password: document.getElementById("password").value,
        }),
      });
      const result = await response.json();
      if (!response.ok) {
        loginError.textContent = result.detail || "Login failed";
        loginError.classList.remove("hidden");
        return;
      }
      currentTeacher = result.username;
      loginForm.reset();
      loginDialog.close();
      renderAuthentication();
      await fetchActivities();
      showMessage("Logged in successfully.", "success");
    } catch (error) {
      loginError.textContent = "Login failed. Please try again.";
      loginError.classList.remove("hidden");
      console.error("Error logging in:", error);
    }
  });

  closeLoginButton.addEventListener("click", () => loginDialog.close());

  async function initialize() {
    try {
      await fetchSession();
    } catch (error) {
      console.error("Error checking teacher session:", error);
      renderAuthentication();
    }
    await fetchActivities();
  }

  initialize();
});
