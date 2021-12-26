
from flask import Flask, render_template, request, url_for, redirect
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_basicauth import BasicAuth
from flask_sqlalchemy import SQLAlchemy
from wtforms import validators
import os

app = Flask(__name__)
app.config['demo'] = os.environ.get('IS_DEMO', True)
app.config['is_production'] = os.environ.get('IS_PRODUCTION', False)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', '0012345679')
app.config['BASIC_AUTH_USERNAME'] = 'sahil'
app.config['BASIC_AUTH_PASSWORD'] = 'shivam'
app.config['FLASK_ADMIN_SWATCH'] = 'darkly'
app.config['BASIC_AUTH_FORCE'] = True

# authentication
basic_auth = BasicAuth(app)

# database init
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', "mysql+pymysql://sahil:sahil@localhost/test")
app.config['SQLALCHEMY_ECHO'] = not (app.config['is_production'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)
engine = db.create_engine(app.config['SQLALCHEMY_DATABASE_URI'], {})


# customs views


class ModelViewProduct(ModelView):
    can_delete = False
    can_view_details = True
    can_export = True
    export_types = ['csv', 'xls']
    column_labels = dict(name='Product Name',
                         description='Product Description')
    column_filters = ['id', 'name', 'description']
    page_size = 20
    column_searchable_list = ['name', 'description']
    column_editable_list = ['name', ]
    form_args = {
        'name': {
            'label': 'Product Name'
        },
        'description': {
            'label': 'Product Description'
        }
    }
    form_widget_args = {
        'description': {
            'rows': 10,
            'style': 'color: black'
        }
    }


class ModelViewLocation(ModelView):
    can_delete = False
    can_view_details = True
    can_export = True
    export_types = ['csv', 'xls']
    column_labels = dict(name='Location Name', other_details='Other Details')
    column_filters = ['id', 'name', 'other_details']
    page_size = 20
    column_searchable_list = ['name', 'other_details']
    column_editable_list = ['name', ]
    form_args = {
        'name': {
            'label': 'Location Name'
        },
        'other_details': {
            'label': 'Other Details'
        }
    }
    form_widget_args = {
        'other_details': {
            'rows': 10,
            'style': 'color: black'
        }
    }


class ModelViewProductSource(ModelView):
    can_delete = False
    can_edit = True
    can_create = True
    column_labels = dict(p_name="Product Name", prod_id="Product ID",
                         prod_name='Product Name', c_name='Company Name')
    column_sortable_list = ('c_name', 'p_name')
    column_default_sort = 'c_id'
    column_searchable_list = ['p_name', 'c_name']
    page_size = 35
    can_export = True
    export_types = ['csv']


class ModelViewProductMovement(ModelView):
    can_delete = False
    can_edit = True
    can_view_details = True
    can_export = True
    export_types = ['csv']
    page_size = 20
    can_set_page_size = True
    column_editable_list = ['qty']

    def on_model_change(self, form, model, is_created):
        if is_created:
            conn = engine.connect()
            trans = conn.begin()
            if not form.from_location.data and not form.to_location.data:
                conn.close()
                raise validators.ValidationError(
                    'Both "From Location" and "To Location" cannot be empty')
            if form.to_location.data:
                select_st = db.text(
                    'SELECT * FROM product_stock WHERE location_id = :l AND product_id = :p')
                res = conn.execute(
                    select_st, p=form.product.data.id, l=form.to_location.data.id)
                row_to = res.fetchone()
                if row_to:
                    q = db.text(
                        'UPDATE product_stock SET available_stock = product_stock.available_stock + (1*:qty) WHERE id = :id')
                    conn.execute(q, qty=form.qty.data, id=row_to.id)
                else:
                    q = db.text(
                        'INSERT INTO product_stock (location_id, product_id, available_stock) VALUES (:l,:p,:qty)')
                    conn.execute(
                        q, qty=form.qty.data, l=form.to_location.data.id, p=form.product.data.id)
            if form.from_location.data:
                select_st = db.text(
                    'SELECT * FROM product_stock WHERE location_id = :l AND product_id = :p')
                res = conn.execute(
                    select_st, p=form.product.data.id, l=form.from_location.data.id)
                row_from = res.fetchone()
                if row_from:
                    if row_from.available_stock < form.qty.data:
                        raise validators.ValidationError(
                            'Stock of "' + form.product.data.name + '" available at "' + form.from_location.data.name + '" is ' + str(row_from.available_stock))
                    q = db.text(
                        'UPDATE product_stock SET available_stock = product_stock.available_stock + (1*:qty) WHERE id = :id')
                    conn.execute(q, qty=-form.qty.data, id=row_from.id)
                else:
                    raise validators.ValidationError(
                        'Zero Stock of "' + form.product.data.name + '" available at "' + form.from_location.data.name + '"')
            trans.commit()
            conn.close()
        else:
            conn = engine.connect()
            trans = conn.begin()
            select_st = db.select([ProductMovement]).where(
                ProductMovement.id == model.list_form_pk)
            res = conn.execute(select_st)
            row = res.fetchone()
            q = db.text(
                'UPDATE product_stock SET available_stock = product_stock.available_stock + (1*:qty) WHERE location_id = :l AND product_id = :p')
            if row.from_location_id:
                select_st = db.text(
                    'SELECT * FROM product_stock WHERE location_id = :l AND product_id = :p')
                res = conn.execute(
                    select_st, p=row.product_id, l=row.from_location_id)
                row_from = res.fetchone()
                if row_from:
                    if row_from.available_stock + (int(row.qty)-int(form.qty.data)) < 0:
                        raise validators.ValidationError(
                            'Insufficient stock at "from_location". Stock available is: ' + str(row_from.available_stock))
                    conn.execute(q, qty=(int(row.qty)-int(form.qty.data)),
                                 l=row.from_location_id, p=row.product_id)
                else:
                    raise validators.ValidationError(
                        'Insufficient stock at "from_location". Stock available is: 0')
            if row.to_location_id:
                select_st = db.text(
                    'SELECT * FROM product_stock WHERE location_id = :l AND product_id = :p')
                res = conn.execute(
                    select_st, p=row.product_id, l=row.to_location_id)
                row_to = res.fetchone()
                if row_to:
                    if (row_to.available_stock + int(form.qty.data)-int(row.qty)) < 0:
                        raise validators.ValidationError(
                            'Insufficient stock at "to_location". Stock available is: ' + str(row_to.available_stock))
                    conn.execute(q, qty=(int(form.qty.data)-int(row.qty)),
                                 l=row.to_location_id, p=row.product_id)
                else:
                    if int(form.qty.data)-int(row.qty) < 0:
                        raise validators.ValidationError(
                            'Insufficient stock at "to_location". Stock available is: 0')
                    q = db.text(
                        'INSERT INTO product_stock (location_id, product_id, available_stock) VALUES (:l,:p,:qty)')
                    conn.execute(
                        q, qty=(int(form.qty.data)-int(row.qty)), l=row.to_location_id, p=row.product_id)
            trans.commit()
            conn.close()


class ModelViewProductStock(ModelView):
    can_delete = False
    can_edit = False
    can_create = False
    column_sortable_list = ('available_stock', )
    column_default_sort = 'product_id'
    page_size = 35
    can_export = True
    export_types = ['csv']

# db model


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.TEXT)

    def __str__(self):
        return "{}".format(self.name)

    def __repr__(self):
        return "{}: {}".format(self.id, self.__str__())


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    other_details = db.Column(db.TEXT)

    def __str__(self):
        return "{}".format(self.name)

    def __repr__(self):
        return "{}: {}".format(self.id, self.__str__())


