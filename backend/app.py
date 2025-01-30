from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_mysqldb import MySQL
import MySQLdb.cursors
import math
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
import subprocess
from io import BytesIO
import uuid
import logging
import time


app = Flask(__name__)
app.secret_key = "your_secret_key"

# Flask-MySQLdb configuration
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'bcs1234'
app.config['MYSQL_DB'] = 'u617101393_cmkemmd'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'  # Use dictionary-like results

mysql = MySQL(app)

@app.route('/')
def index():
    """Render the index page with paginated member data."""
    page = int(request.args.get('page', 1))
    records_per_page = 10
    offset = (page - 1) * records_per_page

    try:
        cursor = mysql.connection.cursor()

        # Fetch total records
        cursor.execute("SELECT COUNT(*) FROM tbl_member_registration")
        total_records = cursor.fetchone()['COUNT(*)']
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
        cursor.close()
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# NEW MEMBER MEMBER REGISTRATION
@app.route('/new_member_registration', methods=['GET', 'POST'])
def new_member_registration():
    """Handle new member registration."""
    if request.method == 'GET':
        try:
            cursor = mysql.connection.cursor()  # Assumes mysql.connection is properly initialized
            cursor.execute("SELECT mill_id, mill_name FROM tbl_mills ORDER BY mill_name ASC")
            mill_names = cursor.fetchall()
            return render_template('new_member_registration.html', mill_names=mill_names)
        except Exception as e:
            flash(f"Error fetching mill names: {e}", "error")
            return render_template('new_member_registration.html', mill_names=[])
        finally:
            cursor.close()

    elif request.method == 'POST':
        form_data = request.form.to_dict()  # Convert ImmutableMultiDict to regular dict

        # Extract form data
        reg_id = form_data.get('txtReg_id')
        mhada_no = form_data.get('txtMhadaNo')
        enrollment_type = form_data.get('select_enrollment_type')
        mill_name_id = form_data.get('select_mill_name', '')
        mill_worker_name = form_data.get('txtMillWorkerName')
        legal_hier_name = form_data.get('txtLegalHierName', '')
        phone_number = form_data.get('txtPhoneNumber')
        email = form_data.get('txtEmail', '')
        address = form_data.get('txtAddress', '')
        aadhar_number = form_data.get('txtAadharNumber', '')
        pan_number = form_data.get('txtPANNumber', '')
        esic_number = form_data.get('txtESICNumber', '')
        gender = form_data.get('select_gender')
        age = form_data.get('txtAge')
        retired_resigned = form_data.get('select_retired_resigned')
        new_reg_fees = form_data.get('txtNewRegFees')
        from_date = form_data.get('txtFromDate')
        to_date = form_data.get('txtToDate')
        pending_amt = form_data.get('txtPendingAmt', '0')
        penalty = form_data.get('txtPenalty', '0')
        pending_from = form_data.get('txtPendingFrom', '2012')
        pending_to = form_data.get('txtPendingTo', '')
        donation = form_data.get('txtDonation', '0')
        office_fund = form_data.get('txtOfficeFund', '0')

        # Validate required fields
        required_fields = {
            "Registration ID": reg_id,
            "Mill Worker Name": mill_worker_name,
            "Gender": gender,
            "Age": age,
            "Retired/Resigned Status": retired_resigned,
            "New Registration Fees": new_reg_fees,
            "From Date": from_date,
            "To Date": to_date,
        }
        for field, value in required_fields.items():
            if not value.strip():
                flash(f"{field} is required.", "error")
                return redirect(url_for('new_member_registration'))

        # Validate numeric fields (convert to float where applicable)
        numeric_fields = {
            "Age": age,
            "New Registration Fees": new_reg_fees,
            "Penalty": penalty,
            "Pending Amount": pending_amt,
            "Donation": donation,
            "Office Fund": office_fund,
        }
        for field, value in numeric_fields.items():
            if value and not value.replace('.', '', 1).isdigit():  # Allow decimal numbers as well
                flash(f"{field} must be a valid number.", "error")
                return redirect(url_for('new_member_registration'))

        # Validate date fields
        try:
            datetime.strptime(from_date, "%Y-%m-%d")
            datetime.strptime(to_date, "%Y-%m-%d")
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", "error")
            return redirect(url_for('new_member_registration'))

        # Check if the registration ID already exists
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT reg_id FROM tbl_member_registration WHERE reg_id = %s", (reg_id,))
            if cursor.fetchone():
                flash(f"Member already exists with Registration ID '{reg_id}'. Try a different ID.", "error")
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
            # Assuming `1` is the logged-in user ID for now; replace with actual user ID
            values = (
                reg_id, mhada_no, enrollment_type, mill_name_id, mill_worker_name, legal_hier_name,
                phone_number, email, address, aadhar_number, pan_number, esic_number, gender, age,
                retired_resigned, new_reg_fees, pending_amt, penalty, pending_from, pending_to,
                donation, office_fund, from_date, 1  # Replace `1` with the logged-in user ID
            )
            cursor.execute(query, values)
            mysql.connection.commit()
            flash("Member registered successfully!", "success")
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error inserting member: {e}", "error")
            print(f"Error: {e}")  # Print the error to the console
        finally:
            cursor.close()

        return redirect(url_for('new_member_registration'))

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 


