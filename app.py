from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import pymysql
import os
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = "super-secret-key"  # change in production

# DB config - EDIT these values to match your MySQL setup
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",     # change if you have a password
    "db": "hospital_db",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": False
}

def get_db_conn():
    return pymysql.connect(**DB_CONFIG)

# ---------- Dashboard ----------
@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/api/stats/patients_by_city")
def patients_by_city():
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT city, COUNT(*) as cnt FROM patient GROUP BY city;")
            rows = cur.fetchall()
        return jsonify(rows)
    finally:
        conn.close()

@app.route("/api/stats/doctors_by_spec")
def doctors_by_spec():
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT specialization AS spec, COUNT(*) as cnt FROM doctor GROUP BY specialization;")
            rows = cur.fetchall()
        return jsonify(rows)
    finally:
        conn.close()

@app.route("/api/stats/appointments_over_time")
def appointments_over_time():
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT appointment_date AS dt, COUNT(*) as cnt FROM appointment GROUP BY appointment_date ORDER BY appointment_date;")
            rows = cur.fetchall()
        # convert date to string for JSON
        for r in rows:
            if isinstance(r['dt'], (date, datetime)):
                r['dt'] = r['dt'].isoformat()
        return jsonify(rows)
    finally:
        conn.close()

# ---------- Patients ----------
@app.route("/patients")
def patients():
    q = request.args.get("q", "")
    city = request.args.get("city", "")
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            sql = "SELECT * FROM patient WHERE 1=1"
            params = []
            if q:
                sql += " AND (name LIKE %s)"
                params.append(f"%{q}%")
            if city:
                sql += " AND city = %s"
                params.append(city)
            sql += " ORDER BY patient_id;"
            cur.execute(sql, params)
            rows = cur.fetchall()
        # for city-filter list
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT city FROM patient;")
            cities = [r['city'] for r in cur.fetchall()]
        return render_template("patients.html", patients=rows, q=q, cities=cities, city=city)
    finally:
        conn.close()

@app.route("/patients/add", methods=["GET", "POST"])
def add_patient():
    if request.method == "POST":
        name = request.form.get("name").strip()
        age = request.form.get("age")
        gender = request.form.get("gender")
        city = request.form.get("city") or "Unknown"
        if not name or age is None:
            flash("Name and age are required", "danger")
            return redirect(url_for("add_patient"))
        conn = get_db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO patient (name, age, gender, city) VALUES (%s,%s,%s,%s);", (name, int(age), gender, city))
            conn.commit()
            flash("Patient added successfully", "success")
            return redirect(url_for("patients"))
        except Exception as e:
            conn.rollback()
            flash(f"Error adding patient: {e}", "danger")
            return redirect(url_for("add_patient"))
        finally:
            conn.close()
    return render_template("patient_form.html", patient=None)

@app.route("/patients/edit/<int:pid>", methods=["GET", "POST"])
def edit_patient(pid):
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            if request.method == "POST":
                name = request.form.get("name").strip()
                age = int(request.form.get("age"))
                gender = request.form.get("gender")
                city = request.form.get("city") or "Unknown"
                cur.execute("UPDATE patient SET name=%s, age=%s, gender=%s, city=%s WHERE patient_id=%s;", (name, age, gender, city, pid))
                conn.commit()
                flash("Patient updated", "success")
                return redirect(url_for("patients"))
            else:
                cur.execute("SELECT * FROM patient WHERE patient_id=%s;", (pid,))
                patient = cur.fetchone()
        return render_template("patient_form.html", patient=patient)
    finally:
        conn.close()

