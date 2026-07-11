from flask import Blueprint, render_template, request
from flask import session ,redirect
from config.db import mysql

agent = Blueprint('agent', __name__)

@agent.route("/agent/search_property")
def search_property():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM properties")
    properties = cursor.fetchall()
    return render_template(  "agent/search_property.html", role='agent', properties=properties )

@agent.route('/agent/property_details/<int:id>')
def property_details(id):

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT *
        FROM properties
        WHERE id=%s
    """,(id,))

    property = cursor.fetchone()

    return render_template(
        'agent/property_details.html',
        property=property,
        role='agent'
    )

@agent.route('/agent/add_comment/<int:property_id>', methods=['GET','POST'])
def add_comment(property_id):

    cursor = mysql.connection.cursor()

    if request.method == "POST":

        status = request.form['status']
        comment = request.form['comment']


        cursor.execute("""
        INSERT INTO comments
        (
        property_id,
        agent_id,
        status,
        comment
        )
        VALUES(%s,%s,%s,%s)
        """,
        (
            property_id,
            session.get('user_id'),
            status,
            comment
        ))


        mysql.connection.commit()


        # review submit ke baad status history pe bhejo
        return redirect('/agent/status_history')



    return render_template(
        'agent/add_comment.html',
        role='agent',
        property_id=property_id
    )



@agent.route('/agent/dashboard')
def dashboard():
    cursor = mysql.connection.cursor()
    cursor.execute(  "SELECT COUNT(*) FROM properties" )
    total_properties = cursor.fetchone()[0]
    cursor.execute(  "SELECT COUNT(*) FROM comments WHERE status='Acquire'" )
    acquire = cursor.fetchone()[0]
    cursor.execute(  "SELECT COUNT(*) FROM comments WHERE status='Pending'" )
    pending = cursor.fetchone()[0]
    cursor.execute(  "SELECT COUNT(*) FROM comments WHERE status='Not Suitable'" )
    not_suitable = cursor.fetchone()[0]
    cursor.execute(  ''' SELECT
        properties.property_name,
        comments.status,
        comments.comment
        FROM comments  JOIN properties ON comments.property_id = properties.id  ORDER BY comments.id DESC ''')
    comments = cursor.fetchall()

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

    return render_template('agent/dashboard.html',role='agent',
        total_properties=total_properties,
        acquire=acquire,
        pending=pending,
        not_suitable=not_suitable,
        comments=comments,
        notifications=notifications)


@agent.route('/agent/profile',methods=['GET', 'POST'])
def profile():
    cursor = mysql.connection.cursor()
    user_id = session['user_id']
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        mobile = request.form['mobile']
        cursor.execute(  ''' UPDATE users
            SET name=%s,
            email=%s,
            mobile=%s
            WHERE id=%s ''', (  name, email, mobile,  user_id ) )
        mysql.connection.commit()
        return redirect('/agent/profile')
    cursor.execute( ''' SELECT * FROM users WHERE id=%s''', (user_id,) )
    user = cursor.fetchone()
    return render_template('agent/profile.html',role='agent', user=user)


@agent.route('/agent/status_history')
def status_history():
    cursor = mysql.connection.cursor()
    cursor.execute('''SELECT
        properties.property_name,
        comments.status,
        comments.comment,
        comments.created_at
        FROM comments

        JOIN properties
        ON comments.property_id = properties.id
        ORDER BY comments.id DESC  ''')
    comments = cursor.fetchall()
    return render_template( 'agent/status_history.html', role='agent',  comments=comments  )


@agent.route('/agent/gallary')
def gallery():
    cursor = mysql.connection.cursor()
    cursor.execute(  ''' SELECT *
        FROM properties
        ORDER BY id DESC  ''' )
    properties = cursor.fetchall()
    return render_template( 'agent/gallary.html',role='agent', properties=properties )


@agent.route('/agent/property/<int:id>')
def property_detail(id):

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT * FROM properties WHERE id=%s
    """, (id,))

    property = cursor.fetchone()

    if not property:
        return "Property not found"

    return render_template('admin/property_details.html', property=property)



@agent.route('/agent/saved_properties')
def saved_properties():
    cursor = mysql.connection.cursor()
    cursor.execute( ''' SELECT properties.*
        FROM saved_properties

        JOIN properties
        ON saved_properties.property_id = properties.id
        WHERE saved_properties.agent_id=%s
        ''', (  session['user_id'],  ))
    properties = cursor.fetchall()
    return render_template('agent/saved_properties.html',role='agent',  properties=properties )

@agent.route('/agent/delete_property/<int:id>')
def delete_property(id):
    cursor = mysql.connection.cursor()
    query =   "DELETE FROM properties WHERE id=%s "
    cursor.execute (query,(id,) )
    mysql.connection.commit()
    return redirect('/agent/search_property',role='agent')

@agent.route('/agent/compare_properties')
def compare_properties():

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT
            id,
            property_type,
            property_name,
            contact_person_name,
            status,
            district,
            city,
            village,
            estimated_cost,
            mobile,
            photo

        FROM properties
        ORDER BY id DESC
    """)

    properties = cursor.fetchall()


    return render_template(
        'agent/compare_properties.html',
        role='agent',
        properties=properties
    )


@agent.route('/agent/assigned_properties')
def assigned_properties():

    cursor = mysql.connection.cursor()

    agent_id = session.get('user_id')

    cursor.execute("""
    SELECT 

    property_assignments.id,
    properties.property_name,
    properties.property_type,
    properties.district,
    property_assignments.status,
    property_assignments.assigned_at

    FROM property_assignments

    JOIN properties
    ON property_assignments.property_id = properties.id

    WHERE property_assignments.agent_id=%s

    ORDER BY property_assignments.id DESC

    """, (agent_id,))


    properties = cursor.fetchall()


    return render_template(
        'agent/assigned_properties.html',
        role='agent',
        properties=properties
    )



@agent.route('/agent/update_assignment/<int:id>/<status>')
def update_assignment(id,status):

    cursor = mysql.connection.cursor()

    cursor.execute("""
        UPDATE property_assignments
        SET status=%s
        WHERE id=%s
    """,
    (
        status,
        id
    ))

    mysql.connection.commit()


    return redirect('/agent/assigned_properties')