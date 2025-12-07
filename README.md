# Neuronix AI JobFlow

**Neuronix AI JobFlow** is an advanced AI-powered job recommendation system designed to bridge the gap between job seekers and their dream careers. By leveraging web scraping, natural language issues, and machine learning, it aggregates job listings from multiple platforms and provides personalized recommendations based on user profiles and resumes.

## 🚀 Main Idea

The core concept of **Neuronix AI JobFlow** is to simplify the job hunt. Instead of searching multiple sites manually, users can:

1.  **Create a Profile** or **Upload a CV** to let the system understand their skills and experience.
2.  **Search** using a structured form or a conversational **Chat Mode**.
3.  **Get Matched** with the most relevant opportunities using an intelligent matching algorithm that ranks jobs by relevance.

## 🏗️ Architecture

The project follows a modern, decoupled architecture:

### **Backend (Python & Flask)**

The server-side logic is built with **Python** using the **Flask** framework, capable of handling API requests, data processing, and serving the frontend.

- **API Layer**: RESTful endpoints defined in `routes/` (Auth, User, Jobs) to handle frontend requests.
- **Data Collection Engine**: Robust web scrapers (`scraper_enhanced.py`) that fetch real-time job data from platforms like Wuzzuf and LinkedIn.
- **Intelligence Layer**:
  - **CV Parser**: Extracts text and skills from uploaded PDF/DOCX resumes (`cv_parser.py`).
  - **Matcher**: Scikit-learn based text analysis to calculate match scores between user profiles and job descriptions (`matcher_enhanced.py`).
- **Database**: SQLite (`jobs.db`) for lightweight, reliable storage of user data, job listings, and search history.

### **Frontend (Vanilla HTML/CSS/JS)**

A lightweight, fast, and responsive user interface built without heavy frameworks.

- **Structure**: Semantic HTML5 pages (`src/*.html`).
- **Styling**: Custom CSS3 with modern design principles, responsive layouts, and dark/light mode support (`src/style.css`).
- **Interactivity**: Vanilla JavaScript (ES6+) handles dynamic content loading, API communication, and state management (`src/app.js`, `src/auth.js`).

## 🌟 Key Features

- **🔍 Smart Job Search**:
  - **Structured Search**: Filter by job title, location, experience, and type.
  - **Chat Mode**: Conversational interface to describe what you are looking for.
- **🤖 AI Resume Parsing**: Upload your CV (PDF), and the system extracts your skills and experience to auto-fill your profile.
- **📊 Intelligent Matching**: Jobs are ranked by a "Match Score" indicating how well they fit your profile.
- **🕵️ Automated Scraping**: Background processes fetch fresh job listings from major job portals.
- **👤 User Management**: Secure Authentication (Signup/Login), Profile Management, and Search History.
- **💾 Saved Jobs**: Bookmark interesting opportunities to review later.
- **🎨 Modern UI**: Clean, professional design with a built-in Dark Mode.

## 📂 Project Structure

```
Job-Recommendation-System/
├── server.py              # Main Flask application entry point
├── database.py            # Database initialization and connection logic
├── schema.sql             # SQL schema for the SQLite database
├── requirements.txt       # Python dependencies
├── start.bat              # Windows batch script to launch the server
│
├── routes/                # API Route modules
│   ├── auth.py            # Authentication endpoints
│   ├── jobs.py            # Job search and recommendation endpoints
│   └── user.py            # User profile and history endpoints
│
├── src/                   # Frontend Source Files
│   ├── index.html         # Landing Page
│   ├── style.css          # Main Stylesheet
│   ├── app.js             # Core frontend logic
│   ├── auth.js            # Frontend authentication logic
│   ├── js/                # Page-specific scripts
│   └── assets/            # Images and icons
│
└── utils/                 # Utility scripts (scrapers, parsers, validators)
    ├── scraper_enhanced.py
    ├── matcher_enhanced.py
    └── cv_parser.py
```

## 🛠️ Installation & Setup

1.  **Prerequisites**:

    - Python 3.8+ installed.
    - Git (optional, for cloning).

2.  **Clone/Download the Repository**:

    ```bash
    git clone <repository-url>
    cd Job-Recommendation-System
    ```

3.  **Install Dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Application**:

    - **Windows**: Double-click `start.bat` or run:
      ```bash
      start.bat
      ```
    - **Manual Start**:
      ```bash
      python server.py
      ```

5.  **Access the App**:
    Open your browser and navigate to `http://localhost:5000`

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
