from flask import Blueprint, render_template,request,redirect
from flask import session
from flask_login import current_user
from config.db import mysql

admin = Blueprint('admin', __name__)

@admin.route('/admin/dashboard')
def admin_dashboard():

    cursor = mysql.connection.cursor()


    # Total Properties
    cursor.execute(
        "SELECT COUNT(*) FROM properties"
    )
    total_properties = cursor.fetchone()[0]



    # Team Members
    cursor.execute(
        "SELECT COUNT(*) FROM users WHERE role='Team Member'"
    )
    total_team = cursor.fetchone()[0]



    # Agents
    cursor.execute(
        "SELECT COUNT(*) FROM users WHERE role='Agent'"
    )
    total_agents = cursor.fetchone()[0]



    # Pending
    cursor.execute(
        "SELECT COUNT(*) FROM comments WHERE status='Pending'"
    )
    pending = cursor.fetchone()[0]



    # Recent Properties

    cursor.execute(
        """
        SELECT property_name,
               property_type,
               district
        FROM properties
        ORDER BY id DESC
        LIMIT 10
        """
    )

    properties = cursor.fetchall()



    # Status

    cursor.execute(
        "SELECT COUNT(*) FROM comments WHERE status='Acquire'"
    )
    acquire = cursor.fetchone()[0]


    cursor.execute(
        "SELECT COUNT(*) FROM comments WHERE status='Sell'"
    )
    sell = cursor.fetchone()[0]


    cursor.execute(
        "SELECT COUNT(*) FROM comments WHERE status='Not Suitable'"
    )
    not_suitable = cursor.fetchone()[0]





    # District Chart

    cursor.execute("""
    SELECT district,COUNT(*)
    FROM properties
    GROUP BY district
    """)


    district_data = cursor.fetchall()


    district_labels=[
        row[0] for row in district_data
    ]


    district_counts=[
        row[1] for row in district_data
    ]






    # MONTHLY PROPERTY GROWTH


    try:

        cursor.execute("""
        SELECT COUNT(*)
        FROM properties
        WHERE MONTH(created_at)=MONTH(CURRENT_DATE())
        AND YEAR(created_at)=YEAR(CURRENT_DATE())
        """)

        current_month = cursor.fetchone()[0]



        cursor.execute("""
        SELECT COUNT(*)
        FROM properties
        WHERE MONTH(created_at)=MONTH(CURRENT_DATE() - INTERVAL 1 MONTH)
        AND YEAR(created_at)=YEAR(CURRENT_DATE() - INTERVAL 1 MONTH)
        """)


        last_month = cursor.fetchone()[0]



        if last_month > 0:

            property_growth = round(
                ((current_month-last_month)
                /last_month)*100,
                1
            )

        else:

            property_growth = 0



    except:

        property_growth = 0

    admin_id = session.get("user_id")
    cursor.execute("""
       SELECT title,message,created_at
       FROM notifications
       WHERE user_id=%s
       ORDER BY created_at DESC
       LIMIT 10
       """,
                   (admin_id,))

    notifications = cursor.fetchall()

    return render_template(

        'admin/dashboard.html',

        role='admin',

        total_properties=total_properties,

        total_team=total_team,

        total_agents=total_agents,

        pending=pending,


        acquire=acquire,

        sell=sell,

        not_suitable=not_suitable,


        properties=properties,


        district_labels=district_labels,

        district_counts=district_counts,


        property_growth=property_growth,
        notifications=notifications
    )


@admin.route('/admin/comments')
def comments():
    cursor = mysql.connection.cursor()
    cursor.execute('''  SELECT properties.property_name,comments.status,comments.comment,comments.created_at
        FROM comments
        JOIN properties
        ON comments.property_id = properties.id''')
    comments = cursor.fetchall()
    return render_template('admin/comments.html',role='admin',comments=comments)

@admin.route('/admin/reports')
def reports():

    cursor = mysql.connection.cursor()

    try:
        # KPI
        cursor.execute("SELECT COUNT(*) FROM properties")
        total_properties = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM comments WHERE status='Acquire'")
        acquire = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM comments WHERE status='Sell'")
        sell = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM comments WHERE status='Pending'")
        pending = cursor.fetchone()[0]

        # District wise
        cursor.execute("""
            SELECT district, COUNT(*)
            FROM properties
            GROUP BY district
            ORDER BY COUNT(*) DESC
        """)
        district_report = cursor.fetchall()

        # Status per district (REAL DATA)
        cursor.execute("""
            SELECT 
                p.district,
                SUM(CASE WHEN c.status='Acquire' THEN 1 ELSE 0 END),
                SUM(CASE WHEN c.status='Sell' THEN 1 ELSE 0 END),
                SUM(CASE WHEN c.status='Pending' THEN 1 ELSE 0 END)
            FROM comments c
            JOIN properties p ON c.property_id = p.id
            GROUP BY p.district
        """)
        status_data = cursor.fetchall()

        return render_template(
            'admin/reports.html',
            role='admin',
            total_properties=total_properties,
            acquire=acquire,
            sell=sell,
            pending=pending,
            district_report=district_report,
            status_data=status_data
        )

    finally:
        cursor.close()



