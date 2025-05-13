# app/controllers/routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from app.models import Student, Admin, MenuItem, Order, Review, Staff, Task 
from app import db
from flask_wtf.csrf import CSRFProtect
from datetime import datetime
import logging
from werkzeug.security import generate_password_hash, check_password_hash
logging.basicConfig(level=logging.DEBUG)

routes_bp = Blueprint('routes', __name__)

# ---------- ROOT ROUTE ----------

@routes_bp.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'student':
            return redirect(url_for('routes.dashboard'))
        else:
            return redirect(url_for('routes.admin_dashboard'))
    return redirect(url_for('routes.signin'))

# ---------- AUTH ----------

@routes_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        department = request.form.get('department')
        username = request.form.get('username')
        password = request.form.get('password')

        if not (first_name and last_name and department and username and password):
            flash('All fields are required.', 'error')
            return redirect(url_for('routes.signup'))

        if Student.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('routes.signup'))

        student = Student(
            first_name=first_name,
            last_name=last_name,
            department=department,
            username=username
        )
        student.set_password(password)
        db.session.add(student)
        db.session.commit()

        session['user_id'] = student.id
        session['role'] = 'student'
        flash('Signup successful! Welcome to your dashboard.', 'success')
        return redirect(url_for('routes.dashboard'))

    return render_template('signup.html')








@routes_bp.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('signin.html')
        
        student = Student.query.filter_by(username=username).first()
        admin = Admin.query.filter_by(username=username).first()
        staff = Staff.query.filter_by(username=username).first()

        if student and student.check_password(password):
            session['user_id'] = student.id
            session['role'] = 'student'
            flash('Signed in successfully.', 'success')
            return redirect(url_for('routes.dashboard'))

        elif admin and admin.check_password(password):
            session['user_id'] = admin.id
            session['role'] = 'admin'
            flash('Signed in successfully.', 'success')
            return redirect(url_for('routes.admin_dashboard'))

        elif staff and staff.check_password(password):
            if staff.status == 'approved':
                session['user_id'] = staff.id
                session['staff_id'] = staff.id  # ✅ Add this line
                session['role'] = 'staff'
                flash('Signed in successfully.', 'success')
                return redirect(url_for('routes.staff_dashboard'))
            else:
                flash('Your account has not been approved yet.', 'error')
        else:
            flash('Invalid username or password.', 'error')

    return render_template('signin.html')




@routes_bp.route('/staff_dashboard', methods=['GET', 'POST'])
def staff_dashboard():
    if 'staff_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('routes.signin'))

    staff_id = session['staff_id']

    if request.method == 'POST':
        task_id = request.form.get('task_id')
        new_status = request.form.get('status')
        task = Task.query.get(task_id)

        if task and task.assigned_to == staff_id:
            task.status = new_status
            db.session.commit()
            flash(f"Task status updated to {new_status}.", "success")

        return redirect(url_for('routes.staff_dashboard'))

    tasks = Task.query.filter_by(assigned_to=staff_id).order_by(Task.due_date).all()
    return render_template('staff_dashboard.html', tasks=tasks)







@routes_bp.route('/signout')
def signout():
    session.pop('user_id', None)
    session.pop('role', None)
    flash('Signed out successfully.', 'success')
    return redirect(url_for('routes.signin'))

# ---------- DASHBOARDS ----------

@routes_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('role') != 'student':
        flash('Please sign in as a student to access the dashboard.', 'error')
        return redirect(url_for('routes.signin'))
    
    student = Student.query.get(session['user_id'])
    if not student:
        flash('User not found.', 'error')
        return redirect(url_for('routes.signin'))
    
    return render_template('dashboard.html', student=student)

@routes_bp.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Please sign in as an admin to access the dashboard.', 'error')
        return redirect(url_for('routes.signin'))
    
    admin = Admin.query.get(session['user_id'])
    if not admin:
        flash('User not found.', 'error')
        return redirect(url_for('routes.signin'))
    
    return render_template('admin_dashboard.html', admin=admin)

# ---------- MENU MANAGEMENT ----------

