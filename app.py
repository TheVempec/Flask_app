import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)
app.config['SECRET_KEY'] = 'museum_secret_key_777'

# Налаштування підключення до PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost:5432/Web_app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ==================== МОДЕЛІ БД ====================

class Country(db.Model):
    __tablename__ = 'countries'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    museums_count = db.Column(db.Integer, default=0)

    museums = db.relationship('Museum', backref='country', cascade="all, delete-orphan", lazy=True)


# Нова модель Категорій (Замість звичайного String рядка)
class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    museums = db.relationship('Museum', backref='category', lazy=True)


class Museum(db.Model):
    __tablename__ = 'museums'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    site_url = db.Column(db.String(255), nullable=False)
    image_url = db.Column(db.String(500), nullable=True,
                          default="https://images.unsplash.com/photo-1544816155-12df9643f363")

    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)


# ==================== СТВОРЕННЯ БД ТА ТРИГЕРА ====================

def init_db():
    with app.app_context():
        db.create_all()

        # Створення тригера у PostgreSQL для підрахунку музеїв у країнах
        trigger_sql = """
        CREATE OR REPLACE FUNCTION update_museum_count()
        RETURNS TRIGGER AS $$
        BEGIN
            IF (TG_OP = 'INSERT') THEN
                UPDATE countries SET museums_count = museums_count + 1 WHERE id = NEW.country_id;
            ELSIF (TG_OP = 'DELETE') THEN
                UPDATE countries SET museums_count = museums_count - 1 WHERE id = OLD.country_id;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS trg_museum_count_changes ON museums;
        CREATE TRIGGER trg_museum_count_changes
        AFTER INSERT OR DELETE ON museums
        FOR EACH ROW
        EXECUTE PROCEDURE update_museum_count();
        """

        try:
            with db.engine.begin() as connection:
                connection.execute(text(trigger_sql))
            print("Тригер у PostgreSQL успішно ініціалізовано!")
        except Exception as trigger_err:
            print(f"Попередження при створенні тригера: {trigger_err}")

        # Автоматичне первинне наповнення даними
        if Country.query.first() is None and Category.query.first() is None:
            try:
                # 1. Створюємо країни
                ukraine = Country(name="Україна")
                france = Country(name="Франція")
                uk = Country(name="Велика Британія")
                germany = Country(name="Німеччина")
                usa = Country(name="США")
                pol = Country(name="Польща")

                # 2. Створюємо категорії
                hist = Category(name="Історичний")
                sci = Category(name="Науковий")
                art = Category(name="Художній")
                tech = Category(name="Технічний")
                nature = Category(name="Природничий")

                db.session.add_all([ukraine, france, uk, germany, usa, pol])
                db.session.add_all([hist, sci, art, tech, nature])
                db.session.flush()  # Фіксуємо об'єкти в пам'яті для отримання їхніх ID

                # 3. Створюємо музеї з прив'язкою через ID
                initial_museums = [
                    Museum(
                        name="Національний художній музей України (NAMU)",
                        description="Один з найстаріших і найвидатніших музеїв Києва, який збирає шедеври українського образотворчого мистецтва.",
                        site_url="https://namu.ua/",
                        image_url="https://tickikids.ams3.cdn.digitaloceanspaces.com/z1.cache/gallery/organizations/3739/image_5aa5957e9f4a31.06147467.jpg",
                        country_id=ukraine.id,
                        category_id=art.id
                    ),
                    Museum(
                        name="Національний музей історії України",
                        description="Провідний історичний музей країни. Фонди музею налічують понад 800 тисяч унікальних пам'яток історії та культури.",
                        site_url="https://nmiu.org/",
                        image_url="https://mistokyia.ua/wp-content/uploads/2023/06/nacionalnyj-muzej-istoriyi-ukrayiny-10.jpg",
                        country_id=ukraine.id,
                        category_id=hist.id
                    ),
                    Museum(
                        name="Лувр (Musée du Louvre)",
                        description="Один з найбільших та найвідвідуваніших художніх музеїв світу, розташований у центрі Парижа. Саме тут зберігається 'Мона Ліза'.",
                        site_url="https://www.louvre.fr/en",
                        image_url="https://www.eurofest.org.ua/wp-content/uploads/2026/01/d0bbd183d0b2d180-d0bcd183d0b7d0b5d0b9.webp",
                        country_id=france.id,
                        category_id=art.id
                    ),
                    Museum(
                        name="Британський музей (The British Museum)",
                        description="Головний історико-археологічний музей Великої Британії в Лондоні. Ілюструє історію людської культури.",
                        site_url="https://www.britishmuseum.org/",
                        image_url="https://risu.ua/uploads/1200x670_DIR/media_news/2020/05/5ed1e8a25a92b141096151.jpeg",
                        country_id=uk.id,
                        category_id=hist.id
                    ),
                    Museum(
                        name="Музей природознавства (Natural History Museum)",
                        description="Один із найбільших наукових музеїв світу, відомий унікальною 80-мільйонною колекцією скелетів динозаврів, метеоритів та мінералів.",
                        site_url="https://www.nhm.ac.uk/",
                        image_url="https://trips.com.ua/wp-content/uploads/2022/11/natural-history-museum-of-london.jpg",
                        country_id=uk.id,
                        category_id=nature.id
                    ),
                    Museum(
                        name="Пергамський музей (Pergamonmuseum)",
                        description="Один із найвеличніших музеїв на Музейному острові в Берліні. Відомий реконструкціями масштабних пам'яток античності.",
                        site_url="https://www.smb.museum/en/museums-institutions/pergamonmuseum/home/",
                        image_url="https://www.smb.museum/fileadmin/_processed_/8/e/csm_Pergamon_Simulation_01_xl_bc1b93b4da.jpg",
                        country_id=germany.id,
                        category_id=hist.id
                    ),
                    Museum(
                        name="Національний музей авіації і космонавтики США",
                        description="Володіє найбільшою у світі колекцією літаків і космічних кораблів, включаючи оригінальний апарат братів Райт та модуль місії 'Аполлон-11'.",
                        site_url="https://airandspace.si.edu/",
                        image_url="https://photos.lookatisrael.com/2017/07/11_washington_avia_museum/usa_dc_avia_museum_001_20170711_5D3_0780.jpg",
                        country_id=usa.id,
                        category_id=tech.id
                    ),
                    Museum(
                        name="Центр науки Коперник",
                        description="Тут розміщені понад 450 інтерактивних експонатів, на яких відвідувачі самі проводять експерименти.",
                        site_url="https://www.kopernik.org.pl/",
                        image_url="https://proekt-obk.com/uploads/articles/383a8d7fc6f47353a560a16defbdc885.jpeg",
                        country_id=pol.id,
                        category_id=sci.id
                    )
                ]

                db.session.add_all(initial_museums)
                db.session.commit()
                print("Базу даних успішно наповнено динамічними прикладами!")

            except Exception as e:
                db.session.rollback()
                print(f"Помилка під час наповнення бази даних: {e}")


