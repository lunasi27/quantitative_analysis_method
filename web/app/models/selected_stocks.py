from app.services import db


class SelectedStocks(db.Document):
    sotck = db.StringField()
    sel_reason = db.StringField()
