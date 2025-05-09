from flask import Flask, request, render_template
from ldap3 import Server, Connection, ALL, SUBTREE

app = Flask(__name__)

# Configuration
LDAP_SERVER = "ldaps://ldaps-eus2.mykft.net"  # Use LDAPS (LDAP over SSL)
LDAP_BASE_DN = 'DC=MYKFT,DC=NET'
LDAP_USER = 'CN=JSE2367,OU=Contractors,OU=Users,OU=Grocery,DC=MYKFT,DC=NET'
LDAP_PASSWORD = 'ahZbpfLfn9U!Xn4mgmZ4'
LDAP_PORT = 636  # Default port for LDAPS

# LDAP connection setup using ldap3
def get_ldap_connection():
    server = Server(LDAP_SERVER, port=LDAP_PORT, use_ssl=True, get_info=ALL)
    conn = Connection(server, user=LDAP_USER, password=LDAP_PASSWORD, auto_bind=True)
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def lookup():
    server_name = request.form.get('server_name')
    if not server_name:
        return render_template('index.html', error="Server name is required")

    try:
        # Setup LDAP connection
        conn = get_ldap_connection()

        # LDAP search for the server
        search_filter = f"(cn={server_name})"
        conn.search(
            search_base=LDAP_BASE_DN,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=['memberOf']
        )

        if not conn.entries:
            return render_template('index.html', error="Server not found in LDAP")

        # Parse group memberships
        entry = conn.entries[0]
        groups = entry.memberOf.values if 'memberOf' in entry else []

        # Extract only the CN value from each group and remove "_BTHAG" (case-insensitive)
        group_names = []
        for group in groups:
            group_parts = [part.strip() for part in str(group).split(',') if part.strip().startswith("CN=")]
            if group_parts:
                group_name = group_parts[0][3:]  # Remove "CN=" prefix
                group_name = group_name.lower().replace("_bthag", "")  # Convert to lowercase for removal
                group_name = group_name[0].upper() + group_name[1:]  # Preserve original case formatting
                group_names.append(group_name)

        return render_template('index.html', server_name=server_name, groups=group_names)
    except Exception as e:
        return render_template('index.html', error=f"Error: {str(e)}")

@app.route('/group_members', methods=['GET'])
def group_members():
    # Log all query parameters received in the request
    parameters = request.args.to_dict()
    
    group_name = request.args.get('group_name')
    if not group_name:
        return render_template('index.html', error="Group name is required", parameters=parameters)

    try:
        # Setup LDAP connection
        conn = get_ldap_connection()

        # LDAP search for the group members
        search_filter = f"(cn={group_name})"
        conn.search(
            search_base=LDAP_BASE_DN,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=['member']
        )

        if not conn.entries:
            return render_template('index.html', error="Group not found in LDAP", parameters=parameters)

        # Parse the group members
        entry = conn.entries[0]
        members = entry.member.values if 'member' in entry else []


# Extract only the CN value from each group and remove "_BTHAG" (case-insensitive)
        member_names = []
        for member in members:
            member_parts = [part.strip() for part in str(member).split(',') if part.strip().startswith("CN=")]
            if member_parts:
                member_name = member_parts[0][3:].lower()  # Remove "CN=" prefix
                member_names.append(member_name)
        
        member_names.sort()
        
        #member_names = [str(member) for member in members]
        #return render_template('index.html', group_name=group_name, members=member_names, parameters=parameters)
        return render_template('index.html', group_name=group_name, members=member_names)
    except Exception as e:
        #return render_template('index.html', error=f"Error: {str(e)}", parameters=parameters)
        return render_template('index.html', error=f"Error: {str(e)}")


application = app

if __name__ == '__main__':
    app.run(debug=True)

