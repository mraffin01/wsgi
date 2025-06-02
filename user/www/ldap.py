from flask import Flask, request, render_template, g
from ldap3 import Server, Connection, ALL, SUBTREE, ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES
import re

app = Flask(__name__)

# LDAP server details
#LDAP_SERVER = "ldaps://ldaps-eus2.mykft.net"
LDAP_SERVER = "ldaps://eus2papgc003.mykft.net"
SEARCH_BASE = "DC=MYKFT,DC=NET"
LDAP_USER = "CN=JSE2367,OU=Contractors,OU=Users,OU=Grocery,DC=MYKFT,DC=NET"
LDAP_PASSWORD = "ahZbpfLfn9U!Xn4mgmZ4"

def get_ldap_connection():
    """Creates and reuses a persistent LDAP connection for the request lifecycle."""
    if "ldap_conn" not in g:
        server = Server(LDAP_SERVER, get_info=ALL)
        g.ldap_conn = Connection(server, user=LDAP_USER, password=LDAP_PASSWORD, auto_bind=True)
    return g.ldap_conn


@app.teardown_appcontext
def close_ldap_connection(exception=None):
    """Closes the LDAP connection at the end of the request."""
    ldap_conn = g.pop("ldap_conn", None)
    if ldap_conn:
        ldap_conn.unbind()


def extract_cn(memberof_list):
    """Extracts only the CN value from memberOf entries and sorts them."""
    return sorted([match.group(1) for group in memberof_list if (match := re.search(r"CN=([^,]+)", group))])


def ldap_search_by_field(field, value):
    """Search for a user in AD by the selected field and return dictionary results."""
    try:
        if "ldap_cache" not in g:
            g.ldap_cache = {}

        cache_key = f"{field}:{value}"
        if cache_key in g.ldap_cache:
            return g.ldap_cache[cache_key]  # Return cached result

        conn = get_ldap_connection()
        search_filter = f"({field}={value})"

        conn.search(
            search_base= SEARCH_BASE,  # More targeted search base
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=['cn', 'displayName', 'sn', 'mail', 'sAMAccountName', 'distinguishedName', 'uid', 'uidnumber', 'gidnumber', 'memberOf', 'whenCreated','whenChanged',"pwdLastSet", "lastLogon","userPrincipalName", 'manager', 'department','physicalDeliveryOfficeName' ]
            
        )

        if not conn.entries:
            return []  # Return empty list instead of error

        results = [
            {
                attr: entry[attr].value if not isinstance(entry[attr].value, list) else extract_cn(entry[attr].values)
                for attr in entry.entry_attributes if entry[attr].value
            }
            for entry in conn.entries
        ]

        g.ldap_cache[cache_key] = results  # Store in session cache
        return results

    except Exception as e:
        return [{"error": str(e)}]  # Return structured error for UI handling


@app.route('/lookup_user', methods=['GET', 'POST'])
def ldap_search_endpoint():
    if request.method == "POST":
        search_field = request.form.get("search_field")  # Get selected search field
        search_value = request.form.get("search_value")  # Get user input

        if not search_field or not search_value:
            return "Error: Missing search parameters", 400

        results = ldap_search_by_field(search_field, search_value)
        return render_template("search.html", results=results)

    return render_template("search.html", results=None)  # Show empty form on GET


#if __name__ == "__main__":
#  app.run(host="0.0.0.0", port=5000, debug=True)