# ==================== МАРШРУТИ (ROUTES) ====================

@app.route('/', methods=['GET'])
def index():
    countries = Country.query.all()
    categories = Category.query.all()  # Тягнемо категорії з бази даних

    selected_country_id = request.args.get('country')
    selected_category_id = request.args.get('category')  # Фільтрація по ID категорії

    query = Museum.query

    if selected_country_id:
        query = query.filter_by(country_id=selected_country_id)
    if selected_category_id:
        query = query.filter_by(category_id=selected_category_id)

    museums = query.all()

    return render_template('index.html', countries=countries, museums=museums,
                           categories=categories, selected_country=selected_country_id,
                           selected_category=selected_category_id)


@app.route('/museum/<int:museum_id>')
def museum_detail(museum_id):
    museum = Museum.query.get_or_404(museum_id)
    return render_template('detail.html', museum=museum)


@app.route('/museum/create', methods=['GET', 'POST'])
def create_museum():
    countries = Country.query.all()
    categories = Category.query.all()

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        site_url = request.form.get('site_url')
        image_url = request.form.get('image_url')

        new_country_name = request.form.get('new_country')
        country_id = request.form.get('country_id')

        new_category_name = request.form.get('new_category')
        category_id = request.form.get('category_id')

        try:
            # Складна транзакція: крок 1 (динамічне створення країни)
            if new_country_name:
                country = Country.query.filter_by(name=new_country_name).first()
                if not country:
                    country = Country(name=new_country_name)
                    db.session.add(country)
                    db.session.flush()
                country_id = country.id

            # Складна транзакція: крок 2 (динамічне створення категорії)
            if new_category_name:
                category = Category.query.filter_by(name=new_category_name).first()
                if not category:
                    category = Category(name=new_category_name)
                    db.session.add(category)
                    db.session.flush()
                category_id = category.id

            # Крок 3: запис самого музею
            new_museum = Museum(name=name, description=description, site_url=site_url,
                                image_url=image_url, country_id=country_id, category_id=category_id)
            db.session.add(new_museum)
            db.session.commit()

            flash('Дякуємо! Музей та нові категорії успішно збережено в БД.', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback()  # Скасує абсолютно все, якщо хоча б один крок впаде
            flash(f'Помилка створення: {str(e)}', 'danger')
            return redirect(url_for('create_museum'))

    return render_template('form.html', action="Додати", museum=None, countries=countries, categories=categories)


@app.route('/museum/<int:museum_id>/edit', methods=['GET', 'POST'])
def edit_museum(museum_id):
    museum = Museum.query.get_or_404(museum_id)
    countries = Country.query.all()
    categories = Category.query.all()

    if request.method == 'POST':
        new_country_name = request.form.get('new_country')
        country_id = request.form.get('country_id')

        new_category_name = request.form.get('new_category')
        category_id = request.form.get('category_id')

        try:
            # Створення країни «на льоту» при редагуванні
            if new_country_name:
                country = Country.query.filter_by(name=new_country_name).first()
                if not country:
                    country = Country(name=new_country_name)
                    db.session.add(country)
                    db.session.flush()
                country_id = country.id

            # Створення категорії «на льоту» при редагуванні
            if new_category_name:
                category = Category.query.filter_by(name=new_category_name).first()
                if not category:
                    category = Category(name=new_category_name)
                    db.session.add(category)
                    db.session.flush()
                category_id = category.id

            museum.name = request.form.get('name')
            museum.description = request.form.get('description')
            museum.site_url = request.form.get('site_url')
            museum.image_url = request.form.get('image_url')
            museum.country_id = country_id if country_id else museum.country_id
            museum.category_id = category_id if category_id else museum.category_id

            db.session.commit()
            flash('Дані музею успішно оновлено!', 'success')
            return redirect(url_for('museum_detail', museum_id=museum.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Помилка при оновленні: {str(e)}', 'danger')

    return render_template('form.html', action="Редагувати", museum=museum, countries=countries, categories=categories)


@app.route('/museum/<int:museum_id>/delete', methods=['POST'])
def delete_museum(museum_id):
    museum = Museum.query.get_or_404(museum_id)
    try:
        db.session.delete(museum)
        db.session.commit()
        flash('Музей видалено з каталогу.', 'success')
    except:
        db.session.rollback()
        flash('Не вдалося видалити музей.', 'danger')
    return redirect(url_for('index'))


@app.route('/login')
def login():
    return "Сторінка входу (буде створена пізніше)"


@app.route('/register')
def register():
    return "Сторінка реєстрації (буде створена пізніше)"


if __name__ == '__main__':
    init_db()
    app.run(debug=True)