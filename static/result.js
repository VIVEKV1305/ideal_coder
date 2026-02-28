// --- TOAST NOTIFICATION FUNCTION ---
function showToast(message, type = "success") {
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        document.body.appendChild(container);
    }
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    let icon = type === "success" ? "✅" : (type === "error" ? "❌" : "⚠️");
    toast.innerHTML = `<span style="font-size: 18px;">${icon}</span> <span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.classList.add("fade-out");
        toast.addEventListener("animationend", () => toast.remove());
    }, 4000);
}

const storedData = sessionStorage.getItem("dietData");
if (!storedData) { window.location.href = "/"; }

const result = JSON.parse(storedData);
let targetCalories = result.daily_calories;
let totalEaten = 0; let totalBurned = 0;

document.getElementById("display-bmr").innerText = result.bmr;
document.getElementById("display-cals").innerText = result.daily_calories;

const generateMealTable = (mealName, mealData) => {
    let rows = mealData.map(item => `<tr><td>${item.food}</td><td>${item.calories}</td><td>${item.protein}g</td><td>${item.carbs}g</td><td>${item.fat}g</td></tr>`).join("");
    return `<h4>${mealName.charAt(0).toUpperCase() + mealName.slice(1)}</h4><table class="diet-table"><tr><th>Food</th><th>Calories</th><th>Protein</th><th>Carbs</th><th>Fats</th></tr>${rows}</table>`;
};

document.getElementById("diet-plan-tables").innerHTML = `
    ${generateMealTable("breakfast", result.diet_plan.breakfast)}
    ${generateMealTable("lunch", result.diet_plan.lunch)}
    ${generateMealTable("snacks", result.diet_plan.snacks)}
    ${generateMealTable("dinner", result.diet_plan.dinner)}
`;

function updateTrackerUI() {
    document.getElementById("track-goal").innerText = targetCalories;
    document.getElementById("track-eaten").innerText = totalEaten;
    document.getElementById("track-burned").innerText = totalBurned;
    let netElement = document.getElementById("track-net");
    netElement.innerText = (totalEaten - totalBurned);
    netElement.style.color = (totalEaten - totalBurned) > targetCalories ? "red" : "black";
}

const workoutCaloriesMap = { "Walking": 150, "Running": 350, "Cycling": 250, "Weightlifting": 200, "Yoga": 150, "Swimming": 300, "HIIT": 400, "Custom": "" };
document.getElementById("workoutName").addEventListener("change", function() { document.getElementById("workoutCals").value = workoutCaloriesMap[this.value]; });

document.getElementById("foodLogForm").addEventListener("submit", function(e) {
    e.preventDefault();
    let name = document.getElementById("foodName").value;
    let cals = parseInt(document.getElementById("foodCals").value);
    totalEaten += cals;
    addLogItem(`🍏 Ate: ${name} (+${cals} kcal)`);
    updateTrackerUI();
    showToast(`Logged ${cals} kcal from ${name}!`, "success");
    this.reset();
});

document.getElementById("workoutLogForm").addEventListener("submit", function(e) {
    e.preventDefault();
    let name = document.getElementById("workoutName").value;
    let cals = parseInt(document.getElementById("workoutCals").value);
    if(!name) { showToast("Please select a workout type.", "warning"); return; }
    totalBurned += cals;
    addLogItem(`🔥 Burned: ${name} (-${cals} kcal)`);
    updateTrackerUI();
    
    let tipBox = document.getElementById("coach-tip");
    tipBox.style.display = "block"; 
    let userGoal = result.goal || "maintain"; 
    
    if (userGoal === "weight_loss") tipBox.innerHTML = `💡 <strong>Coach Tip:</strong> Great job burning ${cals} kcal with ${name}! Try not to eat these calories back.`;
    else if (userGoal === "weight_gain") tipBox.innerHTML = `💡 <strong>Coach Tip:</strong> Awesome ${name} workout! Eat back the ${cals} kcal you burned to build muscle.`;
    else tipBox.innerHTML = `💡 <strong>Coach Tip:</strong> Solid ${name} session! Consider a healthy snack to balance out the ${cals} kcal you burned.`;
    
    showToast(`Great job! Burned ${cals} kcal.`, "success");
    this.reset();
});

function addLogItem(text) {
    let li = document.createElement("li");
    li.innerText = text;
    document.getElementById("log-list").prepend(li);
}
updateTrackerUI();

// --- AI CHATBOT LOGIC ---
const chatToggle = document.getElementById("chatbot-toggle");
const chatWindow = document.getElementById("chatbot-window");
const closeChat = document.getElementById("close-chat");
const chatInput = document.getElementById("chat-input");
const sendChat = document.getElementById("send-chat");
const chatMessages = document.getElementById("chat-messages");

chatToggle.addEventListener("click", () => { chatWindow.style.display = chatWindow.style.display === "flex" ? "none" : "flex"; });
closeChat.addEventListener("click", () => { chatWindow.style.display = "none"; });

async function handleSendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    appendMessage(text, "user-message");
    chatInput.value = "";
    const typingId = appendMessage("Typing...", "bot-message");

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: text,
                calories: targetCalories,
                goal: result.goal || "maintain",
                bmi: result.bmi || "Unknown",
                risk: result.health_risk ? result.health_risk.category : "Unknown"
            })
        });

        const data = await response.json();
        document.getElementById(typingId).remove();
        appendMessage(data.reply, "bot-message");

    } catch (error) {
        document.getElementById(typingId).remove();
        appendMessage("Oops, I lost connection to the server! Make sure your API key is valid.", "bot-message");
    }
}

sendChat.addEventListener("click", handleSendMessage);
chatInput.addEventListener("keypress", (e) => { if (e.key === "Enter") handleSendMessage(); });

function appendMessage(text, className) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${className}`;
    msgDiv.innerText = text;
    msgDiv.id = "msg-" + Date.now(); 
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight; 
    return msgDiv.id;
}