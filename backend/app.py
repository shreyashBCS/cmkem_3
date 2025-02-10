from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_mysqldb import MySQL
import MySQLdb.cursors
import math
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import subprocess
from io import BytesIO
import uuid
import logging
import time
from datetime import datetime
from PIL import Image

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Flask-MySQLdb configuration
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'bcs1234'
app.config['MYSQL_DB'] = 'u617101393_cmkemmd'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'  # Use dictionary-like results

mysql = MySQL(app)

# upload folder
UPLOAD_FOLDER = os.path.join('static','profile_pictures')
os.makedirs(UPLOAD_FOLDER,exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# logging configuration
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def index():
    """Render the index page with paginated and filtered member data."""
    # Get query parameters from the form
    mhada_no = request.args.get('mhada_no', '').strip()
    reg_id = request.args.get('reg_id', '').strip()
    mill_worker_name = request.args.get('mill_worker_name', '').strip()
    phone_number = request.args.get('phone_number', '').strip()
    gender = request.args.get('gender', '').strip()
    from_date = request.args.get('from_date', '').strip()
    to_date = request.args.get('to_date', '').strip()

    # Pagination parameters
    page = int(request.args.get('page', 1))
    records_per_page = 10
    offset = (page - 1) * records_per_page

    try:
        cursor = mysql.connection.cursor()

        # Base query
        query = """
            SELECT reg_id, phone_number, mill_worker_name, gender, 
                   aadhar_number, datetime_created, next_renewal_date
            FROM tbl_member_registration
            WHERE 1=1
        """
        params = []

        # Add filters based on form inputs
        if mhada_no:
            query += " AND mhada_no = %s"  # Exact match for Mhada Number
            params.append(mhada_no)
        if reg_id:
            query += " AND reg_id = %s"  # Exact match for Reg. No.
            params.append(reg_id)
        if mill_worker_name:
            query += " AND mill_worker_name LIKE %s"  # Partial match for Name
            params.append(f"%{mill_worker_name}%")
        if phone_number:
            query += " AND phone_number = %s"  # Exact match for Phone Number
            params.append(phone_number)
        if gender:
            query += " AND gender = %s"  # Exact match for Gender
            params.append(gender)
        if from_date and to_date:
            query += " AND datetime_created BETWEEN %s AND %s"  # Date range filter
            params.extend([from_date, to_date])

        # Fetch total records for pagination
        count_query = f"SELECT COUNT(*) FROM ({query}) AS filtered_data"
        cursor.execute(count_query, params)
        total_records = cursor.fetchone()['COUNT(*)']
        total_pages = math.ceil(total_records / records_per_page)

        # Add pagination to the main query
        query += " LIMIT %s OFFSET %s"
        params.extend([records_per_page, offset])

        # Fetch paginated and filtered records
        cursor.execute(query, params)
        data = cursor.fetchall()

        # Calculate visible pages for pagination
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
            end_page=end_page,
            mhada_no=mhada_no,
            reg_id=reg_id,
            mill_worker_name=mill_worker_name,
            phone_number=phone_number,
            gender=gender,
            from_date=from_date,
            to_date=to_date
        )

    except Exception as e:
        flash(f"An error occurred: {str(e)}", "error")
        return render_template('index.html', users=[], page=1, total_pages=1)

    finally:
        cursor.close()
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# NEW MEMBER MEMBER REGISTRATION
@app.route('/new_member_registration', methods=['GET', 'POST'])
def new_member_registration():
    if request.method == 'POST':
        print("Received Data:", request.form.to_dict())
        try:
            # Extract form data with default handling for optional fields
            mhada_no = request.form['txtMhadaNo'].strip()
            enrollment_type = request.form['select_enrollment_type']
            mill_name_id = request.form.get('select_mill_name', None)  # Optional field
            mill_worker_name = request.form['txtMillWorkerName'].strip()
            legal_hire_name = request.form.get('txtLegalHierName', None)
            phone_number = request.form['txtPhoneNumber'].strip()
            email = request.form['txtEmail'].strip()
            address = request.form['txtAddress'].strip()
            aadhar_number = request.form['txtAadharNumber'].strip()
            pan_number = request.form['txtPANNumber'].strip()
            esic_no = request.form['txtESICNumber'].strip()
            gender = request.form['select_gender']
            age = request.form['txtAge'].strip()
            retired_resigned = request.form['select_retired_resigned']
            new_reg_fee = request.form['txtNewRegFees'].strip()
            penalty = request.form['txtPenalty'].strip()
            regs_from = request.form['txtFromDate']
            regs_to = request.form['txtToDate']
            pending_amt = request.form['txtPendingAmt'].strip()
            pending_from = request.form['txtPendingFrom']
            pending_upto = request.form['txtPendingTo']
            donation = request.form['txtDonation'].strip()
            office_fund = request.form['txtOfficeFund'].strip()

            cur = mysql.connection.cursor()
            mysql.connection.autocommit = False  # Disable auto-commit

            # Insert Member Data
            query = """INSERT INTO tbl_member_registration 
                (mhada_no, enrollment_type, mill_name_id, mill_worker_name, legal_hire_name, phone_number, email, address, 
                aadhar_number, pan_number, esic_no, gender, age, retired_resigned, new_reg_fee, penalty, regs_from, regs_to, 
                pending_amt, pending_from, pending_upto, donation, office_fund) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            
            values = (
                mhada_no, enrollment_type, mill_name_id if mill_name_id else None, mill_worker_name,
                legal_hire_name if legal_hire_name else None, phone_number, email, address,
                aadhar_number, pan_number, esic_no, gender, age, retired_resigned, new_reg_fee, penalty,
                regs_from, regs_to, pending_amt, pending_from, pending_upto, donation, office_fund
            )
            
            cur.execute(query, values)

            # Get the last inserted reg_id (auto-incremented ID)
            cur.execute("SELECT LAST_INSERT_ID()")
            new_reg_id = cur.fetchone()[0]

            # Update next renewal date
            cur.execute("UPDATE tbl_member_registration SET next_renewal_date = %s WHERE reg_id = %s", (regs_to, new_reg_id))

            # Generate Receipt
            cur.execute("SELECT MAX(rec_no) FROM tbl_reciepts")
            last_receipt = cur.fetchone()[0] or 0  # If None, start from 0
            new_receipt = last_receipt + 1
            cur.execute("INSERT INTO tbl_reciepts (rec_no, rec_type, rec_id) VALUES (%s, %s, %s)", (new_receipt, 'registration', new_reg_id))

            mysql.connection.commit()  # Commit all changes
            cur.close()

            flash("Member Registered Successfully!", "success")
            return redirect(url_for('new_member_registration'))

        except Exception as e:
            mysql.connection.rollback()  # Rollback in case of error
            flash(f"An error occurred: {str(e)}", "error")
            return redirect(url_for('new_member_registration'))

    else:
        # Fetch mill names for dropdown from database
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT mill_id, mill_name FROM tbl_mills")
            mill_names = cur.fetchall()
            cur.close()
        except Exception as e:
            flash(f"An error occurred while fetching mill names: {str(e)}", "error")
            mill_names = []

        return render_template('new_member_registration.html', mill_names=mill_names)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
@app.route('/status')
def status():
    # Get the current date in the format YYYY-MM-DD
    current_date = datetime.now().strftime('%Y-%m-%d')

    # Create a cursor to interact with the MySQL database
    cur = mysql.connection.cursor()

    # Fetch Today's Total Earnings (sum of all payments for today)
    cur.execute("""
        SELECT SUM(reg_fee + pending_amt + pending_penalty + donation_fee + office_fund) AS total_earnings
        FROM tbl_member_registration
        WHERE DATE(datetime_created) = %s
    """, (current_date,))
    total_earnings = cur.fetchone()['total_earnings'] or 0

    # Fetch Today's Billed Earnings (sum of payments for today's renewals)
    cur.execute("""
        SELECT SUM(renewal_fees + delay_penalty) AS billed_earnings
        FROM tbl_member_renewals
        WHERE DATE(date_renewed) = %s
    """, (current_date,))
    billed_earnings = cur.fetchone()['billed_earnings'] or 0

    # Fetch Today's Logged-in Sessions count
    cur.execute("""
        SELECT COUNT(*) AS logged_sessions
        FROM tbl_logged_sessions
        WHERE DATE(session_date) = %s
    """, (current_date,))
    logged_sessions = cur.fetchone()['logged_sessions']

    # Fetch Today's New Registrations count
    cur.execute("""
        SELECT COUNT(*) AS new_registrations
        FROM tbl_member_registration
        WHERE DATE(datetime_created) = %s
    """, (current_date,))
    new_registrations = cur.fetchone()['new_registrations']

    # Fetch Today's Renewals count
    cur.execute("""
        SELECT COUNT(*) AS renewals_today
        FROM tbl_member_renewals
        WHERE DATE(date_renewed) = %s
    """, (current_date,))
    renewals_today = cur.fetchone()['renewals_today']

    # Fetch Today's Pending Renewals count
    cur.execute("""
        SELECT COUNT(*) AS pending_to_renew
        FROM tbl_member_registration
        WHERE DATE(next_renewal_date) = %s
    """, (current_date,))
    pending_to_renew = cur.fetchone()['pending_to_renew']

    # Close the cursor and the database connection
    cur.close()

    # Pass all the calculated data to the template and render the page
    return render_template('Status.html', 
                           total_earnings=total_earnings,
                           billed_earnings=billed_earnings,
                           logged_sessions=logged_sessions,
                           new_registrations=new_registrations,
                           renewals_today=renewals_today,
                           pending_to_renew=pending_to_renew,
                           
                           )
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

@app.route('/adv_report')
def adv_report():
    """Render the advanced report page."""
    return render_template('adv_report.html')


@app.route('/today_total_earning')
def today_total_earning():
    """Render the advanced report page."""
    return render_template('Today_Total_Earning.html')


@app.route('/today_billed_earning')
def today_billed_earning():
    """Render the advanced report page."""
    return render_template('Bill_Earning_Today.html')


@app.route('/logged_session')
def logged_session():
    """Render the advanced report page."""
    return render_template('Logged_Session.html')



@app.route('/new_reg_today')
def new_reg_today():
    """Render the advanced report page."""
    return render_template('New_Reg_Today.html')



@app.route('/renewal_today')
def renewal_today():
    """Render the advanced report page."""
    return render_template('Total_Renewal_Today.html')



@app.route('/pending_renewal_today')
def pending_renewal_today():
    """Render the advanced report page."""
    return render_template('Pending_To_Renew.html')
# #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

# VIEW MEMBER
@app.route('/view_member/<int:reg_id>', methods=['GET'])
def view_member(reg_id):
    """View details of a specific member"""
    try:
        cursor = mysql.connection.cursor()

        # Fetch member details
        cursor.execute("SELECT * FROM tbl_member_registration WHERE reg_id = %s", (reg_id,))
        member = cursor.fetchone()

        if not member:
            flash("Member not found.", "error")
            return redirect(url_for('index'))

            
         # Fetch latest renewal_id
        cursor.execute(
            "SELECT renewal_id FROM tbl_member_renewals WHERE member_reg_id = %s ORDER BY renewal_id DESC LIMIT 1",
            (reg_id,)
        )
        renewal = cursor.fetchone()
        renewal_id = renewal['renewal_id'] if renewal else None  # Ensure None if no renewal exists   
            
            
        # Fetch mill name if applicable
        mill_name = None
        if member['enrollment_type'] == 'mill_worker':
            cursor.execute("SELECT mill_name FROM tbl_mills WHERE mill_id = %s", (member['mill_name_id'],))
            mill_name_result = cursor.fetchone()
            mill_name = mill_name_result['mill_name'] if mill_name_result else "Unknown Mill"

        return render_template('membership.html', member=member, mill_name=mill_name, membership_id=reg_id,renewal_id=renewal_id)

    except Exception as e:
        flash(f"An error occurred: {e}", "error")
        return redirect(url_for('index'))

    finally:
        cursor.close()
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

@app.route('/download_dump')
def download_dump():
    """Download the database dump."""
    path_to_sql_dump = 'dump.sql'
    return send_file(path_to_sql_dump, as_attachment=True, download_name="database_dump.sql")
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
@app.route('/renew_membership/<int:membership_id>', methods=['GET', 'POST'])
def renew_membership(membership_id):
    try:
        cursor = mysql.connection.cursor()

        if request.method == 'POST':
            # Get form data and provide default values if not set
            renewal_fees = request.form.get('renewal_fees', 0)
            next_from_date = request.form.get('next_from_date')
            next_to_date = request.form.get('next_to_date')
            renewal_penalty = request.form.get('renewal_penalty', 0)
            delay_in_renewal = request.form.get('delay_in_renewal', '0')

            # Convert renewal fees and penalty to float, set default 0 if not provided
            renewal_fees = float(renewal_fees) if renewal_fees else 0.0
            renewal_penalty = float(renewal_penalty) if renewal_penalty else 0.0

            # Map delay_in_renewal to ENUM values ('No', 'Yes')
            delay_in_renewal = 'Yes' if delay_in_renewal == '1' else 'No'

            # Generate renewal_id (max 15 chars)
            renewal_id = f"R{membership_id}{uuid.uuid4().hex[:4]}"

            # Get the current date for renewal date
            renewal_date = datetime.now().date()

            # Insert renewal record into the database
            cursor.execute("""
                INSERT INTO tbl_member_renewals (
                    renewal_id, member_reg_id, renewal_fees, delayed_renewal,
                    delay_penalty, renewal_date, renewed_by, date_renewed, nextFrom_date, nextTo_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s)
            """, (renewal_id, membership_id, renewal_fees, delay_in_renewal, renewal_penalty, renewal_date, 'admin', next_from_date, next_to_date))

            # Update member's next renewal date in the registration table
            cursor.execute("""
                UPDATE tbl_member_registration
                SET last_renewed_date = next_renewal_date, next_renewal_date = %s
                WHERE reg_id = %s
            """, (next_to_date, membership_id))

            # Commit changes to the database
            mysql.connection.commit()

            # Show success message
            flash("Membership renewed successfully!", "success")
            return redirect(url_for('view_renewals', membership_id=membership_id))

        # Fetch member details for GET request
        cursor.execute("SELECT reg_id, mill_worker_name, reg_from_date, last_renewed_date, next_renewal_date FROM tbl_member_registration WHERE reg_id = %s", (membership_id,))
        member = cursor.fetchone()

        if not member:
            return "Membership not found", 404

        return render_template('Renew_Membership.html', member=member)

    except Exception as e:
        # Rollback transaction in case of error
        mysql.connection.rollback()
        print("SQL Error:", str(e))  # Debugging
        flash(f"An error occurred: {e}", "error")
        return redirect(url_for('renew_membership', membership_id=membership_id))

    finally:
        cursor.close()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

@app.route('/view_renewals/<int:membership_id>')
def view_renewals(membership_id):
    """View renewals for a specific member."""
    try:
        cursor = mysql.connection.cursor()

        # Fetch member details
        cursor.execute("""
            SELECT reg_id, mill_worker_name, gender
            FROM tbl_member_registration
            WHERE reg_id = %s
        """, (membership_id,))
        member = cursor.fetchone()

        if not member:
            return "Member not found", 404

        # Fetch renewals
        cursor.execute("""
            SELECT renewal_id, member_reg_id, renewal_fees, delayed_renewal, delay_penalty, 
                   renewal_date, date_renewed, nextFrom_date, nextTo_date, renewed_by
            FROM tbl_member_renewals
            WHERE member_reg_id = %s
            ORDER BY date_renewed ASC
        """, (membership_id,))
        renewals = cursor.fetchall()

        return render_template(
            'View_Renewal.html',
            renewals=renewals,
            member=member,
            mill_worker_name=member['mill_worker_name']  # Pass member name to the template
        )

    except Exception as e:
        logging.error(f"Error fetching renewals: {e}")
        return "An error occurred while fetching renewals.", 500

    finally:
        cursor.close()
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# Helper function to sanitize input
def test_input(data):
    return data.strip()

@app.route('/donation/<int:membership_id>', methods=['GET', 'POST'])
def donation(membership_id):
    """Handle donations for a specific member."""
    try:
        cursor = mysql.connection.cursor()

        if request.method == 'POST':
            # Process form submission
            donation_amount = test_input(request.form['txtDonation'])
            logged_user_id = 'logged_user_id'  # Replace with actual logged-in user ID

            # Start transaction
            cursor.execute("START TRANSACTION")

            # Insert donation record
            donation_id = f"doid_{int(time.time())}"
            cursor.execute("""
                INSERT INTO tbl_donation (
                    donation_id, member_reg_id, donation_amount, payment_accepted_by, datetime_payment_done
                ) VALUES (%s, %s, %s, %s, NOW() + INTERVAL 630 MINUTE)
            """, (donation_id, membership_id, donation_amount, logged_user_id))

            # Generate receipt
            cursor.execute("SELECT MAX(rec_no) AS last_receipt FROM tbl_reciepts")
            last_receipt = cursor.fetchone()['last_receipt'] or 0
            new_receipt = last_receipt + 1

            cursor.execute("""
                INSERT INTO tbl_reciepts (rec_no, rec_type, rec_id)
                VALUES (%s, %s, %s)
            """, (new_receipt, 'donation', donation_id))

            # Commit transaction
            mysql.connection.commit()
            flash("Donation added successfully!", "success")
            return redirect(url_for('view_donation', membership_id=membership_id))

        # Fetch member details for GET request
        cursor.execute("SELECT reg_id, mill_worker_name, gender FROM tbl_member_registration WHERE reg_id = %s", (membership_id,))
        member = cursor.fetchone()

        if not member:
            flash("Member not found.", "error")
            return redirect(url_for('index'))

        # Determine gender prefix
        gender_prefix = "Mr." if member['gender'] == 'male' else "Mrs."

        return render_template('Donation.html', gender_prefix=gender_prefix, member=member, membership_id=membership_id)

    except Exception as e:
        # Rollback transaction in case of error
        mysql.connection.rollback()
        flash(f"An error occurred: {e}", "error")
        return redirect(url_for('donation', membership_id=membership_id))

    finally:
        cursor.close()
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

    




# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

@app.route('/add_family_member', methods=['GET', 'POST'])
def add_family_member():
    """Add a family member to a member's record."""
    if request.method == 'GET':
        membership_id = request.args.get('membership_id', None)

        if membership_id:
            try:
                cursor = mysql.connection.cursor()
                cursor.execute("SELECT * FROM tbl_member_registration WHERE reg_id = %s", (membership_id,))
                member = cursor.fetchone()

                if member:
                    gender_prefix = "Mr." if member['gender'] == 'male' else "Mrs."
                    return render_template(
                        'add_family_member.html',
                        gender_prefix=gender_prefix,
                        member=member
                    )
            except Exception as e:
                flash(f"An error occurred: {e}", "error")
            finally:
                cursor.close()

        flash("Invalid membership ID", "error")
        return redirect(url_for('index'))

    elif request.method == 'POST':
        try:
            family_member_id = f"fmid_{int(time.time())}"
            txtFamilyMemberName = request.form['txtFamilyMemberName'].strip()
            txtMembershipID = request.form['txtMembershipID'].strip()
            select_relationship = request.form['select_relationship'].strip()
            txtAge = request.form['txtAge'].strip()
            select_gender = request.form['select_gender'].strip()
            txtPhoneNumber = request.form['txtPhoneNumber'].strip()
            select_occupation = request.form['select_occupation'].strip()

            # Insert family member into the database
            cursor = mysql.connection.cursor()
            cursor.execute("""
                INSERT INTO tbl_member_family (
                    family_member_id, member_reg_id, family_member_name, relationship, age, gender, phone_number, occupation, created_by, datetime_created
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                family_member_id, txtMembershipID, txtFamilyMemberName, select_relationship, txtAge, select_gender, txtPhoneNumber, select_occupation, 1  # Replace 1 with the logged-in user ID
            ))
            mysql.connection.commit()
            flash("Family member added successfully!", "success")
            return redirect(url_for('view_member', reg_id=txtMembershipID))

        except Exception as e:
            mysql.connection.rollback()
            flash(f"An error occurred: {e}", "error")
        finally:
            cursor.close()

    return render_template('Add_family_Member.html',
                           gender_prefix=gender_prefix,
                           member=member
                           
                           )



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
@app.route('/view_family_member')
def view_family_member():
    """View family members of a specific member."""
    membership_id = request.args.get('membership_id')
    if membership_id:
        try:
            cursor = mysql.connection.cursor()

            # Fetch member details
            cursor.execute("SELECT * FROM tbl_member_registration WHERE reg_id = %s", (membership_id,))
            member = cursor.fetchone()

            if member:
                gender_prefix = "Mr." if member['gender'] == 'male' else "Mrs."

                # Fetch family members
                cursor.execute(
                    "SELECT * FROM tbl_member_family WHERE member_reg_id = %s ORDER BY family_member_name ASC",
                    (membership_id,)
                )
                family_members = cursor.fetchall()

                return render_template(
                    'ViewFamily.html',
                    gender_prefix=gender_prefix,
                    member=member,
                    family_members=family_members
                )

            else:
                flash("No member found with this membership ID.", "error")
                return redirect(url_for('index'))

        except Exception as e:
            flash(f"An error occurred: {e}", "error")
        finally:
            cursor.close()

    flash("Membership ID is required.", "error")
    return redirect(url_for('index'))


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
@app.route('/view_paid_fund')
def view_paid_fund():
    """View paid funds for a specific member."""
    membership_id = request.args.get('membership_id')
    
    # Debugging: Print membership_id to check if it's being passed
    print(f"Debug: membership_id = {membership_id}")
    
    if not membership_id:
        flash("Membership ID is missing", "error")
        print("Debug: Redirecting to index due to missing membership_id")
        return redirect(url_for('index'))
    
    try:
        # Create a dictionary cursor
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Fetch member details
        cursor.execute("SELECT * FROM tbl_member_registration WHERE reg_id = %s", (membership_id,))
        member = cursor.fetchone()
        
        if not member:
            flash("Invalid membership ID", "error")
            print(f"Debug: Invalid membership_id = {membership_id}")
            return redirect(url_for('index'))
        
        # Determine gender prefix
        gender_prefix = "Mr." if member['gender'] == 'male' else "Mrs."
        
        # Fetch paid funds for the member
        cursor.execute("""
            SELECT * FROM tbl_office_fund 
            WHERE member_reg_id = %s 
            ORDER BY datetime_payment_done ASC
        """, (membership_id,))
        paid_funds = cursor.fetchall()
        
        # Fetch user details for each paid fund
        for fund in paid_funds:
            cursor.execute("SELECT fname, lname FROM cm_users WHERE cm_user_id = %s", (fund['payment_accepted_by'],))
            user = cursor.fetchone()
            fund['payment_accepted_by_name'] = f"{user['fname']} {user['lname']}" if user else "Unknown"
        
        # Render the template with the fetched data
        return render_template(
            'View_Paid_Fund.html',
            gender_prefix=gender_prefix,
            member=member,
            paid_funds=paid_funds,
            membership_id=membership_id
        )
    
    except Exception as e:
        flash(f"An error occurred: {e}", "error")
        print(f"Debug: Error occurred - {e}")
        return redirect(url_for('index'))
    
    finally:
        if 'cursor' in locals():
            cursor.close()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

@app.route('/view_donation/<int:membership_id>')
def view_donation(membership_id):
    """View donations made by a specific member."""
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Fetch member details
        cursor.execute("SELECT * FROM tbl_member_registration WHERE reg_id = %s", (membership_id,))
        member = cursor.fetchone()

        if not member:
            flash("Member not found.", "error")
            print(f"Member with reg_id {membership_id} not found.")  # Debugging
            return redirect(url_for('index'))

        # Determine gender prefix
        gender_prefix = "Mr." if member['gender'] == 'male' else "Mrs."

        # Fetch donations for the specific member
        cursor.execute("""
            SELECT d.donation_id, d.donation_amount, d.payment_accepted_by, d.datetime_payment_done, 
                   u.fname, u.lname
            FROM tbl_donation d
            JOIN cm_users u ON d.payment_accepted_by = u.cm_user_id
            WHERE d.member_reg_id = %s 
            ORDER BY d.datetime_payment_done ASC
        """, (membership_id,))
        donations = cursor.fetchall()

        # Log the donations found (or not)
        if not donations:
            print(f"No donations found for member with reg_id {membership_id}")  # Debugging

        return render_template(
            'View_Donation.html',
            gender_prefix=gender_prefix,
            member=member,
            donations=donations,
            membership_id=membership_id
        )

    except Exception as e:
        flash(f"An error occurred: {e}", "error")
        print(f"Error occurred: {e}")  # Debugging
        return redirect(url_for('index'))

    finally:
        if 'cursor' in locals():
            cursor.close()



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

@app.route('/delete_member/<int:membership_id>', methods=['GET','POST'])
def delete_member(membership_id):
    """Handle member deletion."""
    if request.method == 'GET':
        # Fetch member details for confirmation
        try:
            cursor = mysql.connection.cursor()

            # Fetch member details
            cursor.execute("SELECT * FROM tbl_member_registration WHERE reg_id = %s", (membership_id,))
            member = cursor.fetchone()

            if not member:
                flash("Member not found!", "error")
                return redirect(url_for('index'))  # Redirect to homepage

            # Render confirmation page
            return render_template('Delete.html', member=member)

        except Exception as e:
            flash(f"An error occurred: {e}", "error")
            return redirect(url_for('index'))  # Redirect to homepage

        finally:
            cursor.close()

    elif request.method == 'POST':
        # Delete the member
        try:
            cursor = mysql.connection.cursor()

            # Start transaction
            mysql.connection.begin()

            # Delete member
            cursor.execute("DELETE FROM tbl_member_registration WHERE reg_id = %s", (membership_id,))

            # Commit transaction
            mysql.connection.commit()
            flash("Member deleted successfully!", "success")

        except Exception as e:
            # Rollback on error
            mysql.connection.rollback()
            flash(f"An error occurred: {e}", "error")

        finally:
            cursor.close()

        return redirect(url_for('index'))  # 
    
# 
@app.route('/delete_renewal/<int:member_reg_id>', methods=['POST'])
def delete_renewal(member_reg_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT renewal_id FROM tbl_member_renewals
            WHERE member_reg_id = %s
            ORDER BY renewal_id DESC LIMIT 1
        """, (member_reg_id,))
        
        latest_renewal = cur.fetchone()

        if latest_renewal:
            renewal_id = latest_renewal['renewal_id']
            cur.execute("DELETE FROM tbl_member_renewals WHERE renewal_id = %s", (renewal_id,))
            mysql.connection.commit()
            flash("Latest renewal entry deleted successfully!", "success")
        else:
            flash("No renewal entries found for this member.", "warning")

    except Exception as e:
        mysql.connection.rollback()
        flash(f"Error deleting renewal: {str(e)}", "danger")

    finally:
        cur.close()

    return redirect(url_for('index'))  # Redirect to the index page
    
    
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# receipt generate code
def convert_num_to_words(num):
    ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    triplets = ["", "thousand", "million", "billion", "trillion", "quadrillion", "quintillion"]

    def convert_triplet(num, tri):
        r = num // 1000
        x = (num // 100) % 10
        y = num % 100
        result = ""

        if x > 0:
            result += ones[x] + " hundred"
        if y < 20:
            result += ones[y]
        else:
            result += tens[y // 10] + ones[y % 10]

        if result:
            result += " " + triplets[tri]

        if r > 0:
            return convert_triplet(r, tri + 1) + result
        return result

    return convert_triplet(abs(num), 0).strip().capitalize() + " Rupees Only"
# 

@app.route('/renewal_receipt/<string:renewal_id>', methods=['GET'])
def renewal_receipt(renewal_id):
    data = {}

    try:
        print(f"Received renewal_id: {renewal_id}")  # Debugging Step 1

        with mysql.connection.cursor() as cursor:
            # Fetch renewal details
            cursor.execute("""
                SELECT r.*, m.mill_worker_name, m.gender, m.address, m.phone_number, 
                       m.enrollment_type, mil.mill_name
                FROM tbl_member_renewals r
                JOIN tbl_member_registration m ON r.member_reg_id = m.reg_id
                LEFT JOIN tbl_mills mil ON m.mill_name_id = mil.mill_id
                WHERE r.renewal_id = %s
            """, (renewal_id,))

            renewal = cursor.fetchone()

            if not renewal:
                flash("Renewal not found.", "error")
                return redirect(url_for('index'))  # Redirect to home

            print(f"Renewal details: {renewal}")  # Debugging Step 2

            # Fetch receipt number (rec_no) for the renewal
            cursor.execute("""
                SELECT rec_no 
                FROM tbl_reciepts 
                WHERE rec_id = %s AND rec_type = 'renewal'
            """, (renewal_id,))
            receipt = cursor.fetchone()

            print(f"Receipt details: {receipt}")  # Debugging Step 3

            # Default to renewal_id if no receipt found
            receipt_no = receipt['rec_no'] if receipt else renewal_id

            # Fetch user details (renewed by)
            cursor.execute("SELECT fname, lname FROM cm_users WHERE cm_user_id = %s", 
                           (renewal['renewed_by'],))
            user = cursor.fetchone() or {'fname': 'Unknown', 'lname': ''}

            print(f"User details: {user}")  # Debugging Step 4

            # Prepare data for the template
            data = {
                'receipt_no': receipt_no,
                'member_reg_id': renewal['member_reg_id'],
                'mill_worker_name': renewal['mill_worker_name'],
                'gender_prefix': "Mr." if renewal['gender'] == 'male' else "Mrs.",
                'enrollment_type': renewal['enrollment_type'],
                'mill_name': renewal['mill_name'],
                'address': renewal.get('address', 'Address Unavailable'),
                'phone_number': renewal.get('phone_number', 'Not available'),
                'renewal_fees': renewal['renewal_fees'],
                'delay_penalty': renewal['delay_penalty'] if renewal['delayed_renewal'] == 'yes' else 0,
                'date_renewed': renewal['date_renewed'],
                'next_from_date': renewal['nextFrom_date'],
                'next_to_date': renewal['nextTo_date'],
                'renewed_by': f"{user.get('fname', 'Unknown')} {user.get('lname', '')}",
                'amount_in_words': convert_num_to_words(
                    int(renewal['renewal_fees']) +
                    int(renewal['delay_penalty'] if renewal['delayed_renewal'] == 'yes' else 0)
                )
            }

    except Exception as e:
        print(f"Error: {e}")
        flash(f"An error occurred: {e}", "error")
        return redirect(url_for('index'))

    return render_template('Renewal_Receipt.html', **data)


# 
@app.route('/edit/<int:membership_id>', methods=['GET', 'POST'])
def edit(membership_id):
    if request.method == 'GET':
        # Fetch member details from the database
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM tbl_member_registration WHERE reg_id = %s", (membership_id,))
        member = cur.fetchone()
        cur.close()

        if not member:
            flash('Member not found', 'error')
            return redirect(url_for('member_detail', membership_id=membership_id))

        # Fetch mill names for dropdown
        cur = mysql.connection.cursor()
        cur.execute("SELECT mill_id, mill_name FROM tbl_mills ORDER BY mill_name ASC")
        mills = cur.fetchall()
        cur.close()

        return render_template('Edit.html', member=member, mills=mills)

    elif request.method == 'POST':
        # Handle form submission
        reg_id = request.form['txtReg_id']
        mhada_no = request.form['txtMhadaNo']
        enrollment_type = request.form['select_enrollment_type']
        mill_name_id = request.form.get('select_mill_name', '')
        mill_worker_name = request.form['txtMillWorkerName'].title()
        legal_hier_name = request.form['txtLegalHierName'].title()
        phone_number = request.form['txtPhoneNumber']
        email_id = request.form['txtEmail']
        address = request.form['txtAddress']
        aadhar_number = request.form['txtAadharNumber']
        pan_number = request.form['txtPANNumber']
        esic_number = request.form['txtESICNumber']
        gender = request.form['select_gender']
        age = request.form['txtAge']
        retired_resigned = request.form['select_retired_resigned']
        reg_fee = request.form['txtNewRegFees']
        pending_amt = request.form['txtPendingAmt']
        pending_penalty = request.form['txtPenalty']
        pending_from = request.form['txtPendingFrom']
        pending_to = request.form['txtPendingTo']
        donation_fee = request.form['txtDonation']
        office_fund = request.form['txtOfficeFund']
        from_date = request.form['txtFromDate']
        to_date = request.form['txtToDate']

        # Update the database
        cur = mysql.connection.cursor()
        try:
            if enrollment_type == 'domestic_worker':
                query = """
                    UPDATE tbl_member_registration 
                    SET enrollment_type = %s, mhada_no = %s, mill_worker_name = %s, legal_hier_name = %s, 
                    phone_number = %s, email_id = %s, address = %s, aadhar_number = %s, pan_number = %s, 
                    esic_number = %s, gender = %s, age = %s, retired_resigned = %s, reg_fee = %s, 
                    pending_amt = %s, pending_penalty = %s, pendingFrom = %s, pendingTo = %s, 
                    donation_fee = %s, office_fund = %s, datetime_created = %s, next_renewal_date = %s 
                    WHERE reg_id = %s
                """
                cur.execute(query, (
                    enrollment_type, mhada_no, mill_worker_name, legal_hier_name, phone_number, email_id, address,
                    aadhar_number, pan_number, esic_number, gender, age, retired_resigned, reg_fee, pending_amt,
                    pending_penalty, pending_from, pending_to, donation_fee, office_fund, from_date, to_date, reg_id
                ))
            else:
                query = """
                    UPDATE tbl_member_registration 
                    SET enrollment_type = %s, mhada_no = %s, mill_name_id = %s, mill_worker_name = %s, 
                    legal_hier_name = %s, phone_number = %s, email_id = %s, address = %s, aadhar_number = %s, 
                    pan_number = %s, esic_number = %s, gender = %s, age = %s, retired_resigned = %s, reg_fee = %s, 
                    pending_amt = %s, pending_penalty = %s, pendingFrom = %s, pendingTo = %s, donation_fee = %s, 
                    office_fund = %s, datetime_created = %s, next_renewal_date = %s 
                    WHERE reg_id = %s
                """
                cur.execute(query, (
                    enrollment_type, mhada_no, mill_name_id, mill_worker_name, legal_hier_name, phone_number, email_id,
                    address, aadhar_number, pan_number, esic_number, gender, age, retired_resigned, reg_fee, pending_amt,
                    pending_penalty, pending_from, pending_to, donation_fee, office_fund, from_date, to_date, reg_id
                ))

            mysql.connection.commit()
            flash('Member updated successfully', 'success')
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error updating member: {str(e)}', 'error')
        finally:
            cur.close()

        return redirect(url_for('member_detail', membership_id=reg_id))


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    """Change the password of the logged-in user."""
    if request.method == 'POST':
        current_password = request.form['txtCurrentPassword']
        new_password = request.form['txtNewPassword']

        # Fetch the logged-in user's ID (replace with actual logic)
        user_id = 1  # Replace with the actual user ID

        try:
            cursor = mysql.connection.cursor()

            # Fetch the current password hash
            cursor.execute("SELECT cm_password FROM cm_users WHERE cm_user_id = %s", (user_id,))
            result = cursor.fetchone()

            if result and check_password_hash(result['cm_password'], current_password):
                # Hash the new password
                hashed_new_password = generate_password_hash(new_password)

                # Update the password
                cursor.execute("UPDATE cm_users SET cm_password = %s WHERE cm_user_id = %s", (hashed_new_password, user_id))
                mysql.connection.commit()
                flash("Password changed successfully!", "success")
                return redirect(url_for('logout'))
            else:
                flash("Incorrect current password.", "error")

        except Exception as e:
            mysql.connection.rollback()
            flash(f"An error occurred: {e}", "error")
        finally:
            cursor.close()

    return render_template('Change_Password.html')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
@app.route('/office_fund/<int:membership_id>', methods=['GET', 'POST'])
def office_fund(membership_id):
    try:
        cursor = mysql.connection.cursor()

        if request.method == 'POST':
            office_fund_amount = request.form.get('txtOfficeFund', '').strip()

            if not office_fund_amount or not office_fund_amount.isdigit():
                flash("Invalid fund amount. Please enter a valid number.", "error")
                return redirect(url_for('office_fund', membership_id=membership_id))

            office_fund_amount = float(office_fund_amount)
            logged_user_id = 1  # Replace with actual logged-in user ID

            cursor.execute("START TRANSACTION")

            office_fund_id = f"ofid_{int(time.time())}"
            cursor.execute("""
                INSERT INTO tbl_office_fund (office_fund_id, member_reg_id, fund_amount, payment_accepted_by, datetime_payment_done)
                VALUES (%s, %s, %s, %s, NOW() + INTERVAL 630 MINUTE)
            """, (office_fund_id, membership_id, office_fund_amount, logged_user_id))

            cursor.execute("SELECT MAX(rec_no) AS last_receipt FROM tbl_reciepts")
            last_receipt = cursor.fetchone()['last_receipt'] or 0
            new_receipt = last_receipt + 1

            cursor.execute("""
                INSERT INTO tbl_reciepts (rec_no, rec_type, rec_id)
                VALUES (%s, %s, %s)
            """, (new_receipt, 'office_fund', office_fund_id))

            mysql.connection.commit()

            flash("Office fund submitted successfully!", "success")  # ✅ Success message
            return redirect(url_for('office_fund', membership_id=membership_id))

        cursor.execute("SELECT reg_id, mill_worker_name, gender FROM tbl_member_registration WHERE reg_id = %s", (membership_id,))
        member = cursor.fetchone()

        if not member:
            flash("Member not found.", "error")
            return redirect(url_for('index'))

        gender_prefix = "Mr." if member['gender'] == 'male' else "Mrs."

        return render_template('Office_Fund.html', gender_prefix=gender_prefix, member=member, membership_id=membership_id)

    except Exception as e:
        mysql.connection.rollback()
        flash(f"An error occurred: {e}", "error")
        return redirect(url_for('office_fund', membership_id=membership_id))

    finally:
        cursor.close()
# 
@app.route('/Account_Reg')
def account_reg():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT fname, lname, user_type, datetime_created, profile_picture_location FROM cm_users ORDER BY datetime_created DESC")
    users = cursor.fetchall()
    cursor.close()
    
    return render_template('Account_Reg.html', users=users)


@app.route('/reg_form', methods=['GET', 'POST'])
def reg_form():
    if request.method == 'GET':
        return render_template('reg_form.html')

    elif request.method == 'POST':
        # Get form data
        first_name = request.form['firstName']
        last_name = request.form['lastName']
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['userType']
        profile_pic = request.files['profilePicture']

        # Validate and process the uploaded file
        if profile_pic and allowed_file(profile_pic.filename):
            try:
                # Generate a unique filename
                timestamp = int(datetime.now().timestamp())
                filename = f"{timestamp}-{profile_pic.filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                image=Image.open(profile_pic)
                max_size=(200,200)
                image.thumbnail(max_size)
                profile_pic.save(filepath)
                image.save(filepath)

                # Hash the password
                hashed_password = generate_password_hash(password,method='pbkdf2:sha256')

                # Insert user into the database
                with mysql.connection.cursor() as cursor:
                    sql = """
                        INSERT INTO `cm_users` 
                        (`cm_user_id`, `fname`, `lname`, `cm_password`, `user_type`, `datetime_created`, `profile_picture_location`) 
                        VALUES (%s, %s, %s, %s, %s, NOW(), %s)
                    """
                    cursor.execute(sql, (email, first_name, last_name, hashed_password, user_type, filename))
                    mysql.connection.commit()

                flash("User registered successfully!", "success")
                return redirect(url_for('reg_form'))

            except Exception as e:
                mysql.connection.rollback()
                flash(f"Error registering user: {str(e)}", "danger")
                return redirect(url_for('reg_form'))

        else:
            flash("Invalid file upload. Only images are allowed.", "danger")
            return redirect(url_for('reg_form'))

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
# 
@app.route('/logout')
def logout():
    """Log out the user."""
    # Clear session or perform other logout logic
    flash("You have been logged out.", "success")
    return redirect(url_for('index'))
# 
@app.route('/view_mill', methods=['GET', 'POST'])
def view_mill():
    """View all mills in the database with search functionality and pagination."""
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        search_query = request.form.get('search_query', '').strip()

        # Pagination logic
        page = request.args.get('page', 1, type=int)
        per_page = 10  # Number of records per page
        offset = (page - 1) * per_page

        if search_query:
            cursor.execute(
                "SELECT mill_id, mill_name FROM tbl_mills WHERE mill_name LIKE %s ORDER BY datetime_added DESC LIMIT %s OFFSET %s",
                ('%' + search_query + '%', per_page, offset)
            )
        else:
            cursor.execute(
                "SELECT mill_id, mill_name FROM tbl_mills ORDER BY datetime_added DESC LIMIT %s OFFSET %s",
                (per_page, offset)
            )

        mills = cursor.fetchall()

        # Get total number of mills for pagination
        cursor.execute("SELECT COUNT(*) AS total FROM tbl_mills WHERE mill_name LIKE %s", ('%' + search_query + '%',))
        total_mills = cursor.fetchone()["total"]
        cursor.close()

        total_pages = (total_mills // per_page) + (1 if total_mills % per_page > 0 else 0)

        return render_template(
            'View_Mill.html',
            mills=mills,
            search_query=search_query,
            page=page,
            total_pages=total_pages
        )
    
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "error")
        return render_template('View_Mill.html', mills=[], search_query='')


#
@app.route('/add_mill', methods=['GET', 'POST'])
def add_mill():
    """Add a new mill to the database."""
    if request.method == 'POST':
        try:
            mill_name = request.form.get('txtMillName', '').strip()

            if not mill_name:
                flash("Mill name cannot be empty!", "error")
                return redirect(url_for('add_mill'))

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

            # Get the last mill_id from the database
            cursor.execute("SELECT mill_id FROM tbl_mills ORDER BY datetime_added DESC LIMIT 1")
            last_mill = cursor.fetchone()

            if last_mill and last_mill["mill_id"].startswith("mill_"):
                last_number = int(last_mill["mill_id"].split("_")[1])  # Extract number part
                new_mill_id = f"mill_{last_number + 1:010d}"  # Increment and format
            else:
                new_mill_id = "mill_0000000001"  # Start from mill_0000000001 if no data exists

            # Insert new mill
            query = "INSERT INTO tbl_mills (mill_id, mill_name, datetime_added) VALUES (%s, %s, NOW())"
            cursor.execute(query, (new_mill_id, mill_name))
            mysql.connection.commit()
            cursor.close()

            flash("Mill added successfully!", "success")
            return redirect(url_for('view_mill'))

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")

    return render_template('Add_Mill.html')

@app.route('/edit_profile')
def edit_profile():
    return render_template('Edit_Profile.html')

if __name__ == '__main__':
    app.run(debug=True,use_reloader=False)