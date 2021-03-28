import urllib3
import requests
import re

credentials = {"username": "00-010670", "password": "WDD7tves"}
debug = True

session = requests.Session()


def login(session, credentials: dict):
    if debug:
        proxies = {
            'http': 'http://127.0.0.1:8080',
            'https': 'http://127.0.0.1:8080',
        }
        session.proxies.update(proxies)
        session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0"})
        session.verify = False
        urllib3.disable_warnings()

    auth_site = session.get("https://do.sevsu.ru/auth/saml2/login.php",
                            params={"wants": "https://do.sevsu.ru/?",
                                    "idp": "64044bc53c749f0a74e4a4f13b1c0884",
                                    "passive": "off"})

    auth_link_regex = re.compile(r"<form id=\"login-form\" onsubmit=\"login.disabled = true; return true;\" action=\"([^\"]+)\"")
    auth_link = re.search(auth_link_regex, auth_site.content.decode()).group(1)
    auth_link = auth_link.replace("&amp;", "&")  # Replacing url encoded "&"
    login_data = {"username": credentials["username"],
                  "password": credentials["password"],
                  "rememberMe": "on", "credentialId": ""}

    login_response_content = session.post(auth_link, data=login_data).content.decode()
    if re.search(auth_link_regex, login_response_content):
        print(f"Incorrect username or password. -> {credentials['username']}")
        return

    print(f"Successfully logged in. -> {credentials['username']}")
    saml_login_link_regex = re.compile(r"<form name=\"saml-post-binding\" method=\"post\" action=\"([^\"]+)\"")
    saml_login_data_regex = re.compile(r"<input type=\"hidden\" name=\"(\w+)\" value=\"([^\"]+)\"")

    saml_login_link = saml_login_link_regex.search(login_response_content).group(1)
    saml_login_data = {}
    for match in saml_login_data_regex.finditer(login_response_content):
        saml_login_data[match.group(1)] = match.group(2)

    main_page_content = session.post(saml_login_link, data=saml_login_data).content.decode()

    session_key_regex = re.compile(r"\"sesskey\":\"([^\"]+)\"")

    return session_key_regex.search(main_page_content).group(1)


print(login(session, credentials))
print(session.cookies)
# print(session.get("https://do.sevsu.ru/my/").content.decode())