import mysql.connector
from flask import Flask, render_template, url_for, request, redirect, flash

db = mysql.connector.connect(host="127.0.0.1", database="Pharmacies-Chain", user="USERNAME", password="PASSWORD")

cursor = db.cursor()


def render_patients():
    cursor.execute("SELECT * FROM Patient")
    patients = cursor.fetchall()

    return (patients, len(patients))


def render_doctors():
    cursor.execute("SELECT * FROM Doctor")
    doctors = cursor.fetchall()

    return doctors


def render_pharmacies():
    cursor.execute("SELECT * FROM Pharmacy")
    pharmacies = cursor.fetchall()

    return pharmacies


def render_drugs():
    cursor.execute("SELECT * FROM Drug")
    drugs = cursor.fetchall()

    return drugs


def get_doctor(did):
    cursor.execute(f"SELECT * FROM Doctor D, Patient P WHERE P.did = D.did and D.did = {did}")
    fetched_doctor = cursor.fetchall()
    name = fetched_doctor[0][1]
    patients_number = len(fetched_doctor)
    patient_names = list()
    for i in range(len(fetched_doctor)):
        patient_names.append(fetched_doctor[i][5])

    cursor.execute(
        f"SELECT * FROM Doctor D, Pharmacy P, Supervisor S WHERE D.did = S.did and P.hid = S.hid and D.did = {did}")
    doctor_pharmacy_fetch = cursor.fetchall()
    pharmacy_names = list()

    for i in range(len(doctor_pharmacy_fetch)):
        pharmacy_names.append(doctor_pharmacy_fetch[i][5])

    cursor.execute(
        f"SELECT * FROM Doctor D, Prescription P, Drug WHERE D.did = P.did and D.did = {did} and Drug.mid = P.mid")
    doctor_drug_fetch = cursor.fetchall()

    drug_list_doc = list()
    formula_list_doc = list()

    for i in range(len(doctor_drug_fetch)):
        if doctor_drug_fetch[i][11] not in drug_list_doc:
            drug_list_doc.append(doctor_drug_fetch[i][11])
            formula_list_doc.append(doctor_drug_fetch[i][12])

    drug_formula_dict = {drug_list_doc[i]: formula_list_doc[i] for i in range(len(drug_list_doc))}

    return name, patients_number, patient_names, pharmacy_names, drug_formula_dict


def get_patient(pid):
    cursor.execute(
        f"SELECT * FROM Patient P, Doctor D, Prescription Pr, Drug Dr WHERE P.did = D.did and P.pid = {pid} and P.pid = Pr.pid and Dr.mid = Pr.mid")
    fetched_patient_p = cursor.fetchall()

    if len(fetched_patient_p) == 0:
        cursor.execute(
            f"SELECT * FROM Patient P, Prescription Pr, Drug Dr WHERE  P.pid = {pid} and P.pid = Pr.pid and Dr.mid = Pr.mid")
        fetched_patient_p = cursor.fetchall()

        name = fetched_patient_p[0][1]
        doc_name = None
        drug_list = list()
        formula_list = list()
        for i in range(len(fetched_patient_p)):
            if fetched_patient_p[i][12] not in drug_list:
                drug_list.append(fetched_patient_p[i][12])
                formula_list.append(fetched_patient_p[i][13])
        drug_formula_dict = {drug_list[i]: formula_list[i] for i in range(len(drug_list))}

    else:

        name = fetched_patient_p[0][1]
        doc_name = fetched_patient_p[0][6]

        drug_list = list()
        formula_list = list()
        for i in range(len(fetched_patient_p)):
            if fetched_patient_p[i][16] not in drug_list:
                drug_list.append(fetched_patient_p[i][16])
                formula_list.append(fetched_patient_p[i][17])
        drug_formula_dict = {drug_list[i]: formula_list[i] for i in range(len(drug_list))}

    return name, doc_name, drug_formula_dict


def insert_patient(pid, pname, address, age, did):
    cursor.execute("SELECT * from Patient")
    existing_patients = cursor.fetchall()

    for record in existing_patients:
        while pid == record[0]:
            raise Exception("duplicate patient ID")

    if did == "":
        if address == "" and str(age) == "":
            cursor.execute("INSERT INTO Patient(pid, name, address, age, did) VALUES(%s, %s, NULL, NULL, NULL)",
                           (pid, pname))

        elif address == "":
            cursor.execute("INSERT INTO Patient(pid, name, address, age, did) VALUES(%s, %s, NULL, %s, NULL)",
                           (pid, pname, age))
        elif str(age) == "":
            cursor.execute("INSERT INTO Patient(pid, name, address, age, did) VALUES(%s, %s, %s, NULL, NULL)",
                           (pid, pname, address))
        else:
            cursor.execute("INSERT INTO Patient(pid, name, address, age, did) VALUES(%s, %s, %s, %s, NULL)",
                           (pid, pname, address, age))

        db.commit()
    else:
        if address == "" and str(age) == "":
            cursor.execute("INSERT INTO Patient(pid, name, address, age, did) VALUES(%s, %s, NULL, NULL, %s)",
                           (pid, pname, did))

        elif address == "":
            cursor.execute("INSERT INTO Patient(pid, name, address, age, did) VALUES(%s, %s, NULL, %s, %s)",
                           (pid, pname, age, did))
        elif str(age) == "":
            cursor.execute("INSERT INTO Patient(pid, name, address, age, did) VALUES(%s, %s, %s, NULL, %s)",
                           (pid, pname, address, did))
        else:
            cursor.execute("INSERT INTO Patient(pid, name, address, age, did) VALUES(%s, %s, %s, %s, %s)",
                           (pid, pname, address, age, did))

        db.commit()


