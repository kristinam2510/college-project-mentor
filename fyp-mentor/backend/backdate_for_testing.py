"""
Test helper: backdates a project's created_at so you can verify the
/replan endpoint actually redistributes overdue tasks, without waiting
for real time to pass.

Usage:
    python backdate_for_testing.py <project_id> <days_ago>

Example (simulate being 75 days into the project, so month 1 and 2 tasks
that aren't done will show as overdue if duration allows):
    python backdate_for_testing.py 82fa4b32-4eb9-44f4-9ad7-e641ca9270f8 75

Run this from inside backend/ with the venv activated.
"""
import sys
import datetime
from db import SessionLocal, Project

def main():
    if len(sys.argv) != 3:
        print("Usage: python backdate_for_testing.py <project_id> <days_ago>")
        sys.exit(1)

    project_id = sys.argv[1]
    days_ago = int(sys.argv[2])

    db = SessionLocal()
    project = db.get(Project, project_id)
    if not project:
        print(f"No project found with id {project_id}")
        sys.exit(1)

    old_created_at = project.created_at
    new_created_at = datetime.datetime.utcnow() - datetime.timedelta(days=days_ago)
    project.created_at = new_created_at
    db.commit()

    print(f"Project '{project.title}' created_at updated:")
    print(f"  old: {old_created_at}")
    print(f"  new: {new_created_at}  ({days_ago} days ago)")
    print("\nNow call POST /projects/{}/replan to test.".format(project_id))

if __name__ == "__main__":
    main()