@admin.route('/admin/edit-property/<int:id>', methods=['GET', 'POST'])
def edit_property(id):

    cursor = mysql.connection.cursor()

    if request.method == 'POST':

        property_name = request.form['property_name']
        property_type = request.form['property_type']
        district = request.form['district']
        city = request.form['city']
        village = request.form['village']
        estimated_cost = request.form['estimated_cost']
        mobile = request.form['mobile']
        map_location = request.form['map_location']
        contact_person_name = request.form['contact_person_name']

        cursor.execute("""
            UPDATE properties
            SET property_name=%s,
                property_type=%s,
                district=%s,
                city=%s,
                village=%s,
                estimated_cost=%s,
                mobile=%s,
                map_location=%s,
                contact_person_name=%s
            WHERE id=%s
        """, (
            property_name,
            property_type,
            district,
            city,
            village,
            estimated_cost,
            mobile,
            map_location,
            contact_person_name,
            id
        ))

        mysql.connection.commit()
        return redirect('/admin/all_properties')

    cursor.execute(
        "SELECT * FROM properties WHERE id=%s",
        (id,)
    )

    property = cursor.fetchone()

    return render_template(
        'admin/edit_property.html',
        property=property,
        role='admin'
    )


@admin.route('/admin/team_members')
def team_members():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users" )
    users = cursor.fetchall()
    return render_template(  'admin/team_members.html', role='admin', users=users   )


@admin.route('/admin/add_team_member',methods=['GET', 'POST'])
def add_team_member():
    cursor = mysql.connection.cursor()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        mobile = request.form['mobile']
        password = request.form['password']
        role = request.form['role']
        status="Active"
        cursor.execute('''INSERT INTO users(name, email, mobile, password, role,status)
                 VALUES(%s,%s,%s,%s,%s,%s)   ''', (name, email, mobile, password, role,status) )
        mysql.connection.commit()
        return redirect('/admin/team_members')
    return render_template('admin/add_team_member.html' ,role='admin'  )


@admin.route('/admin/delete_user/<int:id>')
def delete_user(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM users WHERE id=%s",(id,)   )
    mysql.connection.commit()
    return redirect('/admin/team_members',role='admin')


@admin.route('/admin/edit_user/<int:id>',methods=['GET', 'POST'])
def edit_user(id):
    cursor = mysql.connection.cursor()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        mobile = request.form['mobile']
        role = request.form['role']
        cursor.execute( ''' UPDATE users SET name=%s, email=%s,mobile=%s,role=%s WHERE id=%s ''', (name, email, mobile, role, id))
        mysql.connection.commit()
        return redirect('/admin/team_members')
    cursor.execute("SELECT * FROM users WHERE id=%s",  (id,))
    user = cursor.fetchone()
    return render_template('admin/edit_user.html',user=user ,role='admin')


@admin.route('/admin/analytics')
def analytics():
    cursor = mysql.connection.cursor()

    # ================= STATUS COUNTS =================
    cursor.execute(
        "SELECT COUNT(*) FROM properties"
    )
    total_properties = cursor.fetchone()[0]


    cursor.execute("SELECT COUNT(*) FROM comments WHERE status='Acquire'")
    acquire = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM comments WHERE status='Pending'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM comments WHERE status='Sell'")
    sell = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM comments WHERE status='Not Suitable'")
    not_suitable = cursor.fetchone()[0]


    # ================= DISTRICT WISE DATA =================
    cursor.execute("""
        SELECT district, COUNT(*)
        FROM properties
        GROUP BY district
        ORDER BY COUNT(*) DESC
    """)
    district_data = cursor.fetchall()

    district_labels = [row[0] for row in district_data]
    district_counts = [row[1] for row in district_data]


    # ================= MONTHLY DATA =================
    cursor.execute("""
        SELECT 
            DATE_FORMAT(created_at, '%Y-%m') AS month,
            COUNT(*)
        FROM properties
        WHERE created_at IS NOT NULL
        GROUP BY DATE_FORMAT(created_at, '%Y-%m')
        ORDER BY month
    """)

    monthly_rows = cursor.fetchall()

    # Chart.js friendly format
    monthly_data = [[row[0], row[1]] for row in monthly_rows]


    # ================= THIS MONTH vs LAST MONTH =================
    cursor.execute("""
        SELECT COUNT(*) 
        FROM properties 
        WHERE created_at >= DATE_FORMAT(CURDATE(), '%%Y-%%m-01')
    """)
    this_month_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) 
        FROM properties 
        WHERE created_at >= DATE_FORMAT(CURDATE() - INTERVAL 1 MONTH, '%%Y-%%m-01')
        AND created_at < DATE_FORMAT(CURDATE(), '%%Y-%%m-01')
    """)
    last_month_count = cursor.fetchone()[0]


    cursor.close()


    # ================= RENDER =================
    return render_template(
        'admin/analytics.html',
        role='admin',

        # status
        total_properties=total_properties,
        acquire=acquire,
        pending=pending,
        sell=sell,
        not_suitable=not_suitable,

        # district
        district_labels=district_labels,
        district_counts=district_counts,
        district_data=district_data,

        # monthly
        monthly_data=monthly_data,

        # comparison
        this_month_count=this_month_count,
        last_month_count=last_month_count
    )


@admin.route('/admin/property_details/<district>')
def property_details(district):
    cursor = mysql.connection.cursor()
    cursor.execute(
        '''  SELECT property_name,property_type,district,city,estimated_cost,status
        FROM properties
        WHERE district=%s ''', (district,))
    properties = cursor.fetchall()
    return render_template('admin/property_details.html',role='admin', properties=properties,district=district)



@admin.route('/admin/all_properties')
def all_properties():
    cursor = mysql.connection.cursor()
    cursor.execute(
        ''' SELECT *
        FROM properties
        ORDER BY id ASC ''')
    properties = cursor.fetchall()
    return render_template( 'admin/all_properties.html',role='admin',properties=properties )


@admin.route('/admin/single_property/<int:id>')
def single_property(id):

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT *
        FROM properties
        WHERE id=%s
    """,(id,))

    property = cur.fetchone()

    return render_template(
        'admin/single_property.html',
        property=property,role='admin'
    )



