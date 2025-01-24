from flask import Flask, render_template, request, redirect, url_for,flash,send_file
from flask_mysqldb import MySQL
import MySQLdb.cursors 
import math
import time
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
import subprocess
from io import BytesIO
import uuid
import logging
import subprocess


app = Flask(__name__)
app.secret_key = "your_secret_key"

# Database configuration
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'bcs1234',
    'database': 'u617101393_cmkemmd'
}

def get_db_connection():
    return MySQLdb.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],

    )

@app.route('/')
def index():
    page = int(request.args.get('page', 1))
    records_per_page = 10
    offset = (page - 1) * records_per_page

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch total records
        cursor.execute("SELECT COUNT(*) FROM tbl_member_registration")
        total_records = cursor.fetchone()[0]
        total_pages = math.ceil(total_records / records_per_page)

        # Fetch paginated records
        query = """
            SELECT reg_id, phone_number, mill_worker_name, gender, 
                   aadhar_number, datetime_created, next_renewal_date
            FROM tbl_member_registration
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (records_per_page, offset))
        data = cursor.fetchall()

        visible_pages = 3
        start_page = max(1, page - visible_pages // 2)
        end_page = min(total_pages, start_page + visible_pages)
        start_page = max(1, end_page - visible_pages)

        return render_template(
            'index.html',
            users=data,
            page=page,
            total_pages=total_pages,
            start_page=start_page,
            end_page=end_page
        )

    except Exception as e:
        flash(f"An error occurred: {str(e)}", "error")
        return render_template('index.html', users=[], page=1, total_pages=1)

    finally:
        if conn:
            conn.close()
            
 # new_member_registration            
@app.route('/new_member_registration', methods=['GET', 'POST'])
def new_member_registration():
    if request.method == 'GET':
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute("SELECT mill_id, mill_name FROM tbl_mills ORDER BY mill_name ASC")
                mill_names = cursor.fetchall()
                cursor.close()
                connection.close()
                return render_template('new_member_registration.html', mill_names=mill_names)
            except MySQLdb.Error as e:
                flash(f"Error fetching mill names: {e}", "error")
                connection.close()
                return render_template('new_member_registration.html', mill_names=[])
        else:
            return render_template('new_member_registration.html', mill_names=[])

    elif request.method == 'POST':
        # Extract form data
        reg_id = request.form.get('txtReg_id')
        mhada_no = request.form.get('txtMhadaNo')
        enrollment_type = request.form.get('select_enrollment_type')
        mill_name_id = request.form.get('select_mill_name', '')
        mill_worker_name = request.form.get('txtMillWorkerName')
        legal_hier_name = request.form.get('txtLegalHierName', '')
        phone_number = request.form.get('txtPhoneNumber')
        email = request.form.get('txtEmail', '')
        address = request.form.get('txtAddress', '')
        aadhar_number = request.form.get('txtAadharNumber', '')
        pan_number = request.form.get('txtPANNumber', '')
        esic_number = request.form.get('txtESICNumber', '')
        gender = request.form.get('select_gender')
        age = request.form.get('txtAge')
        retired_resigned = request.form.get('select_retired_resigned')
        new_reg_fees = request.form.get('txtNewRegFees')
        from_date = request.form.get('txtFromDate')
        to_date = request.form.get('txtToDate')
        pending_amt = request.form.get('txtPendingAmt', '0')
        penalty = request.form.get('txtPenalty', '0')
        pending_from = request.form.get('txtPendingFrom', '2012')
        pending_to = request.form.get('txtPendingTo', '')
        donation = request.form.get('txtDonation', '0')
        office_fund = request.form.get('txtOfficeFund', '0')

        # Validate required fields
        if not reg_id or not mill_worker_name or not gender or not age or not retired_resigned or not new_reg_fees or not from_date or not to_date:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for('new_member_registration'))

        # Check if the registration ID already exists
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute("SELECT reg_id FROM tbl_member_registration WHERE reg_id = %s", (reg_id,))
                if cursor.fetchone():
                    flash(f"Member already exists with this Registration ID '{reg_id}'. Try a different ID.", "error")
                    return redirect(url_for('new_member_registration'))

                # Insert new member into the database
                query = """
                    INSERT INTO tbl_member_registration (
                        reg_id, mhada_no, enrollment_type, mill_name_id, mill_worker_name, legal_hier_name,
                        phone_number, email_id, address, aadhar_number, pan_number, esic_number, gender, age,
                        retired_resigned, reg_fee, pending_amt, pending_penalty, pendingFrom, pendingTo,
                        donation_fee, office_fund, reg_from_date, datetime_created, created_by
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
                """
                values = (
                    reg_id, mhada_no, enrollment_type, mill_name_id, mill_worker_name, legal_hier_name,
                    phone_number, email, address, aadhar_number, pan_number, esic_number, gender, age,
                    retired_resigned, new_reg_fees, pending_amt, penalty, pending_from, pending_to,
                    donation, office_fund, from_date, 1  # Replace 1 with the logged-in user ID
                )
                cursor.execute(query, values)
                connection.commit()
                flash("Member registered successfully!", "success")
            except MySQLdb.Error as e:
                connection.rollback()
                flash(f"Error inserting member: {e}", "error")
            finally:
                cursor.close()
                connection.close()
        else:
            flash("Failed to connect to the database.", "error")

        return redirect(url_for('new_member_registration'))



#status 
@app.route('/status')
def status():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)  # Use DictCursor for dictionary-like results

        # Get current date and time
        now = datetime.now()
        formatted_datetime_now = now.strftime("%d-%m-%Y %H:%M:%S")
    
        # Fetch today's total earning
        cursor.execute("""
            SELECT SUM(amount) AS total_earning
            FROM u617101393_cmkemmd
            WHERE DATE(transaction_date) = CURDATE()
        """)
        total_earning = cursor.fetchone()['total_earning'] or 0

        # Fetch today's billed earning
        cursor.execute("""
            SELECT SUM(amount) AS total_billed_earning
            FROM u617101393_cmkemmd
            WHERE DATE(transaction_date) = CURDATE() AND status = 'billed'
        """)
        total_billed_earning = cursor.fetchone()['total_billed_earning'] or 0

        # Fetch logged-in session count
        cursor.execute("""
            SELECT COUNT(*) AS session_count
            FROM tbl_logged_sessions
            WHERE DATE(login_time) = CURDATE()
        """)
        fetched_session_count = cursor.fetchone()['session_count'] or 0

        # Fetch new registrations today
        cursor.execute("""
            SELECT COUNT(*) AS reg_count
            FROM tbl_member_registrations
            WHERE DATE(registration_date) = CURDATE()
        """)
        fetched_reg_count = cursor.fetchone()['reg_count'] or 0

        # Fetch renewals today
        cursor.execute("""
            SELECT COUNT(*) AS renewal_count
            FROM tbl_member_renewals
            WHERE DATE(renewal_date) = CURDATE()
        """)
        fetched_renewal_count = cursor.fetchone()['renewal_count'] or 0

        # Fetch pending renewals today
        cursor.execute("""
            SELECT COUNT(*) AS pen_renewal_count
            FROM tbl_member_renewals
            WHERE DATE(renewal_due_date) = CURDATE() AND status = 'pending'
        """)
        fetched_pen_renewal_count = cursor.fetchone()['pen_renewal_count'] or 0

        # Fetch total registrations
        cursor.execute("""
            SELECT COUNT(*) AS total_reg_count
            FROM tbl_member_registrations
        """)
        fetched_total_reg_count = cursor.fetchone()['total_reg_count'] or 0

        # Fetch total renewals
        cursor.execute("""
            SELECT COUNT(*) AS total_renewal_count
            FROM tbl_member_renewals
        """)
        fetched_total_renewal_count = cursor.fetchone()['total_renewal_count'] or 0

        # Fetch total donations
        cursor.execute("""
            SELECT COUNT(*) AS total_donation_count
            FROM tbl_donations
        """)
        fetched_total_donation_count = cursor.fetchone()['total_donation_count'] or 0

        # Pass the data to the template
        return render_template(
            'Status.html',
            formatted_datetime_now=formatted_datetime_now,
            total_earning=total_earning,
            total_billed_earning=total_billed_earning,
            fetched_session_count=fetched_session_count,
            fetched_reg_count=fetched_reg_count,
            fetched_renewal_count=fetched_renewal_count,
            fetched_pen_renewal_count=fetched_pen_renewal_count,
            fetched_total_reg_count=fetched_total_reg_count,
            fetched_total_renewal_count=fetched_total_renewal_count,
            fetched_total_donation_count=fetched_total_donation_count
        )
    except Exception as e:
        logging.error("Error fetching status data: %s", e)
        return "An error occurred while fetching status data.", 500
    finally:
        if conn:
            conn.close()

#adv-report 
@app.route('/adv_report')
def adv_report():
    return render_template('adv_report.html')


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

# View MEMBER ROUTE AFTER CLICKING ON TABLE
@app.route('/view_member/<int:reg_id>', methods=['GET'])
def view_member(reg_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)

        # Fetch member details
        cursor.execute("SELECT * FROM tbl_member_registration WHERE reg_id = %s", (reg_id,))
        member = cursor.fetchone()

        if not member:
            flash("Member not found.", "error")
            return render_template('membership.html', reg_id=reg_id)

        # Map fields
        enrollment_type = member.get("enrollment_type", "Unknown")
        mill_name = None

        if enrollment_type == 'mill_worker':
            cursor.execute("SELECT mill_name FROM tbl_mills WHERE mill_id = %s", (member.get("mill_name_id"),))
            mill_name_result = cursor.fetchone()
            mill_name = mill_name_result["mill_name"] if mill_name_result else "Unknown Mill"

        # Context for template
        context = {
            "reg_id": member.get("reg_id"),
            "mhada_no": member.get("mhada_no", "Not available"),
            "enrollment_type": "Mill Worker" if enrollment_type == 'mill_worker' else "Domestic Worker (Gharelu Kamgar)" if enrollment_type == 'domestic_worker' else "Unknown",
            "mill_name": mill_name,
            "mill_worker_name": member.get("mill_worker_name", "").title(),
            "legal_hier_name": member.get("legal_hier_name", "No Legal Hier"),
            "address": member.get("address", "Address Unavailable"),
            "phone_number": member.get("phone_number", "Not available"),
            "email_id": member.get("email_id", "Not available"),
            "aadhar_number": member.get("aadhar_number", "Not available"),
            "pan_number": member.get("pan_number", "Not available"),
            "esic_number": member.get("esic_number", "Not available"),
            "gender": member.get("gender", "Not available").capitalize(),
            "age": member.get("age"),
            "retired_resigned": member.get("retired_resigned", "Not Available").title(),
            "reg_fee": member.get("reg_fee", 0),
            "pending_amt": member.get("pending_amt", 0),
            "donation_fee": member.get("donation_fee", 0),
            "office_fund": member.get("office_fund", 0),
            "reg_from_date": member.get("reg_from_date"),
            "next_renewal_date": member.get("next_renewal_date"),
        }

        return render_template('membership.html', **context)

    except Exception as e:
        flash(f"An error occurred: {str(e)}", "error")
        return render_template('membership.html', error=f"An error occurred: {str(e)}")

    finally:
        if conn:
            conn.close()


# download mysql file (DONE)
@app.route('/download_dump')
def download_dump():
    path_to_sql_dump='dump.sql'

    return send_file( 
    path_to_sql_dump,
    as_attachment=True,
    download_name="database_dump.sql"
)


# generate pdf route

# view renewals route
@app.route('/view_renewals/<int:membership_id>')
def view_renewals(membership_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch member details
        cursor.execute("""
            SELECT reg_id, mill_worker_name, gender
            FROM tbl_member_registration
            WHERE reg_id = %s
        """, (membership_id,))
        member = cursor.fetchone()

        if not member:
            return "Member not found", 404

        fetched_reg_id = member["reg_id"]
        fetched_mill_worker_name = member["mill_worker_name"].title()
        fetched_gender = member["gender"]
        gender_prefix = "Mr." if fetched_gender.lower() == "male" else "Mrs."

        # Fetch renewals
        cursor.execute("""
            SELECT renewal_id, member_reg_id, renewal_fees, delayed_renewal, delay_penalty, 
                   renewal_date, date_renewed, nextFrom_date, nextTo_date, renewed_by
            FROM tbl_member_renewals
            WHERE member_reg_id = %s
            ORDER BY date_renewed ASC
        """, (membership_id,))
        renewals = cursor.fetchall()

        # Fetch user names for renewals
        for renewal in renewals:
            renewed_by = renewal.get('renewed_by')
            if renewed_by:
                cursor.execute("""
                    SELECT fname, lname
                    FROM cm_users
                    WHERE cm_user_id = %s
                """, (renewed_by,))
                user = cursor.fetchone()
                renewal['renewed_by_name'] = f"{user['fname']} {user['lname']}" if user else "Unknown"
            else:
                renewal['renewed_by_name'] = "Unknown"

        return render_template(
            'View_Renewal.html',
            renewals=renewals,
            mill_worker_name=f"{gender_prefix} {fetched_mill_worker_name}",
            membership_id=membership_id,
            user_type='d'  # Assuming user_type is 'd' for demo
        )
    except Exception as e:
        logging.error("Error fetching renewals for membership ID %s: %s", membership_id, e)
        return "An error occurred while fetching data.", 500
    finally:
        if conn:
            conn.close()
            
            
            
            
            
# renew_membership route
@app.route('/renew_membership/<int:membership_id>', methods=['GET', 'POST'])
def renew_membership(membership_id):
    # Get database connection
    conn = get_db_connection()
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)  # Use DictCursor for dictionary-like rows

    # Fetch member details for the given membership_id
    cursor.execute("SELECT reg_id, mill_worker_name, reg_from_date, last_renewed_date, next_renewal_date FROM tbl_member_registration WHERE reg_id = %s", (membership_id,))
    member = cursor.fetchone()

    if not member:
        return "Membership not found", 404

    # Handle POST request when form is submitted
    if request.method == 'POST':
        renewal_fees = request.form['renewal_fees']
        next_renewal_from = request.form['next_from_date']
        next_renewal_to = request.form['next_to_date']
        renewal_penalty = request.form['renewal_penalty']
        delay_in_renewal = request.form['delay_in_renewal']

        # Insert the renewal details into the database
        renewal_id = f"reid_{membership_id}_{uuid.uuid4().hex[:4]}"
        
        cursor.execute("""
            INSERT INTO tbl_member_renewals (
                renewal_id, member_reg_id, renewal_fees, delayed_renewal,
                delay_penalty, renewal_date, renewed_by, date_renewed, nextFrom_date, nextTo_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s)
        """, (renewal_id, membership_id, renewal_fees, delay_in_renewal, renewal_penalty, '2025-01-18', 'admin', next_renewal_from, next_renewal_to))

        # Commit the transaction
        conn.commit()

        # Update the original member table
        cursor.execute("""
            UPDATE tbl_member_registration
            SET last_renewed_date = next_renewal_date, next_renewal_date = %s
            WHERE reg_id = %s
        """, (next_renewal_to, membership_id))

        conn.commit()

        # Redirect or show success
        # return redirect(url_for('view_renewals', membership_id=membership_id))

    # Handle GET request to display the renewal form
    return render_template('Renew_Membership.html', member=member)

# donation route
@app.route('/donation/<int:membership_id>', methods=['GET', 'POST'])
def donation(membership_id):
    if request.method == 'GET':
        # Establish a database connection
        conn = get_db_connection()
        cur = conn.cursor()

        # Fetch member details
        query = "SELECT reg_id, mill_worker_name, gender FROM tbl_member_registration WHERE reg_id = %s"
        cur.execute(query, (membership_id,))
        member = cur.fetchone()
        cur.close()
        conn.close()

        if not member:
            flash("Member not found.", "danger")
            return redirect(url_for('home'))

        reg_id, mill_worker_name, gender = member
        gender_prefix = "Mr." if gender == 'male' else "Mrs."
        return render_template('Donation.html', gender_prefix=gender_prefix,
                               mill_worker_name=mill_worker_name,
                               reg_id=reg_id)

    elif request.method == 'POST':
        try:
            txt_donation = int(request.form['txtDonation'])

            # Establish a database connection
            conn = get_db_connection()
            cur = conn.cursor()

            # Generate a unique donation ID
            donation_id = f"doid_{int(time.time())}"

            # Insert the donation record
            query = """INSERT INTO tbl_donation (donation_id, member_reg_id, donation_amount, payment_accepted_by, datetime_payment_done)
                       VALUES (%s, %s, %s, %s, NOW())"""
            cur.execute(query, (donation_id, membership_id, txt_donation, 'logged_user_id'))  # Replace logged_user_id with the actual user ID

            # Fetch the last receipt number
            cur.execute("SELECT MAX(rec_no) FROM tbl_reciepts")
            last_receipt = cur.fetchone()[0] or 0
            new_receipt = last_receipt + 1

            # Insert the receipt record
            query = """INSERT INTO tbl_reciepts (rec_no, rec_type, rec_id)
                       VALUES (%s, %s, %s)"""
            cur.execute(query, (new_receipt, 'donation', donation_id))

            # Commit the transaction
            conn.commit()
            cur.close()
            conn.close()

            flash("Donation added successfully.", "success")
            return redirect(url_for('view_donations', membership_id=membership_id))

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for('donation', membership_id=membership_id))


# Helper function to sanitize input
def test_input(data):
    return str(data).strip()


#add family member route
@app.route('/add_family_member', methods=['GET', 'POST'])
def add_family_member():
    if request.method == 'GET':
        membership_id = request.args.get('membership_id', None)

        if membership_id:
            try:
                conn = get_db_connection()
                cursor = conn.cursor(MySQLdb.cursors.DictCursor)  # Use DictCursor for dictionary-like rows
                cursor.execute("SELECT * FROM tbl_member_registration WHERE reg_id = %s", (membership_id,))
                member = cursor.fetchone()

                if member:
                    fetched_reg_id = member['reg_id']
                    fetched_mill_worker_name = member['mill_worker_name'].title()
                    fetched_gender = member['gender']
                    gender_prefix = "Mr." if fetched_gender == "male" else "Mrs."
                    return render_template(
                        'Add_Family_Member.html',
                        gender_prefix=gender_prefix,
                        fetched_mill_worker_name=fetched_mill_worker_name,
                        membership_id=membership_id,
                    )
            except Exception as e:
                flash(f"An error occurred while fetching the member: {e}", "danger")
            finally:
                if conn:
                    conn.close()

        flash("Invalid membership ID", "danger")
        return redirect(url_for('add_family_member'))

    elif request.method == 'POST':
        try:
            date = datetime.datetime.now()
            family_member_id = f"fmid_{int(time.time())}"
            txtFamilyMemberName = request.form['txtFamilyMemberName'].strip()
            txtMembershipID = request.form['txtMembershipID'].strip()
            select_relationship = request.form['select_relationship'].strip()
            txtAge = request.form['txtAge'].strip()
            select_gender = request.form['select_gender'].strip()
            txtPhoneNumber = request.form['txtPhoneNumber'].strip()
            select_occupation = request.form['select_occupation'].strip()

            # Encrypt phone number (example: reverse string)
            txtPhoneNumber_encrypted = txtPhoneNumber[::-1]

            # Get the cursor and connect to DB
            conn = get_db_connection()
            cursor = conn.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
                """
                INSERT INTO tbl_member_family 
                (family_member_id, member_reg_id, family_member_name, relationship, age, gender, phone_number, occupation, created_by, datetime_created)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    family_member_id,
                    txtMembershipID,
                    txtFamilyMemberName,
                    select_relationship,
                    txtAge,
                    select_gender,
                    txtPhoneNumber_encrypted,
                    select_occupation,
                    "logged_user_id",  # Replace with actual logged user ID
                    date,
                ),
            )
            conn.commit()  # Commit the transaction
            flash("Family member added successfully!", "success")
            return redirect(url_for('view_member', reg_id=txtMembershipID))
        except Exception as e:
            if conn:
                conn.rollback()  # Rollback in case of error
            flash(f"An error occurred while adding family member: {e}", "danger")
        finally:
            if conn:
                conn.close()  # Close the connection after use

    return render_template('Add_Family_Member.html')


