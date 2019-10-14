from .main import main

# 我们使用蓝图来区分不同的url地址族，一般以一个文件为一个地址族
DEFAULT_BLUEPRINT = (
    (main, ''),
)


def init_blueprint(app):
    for blueprint, prefix in DEFAULT_BLUEPRINT:
        app.register_blueprint(blueprint, url_prefix=prefix)
