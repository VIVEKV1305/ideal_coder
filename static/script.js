// --- TOAST NOTIFICATION FUNCTION ---
function showToast(message, type = "error") {
    const container = document.getElementById("toast-container");
    if (!container) return; // Failsafe

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    
    // Choose the right emoji based on the type of alert
    let icon = "⚠️";
    if (type === "error") icon = "❌";
    if (type === "success") icon = "✅";

    toast.innerHTML = `<span style="font-size: 18px;">${icon}</span> <span>${message}</span>`;
    container.appendChild(toast);

    // Make it automatically disappear after 4 seconds
    setTimeout(() => {
        toast.classList.add("fade-out");
        toast.addEventListener("animationend", () => toast.remove());
    }, 4000);
}

// --- FORM SUBMISSION LOGIC ---
document.getElementById("dietForm").addEventListener("submit", async function (e) {
    e.preventDefault();
    
    const btn = document.querySelector(".btn");

    // Gather Inputs
    const age = parseInt(document.getElementById("age").value);
    const weight = parseFloat(document.getElementById("weight").value);
    const height = parseFloat(document.getElementById("height").value);

    // --- FRONTEND VALIDATION ALERTS (TOASTS) ---
    if (age < 14 || age > 100) {
        showToast("Please enter an age between 14 and 100 years.", "warning");
        return; 
    }
    if (weight < 35 || weight > 250) {
        showToast("Please enter a realistic weight (35kg - 250kg).", "warning");
        return;
    }
    if (height < 120 || height > 250) {
        showToast("Please enter a realistic height (120cm - 250cm).", "warning");
        return;
    }
    if (age < 18 && weight > 100) {
        showToast("Unusual input: Please verify your age and weight.", "warning");
        return;
    }

    // Proceed if all checks pass
    btn.innerText = "Generating Plan ⏳...";
    btn.disabled = true;

    const data = {
        gender: document.getElementById("gender").value,
        age: age,
        weight: weight,
        height: height,
        activity_level: document.getElementById("activity").value,
        goal: document.getElementById("goal").value,
    };

    try {
        const response = await fetch("/recommend", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (!response.ok) {
            // Server error toast!
            showToast(result.error || "Server error. Check your inputs.", "error");
            btn.innerText = "Generate My Plan ✨";
            btn.disabled = false;
            return;
        }

        // Save goal for the dashboard coach tips
        result.goal = data.goal;

        // Save data and go to the results page
        sessionStorage.setItem("dietData", JSON.stringify(result));
        
        // Show a quick success toast right before redirecting
        showToast("Plan generated successfully!", "success");
        setTimeout(() => {
            window.location.href = "/result";
        }, 800);

    } catch (error) {
        showToast("Failed to connect to the server.", "error");
        btn.innerText = "Generate My Plan ✨";
        btn.disabled = false;
    }
});
