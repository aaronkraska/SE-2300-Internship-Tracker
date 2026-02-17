# Internship Application Tracker (IAT) — V1

A small, offline-first Python application designed to help students track internship/job applications in one place. The Internship Application Tracker (IAT) stores application details (company, role, date applied, status, notes) and provides a built-in follow-up system that highlights when applications are due for follow-up.

This project was designed as part of the **SE 2300 Module 1** assignment and focuses on requirements, architecture planning, and testing design.

---

## Features (Planned for V1)

- Add a new internship/job application entry
- Edit existing entries
- Delete or archive entries
- Track application status:
- Planned, Applied, Follow-up Needed, Interviewing, Offer, Rejected, Archived
- Automatically calculate follow-up date:
- Default rule: **Follow-up Date = Date Applied + 10 days**
- Manual follow-up override supported
- View **Follow-ups Due** (due today or overdue)
- Search by company name or role title
- Filter by application status
- Display summary counts by status
- Offline local storage (SQLite)

---

## Tech Stack

- **Language:** Python  
- **Storage:** SQLite (local database)  
- **UI (planned):** Tkinter (Python built-in GUI library)  
- **Testing (planned):** `unittest` (or `pytest`)

---

## Project Scope (V1 Assumptions)

- **Single user only** (no accounts/login)
- **Offline-first**
- Follow-up reminders are **shown inside the app**
- No external integrations (email/text/calendar)

---

## Architecture Overview (High-Level)

The system uses a simple layered architecture:

1. **Presentation Layer (UI)**  
   - Main dashboard, add/edit form, follow-ups view

2. **Business Logic Layer (Services)**  
   - Input validation  
   - Follow-up calculation  
   - Status workflow rules

3. **Data Layer (SQLite Storage)**  
   - Local database file for persistent storage

---

## Data Model

### `Applications` Table (planned)

| Field Name        | Type    | Description |
|------------------|---------|------------|
| application_id   | Integer | Primary key |
| company_name     | Text    | Required |
| role_title       | Text    | Required |
| date_applied     | Date    | Required |
| status           | Text    | Required |
| follow_up_date   | Date    | Required |
| application_link | Text    | Optional |
| location         | Text    | Optional |
| notes            | Text    | Optional |
| archived         | Boolean | Default false |

---
## Installation and Setup

### 1. Install Python

Ensure Python 3 is installed on your system.

### 2. Clone the Repository

git clone https://github.com/aaronkraska/SE-2300-Internship-Tracker

cd YOUR_REPOSITORY_NAME

Replace `YOUR_REPOSITORY_NAME` with the location that you cloned it into.

### 3. Run the Application

Use python iat_app.py or python3 iat_app.py.

Or if your environment has it, press the **run Python file** button.
## License

This project is for educational purposes as part of coursework.
