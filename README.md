# HACK THE AI - CTF Platform

Welcome to **HACK THE AI**, a Capture The Flag (CTF) platform designed to teach and test cybersecurity concepts in a modern, interactive environment.

## Overview

This platform features a sleek, futuristic dark-mode UI with integrated labs, a leaderboard, mission tracking, and an interactive workstation for solving challenges. Users can learn about vulnerabilities like:
- Access Control Issues
- Information Disclosure
- Insecure Direct Object References (IDOR)
- Cross-Site Scripting (XSS)
- Phishing and Social Engineering

## Features
- **Interactive Labs:** Containerized labs that provide realistic, isolated environments for learning.
- **Mission Progression:** Step-by-step missions and evidence collection to track learning progress.
- **Quiz System:** In-built quiz functionality to validate theoretical understanding.
- **Dynamic Leaderboard:** Real-time scoring based on evidence collected and flags captured.
- **Modern Architecture:** Built with Flask, SQLAlchemy, Docker, and stylized with a beautiful custom UI.

## Getting Started

### Prerequisites
- Python 3.7+
- Docker & Docker Compose (for running interactive labs)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Abhishekagre414/CTFplatform.git
   cd CTFplatform/CTFplatform-modern-ui/CTFplatform
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the platform:**
   ```bash
   ./start.sh
   ```
   Or use Docker Compose:
   ```bash
   docker-compose up --build
   ```

4. **Access the application:**
   Open your browser and navigate to `http://localhost:5000`.

## Architecture Details
The platform is built on a modular Blueprint architecture, making it easy to extend and maintain:
- `routes/`: Controllers and endpoint handlers.
- `services/`: Business logic, database interactions, and Docker orchestration.
- `models.py`: SQLAlchemy database models.
- `static/`: CSS styling, JS components, and images.
- `templates/`: Jinja2 HTML templates.

## Contributing
Contributions are welcome! If you'd like to add new labs, improve the UI, or fix bugs, please submit a Pull Request or open an Issue.

## License
This project is for educational purposes.