@app.route("/patients/delete/<int:pid>", methods=["POST"])
def delete_patient(pid):
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM patient WHERE patient_id=%s;", (pid,))
            conn.commit()
            flash("Patient deleted", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error deleting patient: {e}", "danger")
    finally:
        conn.close()
    return redirect(url_for("patients"))

# ---------- Doctors ----------
@app.route("/doctors")
def doctors():
    q = request.args.get("q", "")
    spec = request.args.get("spec", "")
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            sql = "SELECT * FROM doctor WHERE 1=1"
            params = []
            if q:
                sql += " AND (name LIKE %s)"
                params.append(f"%{q}%")
            if spec:
                sql += " AND specialization = %s"
                params.append(spec)
            sql += " ORDER BY doctor_id;"
            cur.execute(sql, params)
            rows = cur.fetchall()
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT specialization FROM doctor;")
            specs = [r['specialization'] for r in cur.fetchall()]
        return render_template("doctors.html", doctors=rows, q=q, specs=specs, spec=spec)
    finally:
        conn.close()

@app.route("/doctors/add", methods=["GET", "POST"])
def add_doctor():
    if request.method == "POST":
        name = request.form.get("name").strip()
        specialization = request.form.get("specialization").strip()
        if not name or not specialization:
            flash("Name and specialization required", "danger")
            return redirect(url_for("add_doctor"))
        conn = get_db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO doctor (name, specialization) VALUES (%s,%s);", (name, specialization))
            conn.commit()
            flash("Doctor added", "success")
            return redirect(url_for("doctors"))
        except Exception as e:
            conn.rollback()
            flash(f"Error: {e}", "danger")
            return redirect(url_for("add_doctor"))
        finally:
            conn.close()
    return render_template("doctor_form.html", doctor=None)

@app.route("/doctors/edit/<int:did>", methods=["GET", "POST"])
def edit_doctor(did):
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            if request.method == "POST":
                name = request.form.get("name").strip()
                specialization = request.form.get("specialization").strip()
                cur.execute("UPDATE doctor SET name=%s, specialization=%s WHERE doctor_id=%s;", (name, specialization, did))
                conn.commit()
                flash("Doctor updated", "success")
                return redirect(url_for("doctors"))
            else:
                cur.execute("SELECT * FROM doctor WHERE doctor_id=%s;", (did,))
                doctor = cur.fetchone()
        return render_template("doctor_form.html", doctor=doctor)
    finally:
        conn.close()

@app.route("/doctors/delete/<int:did>", methods=["POST"])
def delete_doctor(did):
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM doctor WHERE doctor_id=%s;", (did,))
            conn.commit()
            flash("Doctor deleted", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error deleting doctor: {e}", "danger")
    finally:
        conn.close()
    return redirect(url_for("doctors"))

# ---------- Appointments ----------
@app.route("/appointments")
def appointments():
    doctor_id = request.args.get("doctor_id", type=int)
    patient_id = request.args.get("patient_id", type=int)
    start = request.args.get("start")
    end = request.args.get("end")
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            sql = """SELECT a.*, p.name AS patient_name, d.name AS doctor_name
                     FROM appointment a
                     JOIN patient p ON a.patient_id = p.patient_id
                     JOIN doctor d ON a.doctor_id = d.doctor_id
                     WHERE 1=1"""
            params = []
            if doctor_id:
                sql += " AND a.doctor_id = %s"; params.append(doctor_id)
            if patient_id:
                sql += " AND a.patient_id = %s"; params.append(patient_id)
            if start:
                sql += " AND a.appointment_date >= %s"; params.append(start)
            if end:
                sql += " AND a.appointment_date <= %s"; params.append(end)
            sql += " ORDER BY a.appointment_date DESC;"
            cur.execute(sql, params)
            rows = cur.fetchall()
        # compute status for each
        for r in rows:
            appt_date = r['appointment_date']
            today = date.today()
            if appt_date < today:
                r['status'] = "Completed"
            elif appt_date == today:
                r['status'] = "Today"
            else:
                r['status'] = "Upcoming"
        # lists for filters
        with conn.cursor() as cur:
            cur.execute("SELECT patient_id, name FROM patient ORDER BY name;")
            patients = cur.fetchall()
            cur.execute("SELECT doctor_id, name FROM doctor ORDER BY name;")
            doctors = cur.fetchall()
        return render_template("appointments.html", appointments=rows, patients=patients, doctors=doctors,
                               doctor_id=doctor_id, patient_id=patient_id, start=start, end=end)
    finally:
        conn.close()

@app.route("/appointments/add", methods=["GET", "POST"])
def add_appointment():
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            if request.method == "POST":
                patient_id = int(request.form.get("patient_id"))
                doctor_id = int(request.form.get("doctor_id"))
                appointment_date = request.form.get("appointment_date")
                notes = request.form.get("notes")
                try:
                    cur.execute("INSERT INTO appointment (patient_id, doctor_id, appointment_date, notes) VALUES (%s,%s,%s,%s);",
                                (patient_id, doctor_id, appointment_date, notes))
                    conn.commit()
                    flash("Appointment scheduled", "success")
                    return redirect(url_for("appointments"))
                except Exception as e:
                    conn.rollback()
                    flash(f"Error scheduling appointment: {e}", "danger")
                    return redirect(url_for("add_appointment"))
            # GET - fetch lists
            cur.execute("SELECT patient_id, name FROM patient ORDER BY name;")
            patients = cur.fetchall()
            cur.execute("SELECT doctor_id, name, specialization FROM doctor ORDER BY name;")
            doctors = cur.fetchall()
        return render_template("appointment_form.html", appointment=None, patients=patients, doctors=doctors)
    finally:
        conn.close()

@app.route("/appointments/edit/<int:aid>", methods=["GET", "POST"])
def edit_appointment(aid):
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            if request.method == "POST":
                patient_id = int(request.form.get("patient_id"))
                doctor_id = int(request.form.get("doctor_id"))
                appointment_date = request.form.get("appointment_date")
                notes = request.form.get("notes")
                cur.execute("UPDATE appointment SET patient_id=%s, doctor_id=%s, appointment_date=%s, notes=%s WHERE appointment_id=%s;",
                            (patient_id, doctor_id, appointment_date, notes, aid))
                conn.commit()
                flash("Appointment updated", "success")
                return redirect(url_for("appointments"))
            else:
                cur.execute("""SELECT a.*, p.name AS patient_name, d.name AS doctor_name
                               FROM appointment a
                               JOIN patient p ON a.patient_id = p.patient_id
                               JOIN doctor d ON a.doctor_id = d.doctor_id
                               WHERE a.appointment_id=%s;""", (aid,))
                appt = cur.fetchone()
                cur.execute("SELECT patient_id, name FROM patient ORDER BY name;")
                patients = cur.fetchall()
                cur.execute("SELECT doctor_id, name FROM doctor ORDER BY name;")
                doctors = cur.fetchall()
        return render_template("appointment_form.html", appointment=appt, patients=patients, doctors=doctors)
    finally:
        conn.close()

@app.route("/appointments/delete/<int:aid>", methods=["POST"])
def delete_appointment(aid):
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM appointment WHERE appointment_id=%s;", (aid,))
            conn.commit()
            flash("Appointment deleted", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error deleting appointment: {e}", "danger")
    finally:
        conn.close()
    return redirect(url_for("appointments"))

# ---------- API endpoints to support frontend (optional) ----------
@app.route("/api/patients")
def api_patients():
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM patient;")
            rows = cur.fetchall()
        return jsonify(rows)
    finally:
        conn.close()

@app.route("/api/doctors")
def api_doctors():
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM doctor;")
            rows = cur.fetchall()
        return jsonify(rows)
    finally:
        conn.close()

# Run app
if __name__ == "__main__":
    # Optional: load config from environment variables in production
    app.run(debug=True, host="0.0.0.0", port=5000)
