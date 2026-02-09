from flask import Flask, render_template, url_for, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///date.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    full_name = db.Column(db.String(100))
    dietary_preferences = db.Column(db.Text, default='')
    allergies = db.Column(db.Text, default='')
    balance = db.Column(db.Float, default=0.0)


class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    price = db.Column(db.Float, nullable=False)
    meal_type = db.Column(db.String(20), nullable=False)
    available = db.Column(db.Boolean, default=True, nullable=False)
    tags = db.Column(db.String(200), default='')
    ingredients = db.Column(db.Text, default='')
    average_rating = db.Column(db.Float, default=0.0)
    total_reviews = db.Column(db.Integer, default=0)
    has_subscription = db.Column(db.Boolean, default=False)
    subscription_price = db.Column(db.Float, default=0.0)
    subscription_days = db.Column(db.Integer, default=30)
    meals_per_day = db.Column(db.Integer, default=1)
    stock_quantity = db.Column(db.Integer, default=0)
    min_stock = db.Column(db.Integer, default=10)
    max_stock = db.Column(db.Integer, default=100)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    meal_id = db.Column(db.Integer, db.ForeignKey('meal.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    quantity = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='pending')
    student = db.relationship('User', backref='orders')
    meal = db.relationship('Meal')


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    meal_id = db.Column(db.Integer, db.ForeignKey('meal.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    review_date = db.Column(db.DateTime, default=datetime.utcnow)
    anonymous = db.Column(db.Boolean, default=False)
    student = db.relationship('User', backref='reviews')
    meal = db.relationship('Meal', backref='reviews')


class PurchaseRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cook_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    priority = db.Column(db.String(20), default='normal')
    status = db.Column(db.String(20), default='pending')
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    needed_by = db.Column(db.DateTime)
    reason = db.Column(db.Text)
    admin_notes = db.Column(db.Text)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    decision_date = db.Column(db.DateTime)

    cook = db.relationship('User', foreign_keys=[cook_id], backref='purchase_requests')
    admin = db.relationship('User', foreign_keys=[admin_id])


class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    meal_id = db.Column(db.Integer, db.ForeignKey('meal.id'), nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='active')
    meals_remaining_today = db.Column(db.Integer, default=0)

    student = db.relationship('User', backref='subscriptions')
    meal = db.relationship('Meal', backref='subscriptions')


class SubscriptionUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'), nullable=False)
    usage_date = db.Column(db.Date, nullable=False)
    meal_type = db.Column(db.String(20), nullable=False)
    used_at = db.Column(db.DateTime, default=datetime.utcnow)

    subscription = db.relationship('Subscription', backref='usages')


class MealStockUpdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meal_id = db.Column(db.Integer, db.ForeignKey('meal.id'), nullable=False)
    cook_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quantity_added = db.Column(db.Integer, nullable=False)
    update_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

    meal = db.relationship('Meal', backref='stock_updates')
    cook = db.relationship('User', foreign_keys=[cook_id])


def init_database():
    with app.app_context():
        db.create_all()
        if Meal.query.count() == 0:
            add_sample_meals()
        print(f"База данных инициализирована: {Meal.query.count()} блюд, {User.query.count()} пользователей")
        print(f"Таблицы абонементов созданы")
        print(f"Система учета остатков готова")


def add_sample_meals():
    sample_meals = [
        Meal(name='Каша овсяная', description='Овсяная каша с маслом', price=80, meal_type='breakfast', available=True,
             tags='вегетарианское, безглютеновое', ingredients='овсяные хлопья, молоко, масло сливочное, соль, сахар',
             has_subscription=True, subscription_price=2000, subscription_days=30, meals_per_day=1,
             stock_quantity=50, min_stock=10, max_stock=100),

        Meal(name='Яичница', description='Яичница из 2-х яиц', price=70, meal_type='breakfast', available=True,
             tags='высокобелковое', ingredients='яйца куриные, масло растительное, соль',
             has_subscription=True, subscription_price=1800, subscription_days=30, meals_per_day=1,
             stock_quantity=30, min_stock=15, max_stock=80),

        Meal(name='Бутерброды', description='Бутерброды с сыром и колбасой', price=60, meal_type='breakfast',
             available=True, tags='быстрое', ingredients='хлеб, сыр, колбаса вареная, масло сливочное',
             stock_quantity=40, min_stock=20, max_stock=100),

        Meal(name='Творог', description='Творог со сметаной и сахаром', price=65, meal_type='breakfast', available=True,
             tags='вегетарианское, высокобелковое, безглютеновое', ingredients='творог, сметана, сахар',
             stock_quantity=25, min_stock=10, max_stock=60),

        Meal(name='Манная каша', description='Манная каша с вареньем', price=75, meal_type='breakfast', available=True,
             tags='вегетарианское', ingredients='манная крупа, молоко, сахар, варенье, масло сливочное',
             stock_quantity=35, min_stock=15, max_stock=70),

        Meal(name='Омлет', description='Омлет с зеленью', price=85, meal_type='breakfast', available=True,
             tags='высокобелковое, вегетарианское', ingredients='яйца, молоко, зелень, соль, масло растительное',
             stock_quantity=20, min_stock=10, max_stock=50),

        Meal(name='Суп куриный', description='Куриный суп с лапшой', price=120, meal_type='lunch', available=True,
             tags='горячее, мясное', ingredients='курица, лапша, морковь, лук, картофель, зелень',
             has_subscription=True, subscription_price=3000, subscription_days=30, meals_per_day=1,
             stock_quantity=60, min_stock=20, max_stock=120),

        Meal(name='Гречка с котлетой', description='Гречка и котлета куриная', price=130, meal_type='lunch',
             available=True, tags='мясное, высокобелковое', ingredients='гречка, куриный фарш, лук, яйцо, специи',
             has_subscription=True, subscription_price=3200, subscription_days=30, meals_per_day=1,
             stock_quantity=45, min_stock=15, max_stock=90),

        Meal(name='Пюре с сосиской', description='Картофельное пюре с сосиской', price=110, meal_type='lunch',
             available=True, tags='мясное, быстрое', ingredients='картофель, сосиски, молоко, масло сливочное',
             stock_quantity=55, min_stock=25, max_stock=110),

        Meal(name='Макароны с мясом', description='Макароны по-флотски', price=115, meal_type='lunch', available=True,
             tags='мясное', ingredients='макароны, говяжий фарш, лук, морковь, томатная паста',
             stock_quantity=50, min_stock=20, max_stock=100),

        Meal(name='Рис с овощами', description='Рис с тушеными овощами', price=100, meal_type='lunch', available=True,
             tags='вегетарианское', ingredients='рис, морковь, лук, перец, горошек, кукуруза',
             stock_quantity=40, min_stock=15, max_stock=80),

        Meal(name='Суп гороховый', description='Гороховый суп с сухариками', price=125, meal_type='lunch',
             available=True, tags='вегетарианское, горячее', ingredients='горох, картофель, морковь, лук, сухарики',
             stock_quantity=30, min_stock=10, max_stock=60),

        Meal(name='Плов простой', description='Плов с курицей', price=140, meal_type='lunch', available=True,
             tags='мясное, горячее', ingredients='рис, курица, морковь, лук, специи',
             stock_quantity=35, min_stock=15, max_stock=70),

        Meal(name='Рагу овощное', description='Овощное рагу с мясом', price=135, meal_type='lunch', available=True,
             tags='мясное, овощное', ingredients='говядина, картофель, морковь, лук, капуста, томаты',
             stock_quantity=25, min_stock=10, max_stock=50),
    ]

    for meal in sample_meals:
        existing_meal = Meal.query.filter_by(name=meal.name, meal_type=meal.meal_type).first()
        if not existing_meal:
            db.session.add(meal)
    db.session.commit()


@app.route('/cooks/stock')
def manage_stock():
    if 'user_type' not in session or session['user_type'] != 'cook':
        return redirect('/')

    meals = Meal.query.order_by(Meal.meal_type, Meal.name).all()

    low_stock_meals = [meal for meal in meals if meal.stock_quantity <= meal.min_stock and meal.available]
    out_of_stock_meals = [meal for meal in meals if meal.stock_quantity == 0 and meal.available]

    return render_template("manage_stock.html",
                           meals=meals,
                           low_stock_meals=low_stock_meals,
                           out_of_stock_meals=out_of_stock_meals)


@app.route('/cooks/stock/update/<int:meal_id>', methods=['GET', 'POST'])
def update_meal_stock(meal_id):
    if 'user_type' not in session or session['user_type'] != 'cook':
        return redirect('/')

    meal = Meal.query.get_or_404(meal_id)

    if request.method == 'POST':
        action = request.form.get('action')
        quantity = int(request.form.get('quantity', 0))
        notes = request.form.get('notes', '')

        if action == 'add':
            if quantity <= 0:
                return "Количество должно быть больше 0", 400

            meal.stock_quantity += quantity

            stock_update = MealStockUpdate(
                meal_id=meal_id,
                cook_id=session['user_id'],
                quantity_added=quantity,
                notes=notes
            )
            db.session.add(stock_update)

        elif action == 'set':
            if quantity < 0:
                return "Количество не может быть отрицательным", 400

            old_quantity = meal.stock_quantity
            meal.stock_quantity = quantity

            stock_update = MealStockUpdate(
                meal_id=meal_id,
                cook_id=session['user_id'],
                quantity_added=quantity - old_quantity,
                notes=f"Установлено вручную: {notes}" if notes else "Установлено вручную"
            )
            db.session.add(stock_update)

        db.session.commit()

        return redirect('/cooks/stock')

    return render_template("update_stock.html", meal=meal)


@app.route('/cooks/stock/history/<int:meal_id>')
def stock_history(meal_id):
    if 'user_type' not in session or session['user_type'] != 'cook':
        return redirect('/')

    meal = Meal.query.get_or_404(meal_id)
    stock_updates = MealStockUpdate.query.filter_by(meal_id=meal_id).order_by(MealStockUpdate.update_date.desc()).all()

    return render_template("stock_history.html", meal=meal, stock_updates=stock_updates)


@app.route('/cooks/stock/settings/<int:meal_id>', methods=['GET', 'POST'])
def stock_settings(meal_id):
    if 'user_type' not in session or session['user_type'] != 'cook':
        return redirect('/')

    meal = Meal.query.get_or_404(meal_id)

    if request.method == 'POST':
        meal.min_stock = int(request.form.get('min_stock', 10))
        meal.max_stock = int(request.form.get('max_stock', 100))

        db.session.commit()
        return redirect('/cooks/stock')

    return render_template("stock_settings.html", meal=meal)


@app.route('/students/subscriptions')
def student_subscriptions():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect('/')

    user_id = session['user_id']

    active_subscriptions = Subscription.query.filter_by(
        student_id=user_id,
        status='active'
    ).join(Meal).order_by(Subscription.end_date.desc()).all()

    expired_subscriptions = Subscription.query.filter_by(
        student_id=user_id,
        status='expired'
    ).join(Meal).order_by(Subscription.end_date.desc()).all()

    available_meals = Meal.query.filter_by(has_subscription=True, available=True).all()

    today = date.today()

    for sub in active_subscriptions:
        if sub.end_date < today:
            sub.status = 'expired'
            db.session.commit()

    return render_template("student_subscriptions.html",
                           active_subscriptions=active_subscriptions,
                           expired_subscriptions=expired_subscriptions,
                           available_meals=available_meals,
                           today=date.today())


@app.route('/students/subscriptions/buy/<int:meal_id>', methods=['GET', 'POST'])
def buy_subscription(meal_id):
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect('/')

    meal = Meal.query.get_or_404(meal_id)

    if not meal.has_subscription:
        return "На это блюдо нельзя приобрести абонемент", 400

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        subscription_days = int(request.form.get('subscription_days', 30))
        start_date_str = request.form.get('start_date', '')

        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            start_date = date.today()

        end_date = start_date + timedelta(days=subscription_days)
        total_price = meal.subscription_price * subscription_days

        if user.balance < total_price:
            return "Недостаточно средств на балансе. Пополните баланс.", 400

        user.balance -= total_price

        subscription = Subscription(
            student_id=user.id,
            meal_id=meal_id,
            start_date=start_date,
            end_date=end_date,
            price=total_price,
            status='active',
            meals_remaining_today=meal.meals_per_day
        )

        db.session.add(subscription)
        db.session.commit()

        return redirect('/students/subscriptions')

    return render_template("buy_subscription.html", meal=meal, user=user)


@app.route('/students/balance', methods=['GET', 'POST'])
def student_balance():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect('/')

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))

        if amount <= 0:
            return "Сумма должна быть больше 0", 400

        user.balance += amount
        db.session.commit()

        return redirect('/students/balance')

    return render_template("student_balance.html", user=user)


@app.route('/students/order', methods=['POST'])
def place_order():
    if 'user_type' not in session or session['user_type'] != 'student':
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        meal_id = request.form.get('meal_id')
        quantity = int(request.form.get('quantity', 1))
        meal = Meal.query.get(meal_id)
        if not meal:
            return jsonify({'error': 'Блюдо не найдено'}), 400

        if not meal.available:
            return jsonify({'error': f'"{meal.name}" временно недоступно'}), 400

        if meal.stock_quantity < quantity:
            if meal.stock_quantity == 0:
                return jsonify({'error': f'"{meal.name}" закончился'}), 400
            else:
                return jsonify({'error': f'"{meal.name}" осталось только {meal.stock_quantity} порций'}), 400

        order = Order(student_id=session['user_id'], meal_id=meal_id, quantity=quantity)

        meal.stock_quantity -= quantity

        db.session.add(order)
        db.session.commit()

        total_price = meal.price * quantity
        return jsonify({
            'success': True,
            'message': f'Заказ оформлен: {meal.name} (x{quantity}) - {total_price} руб.',
            'order_id': order.id,
            'total_price': total_price,
            'remaining_stock': meal.stock_quantity
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/students/order-with-subscription', methods=['POST'])
def order_with_subscription():
    if 'user_type' not in session or session['user_type'] != 'student':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        meal_id = int(request.form.get('meal_id'))
        meal_type = request.form.get('meal_type')

        user_id = session['user_id']
        today = date.today()

        meal = Meal.query.get(meal_id)

        if not meal:
            return jsonify({'error': 'Блюдо не найдено'}), 400

        if not meal.available:
            return jsonify({'error': f'"{meal.name}" временно недоступно'}), 400

        if meal.stock_quantity < 1:
            return jsonify({'error': f'"{meal.name}" закончился'}), 400

        active_subscription = Subscription.query.filter_by(
            student_id=user_id,
            meal_id=meal_id,
            status='active'
        ).first()

        if not active_subscription:
            return jsonify({'error': 'У вас нет активного абонемента на это блюдо'}), 400

        if active_subscription.end_date < today:
            active_subscription.status = 'expired'
            db.session.commit()
            return jsonify({'error': 'Ваш абонемент истек'}), 400

        if active_subscription.start_date > today:
            return jsonify({'error': 'Абонемент еще не начал действовать'}), 400

        today_usage = SubscriptionUsage.query.filter_by(
            subscription_id=active_subscription.id,
            usage_date=today,
            meal_type=meal_type
        ).count()

        if today_usage >= active_subscription.meals_remaining_today:
            return jsonify({'error': 'Лимит приемов пищи на сегодня исчерпан'}), 400

        order = Order(student_id=user_id, meal_id=meal_id, quantity=1, status='confirmed')
        db.session.add(order)

        usage = SubscriptionUsage(
            subscription_id=active_subscription.id,
            usage_date=today,
            meal_type=meal_type
        )
        db.session.add(usage)

        meal.stock_quantity -= 1

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Заказ по абонементу оформлен: {meal.name}',
            'order_id': order.id,
            'remaining_today': active_subscription.meals_remaining_today - (today_usage + 1),
            'remaining_stock': meal.stock_quantity
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/students/subscription-usage/<int:subscription_id>')
def subscription_usage(subscription_id):
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect('/')

    subscription = Subscription.query.get_or_404(subscription_id)

    if subscription.student_id != session['user_id']:
        return "Доступ запрещен", 403

    usages = SubscriptionUsage.query.filter_by(
        subscription_id=subscription_id
    ).order_by(SubscriptionUsage.usage_date.desc()).all()

    usage_by_date = {}
    for usage in usages:
        date_str = usage.usage_date.strftime('%Y-%m-%d')
        if date_str not in usage_by_date:
            usage_by_date[date_str] = []
        usage_by_date[date_str].append(usage)

    return render_template("subscription_usage.html",
                           subscription=subscription,
                           usage_by_date=usage_by_date)


@app.route('/cooks/meals/subscription/<int:meal_id>', methods=['GET', 'POST'])
def manage_meal_subscription(meal_id):
    if 'user_type' not in session or session['user_type'] != 'cook':
        return redirect('/')

    meal = Meal.query.get_or_404(meal_id)

    if request.method == 'POST':
        meal.has_subscription = 'has_subscription' in request.form
        meal.subscription_price = float(request.form.get('subscription_price', 0))
        meal.subscription_days = int(request.form.get('subscription_days', 30))
        meal.meals_per_day = int(request.form.get('meals_per_day', 1))

        db.session.commit()
        return redirect('/cooks/meals')

    return render_template("manage_meal_subscription.html", meal=meal)


@app.route('/cooks/purchase-requests')
def purchase_requests():
    if 'user_type' not in session or session['user_type'] != 'cook':
        return redirect('/')

    user_id = session['user_id']
    requests = PurchaseRequest.query.filter_by(cook_id=user_id).order_by(PurchaseRequest.request_date.desc()).all()

    stats = {
        'total': len(requests),
        'pending': len([r for r in requests if r.status == 'pending']),
        'approved': len([r for r in requests if r.status == 'approved']),
        'rejected': len([r for r in requests if r.status == 'rejected']),
        'completed': len([r for r in requests if r.status == 'completed'])
    }

    return render_template("purchase_requests.html", requests=requests, stats=stats)


@app.route('/cooks/purchase-requests/new', methods=['GET', 'POST'])
def new_purchase_request():
    if 'user_type' not in session or session['user_type'] != 'cook':
        return redirect('/')

    if request.method == 'POST':
        product_name = request.form['product_name']
        quantity = float(request.form['quantity'])
        unit = request.form['unit']
        priority = request.form['priority']
        reason = request.form.get('reason', '')

        needed_by_str = request.form.get('needed_by', '')
        needed_by = None
        if needed_by_str:
            try:
                needed_by = datetime.strptime(needed_by_str, '%Y-%m-%d')
            except ValueError:
                pass

        request_obj = PurchaseRequest(
            cook_id=session['user_id'],
            product_name=product_name,
            quantity=quantity,
            unit=unit,
            priority=priority,
            reason=reason,
            needed_by=needed_by,
            status='pending'
        )

        db.session.add(request_obj)
        db.session.commit()

        return redirect('/cooks/purchase-requests')

    return render_template("new_purchase_request.html")


@app.route('/cooks/purchase-requests/<int:request_id>')
def view_purchase_request(request_id):
    if 'user_type' not in session or session['user_type'] != 'cook':
        return redirect('/')

    request_obj = PurchaseRequest.query.get_or_404(request_id)

    if request_obj.cook_id != session['user_id']:
        return "Доступ запрещен", 403

    return render_template("view_purchase_request.html", request_obj=request_obj)


@app.route('/admin/purchase-requests')
def admin_purchase_requests():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return redirect('/')

    status_filter = request.args.get('status', 'all')

    query = PurchaseRequest.query

    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    requests = query.order_by(
        db.case(
            (PurchaseRequest.priority == 'critical', 1),
            (PurchaseRequest.priority == 'high', 2),
            (PurchaseRequest.priority == 'normal', 3),
            (PurchaseRequest.priority == 'low', 4),
            else_=5
        ),
        PurchaseRequest.request_date.desc()
    ).all()

    stats = {
        'total': PurchaseRequest.query.count(),
        'pending': PurchaseRequest.query.filter_by(status='pending').count(),
        'approved': PurchaseRequest.query.filter_by(status='approved').count(),
        'rejected': PurchaseRequest.query.filter_by(status='rejected').count(),
        'completed': PurchaseRequest.query.filter_by(status='completed').count()
    }

    return render_template("admin_purchase_requests.html",
                           requests=requests,
                           stats=stats,
                           status_filter=status_filter)


@app.route('/admin/purchase-requests/<int:request_id>', methods=['GET', 'POST'])
def admin_view_purchase_request(request_id):
    if 'user_type' not in session or session['user_type'] != 'admin':
        return redirect('/')

    request_obj = PurchaseRequest.query.get_or_404(request_id)

    if request.method == 'POST':
        action = request.form.get('action')
        admin_notes = request.form.get('admin_notes', '')

        if action in ['approve', 'reject', 'complete']:
            request_obj.status = action + ('d' if action != 'complete' else '')
            request_obj.admin_notes = admin_notes
            request_obj.admin_id = session['user_id']
            request_obj.decision_date = datetime.utcnow()

            db.session.commit()

            return redirect('/admin/purchase-requests')

    return render_template("admin_view_purchase_request.html", request_obj=request_obj)


@app.route('/admin/purchase-requests/<int:request_id>/delete', methods=['POST'])
def delete_purchase_request(request_id):
    if 'user_type' not in session or session['user_type'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    request_obj = PurchaseRequest.query.get_or_404(request_id)

    db.session.delete(request_obj)
    db.session.commit()

    return jsonify({'success': True})


@app.route('/students/dietary-preferences', methods=['GET', 'POST'])
def dietary_preferences():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect('/')
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        user.dietary_preferences = request.form.get('dietary_preferences', '')
        user.allergies = request.form.get('allergies', '')
        db.session.commit()
        session['full_name'] = user.full_name
        return redirect('/students/meals')
    return render_template("dietary_preferences.html", user=user,
                           common_allergies=['Глютен', 'Лактоза', 'Орехи', 'Яйца', 'Рыба', 'Морепродукты', 'Соя',
                                             'Мед'],
                           common_preferences=['Вегетарианское', 'Веганское', 'Безглютеновое', 'Низкокалорийное',
                                               'Высокобелковое'])


@app.route('/students/profile')
def student_profile():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect('/')
    user = User.query.get(session['user_id'])
    orders_count = Order.query.filter_by(student_id=user.id).count()
    reviews_count = Review.query.filter_by(student_id=user.id).count()
    return render_template("student_profile.html", user=user, orders_count=orders_count, reviews_count=reviews_count)


@app.route('/students/reviews')
def student_reviews():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect('/')
    user = User.query.get(session['user_id'])
    reviews = Review.query.filter_by(student_id=user.id).join(Meal).order_by(Review.review_date.desc()).all()
    return render_template("student_reviews.html", reviews=reviews)


@app.route('/students/add-review/<int:meal_id>', methods=['GET', 'POST'])
def add_review(meal_id):
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect('/')
    meal = Meal.query.get_or_404(meal_id)
    user_id = session['user_id']
    has_ordered = Order.query.filter_by(student_id=user_id, meal_id=meal_id).first() is not None
    if not has_ordered:
        return "Вы можете оставить отзыв только на блюда, которые заказывали", 403
    existing_review = Review.query.filter_by(student_id=user_id, meal_id=meal_id).first()
    if request.method == 'POST':
        if existing_review:
            old_rating = existing_review.rating
            existing_review.rating = int(request.form['rating'])
            existing_review.comment = request.form.get('comment', '')
            existing_review.anonymous = 'anonymous' in request.form
            existing_review.review_date = datetime.utcnow()
            total_rating = meal.average_rating * meal.total_reviews - old_rating + existing_review.rating
            meal.average_rating = total_rating / meal.total_reviews
        else:
            rating = int(request.form['rating'])
            comment = request.form.get('comment', '')
            anonymous = 'anonymous' in request.form
            review = Review(student_id=user_id, meal_id=meal_id, rating=rating, comment=comment, anonymous=anonymous)
            db.session.add(review)
            total_rating = meal.average_rating * meal.total_reviews + rating
            meal.total_reviews += 1
            meal.average_rating = total_rating / meal.total_reviews
        db.session.commit()
        return redirect(f'/students/meal-reviews/{meal_id}')
    return render_template("add_review.html", meal=meal, existing_review=existing_review, has_ordered=has_ordered)


@app.route('/students/meal-reviews/<int:meal_id>')
def meal_reviews(meal_id):
    meal = Meal.query.get_or_404(meal_id)
    reviews = Review.query.filter_by(meal_id=meal_id).join(User).order_by(Review.review_date.desc()).all()
    return render_template("meal_reviews.html", meal=meal, reviews=reviews)


@app.route('/cooks/meals')
def cooks_meals():
    if 'user_type' not in session or session['user_type'] != 'cook':
        return redirect('/')
    meals = Meal.query.order_by(Meal.meal_type, Meal.name).all()
    return render_template("cooks_meals.html", meals=meals)


@app.route('/cooks/meals/edit/<int:meal_id>', methods=['GET', 'POST'])
def edit_meal(meal_id):
    if 'user_type' not in session or session['user_type'] != 'cook':
        return redirect('/')
    meal = Meal.query.get_or_404(meal_id)
    if request.method == 'POST':
        meal.name = request.form['name']
        meal.description = request.form['description']
        meal.price = float(request.form['price'])
        meal.meal_type = request.form['meal_type']
        meal.available = 'available' in request.form
        meal.tags = request.form.get('tags', '')
        meal.ingredients = request.form.get('ingredients', '')
        db.session.commit()
        return redirect('/cooks/meals')
    return render_template("edit_meal.html", meal=meal)


@app.route('/cooks/meals/add', methods=['GET', 'POST'])
def add_meal():
    if 'user_type' not in session or session['user_type'] != 'cook':
        return redirect('/')
    if request.method == 'POST':
        meal = Meal(
            name=request.form['name'],
            description=request.form['description'],
            price=float(request.form['price']),
            meal_type=request.form['meal_type'],
            available='available' in request.form,
            tags=request.form.get('tags', ''),
            ingredients=request.form.get('ingredients', '')
        )
        db.session.add(meal)
        db.session.commit()
        return redirect('/cooks/meals')
    return render_template("add_meal.html")


@app.route('/students')
def students_dashboard():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect('/')
    return render_template("students.html")


@app.route('/students/meals')
def student_meals():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect('/')
    user = User.query.get(session['user_id'])
    all_breakfasts = Meal.query.filter_by(meal_type='breakfast').all()
    all_lunches = Meal.query.filter_by(meal_type='lunch').all()
    breakfasts = []
    lunches = []
    if user.allergies:
        allergies = [a.strip().lower() for a in user.allergies.split(',')]
        for meal in all_breakfasts:
            if meal.available and not any(allergy in meal.ingredients.lower() for allergy in allergies):
                breakfasts.append(meal)
        for meal in all_lunches:
            if meal.available and not any(allergy in meal.ingredients.lower() for allergy in allergies):
                lunches.append(meal)
    else:
        breakfasts = [meal for meal in all_breakfasts if meal.available]
        lunches = [meal for meal in all_lunches if meal.available]
    return render_template("student_meals.html", breakfasts=breakfasts, lunches=lunches, user=user)


@app.route('/students/my-orders')
def my_orders():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect('/')
    orders = Order.query.filter_by(student_id=session['user_id']).join(Meal).order_by(Order.order_date.desc()).all()
    total_spent = sum(order.meal.price * order.quantity for order in orders)
    return render_template("my_orders.html", orders=orders, total_spent=total_spent)


@app.route('/cooks')
def cooks_dashboard():
    if 'user_type' not in session or session['user_type'] != 'cook':
        return redirect('/')

    total_meals = Meal.query.count()
    available_meals = Meal.query.filter_by(available=True).count()
    today_orders = Order.query.filter(db.func.date(Order.order_date) == datetime.utcnow().date()).count()

    user_id = session['user_id']
    purchase_stats = {
        'total': PurchaseRequest.query.filter_by(cook_id=user_id).count(),
        'pending': PurchaseRequest.query.filter_by(cook_id=user_id, status='pending').count(),
        'urgent': PurchaseRequest.query.filter_by(cook_id=user_id, priority='critical', status='pending').count(),
        'approved': PurchaseRequest.query.filter_by(cook_id=user_id, status='approved').count(),
        'completed': PurchaseRequest.query.filter_by(cook_id=user_id, status='completed').count()
    }

    return render_template("cooks.html",
                           total_meals=total_meals,
                           available_meals=available_meals,
                           today_orders=today_orders,
                           purchase_stats=purchase_stats)


@app.route('/admin')
def admin_dashboard():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return redirect('/')

    total_users = User.query.count()
    total_orders = Order.query.count()
    total_reviews = Review.query.count()

    purchase_stats = {
        'total': PurchaseRequest.query.count(),
        'pending': PurchaseRequest.query.filter_by(status='pending').count(),
        'urgent': PurchaseRequest.query.filter_by(priority='critical', status='pending').count(),
        'approved': PurchaseRequest.query.filter_by(status='approved').count(),
        'completed': PurchaseRequest.query.filter_by(status='completed').count()
    }

    return render_template("admin.html",
                           total_users=total_users,
                           total_orders=total_orders,
                           total_reviews=total_reviews,
                           purchase_stats=purchase_stats)


@app.route('/', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        user_type = request.form.get('user_type', '').strip()
        if not email or not password or not user_type:
            return "Пожалуйста, заполните все поля", 400
        if '@' not in email or '.' not in email:
            return "Пожалуйста, введите корректный email", 400
        user = User.query.filter_by(email=email, password=password, user_type=user_type).first()
        if user:
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_type'] = user.user_type
            session['full_name'] = user.full_name
            if user_type == 'student':
                return redirect('/students/meals')
            elif user_type == 'cook':
                return redirect('/cooks')
            elif user_type == 'admin':
                return redirect('/admin')
        else:
            return "Неверные учетные данные или тип пользователя", 401
    else:
        return render_template('base.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        user_type = request.form.get('user_type', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        if not all([full_name, email, user_type, password, confirm_password]):
            return "Пожалуйста, заполните все поля", 400
        if password != confirm_password:
            return "Пароли не совпадают", 400
        if '@' not in email or '.' not in email:
            return "Пожалуйста, введите корректный email", 400
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return "Пользователь с таким email уже существует", 400
        new_user = User(full_name=full_name, email=email, user_type=user_type, password=password)
        try:
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id
            session['user_email'] = new_user.email
            session['user_type'] = new_user.user_type
            session['full_name'] = new_user.full_name
            if user_type == 'student':
                return redirect('/students/meals')
            elif user_type == 'cook':
                return redirect('/cooks')
            elif user_type == 'admin':
                return redirect('/admin')
        except Exception as e:
            db.session.rollback()
            return f"Ошибка: {str(e)}", 500
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/reset-db')
def reset_database():
    if os.path.exists('date.db'):
        os.remove('date.db')
    init_database()
    return "База данных пересоздана успешно! <a href='/'>Перейти к входу</a>"


@app.route('/fix-duplicates')
def fix_duplicates():
    if 'user_type' not in session or session['user_type'] != 'admin':
        return "Доступ запрещен", 403

    all_meals = Meal.query.all()
    unique_meals = {}
    duplicates = []

    for meal in all_meals:
        key = (meal.name, meal.meal_type)
        if key in unique_meals:
            duplicates.append(meal)
        else:
            unique_meals[key] = meal

    for duplicate in duplicates:
        db.session.delete(duplicate)

    db.session.commit()

    return f"Удалено {len(duplicates)} дубликатов. Осталось {Meal.query.count()} уникальных блюд. <a href='/admin'>Вернуться в админку</a>"


init_database()

if __name__ == "__main__":
    app.run(debug=True)