@admin.route('/admin/contact_messages')
def contact_messages():
    cursor = mysql.connection.cursor()
    cursor.execute(
        '''  SELECT *
        FROM contact_messages
        ORDER BY id DESC''')
    messages = cursor.fetchall()
    return render_template('admin/contact_messages.html',role='admin',messages=messages)


@admin.route('/admin/login_activity')
def login_activity():
    cursor = mysql.connection.cursor()
    cursor.execute(
        ''' SELECT *
        FROM login_activity
        ORDER BY id DESC''' )
    logs = cursor.fetchall()
    return render_template('admin/login_activity.html',role='admin',logs=logs )



@admin.route('/admin/notifications')
def notifications():
    cursor = mysql.connection.cursor()
    cursor.execute(
        '''SELECT *
        FROM notifications
        ORDER BY id DESC''' )
    notifications = cursor.fetchall()
    return render_template( 'admin/notifications.html',role='admin', notifications=notifications)



@admin.route('/admin/feedbacks')

def feedbacks():

    cursor = mysql.connection.cursor()

    cursor.execute(
        '''
        SELECT
        properties.property_name,
        users.name,
        comments.status,
        comments.comment,
        comments.created_at

        FROM comments

        JOIN properties
        ON comments.property_id = properties.id

        JOIN users
        ON comments.agent_id = users.id

        ORDER BY comments.id DESC
        '''
    )

    feedbacks = cursor.fetchall()

    return render_template(
        'admin/feedbacks.html',role='admin',
        feedbacks=feedbacks
    )


@admin.route('/admin/user_status')

def user_status():

    cursor = mysql.connection.cursor()

    cursor.execute(
        '''
        SELECT *
        FROM users
        '''
    )

    users = cursor.fetchall()

    return render_template(
        'admin/user_status.html',
        users=users,role='admin'
    )


@admin.route('/admin/change-user-status/<int:id>')

def change_user_status(id):

    cursor = mysql.connection.cursor()

    cursor.execute(
        '''
        SELECT status
        FROM users

        WHERE id=%s
        ''',
        (id,)
    )

    current_status = cursor.fetchone()[0]

    new_status = 'Inactive'

    if current_status == 'Inactive':

        new_status = 'Active'

    cursor.execute(
        '''
        UPDATE users

        SET status=%s

        WHERE id=%s  ''',( new_status, id  ) )

    mysql.connection.commit()
    return redirect('/admin/user_status')


@admin.route('/admin/assign_property/<int:property_id>', methods=['GET','POST'])
def assign_property(property_id):

    cursor = mysql.connection.cursor()


    if request.method == "POST":

        agent_id = request.form['agent_id']


        cursor.execute(
        """
        INSERT INTO property_assignments
        (property_id,agent_id,assigned_by,status)
        VALUES(%s,%s,%s,%s)
        """,
        (
            property_id,
            agent_id,
            session.get('user_id'),
            "Assigned"
        )
        )


        mysql.connection.commit()


        return redirect('/admin/all_properties')



    cursor.execute("""
    SELECT id,name
    FROM users
    WHERE role='Agent'
    """)


    agents = cursor.fetchall()



    return render_template(
        'admin/assign_property.html',
        role='admin',
        agents=agents,
        property_id=property_id
    )