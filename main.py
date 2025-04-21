from flask import Flask, request, session, redirect, url_for, send_from_directory
from supabase import create_client, Client
import os

app = Flask(__name__)
app.secret_key = 'mysecret123'
users = {'POSSEY': 'Guns4Liberaltears'}

# Load Supabase credentials from environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
    
    # Fetch active jobs with bay and part_type
    response = supabase.table('jobs').select('id', 'job_number', 'bay', 'part_type').eq('archived', 0).order('job_number').execute()
    jobs = response.data
    
    # Group jobs by bay (1 to 10)
    bay_jobs = {i: [] for i in range(1, 11)}  # Initialize all 10 bays
    for job in jobs:
        bay = job['bay'] if job['bay'] is not None else None
        if bay in bay_jobs:
            bay_jobs[bay].append(job)
    
    # Generate HTML for each bay
    bay_html = ''
    for bay in range(1, 11):
        jobs_in_bay = bay_jobs[bay]
        if not jobs_in_bay:
            bay_html += f'<h3>Bay {bay}</h3><ul><li>No jobs</li></ul>'
        else:
            job_list = ''
            for job in jobs_in_bay:
                part_type_display = job['part_type'] if job['part_type'] else "Part Type N/A"
                job_list += (
                    f'<li><a href="/add_job_details?job_id={job["id"]}">{job["job_number"]} - {part_type_display}</a> '
                    f'<form method="POST" action="/archive_job" style="display:inline;">'
                    f'<input type="hidden" name="job_id" value="{job["id"]}">'
                    f'<input type="submit" value="Archive" class="archive-btn"></form> '
                    f'<form method="POST" action="/delete_job" style="display:inline;">'
                    f'<input type="hidden" name="job_id" value="{job["id"]}">'
                    f'<input type="submit" value="Delete" class="delete-btn"></form></li>'
                )
            bay_html += f'<h3>Bay {bay}</h3><ul>{job_list}</ul>'
    
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
            h3 {{ color: #2c3e50; margin-top: 20px; }}
            input[type="text"] {{ padding: 5px; margin: 5px; }}
            input[type="submit"] {{ background-color: #3498db; color: white; padding: 8px; border: none; border-radius: 5px; cursor: pointer; }}
            input[type="submit"]:hover {{ background-color: #2980b9; }}
            .archive-btn {{ background-color: #9b59b6; }}
            .archive-btn:hover {{ background-color: #8e44ad; }}
            .delete-btn {{ background-color: #e74c3c; }}
            .delete-btn:hover {{ background-color: #c0392b; }}
            ul {{ list-style-type: none; padding-left: 20px; }}
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
        </div>
        <h2>Active Jobs by Bay</h2>
        {bay_html}
    </body>
    </html>
    """

@app.route('/staff')
def staff():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    # Fetch staff list from Supabase
    response = supabase.table('staff').select('name').execute()
    staff_list = [staff['name'] for staff in response.data]
    
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

@app.route('/add_staff', methods=['POST'])
def add_staff():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    name = request.form['staff_name']
    
    try:
        # Insert new staff into Supabase
        supabase.table('staff').insert({'name': name}).execute()
    except Exception as e:
        # Handle duplicate staff name error
        if 'duplicate key' in str(e):
            pass  # Staff name exists, proceed silently
        else:
            raise e
    
    return redirect(url_for('staff'))

@app.route('/delete_staff', methods=['POST'])
def delete_staff():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    staff_name = request.form['staff_name']
    
    try:
        # Delete staff's job assignments
        supabase.table('job_staff').delete().eq('staff_name', staff_name).execute()
        # Delete staff from Supabase
        supabase.table('staff').delete().eq('name', staff_name).execute()
    except Exception as e:
        return f"Error deleting staff: {str(e)}. <a href='/staff'>Back</a>"
    
    return redirect(url_for('staff'))

@app.route('/add_job', methods=['POST'])
def add_job():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    job_number = request.form['job_number']
    
    try:
        # Insert new job with archived explicitly set to 0
        supabase.table('jobs').insert({'job_number': job_number, 'archived': 0}).execute()
    except Exception as e:
        # Handle duplicate job_number error
        if 'duplicate key' in str(e):
            pass  # Job number exists, proceed silently
        else:
            raise e
    
    return redirect(url_for('home'))

@app.route('/add_job_details', methods=['GET', 'POST'])
def add_job_details():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    job_id = request.args.get('job_id')
    
    # Fetch job details from Supabase
    job_response = supabase.table('jobs').select('job_number', 'bay', 'estimated_time', 'actual_time', 'diameter', 'part_type').eq('id', job_id).execute()
    job = job_response.data[0] if job_response.data else None
    
    # Fetch all staff
    staff_response = supabase.table('staff').select('name').execute()
    staff_list = [staff['name'] for staff in staff_response.data]
    
    # Fetch current staff for this job
    current_staff_response = supabase.table('job_staff').select('staff_name').eq('job_id', job_id).execute()
    current_staff = [staff['staff_name'] for staff in current_staff_response.data]
    
    # Fetch issues for this job
    issues_response = supabase.table('job_issues').select('issue').eq('job_id', job_id).execute()
    issues = '\n'.join([issue['issue'] for issue in issues_response.data])
    
    if not job:
        return "Job not found. <a href='/'>Back</a>"
    
    job_number = job['job_number']
    bay = job['bay'] or ''
    est_time = job['estimated_time'] or ''
    act_time = job['actual_time'] or ''
    diameter = job['diameter'] or ''
    part_type = job['part_type'] or ''
    
    staff_options = ''.join(f'<input type="checkbox" name="staff" value="{staff}" {"checked" if staff in current_staff else ""}> {staff}<br>' 
                            for staff in staff_list)
    
    if request.method == 'POST':
        bay = int(request.form['bay']) if request.form['bay'] else None
        est_time = float(request.form['estimated_time']) if request.form['estimated_time'] else None
        act_time = float(request.form['actual_time']) if request.form['actual_time'] else None
        diameter = float(request.form['diameter']) if request.form['diameter'] else None
        # Enforce diameter range: 1 to 14 feet
        if diameter is not None and (diameter < 1 or diameter > 14):
            return f"Diameter must be between 1 and 14 feet. <a href='/add_job_details?job_id={job_id}'>Try again</a>"
        part_type = request.form['part_type'] or None
        issues_input = request.form['issues']
        issues_list = [issue.strip() for issue in issues_input.split('\n') if issue.strip()]
        
        # Update job details in Supabase
        supabase.table('jobs').update({
            'bay': bay,
            'estimated_time': est_time,
            'actual_time': act_time,
            'diameter': diameter,
            'part_type': part_type
        }).eq('id', job_id).execute()
        
        # Delete existing staff assignments
        supabase.table('job_staff').delete().eq('job_id', job_id).execute()
        
        # Insert new staff assignments
        for staff in request.form.getlist('staff'):
            supabase.table('job_staff').insert({'job_id': job_id, 'staff_name': staff}).execute()
        
        # Delete existing issues
        supabase.table('job_issues').delete().eq('job_id', job_id).execute()
        
        # Insert new issues
        for issue in issues_list:
            supabase.table('job_issues').insert({'job_id': job_id, 'issue': issue}).execute()
        
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
            input[type="text"], input[type="number"], textarea {{ padding: 5px; margin: 5px; }}
            input[type="submit"] {{ background-color: #3498db; color: white; padding: 8px; border: none; border-radius: 5px; cursor: pointer; }}
            input[type="submit"]:hover {{ background-color: #2980b9; }}
            textarea {{ width: 300px; height: 100px; }}
        </style>
    </head>
    <body>
        <h1>Edit Job #{job_number}</h1>
        <form method="POST">
            <label>Select Staff:</label><br>{staff_options}
            <input type="number" name="bay" value="{bay}" placeholder="Bay (1-10)" min="1" max="10">
            <input type="number" name="diameter" value="{diameter}" placeholder="Diameter (1-14 feet)" step="0.5" min="1" max="14">
            <input type="text" name="part_type" value="{part_type}" placeholder="Part Type">
            <input type="number" name="estimated_time" value="{est_time}" placeholder="Estimated Time (hours)" step="0.01">
            <input type="number" name="actual_time" value="{act_time}" placeholder="Actual Time (hours)" step="0.01">
            <textarea name="issues" placeholder="Enter issues, one per line">{issues}</textarea>
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
    
    # Fetch job details from Supabase
    job_response = supabase.table('jobs').select('*').eq('job_number', job_number).execute()
    job = job_response.data[0] if job_response.data else None
    
    if not job:
        return "Job not found. <a href='/'>Back</a>"
    
    job_id = job['id']
    bay = job['bay']
    est_time = job['estimated_time']
    act_time = job['actual_time']
    archived = job['archived']
    diameter = job['diameter']
    part_type = job['part_type']
    
    # Fetch staff for this job
    staff_response = supabase.table('job_staff').select('staff_name').eq('job_id', job_id).execute()
    staff_list = [staff['staff_name'] for staff in staff_response.data]
    
    # Fetch issues for this job
    issues_response = supabase.table('job_issues').select('issue').eq('job_id', job_id).execute()
    issues_list = [issue['issue'] for issue in issues_response.data]
    
    if not staff_list:
        staff_html = "No staff assigned."
    else:
        staff_count = len(staff_list)
        hours_per_staff = act_time / staff_count if staff_count > 0 and act_time else 0
        staff_html = '<ul>'
        for staff in staff_list:
            staff_html += f'<li>{staff}: {hours_per_staff:.2f} hours</li>'
        staff_html += '</ul>'
    
    time_diff = act_time - est_time if est_time and act_time else 0
    diff_text = f"{time_diff} hours {'over' if time_diff > 0 else 'under'}" if time_diff != 0 else "on time"
    status = "Archived" if archived else "Active"
    
    issues_html = '<ul>' + ''.join(f'<li>{issue}</li>' for issue in issues_list) + '</ul>' if issues_list else 'No issues'
    
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
        <p>Diameter: {diameter or 'Not set'} feet</p>
        <p>Part Type: {part_type or 'Not set'}</p>
        <p>Estimated Time: {est_time or 'Not set'} hours</p>
        <p>Actual Time: {act_time or 'Not set'} hours</p>
        <p>Time Difference: {diff_text}</p>
        <h2>Issues</h2>
        {issues_html}
        <h2>Staff</h2>
        {staff_html}
    </body>
    </html>
    """

@app.route('/job_times')
def job_times():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    # Fetch active jobs from Supabase
    jobs_response = supabase.table('jobs').select('id', 'bay', 'job_number', 'estimated_time', 'actual_time', 'part_type', 'diameter').eq('archived', 0).execute()
    jobs = jobs_response.data
    
    job_staff = {}
    for job in jobs:
        staff_response = supabase.table('job_staff').select('staff_name').eq('job_id', job['id']).execute()
        job_staff[job['id']] = [staff['staff_name'] for staff in staff_response.data]
    
    job_html = ''
    for job in jobs:
        time_diff = job['actual_time'] - job['estimated_time'] if job['estimated_time'] and job['actual_time'] else 0
        diff_text = f" ({time_diff} hours {'over' if time_diff > 0 else 'under'})" if time_diff != 0 else " (on time)"
        staff_names = ', '.join(job_staff.get(job['id'], []))
        job_html += f'<li>Staff: {staff_names} | Bay {job["bay"] or "Not set"}, Job #{job["job_number"]}, Part Type: {job["part_type"] or "Not set"}, Diameter: {job["diameter"] or "Not set"} feet, Est. {job["estimated_time"] or "Not set"} hours, Act. {job["actual_time"] or "Not set"} hours{diff_text} ' \
                    f'<form method="POST" action="/delete_job" style="display:inline;">' \
                    f'<input type="hidden" name="job_id" value="{job["id"]}">' \
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
    
    # Fetch archived jobs from Supabase
    jobs_response = supabase.table('jobs').select('id', 'bay', 'job_number', 'estimated_time', 'actual_time', 'part_type', 'diameter').eq('archived', 1).execute()
    jobs = jobs_response.data
    
    job_staff = {}
    for job in jobs:
        staff_response = supabase.table('job_staff').select('staff_name').eq('job_id', job['id']).execute()
        job_staff[job['id']] = [staff['staff_name'] for staff in staff_response.data]
    
    job_html = ''
    for job in jobs:
        time_diff = job['actual_time'] - job['estimated_time'] if job['estimated_time'] and job['actual_time'] else 0
        diff_text = f" ({time_diff} hours {'over' if time_diff > 0 else 'under'})" if time_diff != 0 else " (on time)"
        staff_names = ', '.join(job_staff.get(job['id'], []))
        job_html += f'<li>Staff: {staff_names} | Bay {job["bay"] or "Not set"}, Job #{job["job_number"]}, Part Type: {job["part_type"] or "Not set"}, Diameter: {job["diameter"] or "Not set"} feet, Est. {job["estimated_time"] or "Not set"} hours, Act. {job["actual_time"] or "Not set"} hours{diff_text} ' \
                    f'<form method="POST" action="/delete_job" style="display:inline;">' \
                    f'<input type="hidden" name="job_id" value="{job["id"]}">' \
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

@app.route('/archive_job', methods=['POST'])
def archive_job():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    job_id = request.form['job_id']
    
    # Archive job in Supabase
    supabase.table('jobs').update({'archived': 1}).eq('id', job_id).execute()
    
    return redirect(url_for('home'))

@app.route('/delete_job', methods=['POST'])
def delete_job():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    job_id = request.form['job_id']
    
    try:
        # Delete job staff assignments first
        supabase.table('job_staff').delete().eq('job_id', job_id).execute()
        
        # Delete job from Supabase (issues will be deleted automatically due to ON DELETE CASCADE)
        supabase.table('jobs').delete().eq('id', job_id).execute()
    except Exception as e:
        return f"Error deleting job: {str(e)}. <a href='/'>Back</a>"
    
    referrer = request.referrer or url_for('home')
    if 'job_times' in referrer:
        return redirect(url_for('job_times'))
    elif 'archive' in referrer:
        return redirect(url_for('archive'))
    return redirect(url_for('home'))

if __name__ == '__main__':
    print("Running Flask app on port 8080")
    app.run(host='0.0.0.0', port=8080)
