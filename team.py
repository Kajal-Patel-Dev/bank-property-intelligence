from flask import Blueprint, render_template, request, redirect, session, Response
from werkzeug.utils import secure_filename
from flask import send_file
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from flask import flash
import os
import csv
import io

from config.db import mysql

team = Blueprint('team', __name__)

def add_activity(user_id, action):

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        INSERT INTO activity_log
        (user_id, action)
        VALUES(%s,%s)
        """,
        (user_id, action)
    )

    mysql.connection.commit()


@team.route('/team/export_pdf')
def export_pdf():

    cursor = mysql.connection.cursor()


    cursor.execute("""
        SELECT
            property_name,
            property_type,
            district,
            status,
            estimated_cost,
            mobile,
            contact_person_name

        FROM properties

        ORDER BY id DESC
    """)


    properties = cursor.fetchall()


    filename = "property_report.pdf"


    doc = SimpleDocTemplate(filename)



    data = [

        [
            "Property",
            "Type",
            "District",
            "Status",
            "Cost",
            "Mobile",
            "Contact"
        ]

    ]


    for p in properties:

        data.append(
            [
                p[0],
                p[1],
                p[2],
                p[3],
                str(p[4]),
                p[5],
                p[6]
            ]
        )



    table = Table(data)



    table.setStyle(

        TableStyle([


            (
            'BACKGROUND',
            (0,0),
            (-1,0),
            colors.HexColor("#0f172a")
            ),


            (
            'TEXTCOLOR',
            (0,0),
            (-1,0),
            colors.white
            ),


            (
            'GRID',
            (0,0),
            (-1,-1),
            0.5,
            colors.grey
            ),


            (
            'ALIGN',
            (0,0),
            (-1,-1),
            'CENTER'
            )

        ])

    )


    doc.build([table])



    return send_file(
        filename,
        as_attachment=True
    )

@team.route('/export-reports')
def export_reports():

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT
        property_name,
        property_type,
        district,
        status,
        city,
        village,
        estimated_cost,
        mobile,
        created_by,
        contact_person_name

        FROM properties

        ORDER BY id DESC
    """)

    properties = cursor.fetchall()


    output = io.StringIO()

    writer = csv.writer(output)


    writer.writerow([
        "Property",
        "Type",
        "District",
        "City",
        "Village",
        "Cost",
        "Mobile",
        "Status",
        "Added By"
    ])


    for p in properties:

        writer.writerow([
            p[0],
            p[1],
            p[2],
            p[4],
            p[5],
            p[6],
            p[7],
            p[3],
            p[9]
        ])



    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
        "Content-Disposition":
        "attachment;filename=property_reports.csv"
        }
    )


