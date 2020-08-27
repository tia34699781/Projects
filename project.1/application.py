import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date

from helpers import login_required, apology

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response



# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///recruitement.db")
identity = None

@app.route("/candidate_index")
@login_required
def candidate_index():
    """Show table for candidates"""
    resume = db.execute("SELECT * FROM candidate_resumes WHERE id = :id", id=session["user_id"])
    return render_template("candidate_index.html", resume=resume)

@app.route("/recruiter_index")
@login_required
def recruiter_index():
    """Show table for recruiters"""
    recruiter_details = db.execute("SELECT * FROM recruiter_details WHERE id = :id", id=session["user_id"])
    return render_template("recruiter_index.html",recruiter_details=recruiter_details)

@app.route("/job_post", methods=["GET", "POST"])
@login_required
def job_post():
    if request.method == "POST":
        today = date.today()
        db.execute("INSERT INTO job_openings(user_id, job_type, posting_title, salary, job_owner, zip_code, state, country, skill_set, experience, date_opened) VALUES(:user_id, :job_type, :posting_title, :salary, :job_owner, :zip_code, :state, :country, :skill_set, :experience, :date_opened)", user_id=session["user_id"], job_type=request.form.get("job_type"), posting_title=request.form.get("posting_title"), salary=request.form.get("salary"), job_owner=request.form.get("job_owner"), zip_code=request.form.get("zip_code"), state=request.form.get("state"), country=request.form.get("country"), skill_set=request.form.get("skill_set"), experience=request.form.get("experience"), date_opened=today.strftime("%d/%m/%Y"))
        return redirect("/my_job_openings")
    else:
        return render_template("job_post.html")

@app.route("/my_job_openings", methods=["GET"])
def my_job_openings():
    no_data = False
    job_openings = db.execute("SELECT * FROM job_openings WHERE user_id = :user_id", user_id=session["user_id"],)
    if job_openings == []:
        no_data = True
    return render_template("my_job_openings.html", job_openings=job_openings, no_data=no_data)

@app.route("/job_openings")
@login_required
def job_openings():
    return render_template("job_openings.html")


checked = []
@app.route("/edit_job_openings", methods=["GET", "POST"])
@login_required
def edit_job_openings():
    global checked
    if request.method == "POST":
        db.execute("UPDATE job_openings SET job_type = :job_type, posting_title = :posting_title, salary = :salary, job_owner = :job_owner, zip_code = :zip_code, state = :state, country = :country, skill_set = :skill_set, experience = :experience WHERE user_id = :user_id AND id = :id", job_type=request.form.get("job_type"), posting_title=request.form.get("posting_title"), salary=request.form.get("salary"), job_owner=request.form.get("job_owner"), zip_code=request.form.get("zip_code"), state=request.form.get("state"), country=request.form.get("country"), skill_set=request.form.get("skill_set"), experience=request.form.get("experience"), user_id=session["user_id"], id=checked)
        return redirect("/my_job_openings")
    else:
        checked = request.args.get("edit_job_btn")
        job = db.execute("SELECT * FROM job_openings WHERE id = :id", id=checked)
        return render_template("edit_job_openings.html", job=job)


@app.route("/delete_job_openings", methods=["GET", "POST"])
@login_required
def delete_job_openings():
    checked = str(request.args.get("delete"))
    if checked != None:
        checked = checked.split(',')
        for i in range(len(checked)):
          db.execute("DELETE FROM job_openings WHERE id = :id AND user_id = :user_id", id=checked[i], user_id=session["user_id"])
        flash("deleted!")
    return redirect("/my_job_openings")

@app.route("/candidates")
@login_required
def candidates():
    candidates = db.execute("SELECT * FROM candidate_resumes")
    return render_template("candidates.html", candidates=candidates)


@app.route("/candidates_full_profile", methods=["GET", "POST"])
@login_required
def candidates_full_profile():
    resume = db.execute("SELECT * FROM candidate_resumes WHERE id = :id", id=request.form.get("full_profile_btn"))
    return render_template("candidates_full_profile.html", resume=resume)