def add_prescription(presc_id, date, description, did, pid, mid):
    cursor.execute("INSERT INTO Prescription VALUES(%s, %s, %s, %s, %s, %s)",
                   (presc_id, date, description, did, pid, mid))
    db.commit()


################################################################################################
################################################################################################
# Flask app


app = Flask(__name__)


@app.route("/", methods=['GET'])
def index():
    return render_template("index.html")


@app.route("/patient", methods=['GET'])
def patient():
    if request.method == 'GET':
        patients, total_patients = render_patients()
        return render_template("patients.html", patients=patients, total_patients=total_patients)


@app.route("/doctor", methods=['GET'])
def doctor():
    if request.method == 'GET':
        doctors = render_doctors()
        return render_template("doctors.html", doctors=doctors)


@app.route("/pharmacy", methods=['GET'])
def pharmacy():
    if request.method == 'GET':
        pharmacies = render_pharmacies()
        return render_template("pharmacy.html", pharmacies=pharmacies)


@app.route("/drug", methods=['GET'])
def drug():
    if request.method == 'GET':
        drugs = render_drugs()
        return render_template("drug.html", drugs=drugs)


@app.route("/fetchdoctor", methods=['GET', 'POST'])
def fetch_doctor():
    name, patients_number, patient_names, pharmacy_names, drug_formula_dict = "", 0, list(), list(), dict()
    if request.method == 'POST':

        did = request.form["did"]

        if did != "":
            try:
                did = int(did)

                name, patients_number, patient_names, pharmacy_names, drug_formula_dict = get_doctor(did)

                return render_template("fetchdoctor.html", name=name, patients_number=patients_number,
                                       patient_names=patient_names, pharmacy_names=pharmacy_names,
                                       drug_formula_dict=drug_formula_dict)
            except Exception:
                flash("Doctor ID was not Found")
                return render_template("flash.html")
        else:
            return render_template("fetchdoctor.html", name=name, patients_number=patients_number,
                                   patient_names=patient_names, pharmacy_names=pharmacy_names,
                                   drug_formula_dict=drug_formula_dict)

    else:

        return render_template("fetchdoctor.html", name=name, patients_number=patients_number,
                               patient_names=patient_names, pharmacy_names=pharmacy_names,
                               drug_formula_dict=drug_formula_dict)


@app.route("/fetchpatient", methods=['GET', 'POST'])
def fetch_patient():
    name, doc_name, drug_formula_dict = "", "", dict()

    if request.method == 'POST':

        pid = request.form["pid"]

        if pid != "":
            try:
                pid = int(pid)

                name, doc_name, drug_formula_dict = get_patient(pid)

                return render_template("fetchpatient.html", name=name,
                                       doc_name=doc_name, drug_formula_dict=drug_formula_dict)
            except Exception:
                flash("Patient ID was not Found")
                return render_template("flash.html")
        else:
            return render_template("fetchpatient.html", name=name,
                                   doc_name=doc_name, drug_formula_dict=drug_formula_dict)

    else:

        return render_template("fetchpatient.html", name=name,
                               doc_name=doc_name, drug_formula_dict=drug_formula_dict)


@app.route("/postpatient", methods=['GET', 'POST'])
def post_patient():
    if request.method == 'POST':

        pid = request.form["pid"]

        if pid != "":
            try:
                pid = int(request.form["pid"])
                pname = request.form["pname"]
                address = request.form["address"]
                age = int(request.form["age"])
                did = request.form["did"]

                if did == "":

                    insert_patient(pid, pname, address, age, "")
                else:
                    print("did=", did)
                    insert_patient(pid, pname, address, age, int(did))

                patients, total_patients = render_patients()
                return render_template("patients.html", patients=patients, total_patients=total_patients)

            except Exception:

                flash("Error: Duplicate Patient ID")
                return render_template("flash.html")
        else:
            return render_template("insertpatient.html")

    else:

        return render_template("insertpatient.html")


@app.route('/postprescription', methods=['GET', 'POST'])
def post_prescription():
    if request.method == 'POST':

        try:
            presc_id = int(request.form["presc_id"])
            date = request.form["date"]
            description = request.form["description"]
            did = int(request.form["did"])
            pid = int(request.form["pid"])
            mid = int(request.form["mid"])

            add_prescription(presc_id, date, description, did, pid, mid)

            return render_template('index.html')

        except Exception:

            flash("Error adding prescription")
            return render_template("flash.html")


    else:
        return render_template("postprescription.html")


if __name__ == "__main__":
    # re-render issue required having a secret key and a configuration for session type
    # fix reference: https://stackoverflow.com/questions/26080872/secret-key-not-set-in-flask-session-using-the-flask-session-extension
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(debug=True)
