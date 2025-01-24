from flask import Flask, render_template, request, redirect, url_for,session,flash
import MySQLdb.cursors
import math


# Initialize Flask app
app = Flask(__name__)

# Database configuration
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'bcs1234'
app.config['MYSQL_DB'] = 'u617101393_cmkemmd'

# Initialize MySQL connection
mysql = MySQLdb.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    database=app.config['MYSQL_DB']
)

@app.route('/')
def index():
    # Get the current page from query parameters, default is 1
    page = int(request.args.get('page', 1))
    records_per_page = 10
    offset = (page - 1) * records_per_page

    # Get total number of records
    cursor = mysql.cursor()
    cursor.execute("SELECT COUNT(*) FROM tbl_member_registration")
    total_records = cursor.fetchone()[0]
    total_pages = math.ceil(total_records / records_per_page)

    # Fetch records for the current page
    query = f"""
        SELECT reg_id, phone_number, mill_worker_name, gender, 
               aadhar_number, datetime_created, next_renewal_date
        FROM tbl_member_registration
        LIMIT {records_per_page} OFFSET {offset}
    """
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    
    # determine no of page visible
    visible_page=3
    start_page=max(1,page-visible_page//2)
    end_page=min(total_pages,start_page+visible_page)


# adjusting start page
    start_page=max(1,end_page-visible_page)
    # Render template with data and pagination info
    return render_template(
      'index.html', 
        users=data, 
        page=page, 
        total_pages=total_pages, 
        start_page=start_page, 
        end_page=end_page
    )


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # v
# membership route
@app.route('/membership')
def membership():
    return render_template('membership.html')
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # v

# Status route
@app.route('/Status')
def status():
    return render_template('Status.html')
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # v

# Advance report route
@app.route('/adv_report')
def adv_report():
    return render_template('Donation.html')

# Donation route
@app.route('/donation')
def donation():
    return render_template('Donation.html')

# office fund route
@app.route('/office-fund')
def office_fund():
    return render_template('Office_Fund.html')


# index route(BACK TO HOME)
# @app.route('/index')
# def index_to_home():
#     return render_template('index.html')
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # v


# showing individual profile route

def fetch_member_detail(reg_id):
    with mysql.cursor(cursorclass=MySQLdb.cursors.DictCursor) as cursor:  # Use DictCursor
        query = "SELECT * FROM tbl_member_registration WHERE reg_id=%s"
        cursor.execute(query, (reg_id,))
        return cursor.fetchone()


# route to view individual member profile
@app.route('/view_member/<reg_id>',methods=['GET'])
def view_member(reg_id):
    member=fetch_member_detail(reg_id)
    if not member:
            return render_template('membership.html', reg_id=reg_id)

        # return redirect (url_for('index'))
        #    return render_template('membership.html', member=member)

#  Mapping the database fields
    reg_id = member["reg_id"]
    mhada_no = member["mhada_no"] or 'Not available'
    enrollment_type = member["enrollment_type"]
    
    # Enrollment Type Handling
    if enrollment_type == 'mill_worker':
        enrollment_type_display = 'Mill Worker'
        mill_name_id = member["mill_name_id"]
        mill_name_query = "SELECT mill_name FROM tbl_mills WHERE mill_id=%s"
        cursor = mysql.cursor()
        cursor.execute(mill_name_query, (mill_name_id,))
        mill_name = cursor.fetchone()[0]
    elif enrollment_type == 'domestic_worker':
        enrollment_type_display = 'Domestic Worker (Gharelu Kamgar)'
    else:
        enrollment_type_display = 'Unknown'

    # Fetched Fields
    mill_worker_name = member["mill_worker_name"].title()
    legal_hier_name = member["legal_hier_name"] or 'No Legal Hier'
    address = member["address"] or 'Address Unavailable'
    phone_number = member["phone_number"] or 'Not available'
    email_id = member["email_id"] or 'Not available'
    aadhar_number = member["aadhar_number"] or 'Not available'
    pan_number = member["pan_number"] or 'Not available'
    esic_number = member["esic_number"] or 'Not available'
    gender = member["gender"].capitalize() if member["gender"] else 'Not available'
    age = member["age"]
    retired_resigned = member["retired_resigned"].title() or 'Not Available'
    reg_fee = member["reg_fee"] or 0
    pending_amt = member["pending_amt"] or 0
    donation_fee = member["donation_fee"] or 0
    office_fund = member["office_fund"] or 0
    reg_from_date = member["reg_from_date"]
    next_renewal_date = member["next_renewal_date"]
    
    return render_template(
        'membership.html',
        reg_id=reg_id,
        mhada_no=mhada_no,
        enrollment_type=enrollment_type_display,
        mill_name=mill_name if enrollment_type == 'mill_worker' else None,
        mill_worker_name=mill_worker_name,
        legal_hier_name=legal_hier_name,
        address=address,
        phone_number=phone_number,
        email_id=email_id,
        aadhar_number=aadhar_number,
        pan_number=pan_number,
        esic_number=esic_number,
        gender=gender,
        age=age,
        retired_resigned=retired_resigned,
        reg_fee=reg_fee,
        pending_amt=pending_amt,
        donation_fee=donation_fee,
        office_fund=office_fund,
        reg_from_date=reg_from_date,
        next_renewal_date=next_renewal_date
    )
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # v
# route to Renew_Membership
# @app.route('/renew', methods=['GET', 'POST'])
# def renew_membership():
#     # Fetch membership_id from session
#     membership_id = session.get('reg_id')

#     if not membership_id:
#         return "Membership ID not found in session", 400

#     # Fetch member details from the database
#     cur = mysql.connection.cursor()
#     cur.execute("SELECT mill_worker_name, reg_id FROM tbl_member_registration WHERE reg_id = %s", (membership_id,))
#     member_details = cur.fetchone()
#     cur.close()

#     if not member_details:
#         return f"No details found for membership ID: {membership_id}", 404

#     name = member_details[0]  # mill_worker_name
#     reg_id = member_details[1]  # reg_id

#     # Handle POST request
#     if request.method == 'POST':
#         renewal_fees = request.form.get('renewal_fees')
#         next_from_date = request.form.get('next_from_date')
#         next_to_date = request.form.get('next_to_date')
#         delay_in_renewal = request.form.get('delay_in_renewal')
#         renewal_penalty = request.form.get('renewal_penalty')

#         # Insert renewal data into the database
#         cur = mysql.connection.cursor()
#         cur.execute("""
#             INSERT INTO tbl_member_renewals (membership_id, renewal_fees, next_from_date, next_to_date, delay_in_renewal, penalty)
#             VALUES (%s, %s, %s, %s, %s, %s)
#         """, (membership_id, renewal_fees, next_from_date, next_to_date, delay_in_renewal, renewal_penalty))

#         mysql.connection.commit()
#         cur.close()

#     return render_template('Renew_Membership.html', name=name, reg_id=reg_id)
# unworking route
@app.route('/renew_membership', methods=['GET', 'POST'])
def renew_membership():
    membership_id = request.args.get('membership_id')
    if not membership_id:
        flash('Membership ID not provided', 'error')
        return redirect(url_for('home'))

    # Fetch member details
    member = MemberRegistration.query.filter_by(reg_id=membership_id).first()
    if not member:
        flash('Membership not found', 'error')
        return redirect(url_for('home'))

    gender_prefix = "Mr." if member.gender.lower() == "male" else "Mrs."
    last_renewed_date = member.last_renewed_date.strftime('%d-%B-%Y') if member.last_renewed_date else "Not Yet Renewed"
    next_renewal_date = member.next_renewal_date.strftime('%Y-%m-%d')
    current_date = datetime.now().date()

    if request.method == 'POST':
        # Get form data
        renewal_fees = int(request.form.get('txtRenewalFees'))
        next_from_date = datetime.strptime(request.form.get('txtNextRenewalFrom'), '%Y-%m-%d').date()
        next_to_date = datetime.strptime(request.form.get('txtNextRenewalTo'), '%Y-%m-%d').date()
        delay_in_renewal = request.form.get('select_delayInRenew')
        renewal_penalty = int(request.form.get('txtRenewalPenalty'))

        delay_penalty = 50 if current_date > member.next_renewal_date else 0
        delayed_renewal = "yes" if delay_penalty > 0 else "no"

        # Create renewal entry
        renewal_id = f"reid_{int(time.time())}"
        renewal = MemberRenewals(
            renewal_id=renewal_id,
            member_reg_id=membership_id,
            renewal_fees=renewal_fees,
            delayed_renewal=delay_in_renewal,
            delay_penalty=renewal_penalty,
            renewal_date=member.next_renewal_date,
            renewed_by=session.get('user_id', 'system'),
            date_renewed=datetime.now(),
            next_from_date=next_from_date,
            next_to_date=next_to_date,
        )

        # Update member's next renewal date
        member.last_renewed_date = member.next_renewal_date
        member.next_renewal_date = next_to_date

        try:
            db.session.add(renewal)
            db.session.commit()

            # Create a receipt
            last_receipt = db.session.query(db.func.max(Receipts.rec_no)).scalar() or 0
            new_receipt = Receipts(
                rec_no=last_receipt + 1,
                rec_type='renewal',
                rec_id=renewal_id
            )
            db.session.add(new_receipt)
            db.session.commit()

            flash("Renewal processed successfully!", "success")
            return redirect(url_for('view_renewals', membership_id=membership_id))

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "error")
            return redirect(url_for('renew_membership', membership_id=membership_id))

    return render_template('renew_membership.html', member=member, gender_prefix=gender_prefix, last_renewed_date=last_renewed_date, next_renewal_date=next_renewal_date)

if __name__ == '__main__':
    app.run(debug=True)