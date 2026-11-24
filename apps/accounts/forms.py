from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "用户名或密码不正确，请重试。",
        "inactive": "该账户已停用，请联系管理员。",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "用户名"
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "autofocus": True, "autocomplete": "username"}
        )
        self.fields["password"].label = "密码"
        self.fields["password"].widget.attrs.update(
            {"class": "form-control", "autocomplete": "current-password"}
        )