#View family member route
@app.route('/view_family_member')
def view_family_member():
    membership_id = request.args.get('membership_id')
    if membership_id:
        try:
            conn = get_db_connection()
            cursor = conn.cursor(MySQLdb.cursors.DictCursor)

            # Fetch member details
            cursor.execute("SELECT * FROM tbl_member_registration WHERE reg_id = %s", (membership_id,))
            member = cursor.fetchone()

            if member:
                fetched_reg_id = member["reg_id"]
                fetched_mill_worker_name = member["mill_worker_name"].title()
                fetched_gender = member["gender"]
                gender_prefix = "Mr." if fetched_gender == "male" else "Mrs."

                # Fetch family members
                cursor.execute("SELECT * FROM tbl_member_family WHERE member_reg_id = %s ORDER BY family_member_name ASC", (membership_id,))
                family_members = cursor.fetchall()

                # Close the connection after fetching
                cursor.close()
                conn.close()

                return render_template(
                    'ViewFamily.html',
                    gender_prefix=gender_prefix,
                    fetched_mill_worker_name=fetched_mill_worker_name,
                    membership_id=membership_id,
                    family_members=family_members
                )

            else:
                flash("No member found with this membership ID.", "danger")
                return redirect(url_for('view_family_member'))

        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
            return redirect(url_for('view_family_member'))
    else:
        flash("Membership ID is required.", "danger")
        return redirect(url_for('view_family_member'))
    
    
    
