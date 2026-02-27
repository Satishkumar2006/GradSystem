const firebaseConfig = {
    apiKey: "AIzaSyBWcFRsABNj1W_hAAzwKw9sQwnzWM9JJ0M",
    authDomain: "gradsystem-v2.firebaseapp.com",
    projectId: "gradsystem-v2",
    storageBucket: "gradsystem-v2.firebasestorage.app",
    messagingSenderId: "866241919053",
    appId: "1:866241919053:web:49f27fd942df0421ab0404"
  };

// Initialize Firebase
if (!firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
}

const db = firebase.firestore();
const auth = firebase.auth();
const storage = firebase.storage(); // This will work now after Step 1