class Product_Source(db.Model):
    p_id = db.Column(db.Integer, db.ForeignKey(Product.id))
    c_id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    c_name = db.Column(db.String(100), nullable=False)
    p_name = db.Column(db.String(100), db.ForeignKey(Product.name))
    prod_id = db.relationship(Product, foreign_keys=[p_id])
    prod_name = db.relationship(Product, foreign_keys=[p_name])
    db.UniqueConstraint('p_id', 'c_id',
                        name='product_source__id_product_id_uindex')

    def __str__(self):
        return "{}".format(self.name)

    def __repr__(self):
        return "{}: {}".format(self.id, self.__str__())


class ProductMovement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movement_date = db.Column(db.Date)  # , server_default=db.func.now()
    from_location_id = db.Column(db.Integer(), db.ForeignKey(Location.id))
    to_location_id = db.Column(db.Integer(), db.ForeignKey(Location.id))
    product_id = db.Column(
        db.Integer(), db.ForeignKey(Product.id), nullable=False)
    from_location = db.relationship(Location, foreign_keys=[from_location_id])
    to_location = db.relationship(Location, foreign_keys=[to_location_id])
    product = db.relationship(Product, foreign_keys=[product_id])
    qty = db.Column(db.Integer(), db.CheckConstraint(
        'qty >= 0'), nullable=False)

    def __str__(self):
        return "{}".format(self.id)


class ProductStock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey(Location.id))
    product_id = db.Column(db.Integer, db.ForeignKey(Product.id))
    available_stock = db.Column(db.Integer, db.CheckConstraint(
        'available_stock>=0'), nullable=False)
    location = db.relationship(Location, foreign_keys=[location_id])
    product = db.relationship(Product, foreign_keys=[product_id])
    db.UniqueConstraint('location_id', 'product_id',
                        name='product_stock_location_id_product_id_uindex')


# administrative views
admin = Admin(app, name='WareHouse Manager', template_mode='bootstrap3',
              url='/', base_template='admin/custombase.html')
admin.add_view(ModelViewProductMovement(
    ProductMovement, db.session, name='Product Movement'))
admin.add_view(ModelViewProductStock(
    ProductStock, db.session, name='Product Stock'))
admin.add_view(ModelViewProduct(Product, db.session, category="Master"))
admin.add_view(ModelViewLocation(Location, db.session, category="Master"))
admin.add_view(ModelViewProductSource(
    Product_Source, db.session, category="Master"))


@app.route('/favicon.ico')
@basic_auth.required
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))


if __name__ == "__main__":
    # create demo data if demo flag set
    db.create_all()

    # create_demo_data()
    debug = not (app.config['is_production'])
    app.run(debug=debug)