#View family member route
@app.route('/view_paid_fund')
def view_paid_fund():
    membership_id = request.args.get('membership_id')
    
    if membership_id:
        try:
            connection = get_db_connection()
            cursor = connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Get member details
            cursor.execute("SELECT * FROM tbl_member_registration WHERE reg_id = %s", (membership_id,))
            member = cursor.fetchone()
            
            if member:
                gender_prefix = "Mr." if member['gender'] == "male" else "Mrs."
                member_name = member['mill_worker_name'].title()
                
                # Get the office funds for the given membership
                cursor.execute("SELECT * FROM tbl_office_fund WHERE member_reg_id = %s ORDER BY datetime_payment_done ASC", (membership_id,))
                office_funds = cursor.fetchall()
                
                # Add user names who accepted the payment
                for fund in office_funds:
                    cursor.execute("SELECT fname, lname FROM cm_users WHERE cm_user_id = %s", (fund['payment_accepted_by'],))
                    user = cursor.fetchone()
                    fund['accepted_by_name'] = f"{user['fname']} {user['lname']}" if user else "Unknown"
                
                # Close connection
                cursor.close()
                connection.close()

                return render_template('View_Paid_Fund.html', 
                                       gender_prefix=gender_prefix,
                                       member_name=member_name,
                                       office_funds=office_funds,
                                       membership_id=membership_id)
            else:
                flash("Invalid membership ID", "danger")
                return redirect(url_for('view_paid_fund'))
        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
            return redirect(url_for('view_paid_fund'))
    else:
        flash("Membership ID is missing", "danger")
        return redirect(url_for('view_paid_fund'))
    



    #view donation route 
