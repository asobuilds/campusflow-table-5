# Campusflow-table-5

A robust, command-line technical helpdesk application designed for **Learn2Earn campus staff** to log, prioritize, assign, and track IT support requests. 

This repository represents the output of a **6-Hour/Weekend long AI-Native Engineering Sprint** focused on deliberate learning, comprehensive test automation, and professional peer-review workflows.

---

## Project Overview & Requirements

CampusFlow replaces informal support messages with a structured, reliable CLI ticket manager. The application is built using **Python**, features structured **JSON persistence**, and enforces a **100% automated test suite**.

### Core Ticket Schema
Each ticket manages and tracks the following essential fields:
*   `id`: Unique identifier (auto-generated)
*   `title`: Brief summary of the technical issue
*   `category`: Type of issue (e.g., Wi-Fi, Hardware, Dev Environment, Platform)
*   `urgency`: Criticality level used to calculate priority (e.g., Low, Medium, High)
*   `status`: Current lifecycle state (e.g., Open, In Progress, Resolved)
*   `assignee`: The support fellow or staff member handling the issue
*   `created_at`: Timestamp of ticket creation

---

##  Features

*    **Ticket Management:** Create, update status, and assign support tickets.
*    **Priority Calculation:** Dynamic prioritization based on urgency and category matrix rules.
*    **Queue & Reporting:** View open queues and generate summary reports of campus health.
*    **JSON Data Storage:** Local state persistence ensuring data survives application restarts.
*    **Automated Testing:** Comprehensive test coverage validation for all core business logic.

---

## Architecture & Project Structure

```text
campusflow/
├── src/
│   ├── __init__.py
│   ├── main.py          # CLI Application Entry Point
│   ├── models.py        # Ticket and Queue Data Models
│   └── storage.py       # JSON File Reading/Writing Logic
├── tests/
│   ├── __init__.py
│   ├── test_models.py   # Unit tests for priority, creation, and logic
│   └── test_storage.py  # Unit tests for JSON persistence
├── data/
│   └── tickets.json     # Local database file (git-ignored in production)
├── README.md
└── requirements.txt
```

---

##  Getting Started

### Prerequisites
*   Python 3.10+
*   Git

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com
   cd campusflow
   ```

2. **Set up a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python src/main.py
   ```

### Running the Test Suite
Execution of the complete test suite is mandatory before any main branch integration:
```bash
pytest tests/
```

---

## Sprint Git Workflow

To meet the non-negotiable requirements of the sprint, the team strictly adhered to the following trunk-based branch management protocol:

1. **Feature Isolation:** No fellow committed directly to `main`. All work was performed on isolated feature branches (`fellow-a/feature-name`).
2. **Pull Requests (PRs):** Code integrations required a formal PR detailing changes made and testing steps verified.
3. **Peer Review:** Each fellow thoroughly reviewed, commented on, and approved the other's PR before code was merged.

---

## AI-Native Learning Logs

A core objective of this sprint was **deliberate learning and validation** using AI, rather than blind copy-pasting. Below are the verified interactions where our team evaluated, challenged, and corrected AI outputs.

### Fellow 1 Interactions
*   **Interaction 1 (Concept Learning):** *Used AI to understand how to mock JSON file reads/writes in `pytest`. Implemented a robust `StringIO` fixture based on the concept.*
*   **Interaction 2 (Code Optimization):** *Asked AI for a priority sorting algorithm. Used its feedback to implement Python's built-in `lambda` sorting key structure.*
*   **Interaction 3 (AI Correction/Rejection):** *The AI suggested using an external database library (`SQLAlchemy`) for tracking. **Rejected** this suggestion because it violated the sprint's strict requirement for simple local JSON file persistence. Built a lightweight native `json` module wrapper instead.*

### Fellow 2 Interactions
*   **Interaction 1 (Concept Learning):** *Deepened understanding of Python dataclasses and type-hinting invariants for ticket properties.*
*   **Interaction 2 (Code Optimization):** *Refactored the CLI input loop using an AI-suggested command-pattern dictionary mapping instead of a monolithic `if/else` block.*
*   **Interaction 3 (AI Correction/Rejection):** *The AI provided an edge-case priority calculation formula that incorrectly ranked low-urgency Wi-Fi issues above high-urgency platform issues. **Corrected** the logic independently to align with the core Learn2Earn problem matrix before writing matching unit tests.*
