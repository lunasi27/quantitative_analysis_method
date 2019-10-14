from flask import Blueprint, render_template
from app.models.selected_stocks import Select


# 创建蓝图对象
main = Blueprint('main', __name__)


@main.route('/', methods=['GET', 'POST'])
def index():
    select = Select()
    return render_template('select_stocks.html', select=select)
