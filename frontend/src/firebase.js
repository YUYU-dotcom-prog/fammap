import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: "AIzaSyCcz_RdfAVeesTm149mZDlUXIAg4k1SVig",
  authDomain: "farmmap-9a59f.firebaseapp.com",
  projectId: "farmmap-9a59f",
  storageBucket: "farmmap-9a59f.firebasestorage.app",
  messagingSenderId: "6809224811",
  appId: "1:6809224811:web:7ac93dd1a6df9aa989532e",
  measurementId: "G-4HSPYF26SH"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export default app;