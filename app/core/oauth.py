from typing import Annotated, Union
from typing_extensions import Doc
from fastapi import Form


class OAuth2EmailRequestForm:
    """
    This is a dependency class to collect the `email` and `password` as form data
    for an OAuth2 password flow.

    The OAuth2 specification dictates that for a password flow the data should be
    collected using form data (instead of JSON) and that it should have the specific
    fields `username` and `password`.

    This custom version replaces the `username` field with `email`, which is common
    in modern applications where the email serves as the unique user identifier.

    All the initialization parameters are extracted from the request.

    Read more about it in the
    [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/).

    ## Example

    ```python
    from typing import Annotated
    from fastapi import Depends, FastAPI
    from your_project.security import OAuth2EmailRequestForm

    app = FastAPI()

    @app.post("/login")
    def login(form_data: Annotated[OAuth2EmailRequestForm, Depends()]):
        data = {}
        data["scopes"] = []
        for scope in form_data.scopes:
            data["scopes"].append(scope)
        if form_data.client_id:
            data["client_id"] = form_data.client_id
        if form_data.client_secret:
            data["client_secret"] = form_data.client_secret
        return data
    ```
    """

    def __init__(
        self,
        *,
        grant_type: Annotated[
            Union[str, None],
            Form(pattern="^password$"),
            Doc("""
                The OAuth2 spec says it is required and MUST be the fixed string
                "password". Nevertheless, this dependency class is permissive and
                allows not passing it. If you want to enforce it, use instead the
                `OAuth2PasswordRequestFormStrict` dependency.
                """),
        ] = None,
        email: Annotated[
            str,
            Form(),
            Doc("""
                `email` string. This field replaces the `username` field from the
                OAuth2 specification, for applications that use email as the login
                identifier.
                """),
        ],
        password: Annotated[
            str,
            Form(json_schema_extra={"format": "password"}),
            Doc("""
                `password` string. The OAuth2 spec requires the exact field name
                `password`.
                """),
        ],
        scope: Annotated[
            str,
            Form(),
            Doc("""
                A single string with actually several scopes separated by spaces. Each
                scope is also a string.

                For example, a single string with:

                ```python
                "items:read items:write users:read profile openid"
                ````

                would represent the scopes:

                * `items:read`
                * `items:write`
                * `users:read`
                * `profile`
                * `openid`
                """),
        ] = "",
        client_id: Annotated[
            Union[str, None],
            Form(),
            Doc("""
                If there's a `client_id`, it can be sent as part of the form fields.
                But the OAuth2 specification recommends sending the `client_id` and
                `client_secret` (if any) using HTTP Basic auth.
                """),
        ] = None,
        client_secret: Annotated[
            Union[str, None],
            Form(json_schema_extra={"format": "password"}),
            Doc("""
                If there's a `client_password` (and a `client_id`), they can be sent
                as part of the form fields. But the OAuth2 specification recommends
                sending the `client_id` and `client_secret` (if any) using HTTP Basic
                auth.
                """),
        ] = None,
    ):
        self.grant_type = grant_type
        self.email = email
        self.password = password
        self.scopes = scope.split()
        self.client_id = client_id
        self.client_secret = client_secret