@app.route("/", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            return apology("invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        # Redirect user to home page
        global identity
        resume = db.execute("SELECT * FROM candidate_resumes WHERE id = :id", id=session["user_id"])
        if len(resume) == 1:
            return redirect("/candidate_index")
        else:
            return redirect("/recruiter_index")
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/jobs", methods=["GET", "POST"])
@login_required
def jobs():
    if request.method == "POST":
        no_data = False
        jobs = db.execute("SELECT * FROM job_openings WHERE id = :id", id=request.form.get("view_job_btn"))
        if jobs == []:
            no_data = True
        return render_template("jobs.html", jobs=jobs, no_data=no_data)
    else :
        no_data = False
        jobs = db.execute("SELECT * FROM job_openings")
        if jobs == []:
            no_data = True
        return render_template("jobs.html", jobs=jobs, no_data=no_data)


@app.route("/apply_for_job", methods=["GET","POST"])
@login_required
def apply_for_job():
    job = request.form.get("apply_for_job_btn")
    job = eval(job)
    candidate = db.execute("SELECT * FROM candidate_resumes WHERE id=:id", id=session["user_id"])
    db.execute("INSERT INTO notifications(sender_id, receiver_id, message, is_candidate) VALUES(:sender_id, :receiver_id, :message, :is_candidate)", sender_id=session["user_id"], receiver_id=job["user_id"], is_candidate=True, message=candidate[0]["firstname"] + " " + candidate[0]["lastname"] + " has applied for your job " + job["posting_title"])
    flash("You have applied for job " + job["posting_title"] + "!!!")
    return redirect("/jobs")


@app.route("/offer_job", methods=["GET", "POST"])
@login_required
def offer_job():
    candidate_id = request.form.get("offer_job_btn")
    return render_template("offer_job.html", candidate_id=candidate_id)

candidate_id = None
@app.route("/offer_existing_job", methods=["GET", "POST"])
@login_required
def offer_existing_job():
    """Offer a existing job"""
    global candidate_id
    if candidate_id != None:
        recruiter = db.execute("SELECT company_name FROM recruiter_details WHERE id=:id", id=session["user_id"])
        db.execute("INSERT INTO notifications(sender_id, receiver_id, message, is_job, job_id) VALUES(:sender_id, :receiver_id, :message, :is_job, :job_id)", sender_id=session["user_id"], receiver_id=candidate_id, is_job=True, message="You have been offered a job By " + recruiter[0]["company_name"], job_id=request.form.get("offer_job_btn"))
        candidate = db.execute("SELECT * FROM candidate_resumes WHERE id = :id", id=candidate_id)
        candidate_id = None
        flash("Job sent to " + candidate[0]["firstname"] + " " + candidate[0]["lastname"] + "!!!")
        return redirect("/candidates")
    else:
        no_data = False
        job_openings = db.execute("SELECT * FROM job_openings WHERE user_id = :user_id", user_id=session["user_id"])
        if job_openings == []:
            no_data = True
        candidate_id = request.form.get("offer_existing_job_btn")
        return render_template("offer_existing_job.html", job_openings=job_openings, no_data=no_data)

candidate_id = None
@app.route("/offer_new_job", methods=["GET", "POST"])
@login_required
def offer_new_job():
    global candidate_id
    if candidate_id != None:
        today = date.today()
        job = db.execute("INSERT INTO job_openings(user_id, job_type, posting_title, salary, job_owner, zip_code, state, country, skill_set, experience, date_opened) VALUES(:user_id, :job_type, :posting_title, :salary, :job_owner, :zip_code, :state, :country, :skill_set, :experience, :date_opened)", user_id=session["user_id"], job_type=request.form.get("job_type"), posting_title=request.form.get("posting_title"), salary=request.form.get("salary"), job_owner=request.form.get("job_owner"), zip_code=request.form.get("zip_code"), state=request.form.get("state"), country=request.form.get("country"), skill_set=request.form.get("skill_set"), experience=request.form.get("experience"), date_opened=today.strftime("%d/%m/%Y"))
        recruiter = db.execute("SELECT company_name FROM recruiter_details WHERE id=:id", id=session["user_id"])
        db.execute("INSERT INTO notifications(sender_id, receiver_id, message, is_job, job_id) VALUES(:sender_id, :receiver_id, :message, :is_job, :job_id)", sender_id=session["user_id"], receiver_id=candidate_id, is_job=True, message="You have been offered a job By " + recruiter[0]["company_name"], job_id=job)
        candidate = db.execute("SELECT * FROM candidate_resumes WHERE id = :id", id=candidate_id)
        flash("Job sent to " + candidate[0]["firstname"] + " " + candidate[0]["lastname"] + "!!!")
        candidate_id = None
        return redirect("/candidates")
    else:
        candidate_id = request.form.get("offer_new_job_btn")
        return render_template("offer_new_job.html")

@app.route("/candidate_reports", methods=["GET", "POST"])
@login_required
def candidate_reports():
    data = db.execute("SELECT posting_title FROM job_openings")
    data_keys = []
    data_values = []
    for i in range(len(data)):
        data_keys.append(str(data[i]["posting_title"]).lower())
    checked = []
    for i in range(len(data_keys)):
        if data_keys[i] not in checked[0:]:
            data_values.append(data_keys.count(data_keys[i]))
            checked.append(data_keys[i])
    for i in range(len(data)):
        if str(data[i]).lower() not in str(data[0:]).lower():
            data_keys.append(data[i]["posting_title"])
    data_keys = list(dict.fromkeys(data_keys))
    return render_template("candidate_reports.html", data_keys=data_keys, data_values=data_values)

@app.route("/recruiter_reports", methods=["GET", "POST"])
@login_required
def recruiter_reports():
    data = db.execute("SELECT current_job_title FROM candidate_resumes")
    data_keys = []
    data_values = []
    for i in range(len(data)):
        data_keys.append(str(data[i]["current_job_title"]).lower())
    checked = []
    for i in range(len(data_keys)):
        if data_keys[i] not in checked[0:]:
            data_values.append(data_keys.count(data_keys[i]))
            checked.append(data_keys[i])
    for i in range(len(data)):
        if str(data[i]).lower() not in str(data[0:]).lower():
            data_keys.append(data[i]["current_job_title"])
    data_keys = list(dict.fromkeys(data_keys))
    return render_template("recruiter_reports.html", data_keys=data_keys, data_values=data_values)

@app.route("/accept_candidate", methods=["GET", "POST"])
@login_required
def accept_candidate():
    notification = request.form.get("accept_candidate_btn")
    notification = eval(notification)
    recruiter = db.execute("SELECT company_name FROM recruiter_details WHERE id = :id", id=session["user_id"])
    candidate = db.execute("SELECT * FROM candidate_resumes WHERE id = :id", id=notification["sender_id"])
    db.execute("INSERT INTO notifications(sender_id, receiver_id, message) VALUES(:sender_id, :receiver_id, :message)", sender_id=session["user_id"], receiver_id=notification["sender_id"], message=recruiter[0]["company_name"] + " has hired you. Congratulations!!!")
    db.execute("DELETE FROM notifications WHERE id = :id", id=notification["id"])
    flash("message sent to " + candidate[0]["firstname"] + " " + candidate[0]["lastname"])
    return redirect("/recruiter_notifications")

@app.route("/decline_candidate", methods=["GET", "POST"])
@login_required
def decline_candidate():
    notification = request.form.get("decline_candidate_btn")
    notification = eval(notification)
    recruiter = db.execute("SELECT company_name FROM recruiter_details WHERE id = :id", id=session["user_id"])
    candidate = db.execute("SELECT * FROM candidate_resumes WHERE id = :id", id=notification["sender_id"])
    db.execute("INSERT INTO notifications(sender_id, receiver_id, message) VALUES(:sender_id, :receiver_id, :message)", sender_id=session["user_id"], receiver_id=notification["sender_id"], message=recruiter[0]["company_name"] + " has declined your job request")
    db.execute("DELETE FROM notifications WHERE id = :id", id=notification["id"])
    flash("message sent to " + candidate[0]["firstname"] + " " + candidate[0]["lastname"])
    return redirect("/recruiter_notifications")

@app.route("/accept_job", methods=["GET", "POST"])
@login_required
def accept_job():
    notification = request.form.get("accept_job_btn")
    notification = eval(notification)
    recruiter = db.execute("SELECT company_name FROM recruiter_details WHERE id = :id", id=notification["sender_id"])
    candidate = db.execute("SELECT * FROM candidate_resumes WHERE id = :id", id=session["user_id"])
    db.execute("INSERT INTO notifications(sender_id, receiver_id, message) VALUES(:sender_id, :receiver_id, :message)", sender_id=session["user_id"], receiver_id=notification["sender_id"], message=candidate[0]["firstname"] + " " + candidate[0]["lastname"] + " has accepted your job!!!")
    db.execute("DELETE FROM notifications WHERE id = :id", id=notification["id"])
    flash("message sent to " + recruiter[0]["company_name"])
    return redirect("/candidate_notifications")

@app.route("/decline_job", methods=["GET", "POST"])
@login_required
def decline_job():
    notification = request.form.get("decline_job_btn")
    notification = eval(notification)
    recruiter = db.execute("SELECT company_name FROM recruiter_details WHERE id = :id", id=notification["sender_id"])
    candidate = db.execute("SELECT * FROM candidate_resumes WHERE id = :id", id=session["user_id"])
    db.execute("INSERT INTO notifications(sender_id, receiver_id, message) VALUES(:sender_id, :receiver_id, :message)", sender_id=session["user_id"], receiver_id=notification["sender_id"], message=candidate[0]["firstname"] + " " + candidate[0]["lastname"] + " has declined your job offer")
    db.execute("DELETE FROM notifications WHERE id = :id", id=notification["id"])
    flash("message sent to " + recruiter[0]["company_name"])
    return redirect("/candidate_notifications")

@app.route("/recruiter_notifications", methods=["GET", "POST"])
@login_required
def recruiter_notifications():
    """Shows notifications for a recruiter"""
    no_data = False
    notifications = db.execute("SELECT * FROM notifications WHERE receiver_id = :id", id=session["user_id"])
    if notifications == []:
        no_data = True
    return render_template("recruiter_notifications.html", notifications=notifications, no_data=no_data)


@app.route("/candidate_notifications", methods=["GET", "POST"])
@login_required
def candidate_notifications():
    """Shows notifications for a candidate"""
    no_data = False
    notifications = db.execute("SELECT * FROM notifications WHERE receiver_id = :id", id=session["user_id"])
    if notifications == []:
        no_data = True
    return render_template("candidate_notifications.html", notifications=notifications, no_data=no_data)

@app.route("/delete_notification", methods=["GET", "POST"])
@login_required
def delete_notification():
    """delete's a notifications"""
    notification = request.form.get("delete_notification_btn")
    notification = eval(notification)
    db.execute("DELETE FROM notifications WHERE id = :id", id=notification["id"])
    is_candidate = db.execute("SELECT * FROM candidate_resumes WHERE id = :id", id=notification["receiver_id"])
    if len(is_candidate) == 1:
        return redirect("/candidate_notifications")
    else:
        return redirect("/recruiter_notifications")

@app.route("/register", methods=["GET"])
def register():
    """Register user"""
    return render_template("register.html")

@app.route("/edit_recruiter_details", methods=["GET","POST"])
@login_required
def edit_recruiter_details():
    if request.method == "POST":
        if request.form.get("confirm") != request.form.get("password"):
            return apology("Passwords Don't match")
        result = db.execute("SELECT username FROM users WHERE username = :username",username=request.form.get("username"))
        # Ensure username exists and password is correct
        print(result[0]["username"])
        if len(result) == 1 and result[0]["username"] != request.form.get("username"):
            return apology("Username is not available")
        elif result[0]["username"] != request.form.get("username"):
            db.execute("UPDATE users SET username = :username, password = :password",username=request.form.get("username"), password=generate_password_hash(request.form.get("password")))
        result = db.execute("SELECT id FROM users WHERE username = :username",username=request.form.get("username"))
        db.execute("UPDATE recruiter_details SET email = :email, company_name = :company_name, website = :website, phone = :phone, mobile = :mobile, fax = :fax, address = :address WHERE id = :id", email=request.form.get("email"), company_name=request.form.get("company_name"), website=request.form.get("website"), phone=request.form.get("phone"), mobile=request.form.get("mobile"), fax=request.form.get("fax"), address=request.form.get("address"), id=session["user_id"])
        # Remember which user has logged in
        session["user_id"] = result[0]["id"]
        return redirect("/recruiter_index")
    else:
        user = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])
        recruiter_details = db.execute("SELECT * FROM recruiter_details WHERE id = :id", id=session["user_id"])
        return render_template("edit_recruiter_details.html", recruiter_details=recruiter_details, user=user)

