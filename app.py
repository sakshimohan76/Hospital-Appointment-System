from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user, LoginManager


app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///hospital.db"
app.config['SQLALCHEMY_TRACK_MODIFICATION']=False
app.config['SECRET_KEY']='anyString'

with app.app_context():
    db=SQLAlchemy(app)    


class Patient(db.Model, UserMixin):
    pEmail=db.Column(db.String(200), primary_key=True, unique=True)
    pName=db.Column(db.String(200),nullable=False)
    pPassword=db.Column(db.String(200))  
    doctor_dEmail = db.Column(db.String, db.ForeignKey('doctor.dEmail'))
    assigned_doctor = db.relationship('Doctor', backref='patients')
    appointments=db.relationship('Appointment', backref='patient',lazy=True)
    def get_id(self):
        return self.pEmail

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pName = db.Column(db.String(200), nullable=False)
    data = db.Column(db.String(20000), nullable=False)
    date = db.Column(db.Date)
    patient_pEmail = db.Column(db.String, db.ForeignKey('patient.pEmail', ondelete='CASCADE'))
    doctor_dEmail = db.Column(db.String, db.ForeignKey('doctor.dEmail', ondelete='CASCADE'))
    patient_obj = db.relationship('Patient', backref=db.backref('appointments_patient', cascade='all, delete-orphan'))
    doctor_obj = db.relationship('Doctor', backref=db.backref('appointments_doctor', cascade='all, delete-orphan'))


class Doctor(db.Model, UserMixin):
    dEmail=db.Column(db.String(200), primary_key=True, unique=True)
    dName=db.Column(db.String(200),nullable=False)
    dPassword=db.Column(db.String(200))  
    is_doctor = db.Column(db.Boolean, default=False)
    appointments=db.relationship('Appointment', backref='doctor',lazy=True)
    def get_id(self):
        return self.dEmail


login_manager=LoginManager()
login_manager.login_view='index.html'    
login_manager.init_app(app)

@login_manager.user_loader
def load_user(email):
    patient = Patient.query.get(email)
    if patient:
        return patient

    doctor = Doctor.query.get(email)
    if doctor:
        return doctor

    return None
   
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/patientSignup',methods=['GET','POST'])
def psignup():
    if request.method=='POST':
        pName=request.form.get('pName')
        pEmail=request.form.get('email')
        pPassword1=request.form.get('pPassword1')
        pPassword2=request.form.get('pPassword2')

        patient=Patient.query.filter_by(pEmail=pEmail).first()
        if patient:
            flash('User already exists!', category='error')
            return redirect('/patientLogin')
        elif len(pName)<3:
            flash('Name must be greater than 2 characters!' ,category='error')
        elif len(pEmail)<5:  
            flash('Email must be greater than 4 characters!' ,category='error')
        elif len(pPassword1)<5:  
            flash('Password must be greater than 4 characters!' ,category='error')  
        elif pPassword1!=pPassword2:  
            flash('Passwords do not match!' ,category='error')   
        else:
            pnew_user=Patient(pEmail=pEmail, pName=pName, pPassword=generate_password_hash(pPassword1, method='sha256'))
            db.session.add(pnew_user)
            db.session.commit()
            login_user(pnew_user)
            flash('Account created!', category='success')  
            return redirect('/')

    return render_template("patientSignup.html")

@app.route('/patientLogin' ,methods=['GET','POST'])
def plogin():
    if request.method=='POST':
        pEmail = request.form.get('email')
        pPassword = request.form.get('pPassword1')
        patient=Patient.query.filter_by(pEmail=pEmail).first()
        if patient:
            if check_password_hash(patient.pPassword, pPassword):
                # flash('Logged in successfully', category='success')
                login_user(patient)
                return render_template("home.html")
            else:
                flash('Password is incorrect!', category='error')
        else:
            flash('User does not exist!', category='error') 
            return redirect(url_for('psignup'))
    
    return render_template("patientLogin.html")

@app.route('/appointment', methods=['GET','POST'])
def show():
    if request.method == 'POST':
        name = request.form.get('name')
        desc = request.form.get('message')
        date = request.form.get('date')
        appoint = Appointment(pName=name, data=desc, date=datetime.strptime(date, '%Y-%m-%d').date())
        appoint.patient_pEmail = current_user.pEmail
        db.session.add(appoint)
        db.session.commit()
        return redirect(url_for('show'))
    allAppoint = Appointment.query.filter_by(patient_pEmail=current_user.pEmail).all()
    return render_template("home.html", allAppoint=allAppoint, patient=current_user)

@app.route('/seeApp', methods=['GET','POST']) 
def seeApp():
    appoint=Appointment.query.all()
    return render_template("seeApp1.html",appoint=appoint)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/delete/<int:id>')
def delete(id):
    appoint = Appointment.query.get(id)  
    if appoint is not None:
        db.session.delete(appoint)
        db.session.commit()
    return redirect(url_for('show'))

@app.route('/delete1/<int:id>')
def delete1(id):
    appoint = Appointment.query.get(id)  
    if appoint is not None:
        db.session.delete(appoint)
        db.session.commit()
    return redirect(url_for('seeApp'))


@app.route('/doctorLogin' ,methods=['GET','POST'])
def dlogin():
    if request.method=='POST':
        dEmail = request.form.get('email')
        dPassword = request.form.get('dPassword1')
        doctor=Doctor.query.filter_by(dEmail=dEmail).first()
        if doctor:
            if check_password_hash(doctor.dPassword, dPassword):
                # flash('Logged in successfully', category='success')
                login_user(doctor)
                appointments = Appointment.query.filter_by(doctor_dEmail=dEmail).all()
                return render_template("seeApp.html", appointments=appointments)
            else:
                flash('Password is incorrect!', category='error')
        else:
            flash('User does not exist!', category='error') 
    
    return render_template("doctorLogin.html")

@app.route('/doctorSignup' ,methods=['GET','POST'])
def dsignup():
        if request.method=='POST':
            dName=request.form.get('dName')
            dEmail=request.form.get('email')
            dPassword1=request.form.get('dPassword1')
            dPassword2=request.form.get('dPassword2')

            doctor=Doctor.query.filter_by(dEmail=dEmail).first()
            if doctor:
                flash('User already exists!', category='error')
                return redirect('/doctorLogin')
            elif len(dName)<3:
                flash('Name must be greater than 2 characters!' ,category='error')
            elif len(dEmail)<5:  
                flash('Email must be greater than 4 characters!' ,category='error')
            elif len(dPassword1)<5:  
                flash('Password must be greater than 4 characters!' ,category='error')  
            elif dPassword1!=dPassword2:  
                flash('Passwords do not match!' ,category='error')   
            else:
                pnew_user=Doctor(dEmail=dEmail, dName=dName, dPassword=generate_password_hash(dPassword1, method='sha256'))
                db.session.add(pnew_user)
                db.session.commit()
                login_user(pnew_user)
                flash('Account created!', category='success')  
                return redirect('/')
        return render_template("doctorSignup.html")
            


if __name__=='__main__':
    app.run(debug=True)