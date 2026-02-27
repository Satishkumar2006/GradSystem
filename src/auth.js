// 1. IMPORTANT: This must be at the very top of auth.js
let currentRole = 'student'; 

function switchTab(role) {
    currentRole = role;
    console.log("🎯 Active Role set to:", currentRole);

    const studentTab = document.getElementById('studentTab');
    const teacherTab = document.getElementById('teacherTab');
    const roleLabel = document.getElementById('roleLabel');

    if (role === 'student') {
        // Highlight Student Tab
        studentTab.classList.add('bg-white', 'text-blue-600', 'shadow-sm');
        studentTab.classList.remove('text-slate-500');
        
        // De-highlight Teacher Tab
        teacherTab.classList.remove('bg-white', 'text-blue-600', 'shadow-sm');
        teacherTab.classList.add('text-slate-500');
        
        // Update Button Text
        roleLabel.innerText = "Student";
    } else {
        // Highlight Teacher Tab
        teacherTab.classList.add('bg-white', 'text-blue-600', 'shadow-sm');
        teacherTab.classList.remove('text-slate-500');
        
        // De-highlight Student Tab
        studentTab.classList.remove('bg-white', 'text-blue-600', 'shadow-sm');
        studentTab.classList.add('text-slate-500');
        
        // Update Button Text
        roleLabel.innerText = "Teacher";
    }
}

async function handleLogin() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const errorMsg = document.getElementById('errorMsg');
    
    // Reset error message
    errorMsg.innerText = "";
    errorMsg.classList.add('hidden');

    console.log("🚀 Attempting login for:", email);

    try {
        const userCredential = await auth.signInWithEmailAndPassword(email, password);
        const user = userCredential.user;
        console.log("✅ Auth Success! UID:", user.uid);

        // Fetch User Role from Firestore
        console.log("📡 Fetching role from Firestore...");
        const userDoc = await db.collection('users').doc(user.uid).get();
        
        if (userDoc.exists) {
            const userData = userDoc.data();
            console.log("👤 User Data found:", userData);
            
            if (userData.role === currentRole) {
                console.log(`✨ Redirecting to ${currentRole}.html`);
                window.location.href = `${currentRole}.html`;
            } else {
                throw new Error(`Access Denied: You are registered as a ${userData.role}.`);
            }
        } else {
            throw new Error("User profile not found in Firestore. Check your 'users' collection.");
        }
    } catch (error) {
        console.error("❌ Login Error:", error.code, error.message);
        errorMsg.innerText = error.message;
        errorMsg.classList.remove('hidden');
        // Sign out if there was a role mismatch
        if (auth.currentUser) auth.signOut();
    }
}
let isLoginMode = true;

function toggleAuthMode() {
    isLoginMode = !isLoginMode;
    const nameField = document.getElementById('nameField');
    const loginBtn = document.getElementById('loginBtn');
    const toggleBtn = document.getElementById('toggleBtn');
    const toggleText = document.getElementById('toggleText');

    if (isLoginMode) {
        nameField.classList.add('hidden');
        loginBtn.innerHTML = `<span>Sign In as <span id="roleLabel">${currentRole === 'student' ? 'Student' : 'Teacher'}</span></span>`;
        toggleBtn.innerText = "Register";
        toggleText.innerText = "Don't have an account?";
    } else {
        nameField.classList.remove('hidden');
        loginBtn.innerHTML = `<span>Register as <span id="roleLabel">${currentRole === 'student' ? 'Student' : 'Teacher'}</span></span>`;
        toggleBtn.innerText = "Login";
        toggleText.innerText = "Already have an account?";
    }
}

// Update handleLogin to check mode
async function handleAuth() {
    if (isLoginMode) {
        handleLogin(); // Your existing function
    } else {
        handleRegister();
    }
}

async function handleRegister() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const name = document.getElementById('regName').value;
    const errorMsg = document.getElementById('errorMsg');

    try {
        // 1. Create User in Firebase Authentication
        const userCredential = await auth.createUserWithEmailAndPassword(email, password);
        const user = userCredential.user;

        // 2. Create Profile in Firestore
        await db.collection('users').doc(user.uid).set({
            uid: user.uid,
            name: name,
            email: email,
            role: currentRole, // Taken from the active Tab
            created_at: firebase.firestore.FieldValue.serverTimestamp()
        });

        console.log(`✅ Registered new ${currentRole}: ${name}`);
        window.location.href = `${currentRole}.html`;
    } catch (error) {
        errorMsg.innerText = error.message;
        errorMsg.classList.remove('hidden');
    }
}