@app.route("/edit_candidate_details", methods=["GET","POST"])
@login_required
def edit_candidate_details():
    if request.method == "POST":
        if request.form.get("confirm") != request.form.get("password"):
            return apology("Passwords Don't match")
        result = db.execute("SELECT username FROM users WHERE username = :username",username=request.form.get("username"))
        # Ensure username exists and password is correct
        if len(result) == 1 and result[0]["username"] != request.form.get("username"):
            return apology("Username is not available")
        elif result[0]["username"] != request.form.get("username"):
            db.execute("UPDATE users SET username = :username, password = :password",username=request.form.get("username"), password=generate_password_hash(request.form.get("password")))
        result = db.execute("SELECT id FROM users WHERE username = :username",username=request.form.get("username"))
        db.execute("UPDATE candidate_resumes SET firstname = :firstname, lastname = :lastname, email = :email, mobile = :mobile, address = :address, educational_details = :educational_details, experience_details = :experience_details, skill_set = :skill_set, current_job_title = :current_job_title WHERE id = :id", firstname=request.form.get("firstname"), lastname=request.form.get("lastname"), email=request.form.get("email"), mobile=request.form.get("mobile"), address=request.form.get("address"), educational_details=request.form.get("educational_details"), experience_details=request.form.get("experience_details"), skill_set=request.form.get("skill_set"), current_job_title=request.form.get("current_job_title"), id=session["user_id"])
        # Remember which user has logged in
        session["user_id"] = result[0]["id"]
        return redirect("/candidate_index")
    else:
        user = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])
        resume = db.execute("SELECT * FROM candidate_resumes WHERE id = :id", id=session["user_id"])
        no_data = False
        job_titles_temp = db.execute("SELECT posting_title FROM job_openings")
        job_titles = []
        for i in range(len(job_titles_temp)):
            if str(job_titles_temp[i]).lower() not in str(job_titles_temp[i + 1:]).lower():
                job_titles.append(job_titles_temp[i])
        if len(job_titles) < 1:
            no_data = True
        return render_template("edit_candidate_details.html", resume=resume, user=user, job_titles=job_titles, no_data=no_data)

