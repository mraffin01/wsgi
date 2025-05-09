from flask import Flask, request, render_template
import subprocess

application = Flask(__name__, template_folder='/srv/www/wsgi/ns/templates')

@application.route('/', methods=['GET', 'POST'])
def index():
    server_name = request.form.get('server_name', '').lower()
    ping_result = ""
    nslookup_result = ""
    error = ""

    if server_name:
        allowed = (
            server_name.endswith('.mykft.net') or
            server_name.endswith('.kraftheinz.com') or
            server_name.endswith('.kraftfoods.com') or
            server_name.replace('.', '').isdigit()
        )

        if allowed:
            try:
                ping_result = subprocess.check_output(['/usr/bin/ping', '-c', '4', server_name], stderr=subprocess.DEVNULL).decode()
                if server_name.replace('.', '').isdigit():
                    nslookup_result = subprocess.getoutput(f'/usr/bin/dig -x {server_name} +noall +answer')
                else:
                    nslookup_result = subprocess.getoutput(f'/usr/bin/dig {server_name} +noall +answer')
            except subprocess.CalledProcessError:
                ping_result = f"{server_name} not found in DNS"
                nslookup_result = ping_result
        else:
            error = 'Please use only Kraft server names.'
            server_name = ""

    return render_template('index.html', server_name=server_name, ping_result=ping_result, nslookup_result=nslookup_result, error=error)

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=8000)