@team.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT id, email FROM users
            WHERE email=%s AND password=%s
        """, (email, password))

        user = cursor.fetchone()

        if user:
            session['user_id'] = user[0]   # 🔥 THIS IS MOST IMPORTANT
            return redirect('/team/my_reports')
        else:
            return "Invalid login"

    return render_template('login.html')




@team.route('/team/add_property', methods=['GET', 'POST'])
def add_property():

    if request.method == 'POST':

        property_type = request.form['property_type']
        property_name = request.form['property_name']
        contact_person_name = request.form['contact_person_name']
        mobile = request.form['mobile']
        district = request.form['district']
        city = request.form['city']
        village = request.form['village']
        estimated_cost = request.form['estimated_cost']
        map_location = request.form['map_location']
        user_id = session.get('user_id')


        photo = request.files['photo']
        filename = secure_filename(photo.filename)
        photo.save(os.path.join('static/uploads', filename))
        cursor = mysql.connection.cursor()

        query =  """ INSERT INTO properties (property_type, property_name, contact_person_name, mobile, district, city, village,
        estimated_cost, map_location, photo,created_by)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) """
        values = ( property_type,  property_name,  contact_person_name,    mobile,   district, city,  village, estimated_cost, map_location,  filename,user_id)

        cursor.execute(query, values)
        mysql.connection.commit()

        add_activity(
            session.get('user_id'),
            "New property added : " + property_name
        )


        return redirect('/agent/search_property')

    return render_template('team/add_property.html',role='team')


@team.route('/team/properties')
def properties():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM properties ORDER BY id  ASC")
    properties = cursor.fetchall()
    
    return render_template('team/properties.html',role='team',properties=properties)


@team.route('/team/edit_property/<int:id>', methods=['GET', 'POST'])
def edit_property(id):
    cursor = mysql.connection.cursor()
    if request.method == 'POST':
        property_name = request.form['property_name']
        estimated_cost = request.form['estimated_cost']
        cursor.execute( ''' UPDATE properties
            SET property_name=%s,
            estimated_cost=%s
            WHERE id=%s ''',(property_name, estimated_cost, id) )

        mysql.connection.commit()

        add_activity(
            session.get('user_id'),
            "Property updated : " + property_name
        )

        return redirect('/team/properties')

    cursor.execute( "SELECT * FROM properties WHERE id=%s",(id,) )
    property = cursor.fetchone()
    return render_template('team/edit_property.html',role='team',property=property)


@team.route('/team/delete-property/<int:id>')
def delete_property(id):

    cursor = mysql.connection.cursor()

    # pehle property ka naam nikal lo
    cursor.execute(
        """
        SELECT property_name
        FROM properties
        WHERE id=%s
        """,
        (id,)
    )

    prop = cursor.fetchone()


    # agar property nahi mili
    if prop is None:
        return redirect('/team/properties')


    property_name = prop[0]


    # delete
    cursor.execute(
        """
        DELETE FROM properties
        WHERE id=%s
        """,
        (id,)
    )


    mysql.connection.commit()



    # activity log
    add_activity(
        session.get('user_id'),
        "Property deleted : " + property_name
    )



    return redirect('/team/properties')




@team.route('/team/profile', methods=['GET','POST'])
def team_profile():

    cursor = mysql.connection.cursor()

    user_id = session.get('user_id')


    if not user_id:

        return """
        <div style="
        text-align:center;
        margin-top:100px;
        font-family:Arial">

        <h2>Profile Not Found</h2>

        <p>Please login again.</p>

        </div>
        """


    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        mobile = request.form['mobile']


        cursor.execute("""
        UPDATE users
        SET name=%s,
            email=%s,
            mobile=%s
        WHERE id=%s
        """,
        (
            name,
            email,
            mobile,
            user_id
        ))


        mysql.connection.commit()


        flash("Profile Updated Successfully!", "success")

        return redirect('/team/profile')




    cursor.execute("""
    SELECT *
    FROM users
    WHERE id=%s
    """,
    (user_id,))


    user = cursor.fetchone()



    if user is None:

        return """
        <div style="
        text-align:center;
        margin-top:100px;
        font-family:Arial">

        <h2>Profile Not Found</h2>

        <p>No user record available.</p>

        </div>
        """



    return render_template(
        'team/profile.html',
        role='team',
        user=user
    )


@team.route('/team/my_reports')
def my_reports():
 cursor = mysql.connection.cursor()

# Total Properties
 cursor.execute("""
    SELECT COUNT(*)
    FROM properties
""")
 total_properties = cursor.fetchone()[0]


# Residential
 cursor.execute("""
    SELECT COUNT(*)
    FROM properties
    WHERE property_type='Residential'
""")
 residential = cursor.fetchone()[0]


# Commercial
 cursor.execute("""
    SELECT COUNT(*)
    FROM properties
    WHERE property_type='Commercial'
""")
 commercial = cursor.fetchone()[0]


# Industrial
 cursor.execute("""
    SELECT COUNT(*)
    FROM properties
    WHERE property_type='Industrial'