@app.route("/register_recruiter", methods=["GET","POST"])
def register_recruiter():
    """Register recruiter"""
    session.clear()
    if request.method == "POST":
        if request.form.get("confirm") != request.form.get("password"):
            return apology("Passwords Don't match")
        result = db.execute("SELECT username FROM users WHERE username = :username",username=request.form.get("username"))
        # Ensure username exists and password is correct
        if len(result) == 1:
            return apology("Username is not available")
        db.execute("INSERT INTO users(username, password) VALUES(:username, :password)",username=request.form.get("username"), password=generate_password_hash(request.form.get("password")))
        result = db.execute("SELECT id FROM users WHERE username = :username",username=request.form.get("username"))
        db.execute("INSERT INTO recruiter_details(id, email, company_name, website, phone, mobile, fax, address) VALUES(:id, :email, :company_name, :website, :phone, :mobile, :fax, :address)", id=result[0]["id"], email=request.form.get("email"), company_name=request.form.get("company_name"), website=request.form.get("website"), phone=request.form.get("phone"), mobile=request.form.get("mobile"), fax=request.form.get("fax"), address=request.form.get("address"))
        # Remember which user has logged in
        session["user_id"] = result[0]["id"]
        return redirect("/recruiter_index")
    else:
        return render_template("recruiter_register.html")