@app.route('/view_donation/<membership_id>', methods=['GET'])
def view_donation(membership_id):
    conn = get_db_connection()
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)

    # Fetch member details
    cursor.execute("SELECT * FROM `tbl_member_registration` WHERE `reg_id` = %s", (membership_id,))
    member_details = cursor.fetchone()

    # Fetch donations made by the member
    cursor.execute("SELECT * FROM `tbl_donation` WHERE `member_reg_id` = %s ORDER BY `datetime_payment_done` ASC", (membership_id,))
    donations = cursor.fetchall()

    # Fetch user names for the donation payments
    donation_details = []
    for donation in donations:
        cursor.execute("SELECT `fname`, `lname` FROM `cm_users` WHERE `cm_user_id` = %s", (donation['payment_accepted_by'],))
        user_details = cursor.fetchone()
        donation['payment_accepted_by_name'] = f"{user_details['fname']} {user_details['lname']}" if user_details else ''
        donation_details.append(donation)

    # Close the cursor and connection
    cursor.close()
    conn.close()

    gender_prefix = 'Mr.' if member_details['gender'] == 'male' else 'Mrs.' if member_details['gender'] == 'female' else ''
    mill_worker_name = member_details['mill_worker_name']

    return render_template('View_Donation.html', donations=donation_details, gender_prefix=gender_prefix,
                           mill_worker_name=mill_worker_name, membership_id=membership_id)