""")
 industrial = cursor.fetchone()[0]


# Properties List
 cursor.execute("""
    SELECT
        property_name,
        property_type,
        district,
        status,
        city,
        village,
        estimated_cost,
        mobile,
        photo,
        map_location,
        created_by,
        contact_person_name

    FROM properties

    ORDER BY id DESC
""")

 properties = cursor.fetchall()


 return render_template(
    'team/my_reports.html',
    role='team',
    total_properties=total_properties,
    residential=residential,
    commercial=commercial,
    industrial=industrial,
    properties=properties
)


@team.route('/team/dashboard')
def dashboard():

    cursor = mysql.connection.cursor()


    # total
    cursor.execute("SELECT COUNT(*) FROM properties")
    total_properties = cursor.fetchone()[0]



    # residential
    cursor.execute("""
    SELECT COUNT(*) 
    FROM properties
    WHERE property_type='Residential'
    """)
    residential = cursor.fetchone()[0]



    # commercial
    cursor.execute("""
    SELECT COUNT(*) 
    FROM properties
    WHERE property_type='Commercial'
    """)
    commercial = cursor.fetchone()[0]



    # land
    cursor.execute("""
    SELECT COUNT(*) 
    FROM properties
    WHERE property_type='Land'
    """)
    land = cursor.fetchone()[0]




    # status

    cursor.execute("""
    SELECT COUNT(*) FROM properties
    WHERE status='Available'
    """)
    available = cursor.fetchone()[0]


    cursor.execute("""
    SELECT COUNT(*) FROM properties
    WHERE status='Pending'
    """)
    pending = cursor.fetchone()[0]


    cursor.execute("""
    SELECT COUNT(*) FROM properties
    WHERE status='Sold'
    """)
    sold = cursor.fetchone()[0]




    # district chart

    cursor.execute("""
    SELECT district, COUNT(*)
    FROM properties
    GROUP BY district
    """)

    district_data = cursor.fetchall()


    district_labels = []

    district_counts = []


    for row in district_data:

        district_labels.append(row[0])
        district_counts.append(row[1])






    cursor.execute("""
    SELECT 
    property_name,
    property_type,
    district,
    status
    FROM properties
    ORDER BY id DESC
    """)


    properties = cursor.fetchall()

    cursor.execute("""
    SELECT title,message,created_at
    FROM notifications
    ORDER BY id DESC
    LIMIT 5
    """)

    notifications = cursor.fetchall()

    cursor.execute("""
    SELECT action,created_at
    FROM activity_log
    ORDER BY id DESC
    LIMIT 5
    """)

    activities = cursor.fetchall()

    # CURRENT MONTH PROPERTY COUNT
    cursor.execute("""
    SELECT COUNT(*)
    FROM properties
    WHERE MONTH(created_at)=MONTH(CURDATE())
    AND YEAR(created_at)=YEAR(CURDATE())
    """)

    current_month = cursor.fetchone()[0]

    # LAST MONTH PROPERTY COUNT
    cursor.execute("""
    SELECT COUNT(*)
    FROM properties
    WHERE MONTH(created_at)=MONTH(DATE_SUB(CURDATE(),INTERVAL 1 MONTH))
    AND YEAR(created_at)=YEAR(DATE_SUB(CURDATE(),INTERVAL 1 MONTH))
    """)

    last_month = cursor.fetchone()[0]

    # GROWTH CALCULATION

    if last_month > 0:

        property_growth = round(
            ((current_month - last_month) / last_month) * 100,
            1
        )

    else:

        property_growth = 100


    return render_template(
        'team/dashboard.html',
        role='team',

        total_properties=total_properties,
        property_growth=property_growth,
        residential=residential,

        commercial=commercial,

        land=land,


        available=available,

        pending=pending,

        sold=sold,


        district_labels=district_labels,

        district_counts=district_counts,
        activities=activities,

        properties=properties,
        notifications=notifications
    )