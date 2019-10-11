from flask import Blueprint, render_template
from app.models.selected_stocks import SelectedStocks


# 创建蓝图对象
main = Blueprint('main', __name__)


@main.route('/', methods=['GET', 'POST'])
def index():
    select = SelectedStocks(sotck='12345', sel_reason='随便')
    select.save()
    return 'Hello world!'
