# Task Scheduling Web App

A **Flask-based web application** that reads **resource** and **work list** data from an Excel file, displays the **initial state**, and then runs a **task scheduling algorithm** to produce an **optimized assignment**. The scheduling logic considers **leave schedules**, **effort durations**, and skips **weekends** automatically.

---

## **Features**
- 📂 **Upload Excel file** with two sheets:
  - **`resources`** → Resource availability & leave schedules
  - **`tasks`** → Work items with effort estimates
- 📊 **Initial State View** before scheduling
- ⚡ **Run Scheduling** at the click of a button
- 🖥 **AJAX Loading** for smooth user experience
- 📅 **Weekend Skipping** logic built-in
- 🧮 **Effort-based Allocation** with partial availability
- 🧪 **Tester Delay**: Testing starts next business day after development

---

