import pandas as pd


def read_excel_data(file_path):
    try:
        resources_df = pd.read_excel(file_path, sheet_name="resources")
        work_list_df = pd.read_excel(file_path, sheet_name="tasks")

        # Map Excel headings to expected keys
        resources_df = resources_df.rename(columns={
            "Resource ID": "id",
            "Name": "name",
            "Type": "type",
            "Leave Schedule": "leave_schedule"
        })
        resources_df["leave_schedule"] = resources_df["leave_schedule"].fillna("").apply(
            lambda x: [d.strip() for d in str(x).split(",") if d.strip()]
        )

        work_list_df = work_list_df.rename(columns={
            "Jira ID": "id",
            "Task": "name",
            "Dev Effort": "dev_effort",
            "Tester Effort": "tester_effort",
            "Priority": "priority"
        })

        resources = resources_df.to_dict(orient="records")
        work_items = work_list_df.to_dict(orient="records")

        return resources, work_items
    except Exception as e:
        raise ValueError(f"Error reading Excel: {e}")
