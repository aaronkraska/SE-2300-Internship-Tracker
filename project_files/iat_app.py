import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta, date

DB_FILE = "internships.db"

STATUSES = [
    "Planned",
    "Applied",
    "Follow-up Needed",
    "Interviewing",
    "Offer",
    "Rejected",
    "Archived",
]


def init_db() -> None:
    """Create the SQLite database and Applications table if they do not exist."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS Applications (
                application_id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                role_title TEXT NOT NULL,
                date_applied TEXT NOT NULL,
                status TEXT NOT NULL,
                follow_up_date TEXT NOT NULL,
                application_link TEXT,
                location TEXT,
                notes TEXT,
                archived INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        conn.commit()


def parse_date_iso(date_str: str) -> datetime:
    """Parse YYYY-MM-DD. Raise ValueError if invalid."""
    return datetime.strptime(date_str.strip(), "%Y-%m-%d")


def parse_date_only(date_str: str) -> date:
    """Parse YYYY-MM-DD into a date object. Raise ValueError if invalid."""
    return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()


def calculate_follow_up(date_applied_iso: str) -> str:
    """Default follow-up is +10 days, returned as YYYY-MM-DD."""
    dt = parse_date_iso(date_applied_iso)
    return (dt + timedelta(days=10)).strftime("%Y-%m-%d")


def fetch_application_by_id(app_id: int) -> dict | None:
    """Fetch one application record and return it as a dict, or None if not found."""
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute(
            """
            SELECT application_id, company_name, role_title, date_applied, status, notes, archived
            FROM Applications
            WHERE application_id = ?;
            """,
            (app_id,),
        )
        row = cur.fetchone()

    if not row:
        return None

    return {
        "application_id": row[0],
        "company_name": row[1],
        "role_title": row[2],
        "date_applied": row[3],
        "status": row[4],
        "notes": row[5] or "",
        "archived": bool(row[6]),
    }


class ApplicationFormWindow(tk.Toplevel):
    """
    Reusable window for both Add and Edit.
    If app_id is None -> Add mode
    If app_id is int -> Edit mode (loads record and updates it)
    """

    def __init__(self, parent, on_saved_callback, app_id: int | None = None):
        super().__init__(parent)
        self.resizable(False, False)
        self.on_saved_callback = on_saved_callback
        self.app_id = app_id

        self.title("Edit Application" if self.app_id is not None else "Add Application")

        self.company_var = tk.StringVar()
        self.role_var = tk.StringVar()
        self.date_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Applied")
        self.notes_var = tk.StringVar()

        pad = {"padx": 10, "pady": 6}

        ttk.Label(self, text="Company Name (required)").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(self, textvariable=self.company_var, width=40).grid(row=0, column=1, **pad)

        ttk.Label(self, text="Role Title (required)").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(self, textvariable=self.role_var, width=40).grid(row=1, column=1, **pad)

        ttk.Label(self, text="Date Applied (YYYY-MM-DD) (required)").grid(row=2, column=0, sticky="w", **pad)
        ttk.Entry(self, textvariable=self.date_var, width=40).grid(row=2, column=1, **pad)

        ttk.Label(self, text="Status (required)").grid(row=3, column=0, sticky="w", **pad)
        ttk.Combobox(self, textvariable=self.status_var, values=STATUSES, state="readonly", width=37).grid(
            row=3, column=1, **pad
        )

        ttk.Label(self, text="Notes (optional)").grid(row=4, column=0, sticky="w", **pad)
        ttk.Entry(self, textvariable=self.notes_var, width=40).grid(row=4, column=1, **pad)

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=5, column=0, columnspan=2, sticky="e", **pad)

        ttk.Button(btn_frame, text="Cancel", command=self.destroy).grid(row=0, column=0, padx=6)
        ttk.Button(btn_frame, text="Save", command=self.save).grid(row=0, column=1, padx=6)

        if self.app_id is not None:
            self.load_existing()

        self.after(50, lambda: self.focus_force())

    def load_existing(self) -> None:
        record = fetch_application_by_id(self.app_id)
        if record is None:
            messagebox.showerror("Error", "That application no longer exists.")
            self.destroy()
            return

        self.company_var.set(record["company_name"])
        self.role_var.set(record["role_title"])
        self.date_var.set(record["date_applied"])
        self.status_var.set(record["status"])
        self.notes_var.set(record["notes"])

    def save(self) -> None:
        company = self.company_var.get().strip()
        role = self.role_var.get().strip()
        date_applied = self.date_var.get().strip()
        status = self.status_var.get().strip()
        notes = self.notes_var.get().strip()

        if not company:
            messagebox.showerror("Validation Error", "Company name is required.")
            return
        if not role:
            messagebox.showerror("Validation Error", "Role title is required.")
            return
        if not date_applied:
            messagebox.showerror("Validation Error", "Date applied is required.")
            return
        try:
            _ = parse_date_iso(date_applied)
        except ValueError:
            messagebox.showerror("Validation Error", "Date must be in YYYY-MM-DD format (e.g., 2026-02-11).")
            return
        if status not in STATUSES:
            messagebox.showerror("Validation Error", "Status must be one of the allowed categories.")
            return

        follow_up_date = calculate_follow_up(date_applied)

        with sqlite3.connect(DB_FILE) as conn:
            if self.app_id is None:
                conn.execute(
                    """
                    INSERT INTO Applications
                    (company_name, role_title, date_applied, status, follow_up_date, notes, archived)
                    VALUES (?, ?, ?, ?, ?, ?, 0);
                    """,
                    (company, role, date_applied, status, follow_up_date, notes),
                )
            else:
                conn.execute(
                    """
                    UPDATE Applications
                    SET company_name = ?, role_title = ?, date_applied = ?, status = ?, follow_up_date = ?, notes = ?
                    WHERE application_id = ?;
                    """,
                    (company, role, date_applied, status, follow_up_date, notes, self.app_id),
                )
            conn.commit()

        self.on_saved_callback()
        self.destroy()


class FollowUpsDueWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Follow-ups Due")
        self.geometry("820x360")

        today = date.today()

        header = ttk.Frame(self)
        header.pack(fill="x", padx=10, pady=10)

        ttk.Label(header, text=f"Today: {today.isoformat()}").pack(side="left")

        ttk.Button(header, text="Close", command=self.destroy).pack(side="right")

        # Table
        columns = ("id", "company", "role", "follow_up", "due_label", "status")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=12)

        self.tree.heading("id", text="ID")
        self.tree.heading("company", text="Company")
        self.tree.heading("role", text="Role")
        self.tree.heading("follow_up", text="Follow-up Date")
        self.tree.heading("due_label", text="Due")
        self.tree.heading("status", text="Status")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("company", width=180)
        self.tree.column("role", width=230)
        self.tree.column("follow_up", width=120, anchor="center")
        self.tree.column("due_label", width=120, anchor="center")
        self.tree.column("status", width=140)

        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Load due rows
        self.load_due_rows(today)

        # Footer
        self.footer_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.footer_var).pack(anchor="w", padx=10, pady=(0, 8))

    def load_due_rows(self, today: date) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.execute(
                """
                SELECT application_id, company_name, role_title, follow_up_date, status
                FROM Applications
                WHERE archived = 0 AND follow_up_date <= ?
                ORDER BY follow_up_date ASC, application_id ASC;
                """,
                (today.isoformat(),),
            )
            rows = cur.fetchall()

        overdue_count = 0
        today_count = 0

        for app_id, company, role, follow_up_date, status in rows:
            try:
                fdate = parse_date_only(follow_up_date)
            except ValueError:
                # If somehow invalid, just label it generically
                label = "Due"
            else:
                if fdate < today:
                    label = "Overdue"
                    overdue_count += 1
                else:
                    label = "Due Today"
                    today_count += 1

            self.tree.insert(
                "",
                "end",
                values=(app_id, company, role, follow_up_date, label, status),
            )

        self.footer_var.set(
            f"Total due: {len(rows)}  |  Overdue: {overdue_count}  |  Due today: {today_count}"
        )


class IATApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Internship Application Tracker")
        self.geometry("1120x560")

        # Top controls row
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Button(top, text="Add", command=self.open_add_window).pack(side="left")
        ttk.Button(top, text="Edit", command=self.edit_selected).pack(side="left", padx=6)
        ttk.Button(top, text="Archive", command=self.archive_selected).pack(side="left", padx=6)
        ttk.Button(top, text="Delete", command=self.delete_selected).pack(side="left", padx=6)

        ttk.Separator(top, orient="vertical").pack(side="left", fill="y", padx=10)

        ttk.Button(top, text="Follow-ups Due", command=self.open_followups_due).pack(side="left")

        ttk.Separator(top, orient="vertical").pack(side="left", fill="y", padx=10)

        ttk.Label(top, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(top, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=6)
        search_entry.bind("<Return>", lambda _e: self.load_rows())

        ttk.Label(top, text="Status:").pack(side="left", padx=(10, 0))
        self.status_filter_var = tk.StringVar(value="All")
        self.status_filter = ttk.Combobox(
            top,
            textvariable=self.status_filter_var,
            values=["All"] + STATUSES,
            state="readonly",
            width=18,
        )
        self.status_filter.pack(side="left", padx=6)
        self.status_filter.bind("<<ComboboxSelected>>", lambda _e: self.load_rows())

        self.show_archived_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            top,
            text="Show Archived",
            variable=self.show_archived_var,
            command=self.load_rows,
        ).pack(side="left", padx=(10, 0))

        ttk.Button(top, text="Clear Filters", command=self.clear_filters).pack(side="left", padx=10)
        ttk.Button(top, text="Refresh", command=self.load_rows).pack(side="left", padx=6)

        # Summary counts
        self.summary_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.summary_var).pack(anchor="w", padx=10, pady=(0, 6))

        # Table (Treeview)
        columns = ("id", "company", "role", "date_applied", "status", "follow_up", "archived")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=18)

        self.tree.heading("id", text="ID")
        self.tree.heading("company", text="Company")
        self.tree.heading("role", text="Role")
        self.tree.heading("date_applied", text="Date Applied")
        self.tree.heading("status", text="Status")
        self.tree.heading("follow_up", text="Follow-up Date")
        self.tree.heading("archived", text="Archived")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("company", width=200)
        self.tree.column("role", width=280)
        self.tree.column("date_applied", width=110, anchor="center")
        self.tree.column("status", width=160)
        self.tree.column("follow_up", width=120, anchor="center")
        self.tree.column("archived", width=90, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tree.bind("<Double-1>", lambda _event: self.edit_selected())

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status_var).pack(anchor="w", padx=10, pady=(0, 8))

        self.load_rows()

    def open_followups_due(self) -> None:
        FollowUpsDueWindow(self)

    def clear_filters(self) -> None:
        self.search_var.set("")
        self.status_filter_var.set("All")
        self.show_archived_var.set(False)
        self.load_rows()

    def open_add_window(self) -> None:
        ApplicationFormWindow(self, on_saved_callback=self.load_rows, app_id=None)

    def get_selected_app_id(self) -> int | None:
        selected = self.tree.selection()
        if not selected:
            return None
        values = self.tree.item(selected[0], "values")
        if not values:
            return None
        try:
            return int(values[0])
        except (ValueError, TypeError):
            return None

    def edit_selected(self) -> None:
        app_id = self.get_selected_app_id()
        if app_id is None:
            messagebox.showinfo("Edit", "Please select an application to edit.")
            return
        ApplicationFormWindow(self, on_saved_callback=self.load_rows, app_id=app_id)

    def archive_selected(self) -> None:
        app_id = self.get_selected_app_id()
        if app_id is None:
            messagebox.showinfo("Archive", "Please select an application to archive.")
            return

        if not messagebox.askyesno("Archive", "Archive the selected application?"):
            return

        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                "UPDATE Applications SET archived = 1, status = 'Archived' WHERE application_id = ?;",
                (app_id,),
            )
            conn.commit()

        self.load_rows()

    def delete_selected(self) -> None:
        app_id = self.get_selected_app_id()
        if app_id is None:
            messagebox.showinfo("Delete", "Please select an application to delete.")
            return

        if not messagebox.askyesno("Delete", "This will permanently delete the selected application. Continue?"):
            return

        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("DELETE FROM Applications WHERE application_id = ?;", (app_id,))
            conn.commit()

        self.load_rows()

    def load_rows(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        search_text = self.search_var.get().strip()
        status_filter = self.status_filter_var.get().strip()
        show_archived = self.show_archived_var.get()

        where = []
        params: list[str] = []

        if not show_archived:
            where.append("archived = 0")

        if status_filter and status_filter != "All":
            where.append("status = ?")
            params.append(status_filter)

        if search_text:
            where.append("(company_name LIKE ? OR role_title LIKE ? OR notes LIKE ?)")
            like = f"%{search_text}%"
            params.extend([like, like, like])

        where_sql = ""
        if where:
            where_sql = "WHERE " + " AND ".join(where)

        query = f"""
            SELECT application_id, company_name, role_title, date_applied, status, follow_up_date, archived
            FROM Applications
            {where_sql}
            ORDER BY application_id DESC;
        """

        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.execute(query, params)
            rows = cur.fetchall()

        for (app_id, company, role, date_applied, status, follow_up_date, archived) in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    app_id,
                    company,
                    role,
                    date_applied,
                    status,
                    follow_up_date,
                    "Yes" if archived else "No",
                ),
            )

        self.status_var.set(f"Loaded {len(rows)} application(s).")
        self.update_summary_counts(show_archived=show_archived)

    def update_summary_counts(self, show_archived: bool) -> None:
        where_sql = "" if show_archived else "WHERE archived = 0"

        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.execute(
                f"""
                SELECT status, COUNT(*)
                FROM Applications
                {where_sql}
                GROUP BY status
                ORDER BY status;
                """
            )
            counts = cur.fetchall()

        if not counts:
            self.summary_var.set("Summary: (no applications)")
            return

        parts = [f"{status}: {count}" for status, count in counts]
        self.summary_var.set("Summary: " + " | ".join(parts))


if __name__ == "__main__":
    init_db()
    app = IATApp()
    app.mainloop()
