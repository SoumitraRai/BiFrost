# BIFROST ✨🏦

## Secure & Control Your Digital Payments

**BIFROST** is an innovative application designed to safeguard and manage digital payments. Inspired by the legendary Bifrost bridge from Norse mythology—a connection between realms—this app acts as a secure gateway for financial transactions. BIFROST intercepts payment requests in real-time and routes them to parents or guardians for approval before processing, ensuring safe and controlled spending.

With a strong foundation in **Python** for network monitoring and **Electron + React Native** for cross-platform development, BIFROST delivers a seamless, secure, and private experience.

---

## 🔒 Why Choose BIFROST?
In a world where digital payments are ubiquitous, financial security is more crucial than ever. BIFROST bridges the gap between **security and convenience**, offering:

- **Real-time payment monitoring:** Payment requests are intercepted before processing.
- **Parental Approval Workflow:** Ensures controlled spending by requiring guardian approval.
- **End-to-End Encryption:** SSL/TLS encryption guarantees data privacy.
- **Cross-platform compatibility:** Works on Windows, Mac, and Linux (Debian-based systems).
- **Secure Network Monitoring:** Uses **mitmproxy** to capture and manage requests securely.
- **Future Enhancements:** Upcoming features include multi-device sync, advanced monitoring, and AI-based fraud detection.

---

## 🚀 Features
- **🛡️ Payment Request Monitoring:** Detects and intercepts payment traffic in real-time.
- **👤 Parental Approval Workflow:** Parents can approve or deny transactions via an easy-to-use interface.
- **🔐 Secure Network Monitoring:** Powered by **mitmproxy API**, ensuring all requests are securely routed.
- **💻 Cross-Platform Support:** Runs on Windows, macOS, and Linux (Debian-based distros).
- **🔒 SSL/TLS Encryption:** Transactions are secured with advanced encryption.
- **🚀 Future Updates:** Multi-device synchronization, AI-driven security alerts, and more.

---

## 🔧 How BIFROST Works
1. **Network Monitoring** – BIFROST uses **mitmproxy API** to detect and intercept payment requests.
2. **Approval Workflow** – Intercepted payment requests are sent to a parent's device for approval.
3. **Transaction Processing** – If approved, the payment proceeds; if denied, it is blocked.
4. **Data Encryption** – All communication is encrypted using **SSL/TLS**.

---

## 🖥️ Tech Stack
- **Backend:** Python, mitmproxy API (network monitoring)
- **Frontend:** Electron + React Native (cross-platform UI)
- **Encryption:** SSL/TLS (end-to-end security)
- **Platforms:**
  - **Desktop:** macOS, Windows, Linux (Debian-based)
  - **Mobile:** Planned support for iOS and Android

---

## 🛠️ Installation & Setup
### Backend (Python)
#### macOS
1. Check if Python is installed:
   ```bash
   python3 --version
   ```
2. Install Python via Homebrew (if needed):
   ```bash
   brew install python
   ```
3. Install pip:
   ```bash
   python3 -m ensurepip --upgrade
   ```

#### Windows
1. Download Python from the [official website](https://www.python.org/downloads/).
2. During installation, check "Add Python to PATH".
3. Verify installation:
   ```bash
   python --version
   ```
4. Install pip:
   ```bash
   python -m ensurepip --upgrade
   ```

#### Linux (Debian-based)
1. Check Python installation:
   ```bash
   python3 --version
   ```
2. Install Python and pip:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip
   ```

#### Clone & Install Dependencies
```bash
git clone https://github.com/your-username/bifrost.git
cd bifrost/ProxyVPN
pip install -r requirements.txt
```

### Frontend (Electron + React Native)
1. Navigate to the frontend folder and install dependencies:
   ```bash
   cd bifrost/frontend
   npm install
   ```
2. Run the app:
   ```bash
   # macOS
   npm start --mac

   # Linux (Debian)
   npm start --linux

   # Windows
   npm start --win
   ```

---

## 🏢 Contributing
We welcome contributors! Here's how you can get involved:
1. **Fork the repository**
2. **Create a new branch**
3. **Make changes and improvements**
4. **Submit a pull request**

Please follow coding standards and write tests where necessary.

---

##📜 License  
This project is licensed under the **CC BY-NC 4.0** license.  
You are free to use, modify, and share it **for non-commercial purposes only**.  
![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-blue.svg)


---

## 🛡️ Get Involved
Are you passionate about digital security, parental controls, or fintech? **Join the BIFROST project!**

For questions, feature suggestions, or collaboration, feel free to open an issue or reach out.

🔒 **Your data remains private, secure, and encrypted. Your safety is our priority.** 🔒