# delete route
@app.route('/delete_member/<membership_id>', methods=['POST'])
def delete_member(membership_id):
    try:
        # Get the database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Delete the member from the tbl_member_registration table
        cursor.execute("DELETE FROM tbl_member_registration WHERE reg_id = %s", (membership_id,))
        
        # Commit the changes to the database
        conn.commit()

        # Close the cursor and connection
        cursor.close()
        conn.close()

        flash("Member deleted successfully!", "success")
        return redirect(url_for('some_other_route'))  # Redirect to another page after successful deletion

    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('some_other_route'))  # Redirect to an error page or another route
    
    
    
    # change password route
@app.route('/Change_Password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        current_password = request.form['txtCurrentPassword']
        new_password = request.form['txtNewPassword']
        
        # Get the user ID from session or wherever it's stored
        user_id = 'fetched_user_id'  # Replace with the actual user ID from the session or auth logic

        # Fetch the current password from the database
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT cm_password FROM cm_users WHERE cm_user_id = %s', (user_id,))
        result = cursor.fetchone()
        cursor.close()

        if result:
            fetched_password = result['cm_password']
            
            # Check if the current password matches
            if check_password_hash(fetched_password, current_password):
                # Hash the new password
                hashed_new_password = generate_password_hash(new_password)

                # Update the password in the database
                cursor = mysql.connection.cursor()
                cursor.execute('UPDATE cm_users SET cm_password = %s WHERE cm_user_id = %s', (hashed_new_password, user_id))
                mysql.connection.commit()
                cursor.close()

                flash('Password has been successfully updated. You are being logged out.', 'success')
                return redirect(url_for('logout'))

            else:
                flash('Incorrect current password.', 'error')
        else:
            flash('User not found.', 'error')

    return render_template('change_password.html')

# Route to download a specific file
# Path where you want to store the backup file temporarily
BACKUP_DIR = '/backend/u617101393_cmkemmd.sql'

@app.route('/backup-database', methods=['GET'])
def backup_database():
    # Generate backup file name (you can customize this)
    backup_filename = 'database_backup.sql'

    # Run the backup command (replace with your actual database backup command)
    # Example for MySQL:
    command = f"mysqldump -u root -p'bcs1234' u617101393_cmkemmd > {os.path.join(BACKUP_DIR, backup_filename)}"
    
    # Execute the command (this will create the backup file)
    try:
        subprocess.run(command, shell=True, check=True)
        return send_file(os.path.join(BACKUP_DIR, backup_filename), as_attachment=True)
    except subprocess.CalledProcessError:
        return "Error creating database backup", 500


@app.route('/logout')
def logout():
    # Logic for logout (clear session, etc.)
    return redirect(url_for('login'))





if __name__ == '__main__':
    app.run(debug=True)