@routes_bp.route('/manage_menu', methods=['GET', 'POST'])
def manage_menu():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Please sign in as an admin to access this page.', 'error')
        return redirect(url_for('routes.signin'))
    
    admin = Admin.query.get(session['user_id'])
    if not admin:
        flash('User not found.', 'error')
        return redirect(url_for('routes.signin'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        
        if not (name and description and price):
            flash('All fields are required.', 'error')
            return redirect(url_for('routes.manage_menu'))
        
        try:
            price = float(price)
            if price < 0:
                flash('Price cannot be negative.', 'error')
                return redirect(url_for('routes.manage_menu'))
        except ValueError:
            flash('Price must be a valid number.', 'error')
            return redirect(url_for('routes.manage_menu'))
        
        menu_item = MenuItem(name=name, description=description, price=price)
        db.session.add(menu_item)
        db.session.commit()
        flash('Menu item added successfully.', 'success')
        return redirect(url_for('routes.manage_menu'))
    
    menu_items = MenuItem.query.all()
    return render_template('manage_menu.html', admin=admin, menu_items=menu_items)

@routes_bp.route('/edit_menu_item/<int:item_id>', methods=['GET', 'POST'])
def edit_menu_item(item_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Please sign in as an admin to access this page.', 'error')
        return redirect(url_for('routes.signin'))
    
    admin = Admin.query.get(session['user_id'])
    if not admin:
        flash('User not found.', 'error')
        return redirect(url_for('routes.signin'))
    
    menu_item = MenuItem.query.get_or_404(item_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        
        try:
            price = float(price)
            if price < 0:
                flash('Price cannot be negative.', 'error')
                return redirect(url_for('routes.edit_menu_item', item_id=item_id))
        except ValueError:
            flash('Price must be a valid number.', 'error')
            return redirect(url_for('routes.edit_menu_item', item_id=item_id))
        
        menu_item.name = name
        menu_item.description = description
        menu_item.price = price
        db.session.commit()
        flash('Menu item updated successfully.', 'success')
        return redirect(url_for('routes.manage_menu'))
    
    return render_template('edit_menu_item.html', admin=admin, menu_item=menu_item)

@routes_bp.route('/delete_menu_item/<int:item_id>', methods=['POST'])
def delete_menu_item(item_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Please sign in as an admin to access this page.', 'error')
        return redirect(url_for('routes.signin'))
    
    menu_item = MenuItem.query.get_or_404(item_id)
    db.session.delete(menu_item)
    db.session.commit()
    flash('Menu item deleted successfully.', 'success')
    return redirect(url_for('routes.manage_menu'))

# ---------- ORDER MANAGEMENT ----------

@routes_bp.route('/view_orders')
def view_orders():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Please sign in as an admin to access this page.', 'error')
        return redirect(url_for('routes.signin'))
    
    admin = Admin.query.get(session['user_id'])
    if not admin:
        flash('User not found.', 'error')
        return redirect(url_for('routes.signin'))

    orders = Order.query.all()
    return render_template('view_orders.html', admin=admin, orders=orders)


@routes_bp.route('/delete_order/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Please sign in as an admin to access this page.', 'error')
        return redirect(url_for('routes.signin'))

    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    flash('Order deleted successfully.', 'success')
    return redirect(url_for('routes.view_orders'))




@routes_bp.route('/update_order/<int:order_id>', methods=['POST'])
def update_order(order_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Please sign in as an admin to access this page.', 'error')
        return redirect(url_for('routes.signin'))
    order = Order.query.get_or_404(order_id)
    selected_items = request.form.getlist('menu_items')
    if not selected_items:
        flash('Please select at least one menu item.', 'error')
        return redirect(url_for('routes.order_details', order_id=order_id))
    
    order.menu_items.clear()
    for item_id in selected_items:
        menu_item = MenuItem.query.get(item_id)
        if menu_item:
            order.menu_items.append(menu_item)
    db.session.commit()
    flash('Order updated successfully.', 'success')
    return redirect(url_for('routes.view_orders'))





@routes_bp.route('/create_order', methods=['GET', 'POST'])
def create_order():
    if 'user_id' not in session or session['role'] != 'student':
        flash('Please sign in as a student to create an order.', 'error')
        return redirect(url_for('routes.signin'))

    menu_items = MenuItem.query.all()

    if request.method == 'POST':
        selected_ids = request.form.getlist('menu_item_ids')
        quantities = request.form.getlist('quantities')

        if not selected_ids or not quantities:
            flash('Please select at least one item and specify quantity.', 'error')
            return render_template('create_order.html', menu_items=menu_items)

        try:
            orders_created = 0
            for idx, menu_item_id in enumerate(selected_ids):
                quantity = int(quantities[idx])
                menu_item_id = int(menu_item_id)

                if quantity <= 0:
                    continue  # Skip invalid or zero quantity

                # Double-check if the menu item exists
                menu_item = MenuItem.query.get(menu_item_id)
                if not menu_item:
                    continue

                new_order = Order(
                    student_id=session['user_id'],
                    menu_item_id=menu_item_id,
                    quantity=quantity,
                    created_at=datetime.utcnow()
                )
                db.session.add(new_order)
                orders_created += 1

            db.session.commit()

            if orders_created > 0:
                flash('Order placed successfully!', 'success')
            else:
                flash('No valid items were selected.', 'error')

            return redirect(url_for('routes.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the order.', 'error')
            print(f"Error: {e}")
            return render_template('create_order.html', menu_items=menu_items)

    return render_template('create_order.html', menu_items=menu_items)

@routes_bp.route('/manage_order', methods=['GET', 'POST'])
def manage_order():
    if 'user_id' not in session or session['role'] != 'student':
        flash('Please sign in as a student to manage orders.', 'error')
        return redirect(url_for('routes.signin'))

    student_id = session['user_id']

    if request.method == 'POST':
        order_id = request.form.get('order_id')
        order = Order.query.filter_by(id=order_id, student_id=student_id).first()
        if order:
            db.session.delete(order)
            db.session.commit()
            flash('Order deleted successfully.', 'success')
        else:
            flash('Order not found or unauthorized.', 'error')

    orders = Order.query.filter_by(student_id=student_id).order_by(Order.created_at.desc()).all()
    return render_template('manage_order.html', orders=orders)













@routes_bp.route('/about_us')
def about_us():
    if 'user_id' not in session or session.get('role') != 'student':
        flash('Please sign in as an student to access the dashboard.', 'error')
        return redirect(url_for('routes.signin'))
    return render_template('about_us.html')

@routes_bp.route('/create_review', methods=['GET', 'POST'])
def create_review():
    # Check if user is authenticated and has student role
    if 'user_id' not in session or session.get('role') != 'student':
        flash('Please sign in as a student to create a review.', 'error')
        return redirect(url_for('routes.signin'))

    if request.method == 'POST':
        description = request.form.get('description')

        if not description:
            flash('Review description is required.', 'error')
            return render_template('create_review.html', error='Review description is required.')

        try:
            review = Review(
                student_id=session['user_id'],
                description=description,
                created_at=datetime.utcnow()
            )
            db.session.add(review)
            db.session.commit()
            flash('Review created successfully!', 'success')
            return redirect(url_for('routes.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the review.', 'error')
            return render_template('create_review.html', error=str(e))

    return render_template('create_review.html')




@routes_bp.route('/view_reviews')
def view_reviews():
    # Check if user is authenticated and has student role
    if 'user_id' not in session or session.get('role') != 'student':
        flash('Please sign in as a student to view your reviews.', 'error')
        return redirect(url_for('routes.signin'))
    
    student = Student.query.get(session['user_id'])
    if not student:
        flash('User not found.', 'error')
        return redirect(url_for('routes.signin'))
    
    # Fetch reviews for the current student
    reviews = Review.query.filter_by(student_id=session['user_id']).all()
    
    return render_template('view_reviews.html', student=student, reviews=reviews)

@routes_bp.route('/edit_review/<int:review_id>', methods=['GET', 'POST'])
def edit_review(review_id):
    # Check if user is authenticated and has student role
    if 'user_id' not in session or session.get('role') != 'student':
        flash('Please sign in as a student to edit a review.', 'error')
        return redirect(url_for('routes.signin'))
    
    review = Review.query.get_or_404(review_id)
    
    # Ensure the review belongs to the current student
    if review.student_id != session['user_id']:
        flash('You can only edit your own reviews.', 'error')
        return redirect(url_for('routes.view_reviews'))
    
    if request.method == 'POST':
        description = request.form.get('description')
        
        if not description:
            flash('Review description is required.', 'error')
            return render_template('edit_review.html', review=review, error='Review description is required.')
        
        try:
            review.description = description
            review.created_at = datetime.utcnow()  # Update timestamp
            db.session.commit()
            flash('Review updated successfully!', 'success')
            return redirect(url_for('routes.view_reviews'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the review.', 'error')
            return render_template('edit_review.html', review=review, error=str(e))
    
    return render_template('edit_review.html', review=review)

@routes_bp.route('/delete_review/<int:review_id>', methods=['POST'])
def delete_review(review_id):
    # Check if user is authenticated and has student role
    if 'user_id' not in session or session.get('role') != 'student':
        flash('Please sign in as a student to delete a review.', 'error')
        return redirect(url_for('routes.signin'))
    
    review = Review.query.get_or_404(review_id)
    
    # Ensure the review belongs to the current student
    if review.student_id != session['user_id']:
        flash('You can only delete your own reviews.', 'error')
        return redirect(url_for('routes.view_reviews'))
    
    try:
        db.session.delete(review)
        db.session.commit()
        flash('Review deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the review.', 'error')
    
    return redirect(url_for('routes.view_reviews'))

# ---------- Existing routes continue (create_review, etc.) --------





@routes_bp.route('/create_staff', methods=['GET', 'POST'])
def create_staff():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('routes.signin'))

    if request.method == 'POST':
        staff_id = request.form.get('staff_id')
        action = request.form.get('action')

        if staff_id and action in ['approved', 'rejected']:
            staff = Staff.query.get(staff_id)
            if staff:
                staff.status = action
                db.session.commit()
                flash(f'Staff {staff.username} has been {action}.', 'success')
            else:
                flash('Staff not found.', 'error')
        else:
            flash('Invalid form data.', 'error')

        return redirect(url_for('routes.create_staff'))

    # GET request - show pending staff
    pending_staff = Staff.query.filter_by(status='pending').all()
    return render_template('create_staff.html', pending_staff=pending_staff)











@routes_bp.route('/staff_signup', methods=['GET', 'POST'])
def staff_signup():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if username exists
        if Staff.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('staff_signup.html')

        staff = Staff(
            first_name=first_name,
            last_name=last_name,
            username=username
        )
        staff.set_password(password)
        db.session.add(staff)
        db.session.commit()
        flash('Signup request submitted. Waiting for approval.', 'success')
        return redirect(url_for('routes.signin'))

    return render_template('staff_signup.html')


@routes_bp.route('/show_staff', methods=['GET'])
def show_staff():
    pending_staff = Staff.query.filter_by(status='pending').all()
    accepted_staff = Staff.query.filter_by(status='approved').all()
    rejected_staff = Staff.query.filter_by(status='rejected').all()
    return render_template(
        'show_staff.html',
        pending_staff=pending_staff,
        accepted_staff=accepted_staff,
        rejected_staff=rejected_staff
    )

@routes_bp.route('/assign_task', methods=['GET', 'POST'])
def assign_task():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        assigned_to = request.form['assigned_to']
        due_date_str = request.form.get('due_date')

        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
        except ValueError:
            flash('Invalid due date format.', 'error')
            return redirect(url_for('routes.assign_task'))

        new_task = Task(
            title=title,
            description=description,
            assigned_to=int(assigned_to),
            due_date=due_date
        )

        db.session.add(new_task)
        db.session.commit()
        flash('Task assigned successfully!', 'success')
        return redirect(url_for('routes.assign_task'))

    staff_list = Staff.query.filter(Staff.status.ilike('approved')).all()
    return render_template('assign_task.html', staff_list=staff_list)



@routes_bp.route('/task_progress')
def task_progress():
    tasks = Task.query.order_by(Task.due_date).all()
    return render_template('task_progress.html', tasks=tasks)
