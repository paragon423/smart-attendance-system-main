

# Smart Attendance System

> An AI-powered biometric attendance system that uses deep-learning-based face detection and recognition to automate real-time attendance management.

## 📌 Overview

The **Smart Attendance System** is a web-based application designed to automate attendance using facial recognition.

The system captures faces through a camera, detects and recognizes registered individuals using **InsightFace**, and automatically records their attendance in a **SQLite database**.

It provides a simple dashboard for real-time attendance monitoring and viewing attendance history.

---

## 🚀 Features

* Real-time face detection and recognition
* Multi-face detection
* Automatic attendance marking
* Face enrollment for registered users
* Attendance history and records
* Web-based interface
* SQLite database integration
* Deep-learning-based face recognition
* Lightweight and easy to deploy

---

## 🧠 AI Model

The system uses the **InsightFace** framework with the `buffalo_s` model pack.

### Face Detection

**SCRFD (Sample and Computation Redistribution for Efficient Face Detection)** is used to efficiently detect faces in images and video frames.

### Face Recognition

**MobileFaceNet** is used to generate facial feature embeddings for identifying registered individuals.

### Recognition Pipeline

```
Camera / Image
      ↓
Face Detection
      ↓
Face Alignment
      ↓
Feature Extraction
      ↓
Face Embedding
      ↓
Identity Matching
      ↓
Attendance Recording
      ↓
SQLite Database
```

---

## 🏗️ System Architecture

```
┌─────────────────────┐
│   Camera / User     │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Frontend Interface  │
│ HTML / CSS / JS     │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│    Flask Backend    │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│    InsightFace      │
│ SCRFD + MobileFaceNet│
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Attendance System   │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│   SQLite Database   │
└─────────────────────┘
```

---

## 🛠️ Technology Stack

| Category             | Technology            |
| -------------------- | --------------------- |
| Programming Language | Python                |
| Backend              | Flask                 |
| Computer Vision      | OpenCV                |
| Face Detection       | SCRFD                 |
| Face Recognition     | MobileFaceNet         |
| AI Framework         | InsightFace           |
| Database             | SQLite                |
| Frontend             | HTML, CSS, JavaScript |
| Version Control      | Git & GitHub          |

---

## 📁 Project Structure

```
smart-attendance-system/
│
├── backend/
│   ├── main.py
│   ├── data.py
│   │
│   ├── templates/
│   │   ├── index.html
│   │   └── history.html
│   │
│   └── database/
│
├── .gitignore
├── README.md
└── requirements.txt
```

> Database files and biometric enrollment data are excluded from GitHub for privacy and security.

---

## ⚙️ Installation

### 1. Clone the repository

```
git clone https://github.com/24A31A4209/smart-attendance-system.git
cd smart-attendance-system
```

### 2. Create a virtual environment

```
python -m venv venv
```

Activate it on Windows:

```
venv\Scripts\activate
```

### 3. Install dependencies

```
pip install -r requirements.txt
```

### 4. Run the application

```
python backend/main.py
```

Open the application in your browser:

```
http://127.0.0.1:5000
```

---

## 🔄 How It Works

1. A user is enrolled into the system.
2. The system detects the user's face.
3. Facial features are extracted using the recognition model.
4. The generated embedding is compared with enrolled identities.
5. The system identifies the person.
6. Attendance is automatically recorded.
7. Attendance records can be viewed through the web dashboard.

---

## 🔐 Privacy & Security

Since the system works with biometric information:

* Face enrollment data should be stored securely.
* Database files are excluded from version control.
* Biometric information should not be publicly shared.
* Access to attendance records should be restricted.
* Production deployments should implement proper authentication and authorization.

---

## 🔮 Future Enhancements

* Face liveness detection
* Anti-spoofing protection
* Improved recognition under different lighting conditions
* Attendance analytics and reports
* Student and faculty dashboards
* Email/SMS notifications
* Cloud deployment
* Mobile application
* Role-based authentication

---

## 👥 Team

### Guru Tulasi Hima Bindu

**Project Lead & AI Integration**

* AI model integration
* Face recognition pipeline
* System architecture
* Backend integration

GitHub: [@24A31A4209](https://github.com/24A31A4209)

### Piradi Sai Rupa Sri

**Backend & Database Management**

* Flask backend
* API development
* SQLite database
* Attendance management

GitHub: [@24A31A4227](https://github.com/24A31A4227)

### Jampa Siri Chandana Priya

**UI/UX & Frontend Development**

* Frontend interface
* HTML/CSS
* JavaScript
* User experience

GitHub: [@24A31A4210](https://github.com/24A31A4210)

### Chitturi Dhanu Sree

**Data Engineering & Testing**

* Dataset preparation
* Face enrollment testing
* Recognition testing
* Performance evaluation

GitHub: [@24A31A4207](https://github.com/24A31A4207)

### Chikkala Mary Blessica

**Documentation & Deployment**

* Technical documentation
* Requirement analysis
* Environment configuration
* Deployment support

GitHub: [@24A31A4206](https://github.com/24A31A4206)

---

## 📚 Technologies & References

This project makes use of the following open-source technologies:

* InsightFace
* OpenCV
* Flask
* SQLite
* SCRFD
* MobileFaceNet

---

## ⚠️ Disclaimer

This project is developed primarily for **academic, educational, and research purposes**.

The system should be properly validated for accuracy, security, privacy, and reliability before being used in real-world biometric attendance environments.

---

## ⭐ Support

If you find this project useful, consider giving the repository a ⭐ on GitHub.

**Built with Python, Computer Vision, Deep Learning, and Flask.**