@app.route('/status')
def status():
    """Render the status page with system statistics."""
    try:
        cursor = mysql.connection.cursor()

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
        session_count = cursor.fetchone()['session_count'] or 0

        # Fetch new registrations today
        cursor.execute("""
            SELECT COUNT(*) AS reg_count
            FROM tbl_member_registration
            WHERE DATE(datetime_created) = CURDATE()
        """)
        reg_count = cursor.fetchone()['reg_count'] or 0

        # Fetch renewals today
        cursor.execute("""
            SELECT COUNT(*) AS renewal_count
            FROM tbl_member_renewals
            WHERE DATE(date_renewed) = CURDATE()
        """)
        renewal_count = cursor.fetchone()['renewal_count'] or 0

        # Fetch pending renewals today
        cursor.execute("""
            SELECT COUNT(*) AS pen_renewal_count
            FROM tbl_member_renewals
            WHERE DATE(renewal_due_date) = CURDATE() AND status = 'pending'
        """)
        pen_renewal_count = cursor.fetchone()['pen_renewal_count'] or 0

        # Fetch total registrations
        cursor.execute("""
            SELECT
            formatted_datetime_now=formatted_datetime_now,
            total_earning=total_earning,
            total_billed_earning=total_billed_earning,
            session_count=session_count,
            reg_count=reg_count,
            renewal_count=renewal_count,
            pen_renewal_count=pen_renewal_count,
            total_reg_count=total_reg_count,
            total_renewal_count=total_renewal_count,
            total_donation_count=total_donation_count
       """ )

    except Exception as e:
        logging.error(f"Error fetching status data: {e}")
        return "An error occurred while fetching status data.", 500

    finally:
        cursor.close()
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

@app.route('/adv_report')
def adv_report():
    """Render the advanced report page."""
    return render_template('adv_report.html')
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

        # Fetch mill name if applicable
        mill_name = None
        if member['enrollment_type'] == 'mill_worker':
            cursor.execute("SELECT mill_name FROM tbl_mills WHERE mill_id = %s", (member['mill_name_id'],))
            mill_name_result = cursor.fetchone()
            mill_name = mill_name_result['mill_name'] if mill_name_result else "Unknown Mill"

        return render_template('membership.html', member=member, mill_name=mill_name)

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
# @app.route('/print_renewal')
# def print_renewal():
#     render_template('Print_Renewal.html')
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

# @app.route('/delete_renewal/<int:membership_id>',methods=['POST'])
# def delete(membership_id):
#     try:
#         ...
#         flash("Member deleted successfully!", "success")
#         return redirect(url_for('index'))  # Add this line
#     except Exception as e:
#         flash(f"An error occurred: {e}", "error")
#         return redirect(url_for('index'))  # Add this line
#     finally:
#         cursor.close()
    




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
    """Convert a number to words (basic implementation)."""
    units = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    teens = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

    if num == 0:
        return "zero"
    if num < 10:
        return units[num]
    if 10 <= num < 20:
        return teens[num - 10]
    if 20 <= num < 100:
        return tens[num // 10] + (" " + units[num % 10] if num % 10 != 0 else "")
    if 100 <= num < 1000:
        return units[num // 100] + " hundred" + (" " + convert_num_to_words(num % 100) if num % 100 != 0 else "")
    return "number too large"


@app.route('/renewal_receipt/<string:renewal_id>', methods=['GET'])
def renewal_receipt(renewal_id):
    data = {}
    try:
        cursor = mysql.connection.cursor()

        # Fetch renewal details
        cursor.execute("""
            SELECT r.*, m.mill_worker_name, m.gender, m.address, m.phone_number, m.enrollment_type, mil.mill_name
            FROM tbl_member_renewals r
            JOIN tbl_member_registration m ON r.member_reg_id = m.reg_id
            LEFT JOIN tbl_mills mil ON m.mill_name_id = mil.mill_id
            WHERE r.renewal_id = %s
        """, (renewal_id,))
        renewal = cursor.fetchone()

        if not renewal:
            flash("Renewal not found.", "error")
            return redirect('Error.html', message="Renewal not found for this ID.")

        # Fetch receipt number (rec_no)
        cursor.execute("SELECT rec_no FROM tbl_reciepts WHERE rec_id = %s AND rec_type = 'renewal'", (renewal_id,))
        receipt = cursor.fetchone()
        receipt_no = receipt['rec_no'] if receipt else renewal_id  # Default to renewal_id if no receipt found

        # Fetch user details (renewed by)
        cursor.execute("SELECT fname, lname FROM cm_users WHERE cm_user_id = %s", (renewal['renewed_by'],))
        user = cursor.fetchone()

        # Prepare data for the template
        data = {
            'receipt_no': receipt_no,
            'member_reg_id': renewal['member_reg_id'],
            'mill_worker_name': renewal['mill_worker_name'],
            'gender_prefix': "Mr." if renewal['gender'] == 'male' else "Mrs.",
            'enrollment_type': renewal['enrollment_type'],
            'mill_name': renewal['mill_name'],
            'address': renewal['address'] or 'Address Unavailable',
            'phone_number': renewal['phone_number'] or 'Not available',
            'renewal_fees': renewal['renewal_fees'],
            'delay_penalty': renewal['delay_penalty'] if renewal['delayed_renewal'] == 'yes' else 0,
            'date_renewed': renewal['date_renewed'],
            'next_from_date': renewal['nextFrom_date'],
            'next_to_date': renewal['nextTo_date'],
            'renewed_by': f"{user['fname']} {user['lname']}" if user else 'Unknown',
            'amount_in_words': convert_num_to_words(
                int(renewal['renewal_fees']) +
                int(renewal['delay_penalty'] if renewal['delayed_renewal'] == 'yes' else 0)
            )
        }

    except Exception as e:
        flash(f"An error occurred: {e}", "error")
        return render_template('error.html', message="An error occurred while fetching renewal details.")
    finally:
        cursor.close()

    return render_template('Renewal_Receipt.html', **data)


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



@app.route('/logout')
def logout():
    """Log out the user."""
    # Clear session or perform other logout logic
    flash("You have been logged out.", "success")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)