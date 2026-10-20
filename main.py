
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime, timedelta

from database import Database
from services import BookingService


class SmartCampusApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Smart Campus Resource Booking System")
        self.geometry("1100x760")
        self.minsize(900, 620)

        self.database = Database()
        self.service = BookingService(self.database)

        self.current_user = None
        self.active_campus = ""
        self.available_resource_map = {}

        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self.style.configure("Treeview", rowheight=25)
        self.style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
        )

        self.show_login()

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    def show_login(self, email=""):
        self.clear_window()

        container = ttk.Frame(self, padding=30)
        container.pack(expand=True)

        ttk.Label(
            container,
            text="Smart Campus Resource Booking System",
            font=("Segoe UI", 20, "bold"),
            wraplength=650,
            justify="center",
        ).grid(row=0, column=0, columnspan=2, pady=(0, 25))

        ttk.Label(
            container,
            text="Login",
            font=("Segoe UI", 15, "bold"),
        ).grid(row=1, column=0, columnspan=2, pady=(0, 15))

        ttk.Label(container, text="Email address").grid(
            row=2, column=0, sticky="w", padx=8, pady=8
        )

        self.login_email = tk.StringVar(value=email)

        email_entry = ttk.Entry(
            container,
            textvariable=self.login_email,
            width=35,
        )
        email_entry.grid(row=2, column=1, padx=8, pady=8)

        ttk.Label(container, text="Password").grid(
            row=3, column=0, sticky="w", padx=8, pady=8
        )

        self.login_password = tk.StringVar()

        password_entry = ttk.Entry(
            container,
            textvariable=self.login_password,
            show="*",
            width=35,
        )
        password_entry.grid(row=3, column=1, padx=8, pady=8)

        ttk.Button(
            container,
            text="Login",
            command=self.login,
        ).grid(row=4, column=0, columnspan=2, pady=(15, 8))

        ttk.Button(
            container,
            text="Create Lecturer Account",
            command=self.show_registration,
        ).grid(row=5, column=0, columnspan=2, pady=5)

        email_entry.bind(
            "<Return>",
            lambda event: self.login(),
        )

        password_entry.bind(
            "<Return>",
            lambda event: self.login(),
        )

        email_entry.focus_set()

    def show_registration(self):
        self.clear_window()

        container = ttk.Frame(self, padding=30)
        container.pack(expand=True)

        ttk.Label(
            container,
            text="Lecturer Registration",
            font=("Segoe UI", 20, "bold"),
        ).grid(row=0, column=0, columnspan=2, pady=(0, 20))

        self.registration_name = tk.StringVar()
        self.registration_email = tk.StringVar()
        self.registration_password = tk.StringVar()
        self.registration_confirm = tk.StringVar()

        fields = [
            ("Full name", self.registration_name, False),
            ("Email address", self.registration_email, False),
            ("Password", self.registration_password, True),
            ("Confirm password", self.registration_confirm, True),
        ]

        for index, (label, variable, hidden) in enumerate(fields, start=1):
            ttk.Label(
                container,
                text=label,
            ).grid(
                row=index,
                column=0,
                sticky="w",
                padx=8,
                pady=8,
            )

            ttk.Entry(
                container,
                textvariable=variable,
                show="*" if hidden else "",
                width=35,
            ).grid(
                row=index,
                column=1,
                padx=8,
                pady=8,
            )

        ttk.Button(
            container,
            text="Register",
            command=self.register_lecturer,
        ).grid(row=5, column=0, columnspan=2, pady=(15, 8))

        ttk.Button(
            container,
            text="Back to Login",
            command=self.show_login,
        ).grid(row=6, column=0, columnspan=2, pady=5)

    def register_lecturer(self):
        name = self.registration_name.get().strip()
        email = self.registration_email.get().strip()
        password = self.registration_password.get()
        confirmation = self.registration_confirm.get()

        if not name or not email or not password or not confirmation:
            messagebox.showerror(
                "Registration Error",
                "Complete all fields.",
            )
            return

        if password != confirmation:
            messagebox.showerror(
                "Registration Error",
                "The passwords do not match.",
            )
            return

        try:
            self.database.register_lecturer(
                name,
                email,
                password,
            )

            messagebox.showinfo(
                "Registration Successful",
                "Your lecturer account has been created.",
            )

            self.show_login(email)

        except (ValueError, PermissionError) as error:
            messagebox.showerror(
                "Registration Error",
                str(error),
            )

        except Exception as error:
            messagebox.showerror(
                "Error",
                f"Registration failed: {error}",
            )

    def login(self):
        email = self.login_email.get().strip()
        password = self.login_password.get()

        if not email or not password:
            messagebox.showerror(
                "Login Error",
                "Enter your email address and password.",
            )
            return

        user = self.database.authenticate_user(email, password)

        if user is None:
            messagebox.showerror(
                "Login Error",
                "Incorrect email address or password.",
            )
            return

        self.current_user = user
        self.active_campus = ""
        self.show_workspace()

    def logout(self):
        self.current_user = None
        self.active_campus = ""
        self.available_resource_map = {}
        self.show_login()

    def show_workspace(self):
        self.clear_window()

        header = ttk.Frame(self, padding=(15, 12))
        header.pack(fill="x")

        ttk.Label(
            header,
            text="Smart Campus Resource Booking System",
            font=("Segoe UI", 17, "bold"),
        ).pack(side="left")

        ttk.Button(
            header,
            text="Logout",
            command=self.logout,
        ).pack(side="right")

        ttk.Label(
            self,
            text=(
                f"Logged in as: {self.current_user.full_name}  |  "
                f"Role: {self.current_user.role}"
            ),
            padding=(15, 0, 15, 12),
        ).pack(anchor="w")

        campus_frame = ttk.LabelFrame(
            self,
            text="Campus Selection",
            padding=12,
        )
        campus_frame.pack(fill="x", padx=15, pady=5)

        campuses = self.database.get_campuses()
        campus_names = [campus["name"] for campus in campuses]

        if self.current_user.role == "Campus Administrator":
            self.campus_var = tk.StringVar(
                value=self.current_user.campus_name
            )

            campus_choices = [self.current_user.campus_name]

        else:
            self.campus_var = tk.StringVar(value="")
            campus_choices = campus_names

        ttk.Label(
            campus_frame,
            text="Select campus:",
        ).grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.campus_combo = ttk.Combobox(
            campus_frame,
            textvariable=self.campus_var,
            values=campus_choices,
            state="readonly",
            width=30,
        )
        self.campus_combo.grid(
            row=0,
            column=1,
            sticky="w",
            padx=5,
            pady=5,
        )

        ttk.Button(
            campus_frame,
            text="Open Campus",
            command=self.open_selected_campus,
        ).grid(row=0, column=2, padx=12, pady=5)

        self.active_campus_label = ttk.Label(
            campus_frame,
            text="Active campus: None",
            font=("Segoe UI", 10, "bold"),
        )
        self.active_campus_label.grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="w",
            padx=5,
            pady=(10, 3),
        )

        self.policy_label = ttk.Label(
            campus_frame,
            text="Select a campus to view its booking policy.",
            wraplength=950,
        )
        self.policy_label.grid(
            row=2,
            column=0,
            columnspan=3,
            sticky="w",
            padx=5,
            pady=5,
        )

        self.dashboard_frame = ttk.Frame(self, padding=12)
        self.dashboard_frame.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5,
        )

    def open_selected_campus(self):
        campus_name = self.campus_var.get().strip()

        if not campus_name:
            messagebox.showwarning(
                "Campus Selection",
                "Select a campus before continuing.",
            )
            return

        try:
            policy = self.service.get_campus_policy(
                self.current_user,
                campus_name,
            )

            self.active_campus = campus_name

            self.active_campus_label.config(
                text=f"Active campus: {campus_name}"
            )

            self.policy_label.config(
                text=f"Current booking policy: {policy['policy_description']}"
            )

            self.render_dashboard()

        except (ValueError, PermissionError) as error:
            messagebox.showerror(
                "Campus Error",
                str(error),
            )

    def render_dashboard(self):
        for widget in self.dashboard_frame.winfo_children():
            widget.destroy()

        self.notebook = ttk.Notebook(self.dashboard_frame)
        self.notebook.pack(fill="both", expand=True)

        self.build_resources_tab()
        self.build_bookings_tab()

        if self.current_user.role in (
            "Campus Administrator",
            "System Operator",
        ):
            self.build_reports_tab()

        self.refresh_resources()
        self.refresh_bookings()

        if hasattr(self, "report_tree"):
            self.refresh_reports()

    def create_tree(self, parent, columns, widths):
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True, padx=8, pady=8)

        tree = ttk.Treeview(
            container,
            columns=columns,
            show="headings",
            height=12,
        )

        for column, width in zip(columns, widths):
            tree.heading(column, text=column.replace("_", " ").title())
            tree.column(
                column,
                width=width,
                minwidth=70,
                anchor="w",
            )

        vertical_scroll = ttk.Scrollbar(
            container,
            orient="vertical",
            command=tree.yview,
        )

        horizontal_scroll = ttk.Scrollbar(
            container,
            orient="horizontal",
            command=tree.xview,
        )

        tree.configure(
            yscrollcommand=vertical_scroll.set,
            xscrollcommand=horizontal_scroll.set,
        )

        tree.grid(row=0, column=0, sticky="nsew")
        vertical_scroll.grid(row=0, column=1, sticky="ns")
        horizontal_scroll.grid(row=1, column=0, sticky="ew")

        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        return tree

    def build_resources_tab(self):
        tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab, text="Resources")

        buttons = ttk.Frame(tab)
        buttons.pack(fill="x", padx=8, pady=5)

        ttk.Button(
            buttons,
            text="Refresh Resources",
            command=self.refresh_resources,
        ).pack(side="left", padx=4)

        if self.current_user.role == "Campus Administrator":
            ttk.Button(
                buttons,
                text="Add Resource",
                command=lambda: self.open_resource_form("add"),
            ).pack(side="left", padx=4)

            ttk.Button(
                buttons,
                text="Update Selected",
                command=lambda: self.open_resource_form("update"),
            ).pack(side="left", padx=4)

            ttk.Button(
                buttons,
                text="Remove Selected",
                command=self.remove_selected_resource,
            ).pack(side="left", padx=4)

        columns = (
            "resource_code",
            "campus",
            "name",
            "category",
            "description",
        )

        widths = (130, 160, 200, 160, 300)

        self.resource_tree = self.create_tree(
            tab,
            columns,
            widths,
        )

    def refresh_resources(self):
        if not self.active_campus or not hasattr(
            self,
            "resource_tree",
        ):
            return

        try:
            resources = []

            if self.current_user.role == "System Operator":
                for campus in self.database.get_campuses():
                    resources.extend(
                        self.service.get_resources(
                            self.current_user,
                            campus["name"],
                        )
                    )

            else:
                resources = self.service.get_resources(
                    self.current_user,
                    self.active_campus,
                )

            self.resource_tree.delete(
                *self.resource_tree.get_children()
            )

            for resource in resources:
                self.resource_tree.insert(
                    "",
                    "end",
                    values=(
                        resource["resource_code"],
                        resource["campus_name"],
                        resource["name"],
                        resource["category"],
                        resource["description"],
                    ),
                )

        except (ValueError, PermissionError) as error:
            messagebox.showerror(
                "Resource Error",
                str(error),
            )

    def open_resource_form(self, mode):
        selected_values = None

        if mode == "update":
            selection = self.resource_tree.selection()

            if not selection:
                messagebox.showwarning(
                    "Resource Selection",
                    "Select a resource first.",
                )
                return

            selected_values = self.resource_tree.item(
                selection[0],
                "values",
            )

            if selected_values[1] != self.active_campus:
                messagebox.showwarning(
                    "Resource Selection",
                    "Select a resource from the active campus.",
                )
                return

        dialog = tk.Toplevel(self)
        dialog.title(
            "Add Resource" if mode == "add" else "Update Resource"
        )
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        form = ttk.Frame(dialog, padding=18)
        form.pack(fill="both", expand=True)

        initial_values = {
            "Resource Code": selected_values[0] if selected_values else "",
            "Name": selected_values[2] if selected_values else "",
            "Category": selected_values[3] if selected_values else "",
            "Description": selected_values[4] if selected_values else "",
        }

        variables = {}

        for row, (label, initial) in enumerate(
            initial_values.items()
        ):
            ttk.Label(
                form,
                text=label,
            ).grid(
                row=row,
                column=0,
                sticky="w",
                padx=6,
                pady=6,
            )

            variable = tk.StringVar(value=initial)
            variables[label] = variable

            entry = ttk.Entry(
                form,
                textvariable=variable,
                width=35,
            )

            entry.grid(
                row=row,
                column=1,
                padx=6,
                pady=6,
            )

            if mode == "update" and label == "Resource Code":
                entry.configure(state="readonly")

        def save_resource():
            try:
                code = variables["Resource Code"].get()
                name = variables["Name"].get()
                category = variables["Category"].get()
                description = variables["Description"].get()

                if mode == "add":
                    self.service.add_resource(
                        self.current_user,
                        self.active_campus,
                        code,
                        name,
                        category,
                        description,
                    )

                    message = "Resource added successfully."

                else:
                    self.service.update_resource(
                        self.current_user,
                        self.active_campus,
                        code,
                        name,
                        category,
                        description,
                    )

                    message = "Resource updated successfully."

                dialog.destroy()
                self.refresh_resources()

                messagebox.showinfo(
                    "Success",
                    message,
                )

            except (ValueError, PermissionError) as error:
                messagebox.showerror(
                    "Resource Error",
                    str(error),
                    parent=dialog,
                )

            except Exception as error:
                messagebox.showerror(
                    "Error",
                    str(error),
                    parent=dialog,
                )

        ttk.Button(
            form,
            text="Save",
            command=save_resource,
        ).grid(
            row=len(initial_values),
            column=0,
            columnspan=2,
            pady=15,
        )

    def remove_selected_resource(self):
        selection = self.resource_tree.selection()

        if not selection:
            messagebox.showwarning(
                "Resource Selection",
                "Select a resource first.",
            )
            return

        values = self.resource_tree.item(
            selection[0],
            "values",
        )

        resource_code = values[0]
        resource_campus = values[1]

        if resource_campus != self.active_campus:
            messagebox.showwarning(
                "Resource Selection",
                "Select a resource from the active campus.",
            )
            return

        confirmed = messagebox.askyesno(
            "Confirm Removal",
            f"Remove resource {resource_code}?",
        )

        if not confirmed:
            return

        try:
            self.service.remove_resource(
                self.current_user,
                self.active_campus,
                resource_code,
            )

            self.refresh_resources()

            messagebox.showinfo(
                "Success",
                "Resource removed successfully.",
            )

        except (ValueError, PermissionError) as error:
            messagebox.showerror(
                "Resource Error",
                str(error),
            )

    def build_bookings_tab(self):
        tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab, text="Bookings")

        if self.current_user.role == "Lecturer":
            self.build_booking_form(tab)

        controls = ttk.Frame(tab)
        controls.pack(fill="x", padx=8, pady=6)

        ttk.Label(
            controls,
            text="Show:",
        ).pack(side="left", padx=4)

        self.booking_filter_var = tk.StringVar(
            value="All records"
        )

        filter_combo = ttk.Combobox(
            controls,
            textvariable=self.booking_filter_var,
            values=[
                "All records",
                "Active upcoming",
                "Past / cancelled",
            ],
            state="readonly",
            width=20,
        )

        filter_combo.pack(side="left", padx=4)

        filter_combo.bind(
            "<<ComboboxSelected>>",
            lambda event: self.refresh_bookings(),
        )

        ttk.Button(
            controls,
            text="Refresh Bookings",
            command=self.refresh_bookings,
        ).pack(side="left", padx=5)

        if self.current_user.role == "Lecturer":
            ttk.Button(
                controls,
                text="Cancel Selected Booking",
                command=self.cancel_selected_booking,
            ).pack(side="left", padx=5)

        columns = (
            "booking_id",
            "campus",
            "date",
            "start_time",
            "duration",
            "resource",
            "lecturer",
            "status",
        )

        widths = (90, 150, 110, 100, 90, 210, 180, 100)

        self.booking_tree = self.create_tree(
            tab,
            columns,
            widths,
        )

    def build_booking_form(self, parent):
        form = ttk.LabelFrame(
            parent,
            text="Create a Booking",
            padding=10,
        )
        form.pack(fill="x", padx=8, pady=8)

        self.booking_date_var = tk.StringVar(
            value=(date.today() + timedelta(days=1)).isoformat()
        )

        self.booking_time_var = tk.StringVar(
            value="09:00"
        )

        self.booking_duration_var = tk.StringVar(
            value="1"
        )

        self.booking_resource_var = tk.StringVar()

        ttk.Label(
            form,
            text="Booking Date (YYYY-MM-DD)",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=5,
            pady=4,
        )

        ttk.Label(
            form,
            text="Start Time (HH:MM)",
        ).grid(
            row=0,
            column=1,
            sticky="w",
            padx=5,
            pady=4,
        )

        ttk.Label(
            form,
            text="Duration (hours)",
        ).grid(
            row=0,
            column=2,
            sticky="w",
            padx=5,
            pady=4,
        )

        ttk.Label(
            form,
            text="Available Resource",
        ).grid(
            row=0,
            column=3,
            sticky="w",
            padx=5,
            pady=4,
        )

        ttk.Entry(
            form,
            textvariable=self.booking_date_var,
            width=20,
        ).grid(
            row=1,
            column=0,
            sticky="ew",
            padx=5,
            pady=4,
        )

        ttk.Entry(
            form,
            textvariable=self.booking_time_var,
            width=15,
        ).grid(
            row=1,
            column=1,
            sticky="ew",
            padx=5,
            pady=4,
        )

        ttk.Entry(
            form,
            textvariable=self.booking_duration_var,
            width=15,
        ).grid(
            row=1,
            column=2,
            sticky="ew",
            padx=5,
            pady=4,
        )

        self.booking_resource_combo = ttk.Combobox(
            form,
            textvariable=self.booking_resource_var,
            state="readonly",
            width=30,
        )

        self.booking_resource_combo.grid(
            row=1,
            column=3,
            sticky="ew",
            padx=5,
            pady=4,
        )

        ttk.Button(
            form,
            text="Check Availability",
            command=self.check_availability,
        ).grid(
            row=2,
            column=0,
            padx=5,
            pady=8,
            sticky="w",
        )

        ttk.Button(
            form,
            text="Book Selected Resource",
            command=self.submit_booking,
        ).grid(
            row=2,
            column=1,
            padx=5,
            pady=8,
            sticky="w",
        )

        self.availability_label = ttk.Label(
            form,
            text="Check availability before booking.",
        )

        self.availability_label.grid(
            row=2,
            column=2,
            columnspan=2,
            padx=5,
            pady=8,
            sticky="w",
        )

        for column in range(4):
            form.columnconfigure(column, weight=1)

    def check_availability(self):
        if not self.active_campus:
            messagebox.showwarning(
                "Campus Selection",
                "Select a campus first.",
            )
            return

        try:
            booking_date = self.booking_date_var.get().strip()
            start_time = self.booking_time_var.get().strip()
            duration = self.service.validate_booking(
                self.active_campus,
                booking_date,
                start_time,
                self.booking_duration_var.get(),
            )

            requested_start = datetime.strptime(
                f"{booking_date} {start_time}",
                "%Y-%m-%d %H:%M",
            )

            requested_end = requested_start + timedelta(
                hours=duration
            )

            existing_bookings = self.database.get_bookings(
                campus_name=self.active_campus,
                status="active",
            )

            busy_codes = set()

            for booking in existing_bookings:
                if booking["booking_date"] != booking_date:
                    continue

                existing_start = datetime.strptime(
                    f"{booking['booking_date']} "
                    f"{booking['start_time']}",
                    "%Y-%m-%d %H:%M",
                )

                existing_end = existing_start + timedelta(
                    hours=float(booking["duration_hours"])
                )

                if (
                    requested_start < existing_end
                    and existing_start < requested_end
                ):
                    busy_codes.add(booking["resource_code"])

            resources = self.service.get_resources(
                self.current_user,
                self.active_campus,
            )

            available = [
                resource
                for resource in resources
                if resource["resource_code"] not in busy_codes
            ]

            self.available_resource_map = {
                f"{resource['resource_code']} - {resource['name']}":
                    resource["resource_code"]
                for resource in available
            }

            options = list(self.available_resource_map.keys())

            self.booking_resource_combo.configure(
                values=options
            )

            self.booking_resource_var.set(
                options[0] if options else ""
            )

            self.availability_label.config(
                text=f"{len(available)} resource(s) available."
            )

            if not available:
                messagebox.showinfo(
                    "Availability",
                    "No resources are available for that time.",
                )

        except (ValueError, PermissionError) as error:
            messagebox.showerror(
                "Availability Error",
                str(error),
            )

        except Exception as error:
            messagebox.showerror(
                "Error",
                str(error),
            )

    def submit_booking(self):
        selection = self.booking_resource_var.get()

        if not selection or selection not in self.available_resource_map:
            messagebox.showwarning(
                "Booking",
                "Check availability and select a resource first.",
            )
            return

        resource_code = self.available_resource_map[selection]

        try:
            booking_id = self.service.create_booking(
                self.current_user,
                self.active_campus,
                resource_code,
                self.booking_date_var.get().strip(),
                self.booking_time_var.get().strip(),
                self.booking_duration_var.get().strip(),
            )

            messagebox.showinfo(
                "Booking Successful",
                f"Your booking was created. Booking ID: {booking_id}",
            )

            self.refresh_bookings()
            self.check_availability()

        except (ValueError, PermissionError) as error:
            messagebox.showerror(
                "Booking Error",
                str(error),
            )

        except Exception as error:
            messagebox.showerror(
                "Error",
                str(error),
            )

    def display_booking_status(self, booking):
        if booking["status"] == "cancelled":
            return "Cancelled"

        if booking["status"] == "completed":
            return "Completed"

        start = datetime.strptime(
            f"{booking['booking_date']} {booking['start_time']}",
            "%Y-%m-%d %H:%M",
        )

        end = start + timedelta(
            hours=float(booking["duration_hours"])
        )

        if end <= datetime.now():
            return "Past"

        return "Active"

    def refresh_bookings(self):
        if not hasattr(self, "booking_tree"):
            return

        try:
            bookings = self.service.get_bookings(
                self.current_user
            )

            self.booking_tree.delete(
                *self.booking_tree.get_children()
            )

            selected_filter = self.booking_filter_var.get()

            for booking in bookings:
                display_status = self.display_booking_status(
                    booking
                )

                if (
                    selected_filter == "Active upcoming"
                    and display_status != "Active"
                ):
                    continue

                if (
                    selected_filter == "Past / cancelled"
                    and display_status not in (
                        "Past",
                        "Cancelled",
                        "Completed",
                    )
                ):
                    continue

                self.booking_tree.insert(
                    "",
                    "end",
                    values=(
                        booking["booking_id"],
                        booking["campus_name"],
                        booking["booking_date"],
                        booking["start_time"],
                        f"{float(booking['duration_hours']):g} h",
                        (
                            f"{booking['resource_code']} - "
                            f"{booking['resource_name']}"
                        ),
                        booking["lecturer_name"],
                        display_status,
                    ),
                )

        except (ValueError, PermissionError) as error:
            messagebox.showerror(
                "Booking Error",
                str(error),
            )

    def cancel_selected_booking(self):
        selection = self.booking_tree.selection()

        if not selection:
            messagebox.showwarning(
                "Booking Selection",
                "Select a booking first.",
            )
            return

        values = self.booking_tree.item(
            selection[0],
            "values",
        )

        booking_id = int(values[0])

        if values[7] != "Active":
            messagebox.showwarning(
                "Booking Selection",
                "Select an active booking to cancel.",
            )
            return

        confirmed = messagebox.askyesno(
            "Confirm Cancellation",
            f"Cancel booking {booking_id}?",
        )

        if not confirmed:
            return

        try:
            self.service.cancel_booking(
                self.current_user,
                booking_id,
            )

            self.refresh_bookings()

            messagebox.showinfo(
                "Cancellation Successful",
                "The booking has been cancelled.",
            )

        except (ValueError, PermissionError) as error:
            messagebox.showerror(
                "Cancellation Error",
                str(error),
            )

    def build_reports_tab(self):
        tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab, text="Reports")

        ttk.Button(
            tab,
            text="Generate Report",
            command=self.refresh_reports,
        ).pack(
            anchor="w",
            padx=8,
            pady=8,
        )

        columns = (
            "campus",
            "total_bookings",
            "average_duration",
            "most_used_resource",
            "max_duration",
            "booking_hours",
            "days_ahead",
        )

        widths = (160, 110, 120, 230, 110, 140, 100)

        self.report_tree = self.create_tree(
            tab,
            columns,
            widths,
        )

    def refresh_reports(self):
        if not hasattr(self, "report_tree"):
            return

        try:
            if self.current_user.role == "System Operator":
                reports = self.service.get_cross_campus_report(
                    self.current_user
                )
            else:
                reports = [
                    self.service.get_campus_report(
                        self.current_user,
                        self.active_campus,
                    )
                ]

            self.report_tree.delete(
                *self.report_tree.get_children()
            )

            for report in reports:
                resources = report["most_used_resources"]

                if (
                    report["total_bookings"] > 0
                    and resources
                    and resources[0]["usage_count"] > 0
                ):
                    most_used = (
                        f"{resources[0]['resource_name']} "
                        f"({resources[0]['usage_count']})"
                    )
                else:
                    most_used = "No usage yet"

                policy = report["policy"]

                self.report_tree.insert(
                    "",
                    "end",
                    values=(
                        report["campus_name"],
                        report["total_bookings"],
                        (
                            f"{report['average_duration_hours']:.2f} h"
                        ),
                        most_used,
                        f"{policy['max_duration_hours']} h",
                        (
                            f"{policy['opening_time']} - "
                            f"{policy['closing_time']}"
                        ),
                        f"{policy['max_days_ahead']} days",
                    ),
                )

        except (ValueError, PermissionError) as error:
            messagebox.showerror(
                "Report Error",
                str(error),
            )

        except Exception as error:
            messagebox.showerror(
                "Error",
                str(error),
            )

if __name__ == "__main__":
    app = SmartCampusApp()
    app.mainloop()