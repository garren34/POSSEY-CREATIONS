from flask import Flask, request, session, redirect, url_for, send_file, send_from_directory
import sqlite3

app = Flask(__name__)
app.secret_key = 'mysecret123'
users = {'POSSEY': 'Guns4Liberaltears'}

from supabase import create_client, Client
import os

# Load Supabase credentials from environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
def init_db():
    try:
        print("Initializing database...")
        conn = sqlite3.connect('tracker.db')
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS staff (name TEXT UNIQUE)')
        c.execute('CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY, bay INTEGER, job_number TEXT UNIQUE, estimated_time INTEGER, actual_time INTEGER, issues TEXT, archived INTEGER DEFAULT 0)')
        c.execute('CREATE TABLE IF NOT EXISTS job_staff (job_id INTEGER, staff_name TEXT, FOREIGN KEY(job_id) REFERENCES jobs(id))')
        conn.commit()
        conn.close()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

init_db()

# Serve static files (for PC.png and sw.js)
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/manifest.json')
def manifest():
    return send_from_directory('.', 'manifest.json')

@app.route('/')
def home():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('tracker.db')
    c = conn.cursor()
    c.execute('SELECT id, job_number FROM jobs WHERE archived = 0 ORDER BY id')
    jobs = c.fetchall()
    conn.close()
    job_html = ''
    for job in jobs:
        job_html += f'<li><a href="/add_job_details?job_id={job[0]}">{job[1]}</a> ' \
                    f'<form method="POST" action="/archive_job" style="display:inline;">' \
                    f'<input type="hidden" name="job_id" value="{job[0]}">' \
                    f'<input type="submit" value="Archive" class="archive-btn"></form> ' \
                    f'<form method="POST" action="/delete_job" style="display:inline;">' \
                    f'<input type="hidden" name="job_id" value="{job[0]}">' \
                    f'<input type="submit" value="Delete" class="delete-btn"></form></li>'
    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="manifest" href="/manifest.json">
        <script>
          if ('serviceWorker' in navigator) {{
            navigator.serviceWorker.register('/static/sw.js')
              .then(() => console.log('Service Worker registered'));
          }}
        </script>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f0f4f8; padding: 20px; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #34495e; }}
            input[type="text"] {{ padding: 5px; margin: 5px; }}
            input[type="submit"] {{ background-color: #3498db; color: white; padding: 8px; border: none; border-radius: 5px; cursor: pointer; }}
            input[type="submit"]:hover {{ background-color: #2980b9; }}
            .archive-btn {{ background-color: #9b59b6; }}
            .archive-btn:hover {{ background-color: #8e44ad; }}
            .delete-btn {{ background-color: #e74c3c; }}
            .delete-btn:hover {{ background-color: #c0392b; }}
            ul {{ list-style-type: none; padding: 0; }}
            li {{ margin: 5px 0; }}
            .logout {{ position: absolute; top: 20px; right: 20px; }}
            .nav-buttons {{ margin: 10px 0; display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; }}
            .nav-buttons button {{ background-color: #2c3e50; color: white; padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; }}
            .nav-buttons button:hover {{ background-color: #34495e; }}
        </style>
    </head>
    <body>
        <h1>Production Tracker</h1>
        <a href="/logout" class="logout">Logout</a>
        <form method="GET" action="/job_details">
            <input type="text" name="job_number" placeholder="Search Job Number" required>
            <input type="submit" value="Search">
        </form>
        <form method="POST" action="/add_job">
            <input type="text" name="job_number" placeholder="Enter Job Number" required>
            <input type="submit" value="Add Job">
        </form>
        <div class="nav-buttons">
            <button onclick="window.location.href='/staff'">Manage Staff</button>
            <button onclick="window.location.href='/archive'">View Archive</button>
            <button onclick="window.location.href='/job_times'">View Job Times</button>
            <button onclick="window.location.href='/download_db'">Download Database</button>
            <button onclick="window.location.href='/upload_db'">Upload Database</button>
        </div>
        <h2>Active Jobs (Click to Add/Edit Details)</h2>
        <ul>{job_html}</ul>
    </body>
    </html>
    """

@app.route('/staff')
def staff():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('tracker.db')
    c = conn.cursor()
    c.execute('SELECT name FROM staff')
    staff_list = [row[0] for row in c.fetchall()]
    conn.close()
    staff_html = ''
    for staff in staff_list:
        staff_html += f'<li>{staff} ' \
                      f'<form method="POST" action="/delete_staff" style="display:inline;">' \
                      f'<input type="hidden" name="staff_name" value="{staff}">' \
                      f'<input type="submit" value="Remove" class="delete-btn"></form></li>'
    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="manifest" href="/manifest.json">
        <script>
          if ('serviceWorker' in navigator) {{
            navigator.serviceWorker.register('/static/sw.js')
              .then(() => console.log('Service Worker registered'));
          }}
        </script>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f0f4f8; padding: 20px; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #34495e; }}
            input[type="text"] {{ padding: 5px; margin: 5px; }}
            input[type="submit"] {{ background-color: #3498db; color: white; padding: 8px; border: none; border-radius: 5px; cursor: pointer; }}
            input[type="submit"]:hover {{ background-color: #2980b9; }}
            .delete-btn {{ background-color: #e74c3c; }}
            .delete-btn:hover {{ background-color: #c0392b; }}
            ul {{ list-style-type: none; padding: 0; }}
            li {{ margin: 5px 0; }}
            .logout {{ position: absolute; top: 20px; right: 20px; }}
        </style>
    </head>
    <body>
        <h1>Staff Management</h1>
        <a href="/logout" class="logout">Logout</a>
        <a href="/">Back to Jobs</a>
        <form method="POST" action="/add_staff">
            <input type="text" name="staff_name" placeholder="Enter staff name" required>
            <input type="submit" value="Add Staff">
        </form>
        <h2>Staff List</h2>
        <ul>{staff_html}</ul>
    </body>
    </html>
    """

@app.route('/add_job', methods=['POST'])
def add_job():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    job_number = request.form['job_number']
    conn = sqlite3.connect('tracker.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO jobs (job_number) VALUES (?)', (job_number,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Job number already exists, just proceed
    conn.close()
    return redirect(url_for('home'))

@app.route('/add_job_details', methods=['GET', 'POST'])
def add_job_details():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    job_id = request.args.get('job_id')
    conn = sqlite3.connect('tracker.db')
    c = conn.cursor()
    c.execute('SELECT job_number, bay, estimated_time, actual_time, issues FROM jobs WHERE id = ?', (job_id,))
    job = c.fetchone()
    c.execute('SELECT name FROM staff')
    staff_list = [row[0] for row in c.fetchall()]
    c.execute('SELECT staff_name FROM job_staff WHERE job_id = ?', (job_id,))
    current_staff = [row[0] for row in c.fetchall()]
    conn.close()

    if not job:
        return "Job not found. <a href='/'>Back</a>"

    job_number, bay, est_time, act_time, issues = job
    bay = bay or ''
    est_time = est_time or ''
    act_time = act_time or ''
    issues = issues or ''

    staff_options = ''.join(f'<input type="checkbox" name="staff" value="{staff}" {"checked" if staff in current_staff else ""}> {staff}<br>' 
                            for staff in staff_list)

    if request.method == 'POST':
        bay = int(request.form['bay']) if request.form['bay'] else None
        est_time = int(request.form['estimated_time']) if request.form['estimated_time'] else None
        act_time = int(request.form['actual_time']) if request.form['actual_time'] else None
        issues = request.form['issues'] or 'None'
        staff_names = request.form.getlist('staff')

        conn = sqlite3.connect('tracker.db')
        c = conn.cursor()
        c.execute('UPDATE jobs SET bay=?, estimated_time=?, actual_time=?, issues=? WHERE id=?',
                  (bay, est_time, act_time, issues, job_id))
        c.execute('DELETE FROM job_staff WHERE job_id = ?', (job_id,))
        for staff in staff_names:
            c.execute('INSERT INTO job_staff (job_id, staff_name) VALUES (?, ?)', (job_id, staff))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))

    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="manifest" href="/manifest.json">
        <script>
          if ('serviceWorker' in navigator) {{
            navigator.serviceWorker.register('/static/sw.js')
              .then(() => console.log('Service Worker registered'));
          }}
        </script>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f0f4f8; padding: 20px; }}
            h1 {{ color: #2c3e50; }}
            input[type="text"], input[type="number"] {{ padding: 5px; margin: 5px; }}
            input[type="submit"] {{ background-color: #3498db; color: white; padding: 8px; border: none; border-radius: 5px; cursor: pointer; }}
            input[type="submit"]:hover {{ background-color: #2980b9; }}
        </style>
    </head>
    <body>
        <h1>Edit Job #{job_number}</h1>
        <form method="POST">
            <label>Select Staff:</label><br>{staff_options}
            <input type="number" name="bay" value="{bay}" placeholder="Bay (1-10)" min="1" max="10">
            <input type="number" name="estimated_time" value="{est_time}" placeholder="Estimated Time (mins)">
            <input type="number" name="actual_time" value="{act_time}" placeholder="Actual Time (mins)">
            <input type="text" name="issues" value="{issues}" placeholder="Issues (optional)">
            <input type="submit" value="Save Details">
        </form>
        <a href="/">Back</a>
    </body>
    </html>
    """

@app.route('/job_details', methods=['GET'])
def job_details():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    job_number = request.args.get('job_number')
    conn = sqlite3.connect('tracker.db')
    c = conn.cursor()
    c.execute('SELECT id, bay, estimated_time, actual_time, issues, archived FROM jobs WHERE job_number = ?', (job_number,))
    job = c.fetchone()
    if not job:
        return "Job not found. <a href='/'>Back</a>"
    job_id, bay, est_time, act_time, issues, archived = job
    c.execute('SELECT staff_name FROM job_staff WHERE job_id = ?', (job_id,))
    staff_list = [row[0] for row in c.fetchall()]
    conn.close()

    if not staff_list:
        staff_html = "No staff assigned."
    else:
        staff_count = len(staff_list)
        hours_per_staff = act_time / staff_count if staff_count > 0 and act_time else 0
        staff_html = '<ul>'
        for staff in staff_list:
            staff_html += f'<li>{staff}: {hours_per_staff:.2f} mins</li>'
        staff_html += '</ul>'

    time_diff = act_time - est_time if est_time and act_time else 0
    diff_text = f"{time_diff} mins {'over' if time_diff > 0 else 'under'}" if time_diff != 0 else "on time"
    status = "Archived" if archived else "Active"

    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="manifest" href="/manifest.json">
        <script>
          if ('serviceWorker' in navigator) {{
            navigator.serviceWorker.register('/static/sw.js')
              .then(() => console.log('Service Worker registered'));
          }}
        </script>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f0f4f8; padding: 20px; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #34495e; }}
            ul {{ list-style-type: none; padding: 0; }}
            li {{ margin: 5px 0; }}
            .logout {{ position: absolute; top: 20px; right: 20px; }}
        </style>
    </head>
    <body>
        <h1>Job Details: #{job_number}</h1>
        <a href="/logout" class="logout">Logout</a>
        <a href="/">Back to Active Jobs</a>
        <h2>Job Information</h2>
        <p>Bay: {bay or 'Not set'}</p>
        <p>Status: {status}</p>
        <p>Estimated Time: {est_time or 'Not set'} mins</p>
        <p>Actual Time: {act_time or 'Not set'} mins</p>
        <p>Time Difference: {diff_text}</p>
        <p>Issues: {issues or 'None'}</p>
        <h2>Staff</h2>
        {staff_html}
    </body>
    </html>
    """

@app.route('/job_times')
def job_times():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('tracker.db')
    c = conn.cursor()
    c.execute('SELECT id, bay, job_number, estimated_time, actual_time FROM jobs WHERE archived = 0')
    jobs = c.fetchall()
    job_staff = {}
    for job_id in [job[0] for job in jobs]:
        c.execute('SELECT staff_name FROM job_staff WHERE job_id = ?', (job_id,))
        job_staff[job_id] = [row[0] for row in c.fetchall()]
    conn.close()
    job_html = ''
    for job in jobs:
        time_diff = job[4] - job[3] if job[3] and job[4] else 0
        diff_text = f" ({time_diff} mins {'over' if time_diff > 0 else 'under'})" if time_diff != 0 else " (on time)"
        staff_names = ', '.join(job_staff.get(job[0], []))
        job_html += f'<li>Staff: {staff_names} | Bay {job[1] or "Not set"}, Job #{job[2]}, Est. {job[3] or "Not set"} mins, Act. {job[4] or "Not set"} mins{diff_text} ' \
                    f'<form method="POST" action="/delete_job" style="display:inline;">' \
                    f'<input type="hidden" name="job_id" value="{job[0]}">' \
                    f'<input type="submit" value="Delete" class="delete-btn"></form></li>'
    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="manifest" href="/manifest.json">
        <script>
          if ('serviceWorker' in navigator) {{
            navigator.serviceWorker.register('/static/sw.js')
              .then(() => console.log('Service Worker registered'));
          }}
        </script>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f0f4f8; padding: 20px; }}
            h1 {{ color: #2c3e50; }}
            ul {{ list-style-type: none; padding: 0; }}
            li {{ margin: 5px 0; }}
            .logout {{ position: absolute; top: 20px; right: 20px; }}
            .delete-btn {{ background-color: #e74c3c; color: white; padding: 8px; border: none; border-radius: 5px; cursor: pointer; }}
            .delete-btn:hover {{ background-color: #c0392b; }}
        </style>
    </head>
    <body>
        <h1>Job Times</h1>
        <a href="/logout" class="logout">Logout</a>
        <a href="/">Back to Active Jobs</a>
        <ul>{job_html}</ul>
    </body>
    </html>
    """

@app.route('/archive')
def archive():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('tracker.db')
    c = conn.cursor()
    c.execute('SELECT id, bay, job_number, estimated_time, actual_time, issues FROM jobs WHERE archived = 1')
    jobs = c.fetchall()
    job_staff = {}
    for job_id in [job[0] for job in jobs]:
        c.execute('SELECT staff_name FROM job_staff WHERE job_id = ?', (job_id,))
        job_staff[job_id] = [row[0] for row in c.fetchall()]
    conn.close()
    job_html = ''
    for job in jobs:
        time_diff = job[4] - job[3] if job[3] and job[4] else 0
        diff_text = f" ({time_diff} mins {'over' if time_diff > 0 else 'under'})" if time_diff != 0 else " (on time)"
        staff_names = ', '.join(job_staff.get(job[0], []))
        job_html += f'<li>Staff: {staff_names} | Bay {job[1] or "Not set"}, Job #{job[2]}, Est. {job[3] or "Not set"} mins, Act. {job[4] or "Not set"} mins{diff_text}, Issues: {job[5]} ' \
                    f'<form method="POST" action="/delete_job" style="display:inline;">' \
                    f'<input type="hidden" name="job_id" value="{job[0]}">' \
                    f'<input type="submit" value="Delete" class="delete-btn"></form></li>'
    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="manifest" href="/manifest.json">
        <script>
          if ('serviceWorker' in navigator) {{
            navigator.serviceWorker.register('/static/sw.js')
              .then(() => console.log('Service Worker registered'));
          }}
        </script>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f0f4f8; padding: 20px; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #34495e; }}
            input[type="submit"] {{ background-color: #e74c3c; color: white; padding: 8px; border: none; border-radius: 5px; cursor: pointer; }}
            input[type="submit"]:hover {{ background-color: #c0392b; }}
            ul {{ list-style-type: none; padding: 0; }}
            li {{ margin: 5px 0; }}
            .logout {{ position: absolute; top: 20px; right: 20px; }}
        </style>
    </head>
    <body>
        <h1>Archived Jobs</h1>
        <a href="/logout" class="logout">Logout</a>
        <a href="/">Back to Active Jobs</a>
        <ul>{job_html}</ul>
    </body>
    </html>
    """

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['logged_in'] = True
            return redirect(url_for('home'))
        return "Wrong username or password. <a href='/login'>Try again</a>"
    return """
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="manifest" href="/manifest.json">
        <script>
          if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/sw.js')
              .then(() => console.log('Service Worker registered'));
          }
        </script>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f0f4f8; padding: 20px; text-align: center; }}
            input[type="text"], input[type="password"] {{ padding: 5px; margin: 5px; }}
            input[type="submit"] {{ background-color: #3498db; color: white; padding: 8px; border: none; border-radius: 5px; cursor: pointer; }}
            input[type="submit"]:hover {{ background-color: #2980b9; }}
        </style>
    </head>
    <body>
        <h1>Login</h1>
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <input type="submit" value="Login">
        </form>
    </body>
    </html>
    """

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/add_staff', methods=['POST'])
def add_staff():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    name = request.form['staff_name']
    conn = sqlite3.connect('tracker.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO staff (name) VALUES (?)', (name,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()
    return redirect(url_for('staff'))

@app.route('/delete_staff', methods=['POST'])
def delete_staff():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    staff_name = request.form['staff_name']
    conn = sqlite3.connect('tracker.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM job_staff WHERE staff_name = ?', (staff_name,))
    job_count = c.fetchone()[0]
    if job_count == 0:
        c.execute('DELETE FROM staff WHERE name = ?', (staff_name,))
        conn.commit()
    conn.close()
    return redirect(url_for('staff'))

@app.route('/archive_job', methods=['POST'])
def archive_job():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    job_id = request.form['job_id']
    conn = sqlite3.connect('tracker.db')
    c = conn.cursor()
    c.execute('UPDATE jobs SET archived = 1 WHERE id = ?', (job_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/delete_job', methods=['POST'])
def delete_job():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    job_id = request.form['job_id']
    conn = sqlite3.connect('tracker.db')
    c = conn.cursor()
    c.execute('DELETE FROM job_staff WHERE job_id = ?', (job_id,))
    c.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
    conn.commit()
    conn.close()
    referrer = request.referrer or url_for('home')
    if 'job_times' in referrer:
        return redirect(url_for('job_times'))
    elif 'archive' in referrer:
        return redirect(url_for('archive'))
    return redirect(url_for('home'))

# Download database route
@app.route('/download_db')
def download_db():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return send_file('tracker.db', as_attachment=True, download_name='tracker.db')

# Upload database route
@app.route('/upload_db', methods=['GET', 'POST'])
def upload_db():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        file = request.files['db_file']
        if file and file.filename.endswith('.db'):
            file.save('tracker.db')
            return redirect(url_for('home'))
        return "Invalid file. <a href='/upload_db'>Try again</a>"
    return """
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="manifest" href="/manifest.json">
        <script>
          if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/sw.js')
              .then(() => console.log('Service Worker registered'));
          }
        </script>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; text-align: center; }}
            input[type="submit"] {{ background-color: #3498db; color: white; padding: 8px; border: none; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <h1>Upload Database</h1>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="db_file" accept=".db">
            <input type="submit" value="Upload">
        </form>
        <a href="/">Back</a>
    </body>
    </html>
    """

if __name__ == '__main__':
    print("Running Flask app on port 8080")
    app.run(host='0.0.0.0', port=8080)