@app.route("/register_candidate", methods=["GET","POST"])
def register_candidate():
    """Register candidate"""
    session.clear()
    if request.method == "POST":
        if request.form.get("confirm") != request.form.get("password"):
            return apology("Passwords Don't match")
        result = db.execute("SELECT username FROM users WHERE username = :username",username=request.form.get("username"))
        # Ensure username exists and password is correct
        if len(result) == 1:
            return apology("Username is not available")
        db.execute("INSERT INTO users(username, password) VALUES(:username, :password)", username=request.form.get("username"), password=generate_password_hash(request.form.get("password")))
        result = db.execute("SELECT id FROM users WHERE username = :username",username=request.form.get("username"))
        db.execute("INSERT INTO candidate_resumes(id, firstname, lastname, email, mobile, address, educational_details, experience_details, skill_set, current_job_title) VALUES(:id, :firstname, :lastname, :email, :mobile, :address, :educational_details, :experience_details, :skill_set, :current_job_title)", id=result[0]["id"], firstname=request.form.get("firstname"), lastname=request.form.get("lastname"), email=request.form.get("email"), mobile=request.form.get("mobile"), address=request.form.get("address"), educational_details=request.form.get("educational_details"), experience_details=request.form.get("experience_details"), skill_set=request.form.get("skill_set"), current_job_title=request.form.get("current_job_title"))
        # Remember which user has logged in
        session["user_id"] = result[0]["id"]
        return redirect("/candidate_index")
    else:
        no_data = False
        job_titles_temp = db.execute("SELECT posting_title FROM job_openings")
        job_titles = []
        for i in range(len(job_titles_temp)):
            if str(job_titles_temp[i]).lower() not in str(job_titles_temp[i + 1:]).lower():
                job_titles.append(job_titles_temp[i])
        if len(job_titles) < 1:
            no_data = True
        return render_template("candidate_register.html", job_titles=job_titles, no_data=no_data)


@app.route("/about", methods=["GET", "POST"])
@login_required
def about():
    indentity = db.execute("SELECT * FROM candidate_resumes WHERE id = :id", id=session["user_id"]);
    if len(indentity) == 1:
        return render_template("candidate_about.html")
    else:
        return render_template("recruiter_about.html")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
