import os
import cv2
import numpy as np
import base64
import csv
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, send_file, redirect, url_for, session, flash
from insightface.app import FaceAnalysis
from data import init_db, save_staff_face, save_staff_face, get_known_faces, save_daily_attendance, DB_PATH

app = Flask(__name__)
app.secret_key = '65de29cb8a5bf78e89e9bb840287cb60bf01e312b87eef590ada2aadc3fe4826'  # Required for session to work!


# --- PATH LOGIC ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
BASE_DB_PATH = os.path.join(BASE_DIR, "database", "department_data")

if not os.path.exists(BASE_DB_PATH):
    os.makedirs(BASE_DB_PATH, exist_ok=True)

# --- AI INITIALIZATION ---
face_app = FaceAnalysis(name='buffalo_s', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
face_app.prepare(ctx_id=0, det_size=(640, 640)) 

@app.route('/')
def index():
    return render_template('index.html')

# --- 1. ENROLLMENT (UPDATED TO USE SQLITE) ---
@app.route('/enroll_capture', methods=['POST'])
def enroll_capture():
    try:
        data = request.json
        staff_id = data.get('staff_id')
        department_section = data.get('department_section')
        image_data = data.get('image').split(',')[1]

        img_bytes = base64.decodebytes(image_data.encode())
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        faces = face_app.get(rgb_img)
        if not faces:
            return jsonify({"success": False, "error": "AI could not see your face."})

        # Keep saving the image for your records
        user_dir = os.path.join(BASE_DB_PATH, department_section, staff_id)
        os.makedirs(user_dir, exist_ok=True)
        cv2.imwrite(os.path.join(user_dir, "enrolled_face.jpg"), img)
        
        # Save to Database instead of Pickle
        embedding = faces[0].normed_embedding
        success = save_staff_face(staff_id, department_section, embedding)

        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Database error"})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# --- 2. PHOTO PROCESSING (UPDATED TO USE SQLITE) ---
@app.route('/process_photo', methods=['POST'])
def process_photo():
    try:
        department_section = request.form.get('department_section')
        file = request.files['class_photo']
        
        # Pull faces from Database
        known_faces = get_known_faces(department_section)
        if not known_faces:
            return jsonify({"error": "No staff enrolled in this department"}), 404

        img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
        h, w, _ = img.shape
        img = cv2.convertScaleAbs(img, alpha=1.1, beta=10)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Your original Tiling Logic
        h_step, w_step, overlap = h // 2, w // 3, 150 
        tiles = []
        for i in range(2):
            for j in range(3):
                y1, y2 = max(0, i * h_step - overlap), min(h, (i + 1) * h_step + overlap)
                x1, x2 = max(0, j * w_step - overlap), min(w, (j + 1) * w_step + overlap)
                tiles.append(rgb_img[y1:y2, x1:x2])

        present = set()
        face_app.prepare(ctx_id=0, det_size=(640, 640)) 

        for tile in tiles:
            if tile.size == 0: continue
            detected_faces = face_app.get(tile)
            for face in detected_faces:
                if face.det_score < 0.10: continue 
                
                best_score, best_roll = -1, None
                for roll, known_vec in known_faces.items():
                    score = np.dot(face.normed_embedding, known_vec)
                    if score > best_score:
                        best_score, best_roll = score, roll
                
                if best_score > 0.23:
                    present.add(best_roll)

        absent = list(set(known_faces.keys()) - present)

        return jsonify({
            "present_count": len(present),
            "present_list": sorted(list(present)),
            "absent_count": len(absent),
            "absent_list": sorted(absent),
            "message": f"Detected {len(present)} staff"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- 3. VIDEO PROCESSING (UPDATED TO USE SQLITE) ---
@app.route('/process_video', methods=['POST'])
def process_video():
    try:
        department_section = request.form.get('department_section')
        video_file = request.files['class_video']
        temp_path = "temp_video.mp4"
        video_file.save(temp_path)
        
        known_faces = get_known_faces(department_section)
        if not known_faces: return jsonify({"error": "DB empty"}), 404
            
        cap = cv2.VideoCapture(temp_path)
        present = set()
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            if count % int(fps) == 0: 
                small_rgb = cv2.cvtColor(cv2.resize(frame, (640, 480)), cv2.COLOR_BGR2RGB)
                faces = face_app.get(small_rgb)
                for face in faces:
                    for roll, known_vec in known_faces.items():
                        if np.dot(face.normed_embedding, known_vec) > 0.38:
                            present.add(roll)
            count += 1
            
        cap.release()
        if os.path.exists(temp_path): os.remove(temp_path)
        absent = list(set(known_faces.keys()) - present)
        
        return jsonify({
            "present_count": len(present), "present_list": sorted(list(present)), 
            "absent_count": len(absent), "absent_list": sorted(absent)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- 4. EXPORT ATTENDANCE ---
@app.route('/export_attendance', methods=['POST'])
def export_attendance():
    try:
        data = request.json
        department_section = data.get('department_section', 'Class_Report')
        present_list = data.get('present_list', [])
        absent_list = data.get('absent_list', [])
        
        # --- NEW: SAVE TO DATABASE HISTORY ---
        save_daily_attendance(present_list, absent_list, department_section)
        # -------------------------------------

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Attendance_{department_section}_{timestamp}.csv"
        filepath = os.path.join(BASE_DIR, filename)

        with open(filepath, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Smart Attendance Report"])
            writer.writerow(["department/Section", department_section])
            writer.writerow(["Date & Time", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow([])
            writer.writerow(["Staff ID", "Status"])
            for roll in present_list: writer.writerow([roll, "PRESENT"])
            for roll in absent_list: writer.writerow([roll, "ABSENT"])

        return send_file(filepath, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
#=========== LIVE SESSION LOGIC (UPDATED TO USE SQLITE) ============

#=========== REFINED LIVE SESSION LOGIC ============

# Global to track attendance during the session
active_session = {"present": set(), "is_running": False}

@app.route('/start_live_session/<bs>')
def start_live_session(bs):
    active_session["present"] = set()
    active_session["is_running"] = True
    return jsonify({"status": "session_started", "department": bs})

@app.route('/analyze_frame', methods=['POST'])
def analyze_frame():
    # Only process if a session is actually active
    if not active_session["is_running"]:
        return jsonify({"success": False, "error": "Session not active"})

    try:
        data = request.json
        department_section = data.get('department_section')
        # Check if image data exists to prevent split errors
        if not data.get('image'):
            return jsonify({"success": False, "error": "No image data"})
            
        image_data = data.get('image').split(',')[1]

        # Decode & Process
        img_bytes = base64.b64decode(image_data) # Use b64decode for standard base64
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        known_faces = get_known_faces(department_section)
        if not known_faces:
             return jsonify({"success": True, "results": [], "message": "No enrolled staff"})

        # Run detection
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        faces = face_app.get(rgb_img)
        
        results = []
        for face in faces:
            best_roll = "Unknown"
            max_sim = 0
            
            # Recognition Logic
            for roll, vec in known_faces.items():
                sim = np.dot(face.normed_embedding, vec)
                if sim > 0.35: # Threshold
                    if sim > max_sim:
                        max_sim = sim
                        best_roll = roll
            
            if best_roll != "Unknown":
                active_session["present"].add(best_roll)
            
            # Send BBOX as list for JSON compatibility
            bbox = [int(x) for x in face.bbox.tolist()]
            results.append({"name": best_roll, "bbox": bbox})
        return jsonify({"success": True, "results": results})
    except Exception as e:
        print(f"Error: {e}") # Log error to console for debugging
        return jsonify({"success": False, "error": str(e)})

#=========== live data ===#
@app.route('/get_session_status')
def get_session_status():
    department = request.args.get('department')
    # Get total class strength
    known_faces = get_known_faces(department)
    total_strength = len(known_faces)
    
    # Calculate progress
    marked = list(active_session["present"])
    present_count = len(marked)
    progress = (present_count / total_strength * 100) if total_strength > 0 else 0
    
    return jsonify({
        "marked": marked,
        "count": present_count,
        "total": total_strength,
        "percentage": round(progress, 1)
    })
#======== stopping session and saving history==========#
@app.route('/stop_live_session/<bs>')
def stop_live_session(bs):
    active_session["is_running"] = False
    known_faces = get_known_faces(bs)
    
    p_list = sorted(list(active_session["present"]))
    # Calculate absent staff based on the full class list
    all_staff = set(known_faces.keys())
    a_list = sorted(list(all_staff - active_session["present"]))
    
    return jsonify({
        "present_count": len(p_list), 
        "present_list": p_list, 
        "absent_count": len(a_list), 
        "absent_list": a_list
    })
#=========== HISTORY VIEWER LOGIC (NEW) ============
@app.route('/history')
def history():
    selected_department = request.args.get('department')
    selected_date = request.args.get('date', datetime.now().strftime("%Y-%m-%d"))
    view_mode = request.args.get('view') 
    
    history_records = []
    monthly_stats = []
    corrections = []  # Added this list
    
    from data import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if selected_department:
        # A. Logic for DAILY REPORT
        if not view_mode: 
            cursor.execute('''
                SELECT roll_no, status FROM attendance_history 
                WHERE department_section = ? AND date = ? 
                ORDER BY roll_no ASC
            ''', (selected_department, selected_date))
            history_records = cursor.fetchall()

            # NEW: Fetch corrections for this specific date
            cursor.execute('''
                SELECT roll_no, old_status, new_status, modified_by 
                FROM attendance_corrections 
                WHERE date = ? ORDER BY modified_time DESC
            ''', (selected_date,))
            corrections = cursor.fetchall()

        # B. Logic for MONTHLY ANALYTICS
        elif view_mode == 'analytics':
            selected_month = request.args.get('month', datetime.now().strftime("%Y-%m"))
            cursor.execute('''
                SELECT roll_no, 
                       (SUM(CASE WHEN status = 'PRESENT' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as percentage
                FROM attendance_history 
                WHERE department_section = ? AND date LIKE ?
                GROUP BY roll_no
                ORDER BY percentage DESC
            ''', (selected_department, f"{selected_month}%"))
            
            for row in cursor.fetchall():
                percentage = round(row[1], 2)
                if percentage >= 75: status = "Good"
                elif percentage >= 40: status = "Needs Attention"
                else: status = "Poor"
                
                monthly_stats.append({
                    "roll_no": row[0], 
                    "percentage": percentage, 
                    "status": status
                })
            
    conn.close()

    return render_template('history.html', 
                           history=history_records, 
                           corrections=corrections, # Pass this to the HTML
                           monthly_stats=monthly_stats,
                           selected_department=selected_department, 
                           selected_date=selected_date,
                           view_mode=view_mode)

#=========== EXPORT HISTORY AS CSV (NEW) ============

@app.route('/export_history_csv')
def export_history_csv():
    department = request.args.get('department')
    date = request.args.get('date')
    
    if not department or not date:
        return "Missing parameters", 400

    from data import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT roll_no, status FROM attendance_history 
        WHERE department_section = ? AND date = ? 
        ORDER BY roll_no ASC
    ''', (department, date))
    rows = cursor.fetchall()
    conn.close()

    # Create the CSV in memory
    filename = f"History_{department}_{date}.csv"
    filepath = os.path.join(BASE_DIR, filename)

    with open(filepath, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Attendance History Report"])
        writer.writerow(["department", department])
        writer.writerow(["Date", date])
        writer.writerow([])
        writer.writerow(["Roll Number", "Status"])
        for roll, status in rows:
            writer.writerow([roll, status])

    return send_file(filepath, as_attachment=True)

#=========== UPDATE ATTENDANCE ============

@app.route('/update_attendance', methods=['POST'])
def update_attendance():
    date = request.form.get('date')
    department = request.form.get('department')
    faculty_name = session.get('user_name', 'Admin') 
    
    # 1. Use 'timeout=10' to wait if the DB is busy
    # 2. Use 'with' to ensure it closes automatically
    try:
        with sqlite3.connect(DB_PATH, timeout=10) as conn:
            cursor = conn.cursor()

            for key, new_status in request.form.items():
                if key.startswith('status_'):
                    roll_no = key.split('_')[1]
                    
                    cursor.execute("SELECT status FROM attendance_history WHERE roll_no = ? AND date = ? AND department_section = ?", 
                                   (roll_no, date, department))
                    result = cursor.fetchone()
                    
                    if result:
                        old_status = result[0]
                        if old_status != new_status:
                            cursor.execute('''UPDATE attendance_history 
                                              SET status = ? 
                                              WHERE roll_no = ? AND date = ? AND department_section = ?''', 
                                           (new_status, roll_no, date, department))
                            
                            cursor.execute('''INSERT INTO attendance_corrections 
                                              (roll_no, date, old_status, new_status, modified_by) 
                                              VALUES (?, ?, ?, ?, ?)''', 
                                           (roll_no, date, old_status, new_status, faculty_name))
            conn.commit()
    except sqlite3.OperationalError as e:
        print(f"Database busy, retrying: {e}")
        return "Database is busy, please try again in a moment.", 503
        
    return redirect(url_for('history', department=department, date=date))

if __name__ == '__main__':
    init_db() # Initializes the SQLite Database
    app.run(debug=True, port=5000)